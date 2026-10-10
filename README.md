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

Local `gpt-oss:20b` on RTX 3080 Ti. `PROCESSOR` is taken from `ollama ps`,
tokens/s is the `eval rate` from `ollama run gpt-oss:20b --verbose`.

| num_ctx | PROCESSOR (`ollama ps`) | Tokens/s | Notes |
|---------|-------------------------|----------|-------|
| 4096    | TODO                    | TODO     |       |
| 8192    | TODO                    | TODO     |       |
| 16384   | TODO                    | TODO     |       |
| 32768   | TODO                    | TODO     |       |

TODO: not measured yet, see #4.

## Roadmap

- **v0.1 Local model:** project setup, CI, streaming CLI, benchmarks.
- **v0.2 Agent loop:** hand-written tool-calling loop.
- **v0.3 Provider and evals:** switchable providers, evaluation of answers.
- **v0.4 Telegram:** the assistant as a Telegram bot.

## License

[MIT](LICENSE)
