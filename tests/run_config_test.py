"""Tests for MultiAgentCouncil/run_config.py (CLI arguments, language and project-name rules)."""
import contextlib
import io
import re
import unittest

import _paths  # noqa: F401
import run_config


def scripted(*answers):
    """An input() stand-in that returns the given answers in order and records the prompts."""
    remaining = iter(answers)
    prompts = []

    def fn(prompt=""):
        prompts.append(prompt)
        return next(remaining)

    fn.prompts = prompts
    return fn


def forbidden_input(prompt=""):
    raise AssertionError(f"input() must not be called here, but was asked: {prompt!r}")


def quiet():
    return contextlib.redirect_stdout(io.StringIO())


class NormalizeLanguageTest(unittest.TestCase):
    def test_accepts_supported_languages_case_insensitively(self):
        self.assertEqual(run_config.normalize_language("python"), "Python")
        self.assertEqual(run_config.normalize_language("  JAVASCRIPT "), "JavaScript")
        self.assertEqual(run_config.normalize_language("go"), "Go")

    def test_rejects_unsupported_language_and_lists_the_supported_ones(self):
        with self.assertRaises(ValueError) as ctx:
            run_config.normalize_language("Swift")
        message = str(ctx.exception)
        for name in run_config.SUPPORTED_LANGUAGES:
            self.assertIn(name, message)

    def test_supported_languages_match_what_the_coder_and_qa_agents_can_run(self):
        self.assertEqual(
            sorted(n.lower() for n in run_config.SUPPORTED_LANGUAGES), ["go", "javascript", "python"]
        )


class ProjectNameTest(unittest.TestCase):
    def test_valid_names_are_returned_unchanged(self):
        for name in ("calc", "my_project", "Billing-2", "a" * 64):
            self.assertEqual(run_config.validate_project_name(name), name)

    def test_names_that_could_escape_the_workspace_are_rejected(self):
        for name in ("", "../escape", "a/b", "a\\b", ".hidden", "-leading-dash", "has space", "a" * 65, "/abs"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    run_config.validate_project_name(name)


class SlugifyStoryTest(unittest.TestCase):
    STORY = "As a Customer, I want to securely pay via an API endpoint."

    def test_slug_is_valid_deterministic_and_readable(self):
        slug = run_config.slugify_story(self.STORY)
        self.assertEqual(slug, run_config.slugify_story(self.STORY))
        self.assertEqual(run_config.validate_project_name(slug), slug)
        self.assertTrue(slug.startswith("as_a_customer_i_want"))

    def test_surrounding_whitespace_does_not_change_the_slug(self):
        self.assertEqual(run_config.slugify_story(self.STORY), run_config.slugify_story("  " + self.STORY + "\n"))

    def test_stories_sharing_a_long_prefix_get_different_workspaces(self):
        a = run_config.slugify_story("As a customer I want to pay by card so that I can buy things quickly.")
        b = run_config.slugify_story("As a customer I want to pay by card so that I can get a receipt emailed.")
        self.assertNotEqual(a, b)

    def test_slug_is_short_enough_for_a_directory_name(self):
        slug = run_config.slugify_story("word " * 500)
        self.assertLessEqual(len(slug), 64)

    def test_symbols_only_story_still_yields_a_valid_name(self):
        slug = run_config.slugify_story("!!! ???")
        self.assertTrue(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", slug))

    def test_non_ascii_story_still_yields_a_valid_name(self):
        slug = run_config.slugify_story("Als Kunde möchte ich 支払い bezahlen")
        self.assertEqual(run_config.validate_project_name(slug), slug)


class ParseArgsTest(unittest.TestCase):
    def test_no_arguments_leaves_everything_unset(self):
        args = run_config.parse_args([])
        self.assertIsNone(args.story)
        self.assertIsNone(args.lang)
        self.assertIsNone(args.project)

    def test_all_arguments_are_parsed_and_language_is_normalised(self):
        args = run_config.parse_args(["--story", "As a user I want x.", "--lang", "go", "--project", "demo"])
        self.assertEqual(args.story, "As a user I want x.")
        self.assertEqual(args.lang, "Go")
        self.assertEqual(args.project, "demo")

    def assert_rejected(self, argv):
        with contextlib.redirect_stderr(io.StringIO()) as err:
            with self.assertRaises(SystemExit) as ctx:
                run_config.parse_args(argv)
        self.assertEqual(ctx.exception.code, 2)
        return err.getvalue()

    def test_unsupported_language_is_rejected_up_front(self):
        self.assertIn("Swift", self.assert_rejected(["--lang", "Swift"]))

    def test_unsafe_project_name_is_rejected(self):
        self.assert_rejected(["--project", "../escape"])

    def test_blank_story_is_rejected(self):
        self.assert_rejected(["--story", "   "])


class ResolveConfigTest(unittest.TestCase):
    def test_fully_specified_run_never_prompts(self):
        args = run_config.parse_args(["--story", "As a user I want x.", "--lang", "Python", "--project", "demo"])
        cfg = run_config.resolve_config(args, input_fn=forbidden_input)
        self.assertEqual(
            cfg, {"project_name": "demo", "target_lang": "Python", "raw_user_story": "As a user I want x."}
        )

    def test_story_without_language_defaults_to_python_without_prompting(self):
        args = run_config.parse_args(["--story", "As a user I want x."])
        cfg = run_config.resolve_config(args, input_fn=forbidden_input)
        self.assertEqual(cfg["target_lang"], "Python")

    def test_project_name_is_derived_from_the_story_when_not_given(self):
        args = run_config.parse_args(["--story", "As a user I want x."])
        cfg = run_config.resolve_config(args, input_fn=forbidden_input)
        self.assertEqual(cfg["project_name"], run_config.slugify_story("As a user I want x."))

    def test_missing_story_falls_back_to_prompting_for_story_and_language(self):
        ask = scripted("As a user I want y.", "javascript")
        with quiet():
            cfg = run_config.resolve_config(run_config.parse_args([]), input_fn=ask)
        self.assertEqual(cfg["raw_user_story"], "As a user I want y.")
        self.assertEqual(cfg["target_lang"], "JavaScript")
        self.assertEqual(len(ask.prompts), 2)

    def test_language_given_on_the_command_line_is_not_asked_again(self):
        ask = scripted("As a user I want y.")
        with quiet():
            cfg = run_config.resolve_config(run_config.parse_args(["--lang", "Go"]), input_fn=ask)
        self.assertEqual(cfg["target_lang"], "Go")
        self.assertEqual(len(ask.prompts), 1)

    def test_empty_answers_use_the_documented_defaults(self):
        ask = scripted("", "")
        with quiet():
            cfg = run_config.resolve_config(run_config.parse_args([]), input_fn=ask)
        self.assertEqual(cfg["raw_user_story"], run_config.DEFAULT_STORY)
        self.assertEqual(cfg["target_lang"], run_config.DEFAULT_LANGUAGE)

    def test_invalid_language_answer_is_asked_again(self):
        ask = scripted("As a user I want y.", "cobol", "go")
        with quiet():
            cfg = run_config.resolve_config(run_config.parse_args([]), input_fn=ask)
        self.assertEqual(cfg["target_lang"], "Go")
        self.assertEqual(len(ask.prompts), 3)

    def test_gives_up_after_repeated_invalid_language_answers(self):
        ask = scripted("As a user I want y.", "cobol", "fortran", "pascal")
        with quiet():
            with self.assertRaises(ValueError):
                run_config.resolve_config(run_config.parse_args([]), input_fn=ask)


if __name__ == "__main__":
    unittest.main()
