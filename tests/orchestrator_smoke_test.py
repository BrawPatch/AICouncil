"""End-to-end smoke test of the LangGraph pipeline with a stubbed LLM (no Ollama needed).

Skipped when langgraph is not installed. Workspaces and memory files go to a temp directory.
"""
import builtins
import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _paths  # noqa: F401

HAS_LANGGRAPH = importlib.util.find_spec("langgraph") is not None

STORY = "As a user I want to add two numbers."
IMPLEMENTATION = "=== FILE: src/calc.py ===\ndef add(a, b):\n    return a + b\n"
TESTS = (
    "=== FILE: tests/calc_test.py ===\n"
    "import unittest\n"
    "from src.calc import add\n\n"
    "class AddTest(unittest.TestCase):\n"
    "    def test_add(self):\n"
    "        self.assertEqual(add(1, 2), 3)\n\n"
    "if __name__ == '__main__':\n"
    "    unittest.main()\n"
)


@unittest.skipUnless(HAS_LANGGRAPH, "langgraph is not installed")
class NonInteractiveRunTest(unittest.TestCase):
    def setUp(self):
        import agents.coder
        import agents.requirements
        import agents.scrum_master
        import agents.security
        import memory_manager
        import orchestrator

        self.orchestrator = orchestrator
        self.llm_calls = []

        def stub(model, prompt):
            self.llm_calls.append(model)
            if "business analyst" in prompt:
                return "- add two numbers\n"
            if "Given/When/Then" in prompt:
                return "1. Given 1 and 2 When added Then 3\n"
            if "application security engineer" in prompt:
                return "- validate input\n"
            if "Scrum Master" in prompt:
                return '[{"title": "Add", "description": "Implement add(a, b)"}]'
            return IMPLEMENTATION + "\n" + TESTS

        tmp = Path(tempfile.mkdtemp(prefix="council-smoke-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))
        self.workspace_root = tmp / "workspace"
        store = tmp / "MemoryStore"
        store.mkdir()
        self.store = store

        for module in (agents.requirements, agents.security, agents.scrum_master, agents.coder):
            patcher = mock.patch.object(module, "query_local_llm", stub)
            patcher.start()
            self.addCleanup(patcher.stop)
        for target, value in (
            (agents.coder, ("WORKSPACE_ROOT", self.workspace_root)),
            (memory_manager, ("MEMORY_STORE_DIR", store)),
            (memory_manager, ("CONTEXT_FILE", store / "Context.md")),
            (memory_manager, ("HISTORY_FILE", store / "ChatHistory.md")),
        ):
            patcher = mock.patch.object(target, value[0], value[1])
            patcher.start()
            self.addCleanup(patcher.stop)

        no_input = mock.patch.object(
            builtins, "input", side_effect=AssertionError("input() must not be called in a non-interactive run")
        )
        no_input.start()
        self.addCleanup(no_input.stop)

    def run_main(self, argv):
        with contextlib.redirect_stdout(io.StringIO()):
            return self.orchestrator.main(argv)

    def test_fully_specified_run_completes_without_prompting(self):
        final = self.run_main(["--story", STORY, "--lang", "Python", "--project", "smoke_calc"])
        self.assertEqual(final["project_name"], "smoke_calc")
        self.assertEqual(final["test_results"]["status"], "PASS")
        self.assertTrue(final["promotion_approved"])
        self.assertTrue((self.workspace_root / "smoke_calc" / "src" / "calc.py").is_file())

    def test_project_name_is_derived_from_the_story_when_not_given(self):
        import run_config

        final = self.run_main(["--story", STORY])
        expected = run_config.slugify_story(STORY)
        self.assertEqual(final["project_name"], expected)
        self.assertEqual(final["target_lang"], "Python")
        self.assertTrue((self.workspace_root / expected).is_dir())

    def test_different_stories_get_separate_workspaces(self):
        self.run_main(["--story", STORY])
        self.run_main(["--story", "As a user I want to subtract two numbers."])
        self.assertEqual(len([p for p in self.workspace_root.iterdir() if p.is_dir()]), 2)

    def test_unsupported_language_stops_before_any_model_call(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                self.run_main(["--story", STORY, "--lang", "Swift"])
        self.assertEqual(ctx.exception.code, 2)
        self.assertEqual(self.llm_calls, [])

    def test_run_is_recorded_in_memory(self):
        self.run_main(["--story", STORY, "--project", "smoke_calc"])
        self.assertIn("smoke_calc", (self.store / "Context.md").read_text(encoding="utf-8"))
        self.assertIn(STORY, (self.store / "ChatHistory.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
