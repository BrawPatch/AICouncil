"""Tests for MultiAgentCouncil/council_engine.py (draft, blind critique, chairman synthesis).

A scripted fake LLM stands in for Ollama. Calls are sequential and ordered: every draft (in
drafter order), then every critique (in draft order), then the chairman. The fake therefore just
hands out replies in call order, and an Exception in the script is raised instead of returned.
"""
import inspect
import unittest

import _paths  # noqa: F401
import council_engine
import llm_client

TASK = "TASK: write the functional specification for adding two numbers."
ALPHA, BETA, CHAIR = "model-alpha", "model-beta", "model-chair"


class Recorder:
    def __init__(self, replies):
        self._replies = list(replies)
        self.models = []
        self.prompts = []

    def __call__(self, model, prompt):
        self.models.append(model)
        self.prompts.append(prompt)
        if not self._replies:
            raise AssertionError(f"unexpected extra LLM call to {model}")
        reply = self._replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def no_log(*_args, **_kwargs):
    return None


def run(replies, drafters=(ALPHA, BETA), chairman=CHAIR, **kwargs):
    rec = Recorder(replies)
    kwargs.setdefault("log", no_log)
    result = council_engine.deliberate(TASK, list(drafters), chairman, llm=rec, **kwargs)
    return result, rec


HAPPY = ["draft A", "draft B", "critique A", "critique B", "FINAL ANSWER"]


class HappyPathTest(unittest.TestCase):
    def test_returns_final_drafts_and_critiques(self):
        result, _ = run(HAPPY)
        self.assertEqual(result["final"], "FINAL ANSWER")
        self.assertEqual(result["drafts"], ["draft A", "draft B"])
        self.assertEqual(result["critiques"], ["critique A", "critique B"])
        self.assertEqual(result["errors"], [])

    def test_calls_are_ordered_drafts_then_critiques_then_chairman(self):
        _, rec = run(HAPPY)
        self.assertEqual(rec.models, [ALPHA, BETA, BETA, ALPHA, CHAIR])

    def test_each_critique_is_written_by_a_different_model_than_the_author(self):
        _, rec = run(HAPPY)
        self.assertNotEqual(rec.models[2], rec.models[0])  # critique of draft A vs its author
        self.assertNotEqual(rec.models[3], rec.models[1])  # critique of draft B vs its author

    def test_three_drafters_critique_in_a_ring(self):
        replies = ["d1", "d2", "d3", "c1", "c2", "c3", "FINAL"]
        _, rec = run(replies, drafters=("m1", "m2", "m3"))
        self.assertEqual(rec.models, ["m1", "m2", "m3", "m2", "m3", "m1", CHAIR])

    def test_drafters_receive_the_task_unchanged(self):
        _, rec = run(HAPPY)
        self.assertEqual(rec.prompts[0], TASK)
        self.assertEqual(rec.prompts[1], TASK)

    def test_critique_prompts_are_blind_to_the_author(self):
        _, rec = run(HAPPY)
        self.assertIn("draft A", rec.prompts[2])
        self.assertIn(TASK, rec.prompts[2])
        self.assertNotIn(ALPHA, rec.prompts[2])
        self.assertNotIn(BETA, rec.prompts[3])

    def test_chairman_prompt_contains_the_task_every_draft_and_every_critique(self):
        _, rec = run(HAPPY)
        chairman_prompt = rec.prompts[-1]
        for expected in (TASK, "draft A", "draft B", "critique A", "critique B"):
            self.assertIn(expected, chairman_prompt)

    def test_replies_are_stripped_of_surrounding_whitespace(self):
        result, _ = run(["  draft A\n", "draft B", "critique A", "critique B", "\nFINAL ANSWER \n"])
        self.assertEqual(result["drafts"][0], "draft A")
        self.assertEqual(result["final"], "FINAL ANSWER")

    def test_a_single_drafter_critiques_its_own_draft(self):
        result, rec = run(["draft A", "critique A", "FINAL"], drafters=(ALPHA,))
        self.assertEqual(rec.models, [ALPHA, ALPHA, CHAIR])
        self.assertEqual(result["final"], "FINAL")


class FailureHandlingTest(unittest.TestCase):
    def test_a_failing_drafter_does_not_stop_the_run(self):
        result, rec = run([RuntimeError("model unloaded"), "draft B", "critique B", "FINAL"])
        self.assertEqual(result["final"], "FINAL")
        self.assertEqual(result["drafts"], ["draft B"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn(ALPHA, result["errors"][0])
        # The surviving draft is critiqued by a surviving drafter, never by the one that failed.
        self.assertEqual(rec.models, [ALPHA, BETA, BETA, CHAIR])

    def test_all_drafters_failing_raises_and_never_calls_the_chairman(self):
        rec = Recorder([RuntimeError("a down"), RuntimeError("b down")])
        with self.assertRaises(RuntimeError):
            council_engine.deliberate(TASK, [ALPHA, BETA], CHAIR, llm=rec, log=no_log)
        self.assertNotIn(CHAIR, rec.models)

    def test_a_failing_critique_is_recorded_and_the_run_continues(self):
        result, rec = run(["draft A", "draft B", RuntimeError("down"), "critique B", "FINAL"])
        self.assertEqual(result["critiques"], ["", "critique B"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn(council_engine.NO_CRITIQUE, rec.prompts[-1])
        self.assertEqual(result["final"], "FINAL")

    def test_a_failing_chairman_raises(self):
        rec = Recorder(["draft A", "draft B", "critique A", "critique B", RuntimeError("chair down")])
        with self.assertRaises(RuntimeError):
            council_engine.deliberate(TASK, [ALPHA, BETA], CHAIR, llm=rec, log=no_log)

    def test_programming_errors_are_not_swallowed(self):
        rec = Recorder([TypeError("bug in the llm wrapper")])
        with self.assertRaises(TypeError):
            council_engine.deliberate(TASK, [ALPHA, BETA], CHAIR, llm=rec, log=no_log)


class EmptyOutputTest(unittest.TestCase):
    def test_an_empty_first_response_is_retried_once(self):
        result, rec = run(["", "draft A", "draft B", "critique A", "critique B", "FINAL"])
        self.assertEqual(rec.models[:2], [ALPHA, ALPHA])
        self.assertEqual(rec.prompts[0], rec.prompts[1])
        self.assertEqual(result["drafts"], ["draft A", "draft B"])

    def test_a_whitespace_only_response_counts_as_empty(self):
        result, rec = run(["  \n", "draft A", "draft B", "critique A", "critique B", "FINAL"])
        self.assertEqual(rec.models[:2], [ALPHA, ALPHA])
        self.assertEqual(result["drafts"][0], "draft A")

    def test_empty_twice_counts_as_a_failure_and_is_not_retried_again(self):
        result, rec = run(["", "", "draft B", "critique B", "FINAL"])
        self.assertEqual(rec.models, [ALPHA, ALPHA, BETA, BETA, CHAIR])
        self.assertEqual(result["drafts"], ["draft B"])
        self.assertIn(ALPHA, result["errors"][0])
        self.assertIn("empty", result["errors"][0].lower())

    def test_a_chairman_that_returns_nothing_twice_raises(self):
        rec = Recorder(["draft A", "draft B", "critique A", "critique B", "", ""])
        with self.assertRaises(RuntimeError):
            council_engine.deliberate(TASK, [ALPHA, BETA], CHAIR, llm=rec, log=no_log)


class TruncationTest(unittest.TestCase):
    def long(self, name):
        return name + "x" * 500 + "TAILMARK"

    def test_sections_are_truncated_before_they_reach_other_models(self):
        replies = [self.long("A"), self.long("B"), self.long("cA"), self.long("cB"), "FINAL"]
        result, rec = run(replies, max_section_chars=100)
        for section in result["drafts"] + result["critiques"]:
            self.assertLessEqual(len(section), 100)
            self.assertTrue(section.endswith(council_engine.TRUNCATION_MARKER))
        for prompt in rec.prompts[2:]:  # both critique prompts and the chairman prompt
            self.assertNotIn("TAILMARK", prompt)

    def test_sections_within_the_limit_are_left_alone(self):
        result, _ = run(HAPPY, max_section_chars=100)
        self.assertEqual(result["drafts"], ["draft A", "draft B"])

    def test_the_final_answer_is_not_truncated(self):
        replies = ["draft A", "draft B", "critique A", "critique B", "F" * 500]
        result, _ = run(replies, max_section_chars=100)
        self.assertEqual(len(result["final"]), 500)

    def test_truncate_never_exceeds_the_limit_even_for_tiny_limits(self):
        self.assertLessEqual(len(council_engine.truncate("y" * 50, 5)), 5)
        self.assertEqual(council_engine.truncate("short", 100), "short")


class ArgumentValidationTest(unittest.TestCase):
    def deliberate(self, task=TASK, drafters=(ALPHA, BETA), chairman=CHAIR, **kwargs):
        return council_engine.deliberate(task, list(drafters), chairman, llm=Recorder([]), log=no_log, **kwargs)

    def test_blank_task_is_rejected(self):
        with self.assertRaises(ValueError):
            self.deliberate(task="   ")

    def test_no_drafters_is_rejected(self):
        with self.assertRaises(ValueError):
            self.deliberate(drafters=())

    def test_blank_chairman_is_rejected(self):
        with self.assertRaises(ValueError):
            self.deliberate(chairman="")

    def test_non_positive_section_limit_is_rejected(self):
        for bad in (0, -5):
            with self.subTest(limit=bad):
                with self.assertRaises(ValueError):
                    self.deliberate(max_section_chars=bad)


class InterfaceAndLoggingTest(unittest.TestCase):
    def test_default_llm_is_the_shared_ollama_client(self):
        params = inspect.signature(council_engine.deliberate).parameters
        self.assertIs(params["llm"].default, llm_client.query_local_llm)
        self.assertEqual(params["max_section_chars"].default, 6000)

    def test_progress_log_shows_draft_critique_and_synthesis_steps(self):
        lines = []
        run(HAPPY, log=lines.append)
        text = "\n".join(lines).lower()
        for stage in ("draft", "critique", "synthesi"):
            self.assertIn(stage, text)
        for model in (ALPHA, BETA, CHAIR):
            self.assertIn(model, text)

    def test_a_chairman_prompt_that_may_overflow_the_context_window_logs_a_warning(self):
        lines = []
        run(["a" * 6000, "b" * 6000, "c" * 6000, "d" * 6000, "FINAL"], log=lines.append)
        self.assertTrue(any("warning" in line.lower() and "chairman" in line.lower() for line in lines))

    def test_a_normal_sized_run_logs_no_warning(self):
        lines = []
        run(HAPPY, log=lines.append)
        self.assertFalse(any("warning" in line.lower() for line in lines))


if __name__ == "__main__":
    unittest.main()
