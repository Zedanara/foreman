"""Ask the model one question and stream the answer to the terminal.

Usage:
    uv run python -m foreman.ask "Why is the sky blue?"
"""

import argparse
import asyncio
import os
import sys
from collections.abc import AsyncIterator
from dataclasses import dataclass

import openai
from dotenv import load_dotenv
from openai import AsyncOpenAI

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "gpt-oss:20b"
# Ollama ignores the key, but the OpenAI client refuses to start without one.
DEFAULT_API_KEY = "ollama"


@dataclass(frozen=True)
class Settings:
    base_url: str
    model: str
    api_key: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            base_url=os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL),
            model=os.getenv("LLM_MODEL", DEFAULT_MODEL),
            api_key=os.getenv("LLM_API_KEY", DEFAULT_API_KEY),
        )


async def stream_answer(
    client: AsyncOpenAI, model: str, question: str
) -> AsyncIterator[str]:
    """Yield pieces of the answer text as the model generates them."""
    stream = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": question}],
        stream=True,
    )
    async for chunk in stream:
        if not chunk.choices:
            continue
        text = chunk.choices[0].delta.content
        if text:
            yield text


async def ask(question: str, settings: Settings) -> None:
    async with AsyncOpenAI(
        base_url=settings.base_url, api_key=settings.api_key
    ) as client:
        async for text in stream_answer(client, settings.model, question):
            print(text, end="", flush=True)
    print()


def parse_args(argv: list[str] | None) -> str:
    parser = argparse.ArgumentParser(
        prog="python -m foreman.ask",
        description="Ask the model a question and stream the answer.",
    )
    parser.add_argument("question", nargs="+", help="question text")
    args = parser.parse_args(argv)
    return " ".join(args.question)


def main(argv: list[str] | None = None) -> int:
    question = parse_args(argv)
    load_dotenv()
    settings = Settings.from_env()

    try:
        asyncio.run(ask(question, settings))
    except openai.APIConnectionError:
        print(
            f"\nError: cannot reach the model server at {settings.base_url}.\n"
            "Is Ollama running? Start it with `ollama serve`.",
            file=sys.stderr,
        )
        return 1
    except openai.NotFoundError:
        print(
            f"\nError: model '{settings.model}' not found.\n"
            f"Download it with `ollama pull {settings.model}`.",
            file=sys.stderr,
        )
        return 1
    except openai.APIError as exc:
        print(f"\nError: the model server returned an error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
