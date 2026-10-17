"""Guards against broken Python files being committed.

Every .py file in the repository must at least compile. This catches truncated LLM output and
markdown-fenced files, which previously went unnoticed.

Run from the repository root:
    python3 -m unittest discover -s tests -p "*_test.py"
"""
import os
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "workspace", "MemoryStore"}


def python_files():
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith("sonarqube-")]
        for name in filenames:
            if name.endswith(".py"):
                yield Path(dirpath) / name


class EveryPythonFileCompiles(unittest.TestCase):
    def test_all_python_files_compile(self):
        failures = []
        for path in sorted(python_files()):
            try:
                # compile() builtin: parses without writing any .pyc files
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
            except SyntaxError as e:
                failures.append(f"{path.relative_to(REPO_ROOT)}: line {e.lineno}: {e.msg}")
        self.assertEqual(failures, [], "These files do not compile:\n  " + "\n  ".join(failures))


if __name__ == "__main__":
    unittest.main()
