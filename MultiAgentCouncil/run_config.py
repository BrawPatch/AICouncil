"""Run configuration for the council orchestrator: command-line arguments, language validation and
project-name rules. Pure standard library (no langgraph) so it can be tested anywhere.

Typical non-interactive use (no prompts at all):

    python3 StartCouncil.py --story "As a user I want to add numbers." --lang Python --project calc
"""
import argparse
import hashlib
import re
import unicodedata

# Languages the coder and QA agents can actually run (see agents/coder.py STYLE and agents/qa.py).
SUPPORTED_LANGUAGES = ("Python", "JavaScript", "Go")
DEFAULT_LANGUAGE = "Python"
DEFAULT_STORY = (
    "As a Customer, I want to securely pay via an API endpoint, "
    "so that my account credentials remain encrypted."
)
MAX_LANGUAGE_ATTEMPTS = 3

# The project name becomes a directory under workspace/, so it must not be able to escape it.
_PROJECT_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
_SLUG_BASE_CHARS = 40


def normalize_language(value: str) -> str:
    """Returns the canonical spelling of a supported language, or raises ValueError."""
    wanted = value.strip().lower()
    for name in SUPPORTED_LANGUAGES:
        if name.lower() == wanted:
            return name
    raise ValueError(
        f"Unsupported language {value!r}. Choose one of: {', '.join(SUPPORTED_LANGUAGES)}."
    )


def validate_project_name(name: str) -> str:
    """A project name is 1-64 characters: letters, digits, '_' or '-', starting with a letter or digit."""
    if not _PROJECT_NAME.fullmatch(name):
        raise ValueError(
            f"Invalid project name {name!r}. Use 1-64 letters, digits, '_' or '-', starting with a letter or digit."
        )
    return name


def slugify_story(story: str) -> str:
    """Derives a stable, readable project name from a story.

    A short hash of the full story is appended, because stories often share a long opening
    ("As a customer I want to ...") and would otherwise overwrite each other's workspace.
    """
    normalized = " ".join(story.split())
    ascii_text = unicodedata.normalize("NFKD", normalized).encode("ascii", "ignore").decode("ascii")
    words = re.findall(r"[a-z0-9]+", ascii_text.lower())
    base = "_".join(words)[:_SLUG_BASE_CHARS].strip("_") or "project"
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:6]
    return f"{base}_{digest}"


def _language_arg(value: str) -> str:
    try:
        return normalize_language(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e))


def _project_arg(value: str) -> str:
    try:
        return validate_project_name(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e))


def _story_arg(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("the story must not be empty")
    return value.strip()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the local Ollama council on a user story. Anything not given on the "
                    "command line is asked for interactively, unless --story is given.",
    )
    parser.add_argument("--story", type=_story_arg, help="the user story to build")
    parser.add_argument("--lang", type=_language_arg,
                        help=f"target language ({'/'.join(SUPPORTED_LANGUAGES)}); default {DEFAULT_LANGUAGE}")
    parser.add_argument("--project", type=_project_arg,
                        help="workspace name (default: derived from the story)")
    return parser.parse_args(argv)


def _prompt_language(input_fn) -> str:
    prompt = f"⌨️ Choose target language [{'/'.join(SUPPORTED_LANGUAGES)}] (Default: {DEFAULT_LANGUAGE}): "
    for _ in range(MAX_LANGUAGE_ATTEMPTS):
        answer = input_fn(prompt).strip()
        if not answer:
            return DEFAULT_LANGUAGE
        try:
            return normalize_language(answer)
        except ValueError as e:
            print(f"❌ {e}")
    raise ValueError(f"No supported language chosen after {MAX_LANGUAGE_ATTEMPTS} attempts.")


def resolve_config(args, input_fn=input) -> dict:
    """Combines parsed arguments with interactive fallbacks.

    input_fn is only used when --story was not given. With --story the run is fully
    non-interactive: a missing --lang defaults to Python and a missing --project is derived.
    """
    story = args.story
    prompted = story is None
    if prompted:
        print("\n💬 --- Welcome to the Agile Council Configuration Matrix ---")
        story = input_fn("⌨️ Provide input User Story: ").strip() or DEFAULT_STORY

    lang = args.lang
    if lang is None:
        lang = _prompt_language(input_fn) if prompted else DEFAULT_LANGUAGE

    return {
        "project_name": args.project or slugify_story(story),
        "target_lang": lang,
        "raw_user_story": story,
    }
