#!/usr/bin/env python3
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
