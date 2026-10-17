import os
from pathlib import Path

from llm_client import query_local_llm, CODER_MODEL

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent / "workspace"

STYLE = {
    "python": "PEP 8. Implementation in src/, tests in tests/ named *_test.py using unittest. Import as `from src.module import ...`.",
    "javascript": "camelCase. Implementation in lib/ (CommonJS), tests in tests/ named *.test.js using node:test and node:assert.",
    "go": "Idiomatic Go. Include a go.mod, implementation in the root package, tests in *_test.go.",
}


def workspace_for(state) -> Path:
    return WORKSPACE_ROOT / state["project_name"]


def parse_file_blocks(text: str) -> dict:
    """Parses '=== FILE: path ===' blocks into {relative_path: content}."""
    files, current, buf = {}, None, []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("=== FILE:") or stripped.startswith("FILE:"):
            if current and buf:
                files[current] = "\n".join(buf).strip() + "\n"
            current = stripped.replace("=== FILE:", "").replace("FILE:", "").replace("===", "").strip()
            buf = []
        elif current is not None and not stripped.startswith("```"):
            buf.append(line)
    if current and buf:
        files[current] = "\n".join(buf).strip() + "\n"
    return files


def write_files(root: Path, files: dict) -> dict:
    """Writes files inside root only; rejects absolute or escaping paths."""
    root.mkdir(parents=True, exist_ok=True)
    written = {}
    for rel, content in files.items():
        target = (root / rel).resolve()
        if not rel or Path(rel).is_absolute() or root.resolve() not in target.parents:
            print(f"⚠️ Skipping unsafe path from model output: {rel!r}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written[rel] = content
    return written


def ensure_python_packages(root: Path) -> None:
    """unittest discovery needs __init__.py in every directory that holds Python files."""
    for dirpath, _, filenames in os.walk(root):
        if ".venv" in dirpath or "__pycache__" in dirpath:
            continue
        if any(f.endswith(".py") for f in filenames):
            init = Path(dirpath) / "__init__.py"
            if not init.exists():
                init.write_text("", encoding="utf-8")


def run_coding_agent(state):
    attempt = state.get("repair_attempts", 0) + 1
    print(f"💻 [Coder] Implementation pass {attempt}...")
    lang = state["target_lang"]
    style = STYLE.get(lang.lower(), "Follow the idiomatic conventions of the language.")

    fix_block = ""
    if state.get("bug_list"):
        bugs = "\n".join(f"- {b.get('summary', b)}" for b in state["bug_list"])
        existing = "\n\n".join(f"=== FILE: {p} ===\n{c}" for p, c in state.get("source_code", {}).items())
        fix_block = f"""
The previous attempt FAILED QA. Fix these problems and return the COMPLETE corrected files.

QA findings:
{bugs}

Current files:
{existing}
"""

    prompt = f"""You are a TDD software engineer writing {lang}.
Conventions: {style}

Task: {state["current_task"].get("title")} - {state["current_task"].get("description")}

Specifications:
{state["functional_specs"]}

Acceptance criteria (each needs a unit test):
{state["tdd_criteria"]}

Security standards:
{state["security_standards"]}
{fix_block}
Output format - for every file emit exactly:
=== FILE: relative/path/to/file ===
<file content>

Include both the implementation and its unit tests. Use mocks/in-memory fakes; no network or real databases.
Output only file blocks, no commentary.
"""
    raw = query_local_llm(CODER_MODEL, prompt)
    files = parse_file_blocks(raw)
    root = workspace_for(state)
    written = write_files(root, files)
    if lang.lower() == "python":
        ensure_python_packages(root)
    print(f"   -> wrote {len(written)} file(s) to {root}")
    return {"source_code": written, "repair_attempts": attempt}
