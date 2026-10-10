# Foreman

[![CI](https://github.com/Zedanara/foreman/actions/workflows/ci.yml/badge.svg)](https://github.com/Zedanara/foreman/actions/workflows/ci.yml)

Local-first multi-agent assistant in Telegram. The agent loop is written by
hand, without an agent framework (see [ADR 0001](docs/adr/0001-no-agent-framework.md)).
It runs on a local model through [Ollama](https://ollama.com) and can switch to
any OpenAI-compatible API by changing configuration.

> Status: **v0.1, local model.** Right now Foreman is a command-line tool that
> streams an answer from the local model. The agent loop and the Telegram bot
> come in later milestones.

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com) with the model pulled:

  ```
  ollama pull gpt-oss:20b
  ```

## Quick start

```
git clone https://github.com/Zedanara/foreman.git
cd foreman
uv sync
cp .env.example .env    # optional: defaults already point to local Ollama
uv run python -m foreman.ask "Why is the sky blue?"
```

The answer is printed while the model generates it. If Ollama is not running,
you get a short hint instead of a traceback.

### Configuration

Settings come from environment variables or a `.env` file
(see [`.env.example`](.env.example)):

| Variable       | Default                     | Meaning                        |
|----------------|-----------------------------|--------------------------------|
| `LLM_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible API endpoint |
| `LLM_MODEL`    | `gpt-oss:20b`               | Model name                     |
| `LLM_API_KEY`  | `ollama`                    | API key (Ollama ignores it)    |

## Development

```
uv sync                              # install the project and dev tools
uv run pre-commit install            # run ruff and other checks on every commit
uv run pre-commit run --all-files    # run all checks manually
uv run python -m pytest              # tests, no Ollama needed
```

CI runs ruff and pytest on every pull request and on pushes to `main`.

## Benchmarks

`gpt-oss:20b` (MXFP4) on Ollama 0.40.2, NVIDIA RTX 3080 Ti Laptop GPU (16 GB).
Measured on 2026-10-10 with [`scripts/bench_ctx.py`](scripts/bench_ctx.py):
the same 256-token generation, median of 3 runs after a warm-up, tokens/s from
Ollama's own `eval_count / eval_duration`. `PROCESSOR` and `CONTEXT` are taken
from `ollama ps` after the runs to confirm the setting was applied.

| num_ctx | PROCESSOR (`ollama ps`) | Tokens/s (median) | Runs             |
|---------|-------------------------|-------------------|------------------|
| 4096    | 100% GPU                | 56.2              | 55.1, 56.4, 56.2 |
| 8192    | 100% GPU                | 56.3              | 55.2, 57.1, 56.3 |
| 16384   | 100% GPU                | 55.8              | 57.2, 54.6, 55.8 |
| 32768   | 100% GPU                | 55.6              | 51.8, 57.6, 55.6 |

Up to 32768 the model stays fully on the GPU and speed does not depend on
num_ctx, so Foreman uses **16384**: plenty of room for tool results without
wasting VRAM. On a laptop the numbers depend on the power mode (on AC power or
on battery), so compare runs only under the same conditions.

Reproduce: `uv run python scripts/bench_ctx.py`.

### Context size

The OpenAI-compatible API has no `num_ctx` parameter, so the context size is
set on the Ollama server. On Windows:

```
setx OLLAMA_CONTEXT_LENGTH 16384
```

Then quit Ollama from the tray and start it again (the variable is read only at
startup). Check with `ollama ps` while a model is loaded: the `CONTEXT`
column must show `16384`.

## Roadmap

- **v0.1 Local model:** project setup, CI, streaming CLI, benchmarks.
- **v0.2 Agent loop:** hand-written tool-calling loop.
- **v0.3 Provider and evals:** switchable providers, evaluation of answers.
- **v0.4 Telegram:** the assistant as a Telegram bot.

## License

[MIT](LICENSE)
