import json
import os
import re
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"

CHAIRMAN_MODEL = "llama3.1:8b"   # Scrum Master / synthesizer / router
SECURITY_MODEL = "mistral:7b"    # Security craftsman / deep logic
CODER_MODEL = "qwen2.5-coder:7b"  # TDD software engineer

# Context window. Ollama's own default is small and silently truncates long prompts, so every call
# states its window explicitly and refuses to go below the floor.
MIN_NUM_CTX = 8192
DEFAULT_NUM_CTX = 8192
DEFAULT_TEMPERATURE = 0.2

# Model residency. 0 unloads a model straight after each call (the safe choice on a 24GB machine).
# Set COUNCIL_KEEP_ALIVE=10m to keep models loaded between calls (faster, but needs the memory for
# every resident model; see Council_MVP_7_Day_Plan.md). This per-request value overrides the
# OLLAMA_KEEP_ALIVE setting of the Ollama server.
KEEP_ALIVE_ENV = "COUNCIL_KEEP_ALIVE"
DEFAULT_KEEP_ALIVE = 0

_INTEGER = re.compile(r"-?\d+")
_DURATION = re.compile(r"(\d+(\.\d+)?(ms|s|m|h))+")  # Go-style durations: 90s, 10m, 1h30m


def resolve_keep_alive():
    """Reads COUNCIL_KEEP_ALIVE: an integer (seconds, -1 = forever) or a duration such as '10m'."""
    raw = os.environ.get(KEEP_ALIVE_ENV, "").strip()
    if not raw:
        return DEFAULT_KEEP_ALIVE
    if _INTEGER.fullmatch(raw):
        return int(raw)
    if _DURATION.fullmatch(raw):
        return raw
    raise ValueError(
        f"{KEEP_ALIVE_ENV}={raw!r} is not a valid keep-alive. Use seconds (0, 300, -1) or a duration such as 10m or 1h30m."
    )


def build_payload(model_name: str, prompt: str, num_ctx: int = DEFAULT_NUM_CTX,
                  temperature: float = DEFAULT_TEMPERATURE) -> dict:
    """Builds the Ollama /api/generate request body, validating the context window and keep-alive."""
    if num_ctx < MIN_NUM_CTX:
        raise ValueError(f"num_ctx={num_ctx} is below the minimum of {MIN_NUM_CTX}.")
    return {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "keep_alive": resolve_keep_alive(),
        "options": {"num_ctx": num_ctx, "temperature": temperature},
    }


def query_local_llm(model_name: str, prompt: str, timeout: int = 600,
                    num_ctx: int = DEFAULT_NUM_CTX, temperature: float = DEFAULT_TEMPERATURE) -> str:
    """Calls Ollama and returns the response text.

    Invalid arguments or configuration raise ValueError before any request is made. Any failure
    talking to Ollama raises RuntimeError naming the model.
    """
    payload = build_payload(model_name, prompt, num_ctx=num_ctx, temperature=temperature)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))["response"]
    except Exception as e:
        raise RuntimeError(f"Ollama call failed for model '{model_name}': {e!r}") from e
