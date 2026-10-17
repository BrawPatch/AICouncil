#!/usr/bin/env python3
"""CouncilBuilder.py.

Automated deployment bootstrap builder for the Multi-Agent Council.
Natively structures, maps, and writes out all modular file components.
"""

import os
import sys
from pathlib import Path


def get_state_schema_content() -> str:
    """Returns the code content for state_schema.py."""
    lines = [
        "from typing import TypedDict, List, Dict, Any, Literal",
        "",
        "class CouncilState(TypedDict):",
        "    project_name: str",
        "    target_lang: str",
        "    raw_user_story: str",
        "    historical_memory: str",
        "    functional_specs: str",
        "    tdd_criteria: str",
        "    security_standards: str",
        "    backlog: List[Dict[str, Any]]",
        "    current_task: Dict[str, Any]",
        "    source_code: Dict[str, str]",
        "    test_results: Dict[str, Any]",
        "    bug_list: List[Dict[str, Any]]",
        "    release_environment: Literal['dev', 'test', 'production']",
        "    promotion_approved: bool",
        "    repair_attempts: int",
    ]
    return "\n".join(lines)


def get_memory_manager_content() -> str:
    """Returns the code content for memory_manager.py."""
    lines = [
        "from pathlib import Path",
        "from datetime import datetime",
        "",
        "BASE_DIR = Path(__file__).resolve().parent",
        "MEMORY_STORE_DIR = BASE_DIR / 'MemoryStore'",
        "CONTEXT_FILE = MEMORY_STORE_DIR / 'Context.md'",
        "HISTORY_FILE = MEMORY_STORE_DIR / 'ChatHistory.md'",
        "",
        "MEMORY_STORE_DIR.mkdir(parents=True, exist_ok=True)",
        "",
        "",
        "def load_historical_memory() -> str:",
        "    memory_blocks = []",
        "    if CONTEXT_FILE.exists():",
        "        try:",
        "            with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:",
        "                memory_blocks.append(f'### [HISTORICAL GLOBAL CONTEXT]\\n{f.read()}')",
        "        except Exception as e:",
        "            print(f'⚠️ Error reading global context file: {e}')",
        "            ",
        "    if HISTORY_FILE.exists():",
        "        try:",
        "            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:",
        "                history_data = f.read()",
        "                tail_lines = history_data.split('\\n')[-100:]",
        "                memory_blocks.append(f'### [RECENT CHAT HISTORY RECORDS]\\n...\\n' + '\\n'.join(tail_lines))",
        "        except Exception as e:",
        "            print(f'⚠️ Error reading execution history logs: {e}')",
        "            ",
        "    return '\\n\\n'.join(memory_blocks) if memory_blocks else 'No historical memory discovered.'",
        "",
        "",
        "def persist_session_knowledge(project_name: str, raw_story: str, specs: str, approved: bool):",
        "    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')",
        "    status_str = 'APPROVED & DEPLOYED' if approved else 'PAUSED / REJECTED'",
        "    ",
        "    context_markdown = (",
        "        f'# System Operational Context Snapshot\\n'",
        "        f'- **Last Active Project:** `{project_name}`\\n'",
        "        f'- **Last Analyzed Timestamp:** {timestamp}\\n'",
        "        f'- **Status Gate Result:** `{status_str}`\\n\\n'",
        "        f'## Active Technical Specification Matrix\\n{specs}\\n'",
        "    )",
        "    ",
        "    try:",
        "        with open(CONTEXT_FILE, 'w', encoding='utf-8') as f:",
        "            f.write(context_markdown.strip() + '\\n')",
        "        print(f'💾 Global state snapshot written to: {CONTEXT_FILE}')",
        "    except Exception as e:",
        "        print(f'❌ Failed to persist context file: {e}')",
        "",
        "    promo_str = 'PASSED' if approved else 'FAILED / HALTED'",
        "    history_entry = (",
        "        f'\\n## Session Audit Entry: {timestamp}\\n'",
        "        f'- **Target Project Workspace:** `{project_name}`\\n'",
        "        f'- **Source Input Story Card:** \\\"{raw_story}\\\"\\n'",
        "        f'- **Quality Promotion Gate Sign-Off:** `{promo_str}`\\n'",
        "        f'---\\n'",
        "    )",
        "    ",
        "    try:",
        "        if not HISTORY_FILE.exists():",
        "            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:",
        "                f.write('# Chat Session Execution History Logs\\nAll pipeline run history is logged here automatically.\\n')",
        "        with open(HISTORY_FILE, 'a', encoding='utf-8') as f:",
        "            f.write(history_entry)",
        "        print(f'📝 Incremental run logging entry appended to: {HISTORY_FILE}')",
        "    except Exception as e:",
        "        print(f'❌ Failed to append log entry: {e}')",
    ]
    return "\n".join(lines)


def get_orchestrator_content() -> str:
    """Returns the code content for orchestrator.py."""
    lines = [
        "import sys",
        "from langgraph.graph import StateGraph, END",
        "",
        "from state_schema import CouncilState",
        "from memory_manager import load_historical_memory, persist_session_knowledge",
        "",
        "from agents.requirements import run_requirements_agent",
        "from agents.security import run_security_agent",
        "from agents.scrum_master import run_scrum_master_agent",
        "from agents.coder import run_coding_agent",
        "from agents.qa import run_qa_agent",
        "from agents.promotion import run_promotion_agent",
        "",
        "workflow = StateGraph(CouncilState)",
        "",
        "workflow.add_node('requirements_refiner', run_requirements_agent)",
        "workflow.add_node('security_hardening', run_security_agent)",
        "workflow.add_node('scrum_master', run_scrum_master_agent)",
        "workflow.add_node('coder', run_coding_agent)",
        "workflow.add_node('qa_validator', run_qa_agent)",
        "workflow.add_node('promotion_gate', run_promotion_agent)",
        "",
        "workflow.set_entry_point('requirements_refiner')",
        "workflow.add_edge('requirements_refiner', 'security_hardening')",
        "workflow.add_edge('security_hardening', 'scrum_master')",
        "workflow.add_edge('scrum_master', 'coder')",
        "workflow.add_edge('coder', 'qa_validator')",
        "",
        "",
        "MAX_REPAIR_ATTEMPTS = 5",
        "",
        "",
        "def route_qa_verdict(state: CouncilState):",
        "    status = state.get('test_results', {}).get('status', 'FAIL')",
        "    if status != 'FAIL':",
        "        return 'promotion_gate'",
        "    if state.get('repair_attempts', 0) >= MAX_REPAIR_ATTEMPTS:",
        "        print('🛑 Repair attempts exhausted. Sending failing build to the promotion gate for rejection.')",
        "        return 'promotion_gate'",
        "    print('⚠️ QA validation suite failed. Routing back to coder.')",
        "    return 'coder'",
        "",
        "",
        "workflow.add_conditional_edges(",
        "    'qa_validator',",
        "    route_qa_verdict,",
        "    {",
        "        'coder': 'coder',",
        "        'promotion_gate': 'promotion_gate'",
        "    }",
        ")",
        "workflow.add_edge('promotion_gate', END)",
        "",
        "app = workflow.compile()",
        "",
        "",
        "def start_execution_harness():",
        "    loaded_memory = load_historical_memory()",
        "    print('📖 Loaded global context files from storage ecosystem successfully.')",
        "",
        "    print('\\n💬 --- Welcome to the Agile Council Configuration Matrix ---')",
        "    user_story = input('⌨️ Provide input User Story: ').strip()",
        "    if not user_story:",
        "        user_story = 'As a Customer, I want to securely pay via an API endpoint, so that my account credentials remain encrypted.'",
        "    ",
        "    lang_stack = input('⌨️ Choose target language [Python/JavaScript/Go] (Default: Python): ').strip()",
        "    if not lang_stack:",
        "        lang_stack = 'Python'",
        "",
        "    initial_input: CouncilState = {",
        "        'project_name': 'modular_billing_system',",
        "        'target_lang': lang_stack,",
        "        'raw_user_story': user_story,",
        "        'historical_memory': loaded_memory,",
        "        'functional_specs': '',",
        "        'tdd_criteria': '',",
        "        'security_standards': '',",
        "        'backlog': [],",
        "        'current_task': {},",
        "        'source_code': {},",
        "        'test_results': {},",
        "        'bug_list': [],",
        "        'release_environment': 'dev',",
        "        'promotion_approved': False,",
        "        'repair_attempts': 0",
        "    }",
        "    ",
        "    print('\\n🚀 Triggering modular state workflow engine...')",
        "    final_output = app.invoke(initial_input, {'recursion_limit': 60})",
        "    ",
        "    persist_session_knowledge(",
        "        project_name=final_output['project_name'],",
        "        raw_story=final_output['raw_user_story'],",
        "        specs=final_output['functional_specs'],",
        "        approved=final_output['promotion_approved']",
        "    )",
        "    print('\\n[✨ Success] Execution finished cleanly.')",
        "",
        "",
        "if __name__ == '__main__':",
        "    start_execution_harness()",
    ]
    return "\n".join(lines)

def get_start_council_content() -> str:
    """Returns the code content for StartCouncil.py."""
    return r'''#!/usr/bin/env python3
"""StartCouncil.py - environment sanity checks, then launches the orchestrator."""
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

REQUIRED_MODELS = ["llama3.1:8b", "mistral:7b", "qwen2.5-coder:7b"]
REQUIRED_PACKAGES = ["langgraph"]
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"


def venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def check_ollama() -> None:
    try:
        with urllib.request.urlopen(OLLAMA_TAGS_URL, timeout=5) as resp:
            installed = {m["name"] for m in json.loads(resp.read().decode("utf-8")).get("models", [])}
    except Exception as e:
        print(f"❌ Ollama is not reachable at {OLLAMA_TAGS_URL}: {e}")
        print("   Start it first (e.g. `OLLAMA_KEEP_ALIVE=0s ollama serve`).")
        sys.exit(1)

    missing = [m for m in REQUIRED_MODELS if m not in installed]
    if missing:
        print("❌ Missing Ollama models: " + ", ".join(missing))
        for m in missing:
            print(f"   ollama pull {m}")
        sys.exit(1)
    print("✔ Ollama is running and all council models are installed.")


def run_environment_sanity_checks() -> Path:
    print("==============================================================")
    print(" ⚡ StartCouncil: Initializing local Multi-Agent Framework...")
    print("==============================================================")

    base_dir = Path(__file__).resolve().parent
    venv_dir = base_dir / ".venv"

    if not venv_dir.exists():
        print("[*] Creating virtual environment (.venv)...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    py = venv_python(venv_dir)
    for pkg in REQUIRED_PACKAGES:
        probe = subprocess.run([str(py), "-c", f"import {pkg}"], capture_output=True)
        if probe.returncode != 0:
            print(f"[*] Installing {pkg}...")
            subprocess.run([str(py), "-m", "pip", "install", "--upgrade", pkg], check=True)

    check_ollama()
    return py


def main() -> None:
    py = run_environment_sanity_checks()
    base_dir = Path(__file__).resolve().parent
    env = dict(os.environ, OLLAMA_KEEP_ALIVE="0s")
    print("\n🚀 Launching orchestrator...\n")
    result = subprocess.run([str(py), str(base_dir / "orchestrator.py")], cwd=str(base_dir), env=env)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
'''


def get_llm_client_content() -> str:
    """Returns the code content for llm_client.py."""
    return r'''import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"

CHAIRMAN_MODEL = "llama3.1:8b"   # Scrum Master / synthesizer / router
SECURITY_MODEL = "mistral:7b"    # Security craftsman / deep logic
CODER_MODEL = "qwen2.5-coder:7b"  # TDD software engineer


def query_local_llm(model_name: str, prompt: str, timeout: int = 600) -> str:
    """Calls Ollama. keep_alive=0 unloads the model straight after the call (memory budget)."""
    payload = {"model": model_name, "prompt": prompt, "stream": False, "keep_alive": 0}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))["response"]
    except Exception as e:
        raise RuntimeError(f"Ollama call failed for model '{model_name}': {e}") from e
'''


def get_requirements_agent_content() -> str:
    """Returns the code content for agents/requirements.py."""
    return r'''from llm_client import query_local_llm, CHAIRMAN_MODEL


def run_requirements_agent(state):
    print("📝 [Requirements Refiner] Expanding the user story into specs...")
    story = state["raw_user_story"]
    lang = state["target_lang"]
    memory = state.get("historical_memory", "")

    specs = query_local_llm(CHAIRMAN_MODEL, f"""You are a business analyst. Turn this user story into concise
functional specifications for a {lang} implementation. Use short bullet points only.

User story: {story}

Prior project context (may be empty):
{memory}
""")
    criteria = query_local_llm(CHAIRMAN_MODEL, f"""Write TDD acceptance criteria for these specifications as a
numbered list of testable Given/When/Then statements.

{specs}
""")
    return {"functional_specs": specs, "tdd_criteria": criteria}
'''


def get_security_agent_content() -> str:
    """Returns the code content for agents/security.py."""
    return r'''from llm_client import query_local_llm, SECURITY_MODEL


def run_security_agent(state):
    print("🔐 [Security Hardening] Defining security standards...")
    standards = query_local_llm(SECURITY_MODEL, f"""You are an application security engineer. For the specification
below, list the concrete security requirements the implementation must meet (input validation, secrets handling,
authentication, error handling, injection, logging). Be specific and brief.

{state["functional_specs"]}
""")
    return {"security_standards": standards}
'''


def get_scrum_master_agent_content() -> str:
    """Returns the code content for agents/scrum_master.py."""
    return r'''import json
import re

from llm_client import query_local_llm, CHAIRMAN_MODEL


def _parse_tasks(raw: str):
    """Extracts a JSON array of tasks from an LLM reply, tolerating code fences and chatter."""
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        return []
    try:
        tasks = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    return [t for t in tasks if isinstance(t, dict) and t.get("title")]


def run_scrum_master_agent(state):
    print("📋 [Scrum Master] Building the backlog...")
    raw = query_local_llm(CHAIRMAN_MODEL, f"""You are a Scrum Master. Break the work below into 1 to 3 small,
independently testable tasks. Reply with ONLY a JSON array; each item has the keys "title" and "description".

Specifications:
{state["functional_specs"]}

Acceptance criteria:
{state["tdd_criteria"]}
""")
    backlog = _parse_tasks(raw)
    if not backlog:
        backlog = [{"title": "Implement user story", "description": state["raw_user_story"]}]
    return {"backlog": backlog, "current_task": backlog[0], "repair_attempts": 0}
'''


def get_coder_agent_content() -> str:
    """Returns the code content for agents/coder.py."""
    return r'''import os
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
'''


def get_qa_agent_content() -> str:
    """Returns the code content for agents/qa.py."""
    return r'''import os
import subprocess
import sys
from pathlib import Path

from agents.coder import workspace_for


def _test_command(lang: str, root: Path):
    lang = lang.lower()
    if lang == "python":
        return [sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "*_test.py", "-t", "."]
    if lang == "javascript":
        return ["node", "--test"]
    if lang == "go":
        if not (root / "go.mod").exists():
            subprocess.run(["go", "mod", "init", "councilproject"], cwd=str(root), capture_output=True)
        return ["go", "test", "./..."]
    return None


def run_qa_agent(state):
    print("🧪 [QA Validator] Running the test suite...")
    root = workspace_for(state)
    cmd = _test_command(state["target_lang"], root)

    if not state.get("source_code"):
        return _fail("The coder produced no files. Return the implementation and tests as === FILE: path === blocks.")
    if cmd is None:
        return _fail(f"No test runner configured for language '{state['target_lang']}'.")

    env = dict(os.environ, PYTHONPATH=str(root), PYTHONDONTWRITEBYTECODE="1")  # avoid stale .pyc on rapid rewrites
    try:
        result = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=60, env=env)
    except FileNotFoundError as e:
        return _fail(f"Test runner not installed: {e}")
    except subprocess.TimeoutExpired:
        return _fail("Test run timed out after 60 seconds (possible infinite loop or blocking call).")

    logs = (result.stdout + "\n" + result.stderr).strip()
    if result.returncode == 0:
        print("   ✔ All tests passed.")
        return {"test_results": {"status": "PASS", "logs": logs}, "bug_list": []}
    print("   ✘ Tests failed.")
    return _fail(logs[-3000:], logs)


def _fail(summary: str, logs: str = ""):
    return {
        "test_results": {"status": "FAIL", "logs": logs or summary},
        "bug_list": [{"summary": summary}],
    }
'''


def get_promotion_agent_content() -> str:
    """Returns the code content for agents/promotion.py."""
    return r'''def run_promotion_agent(state):
    passed = state.get("test_results", {}).get("status") == "PASS"
    if passed:
        print("✅ [Promotion Gate] Quality gate passed. Build approved.")
    else:
        print("⛔ [Promotion Gate] Quality gate failed. Promotion rejected.")
    return {"promotion_approved": passed, "release_environment": "dev"}
'''


def build_council(target_dir: Path) -> None:
    """Writes every generated module into target_dir."""
    files = {
        "state_schema.py": get_state_schema_content(),
        "memory_manager.py": get_memory_manager_content(),
        "orchestrator.py": get_orchestrator_content(),
        "StartCouncil.py": get_start_council_content(),
        "llm_client.py": get_llm_client_content(),
        "agents/__init__.py": "",
        "agents/requirements.py": get_requirements_agent_content(),
        "agents/security.py": get_security_agent_content(),
        "agents/scrum_master.py": get_scrum_master_agent_content(),
        "agents/coder.py": get_coder_agent_content(),
        "agents/qa.py": get_qa_agent_content(),
        "agents/promotion.py": get_promotion_agent_content(),
    }
    target_dir.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        path = target_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip("\n") + "\n" if content else "", encoding="utf-8")
        print(f"  ✔ wrote {path}")
    start = target_dir / "StartCouncil.py"
    start.chmod(start.stat().st_mode | 0o111)


def main() -> None:
    target = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path.cwd() / "MultiAgentCouncil"
    print(f"🏗️  Building Multi-Agent Council into: {target}")
    build_council(target)
    print(f"\n✨ Done. Next: cd {target} && python3 StartCouncil.py")


if __name__ == "__main__":
    main()
