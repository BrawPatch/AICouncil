#!/usr/bin/env python3
"""ask_qwen.py - send a prompt file (plus optional context files) to a local Ollama model.

Usage:
  python3 ask_qwen.py prompts/day2_tests.md --files llm_client.py state_schema.py --out out/day2_tests.txt
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

URL = "http://localhost:11434/api/generate"
WARN_CHARS = 20000  # roughly 5k tokens; leave headroom inside an 8k context


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt_file")
    ap.add_argument("--files", nargs="*", default=[], help="context files appended to the prompt")
    ap.add_argument("--model", default="qwen2.5-coder:7b")
    ap.add_argument("--num-ctx", type=int, default=8192)
    ap.add_argument("--out", help="also save the raw response here")
    args = ap.parse_args()

    prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    for f in args.files:
        prompt += f"\n\n=== CONTEXT FILE: {f} ===\n{Path(f).read_text(encoding='utf-8')}\n"

    if len(prompt) > WARN_CHARS:
        print(f"⚠️ Prompt is {len(prompt)} chars; it may not fit num_ctx={args.num_ctx}. "
              "Send fewer files or only signatures.", file=sys.stderr)

    payload = {
        "model": args.model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "10m",
        "options": {"num_ctx": args.num_ctx, "temperature": 0.2},
    }
    req = urllib.request.Request(URL, json.dumps(payload).encode("utf-8"),
                                 {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=900) as resp:
            text = json.loads(resp.read().decode("utf-8"))["response"]
    except Exception as e:
        sys.exit(f"❌ Ollama call failed: {e}")

    print(text)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"\n💾 saved to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
