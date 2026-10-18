"""council_engine.py - one reusable "council" step: draft, blind critique, chairman synthesis.

Until now this pattern only existed inside standalone scripts (council.py, ProductOwner.py,
code_quality_system.py). `deliberate()` makes it available to any agent node.

    result = deliberate(
        task="Write the functional specification for ...",
        drafters=["llama3.1:8b", "mistral:7b"],
        chairman="llama3.1:8b",
    )
    result["final"]
"""
from typing import Any, Callable, Dict, List

from llm_client import query_local_llm

TRUNCATION_MARKER = "\n[...truncated]"
NO_CRITIQUE = "(no critique available)"

# Roughly 5k tokens. Beyond this a chairman prompt may overflow an 8k context window, and Ollama
# then drops part of the prompt silently.
CHAIRMAN_PROMPT_WARN_CHARS = 20000


def truncate(text: str, limit: int) -> str:
    """Cuts text to at most `limit` characters, ending with a visible marker when it was cut."""
    if len(text) <= limit:
        return text
    keep = limit - len(TRUNCATION_MARKER)
    if keep <= 0:
        return text[:limit]
    return text[:keep] + TRUNCATION_MARKER


def _ask(llm: Callable[[str, str], str], model: str, prompt: str) -> str:
    """One model call. An empty reply is retried once; empty twice raises RuntimeError."""
    reply = llm(model, prompt)
    if not (reply or "").strip():
        reply = llm(model, prompt)
    if not (reply or "").strip():
        raise RuntimeError(f"{model} returned empty output twice")
    return reply.strip()


def _critique_prompt(task: str, draft: str) -> str:
    # Deliberately says nothing about who wrote the draft (blind review).
    return (
        "You are reviewing a colleague's answer to the task below. You do not know who wrote it. "
        "List its flaws, omissions and errors concisely. Do not rewrite the answer.\n\n"
        f"[TASK]\n{task}\n[END TASK]\n\n"
        f"[ANSWER]\n{draft}\n[END ANSWER]\n"
    )


def _chairman_prompt(task: str, drafts: List[str], critiques: List[str]) -> str:
    sections = []
    for i, draft in enumerate(drafts, 1):
        critique = critiques[i - 1] or NO_CRITIQUE
        sections.append(
            f"[DRAFT {i}]\n{draft}\n[END DRAFT {i}]\n\n"
            f"[CRITIQUE OF DRAFT {i}]\n{critique}\n[END CRITIQUE OF DRAFT {i}]"
        )
    return (
        "You are the Council Chairman. Several council members each drafted an answer to the task "
        "below, and each draft was critiqued by a peer. Produce the single best final answer: keep "
        "what is correct, apply the valid critique points, and fix errors and gaps. Follow any output "
        "format the task requires exactly, and output only the final answer, with no commentary about "
        "the drafts or the critiques.\n\n"
        f"[TASK]\n{task}\n[END TASK]\n\n" + "\n\n".join(sections) + "\n"
    )


def deliberate(task: str, drafters: List[str], chairman: str,
               llm: Callable[[str, str], str] = query_local_llm,
               max_section_chars: int = 6000,
               log: Callable[[str], None] = print) -> Dict[str, Any]:
    """Runs one council round and returns
    {"final": str, "drafts": [str], "critiques": [str], "errors": [str]}.

    1. Each drafter answers `task` (sent unchanged).
    2. Each draft is critiqued, blind, by the next drafter in the ring: draft i by drafter
       (i + 1) % n. If a drafter failed, the ring is formed from the drafters that succeeded.
       With a single drafter it critiques its own draft.
    3. The chairman reads the task, every draft and every critique and writes `final`.

    Calls are sequential (drafts, then critiques, then the chairman), which suits keep_alive=0
    on a machine that cannot hold every model in memory.

    Robustness:
    - A drafter that raises RuntimeError (llm_client's error type), or returns empty output twice,
      is skipped and noted in "errors". If every drafter fails, RuntimeError is raised.
    - A failed critique is recorded as "" in "critiques" and noted in "errors".
    - An empty reply is retried once before counting as a failure.
    - Each draft and critique is truncated to `max_section_chars` before any later prompt, and
      the returned lists hold the truncated text. `final` is never truncated.
    - A failing chairman raises RuntimeError: there is no honest final answer without one.
    - Other exceptions (programming errors) are not swallowed.
    """
    if not task.strip():
        raise ValueError("task must not be blank")
    if not drafters or any(not str(d).strip() for d in drafters):
        raise ValueError("drafters must be a non-empty list of model names")
    if not chairman.strip():
        raise ValueError("chairman must be a model name")
    if max_section_chars <= 0:
        raise ValueError("max_section_chars must be positive")

    errors: List[str] = []

    # Stage 1: independent drafts
    drafts: List[str] = []
    authors: List[str] = []
    for i, model in enumerate(drafters, 1):
        log(f"📝 [Council] Draft {i}/{len(drafters)} by {model}...")
        try:
            text = _ask(llm, model, task)
        except RuntimeError as e:
            errors.append(f"draft by {model} failed: {e}")
            log(f"⚠️ [Council] {model} could not draft, continuing without it: {e}")
            continue
        drafts.append(truncate(text, max_section_chars))
        authors.append(model)
    if not drafts:
        raise RuntimeError("every drafter failed: " + "; ".join(errors))

    # Stage 2: blind peer critiques, in a ring over the surviving drafters
    critiques: List[str] = []
    for k, draft in enumerate(drafts):
        critic = authors[(k + 1) % len(authors)]
        log(f"🔍 [Council] Critique of draft {k + 1}/{len(drafts)} by {critic}...")
        try:
            text = _ask(llm, critic, _critique_prompt(task, draft))
        except RuntimeError as e:
            errors.append(f"critique of draft {k + 1} by {critic} failed: {e}")
            log(f"⚠️ [Council] {critic} could not critique draft {k + 1}, continuing: {e}")
            critiques.append("")
            continue
        critiques.append(truncate(text, max_section_chars))

    # Stage 3: chairman synthesis
    prompt = _chairman_prompt(task, drafts, critiques)
    if len(prompt) > CHAIRMAN_PROMPT_WARN_CHARS:
        log(f"⚠️ [Council] Warning: the chairman prompt is {len(prompt)} characters "
            f"(over {CHAIRMAN_PROMPT_WARN_CHARS}) and may not fit the context window. "
            "Lower max_section_chars or use fewer drafters.")
    log(f"👑 [Council] Synthesis by chairman {chairman}...")
    final = _ask(llm, chairman, prompt)

    return {"final": final, "drafts": drafts, "critiques": critiques, "errors": errors}
