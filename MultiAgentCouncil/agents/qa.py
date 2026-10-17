import os
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
