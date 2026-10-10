"""Measure Ollama generation speed for several num_ctx values.

Usage:
    uv run python scripts/bench_ctx.py [model]

For every num_ctx it loads the model with that context, runs the same prompt
a few times and prints the median eval rate, plus the PROCESSOR and CONTEXT
columns from `ollama ps` so you can confirm the setting was really applied.
"""

import json
import statistics
import subprocess
import sys
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
CONTEXTS = [4096, 8192, 16384, 32768]
RUNS = 3
PROMPT = "Explain in about 200 words how a hash map works."


def generate(model: str, num_ctx: int) -> dict:
    payload = {
        "model": model,
        "prompt": PROMPT,
        "stream": False,
        "options": {"num_ctx": num_ctx, "num_predict": 256, "seed": 42},
    }
    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        return json.load(response)


def ollama_ps_row(model: str) -> str:
    output = subprocess.run(
        ["ollama", "ps"], capture_output=True, text=True, check=True
    ).stdout
    rows = [line for line in output.splitlines() if line.startswith(model)]
    return rows[0] if rows else "model not loaded"


def main() -> None:
    model = sys.argv[1] if len(sys.argv) > 1 else "gpt-oss:20b"
    print(f"model: {model}, runs per context: {RUNS} (+1 warm-up)\n")
    for num_ctx in CONTEXTS:
        generate(model, num_ctx)  # warm-up: loads the model with this num_ctx
        rates = []
        for _ in range(RUNS):
            result = generate(model, num_ctx)
            rates.append(result["eval_count"] / result["eval_duration"] * 1e9)
        print(f"num_ctx={num_ctx}: median {statistics.median(rates):.1f} tokens/s")
        print(f"  runs: {', '.join(f'{r:.1f}' for r in rates)}")
        print(f"  ollama ps: {ollama_ps_row(model)}\n")


if __name__ == "__main__":
    main()
