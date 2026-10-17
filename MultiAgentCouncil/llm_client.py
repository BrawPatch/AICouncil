import json
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
