import asyncio
from types import SimpleNamespace

import httpx2
import openai
import pytest

from foreman import ask as ask_module
from foreman.ask import Settings, main, stream_answer


@pytest.fixture(autouse=True)
def ignore_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep a developer's local .env from leaking into the tests."""
    monkeypatch.setattr(ask_module, "load_dotenv", lambda: None)


def make_chunk(text: str | None) -> SimpleNamespace:
    """Build an object shaped like openai's ChatCompletionChunk."""
    delta = SimpleNamespace(content=text)
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)])


class FakeCompletions:
    def __init__(self, chunks: list[SimpleNamespace]) -> None:
        self.chunks = chunks
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)

        async def stream():
            for chunk in self.chunks:
                yield chunk

        return stream()


class FakeClient:
    """Stands in for AsyncOpenAI, so tests never touch the network."""

    def __init__(self, chunks: list[SimpleNamespace]) -> None:
        self.chat = SimpleNamespace(completions=FakeCompletions(chunks))

    async def __aenter__(self) -> "FakeClient":
        return self

    async def __aexit__(self, *exc_info) -> None:
        return None


def test_settings_use_ollama_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY"):
        monkeypatch.delenv(name, raising=False)

    settings = Settings.from_env()

    assert settings == Settings(
        base_url="http://localhost:11434/v1", model="gpt-oss:20b", api_key="ollama"
    )


def test_settings_read_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_BASE_URL", "http://example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "some-model")
    monkeypatch.setenv("LLM_API_KEY", "secret")

    settings = Settings.from_env()

    assert settings == Settings("http://example.test/v1", "some-model", "secret")


def test_stream_answer_yields_only_text() -> None:
    chunks = [
        make_chunk(None),  # first chunk carries only the role
        make_chunk("Hello"),
        SimpleNamespace(choices=[]),  # usage-only chunk at the end
        make_chunk(", world"),
    ]
    client = FakeClient(chunks)

    async def collect() -> list[str]:
        return [text async for text in stream_answer(client, "m", "hi")]

    assert asyncio.run(collect()) == ["Hello", ", world"]
    call = client.chat.completions.calls[0]
    assert call["stream"] is True
    assert call["messages"] == [{"role": "user", "content": "hi"}]


def test_main_prints_streamed_answer(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    chunks = [make_chunk("Blue "), make_chunk("sky.")]
    monkeypatch.setattr(ask_module, "AsyncOpenAI", lambda **_: FakeClient(chunks))

    exit_code = main(["Why", "is", "the", "sky", "blue?"])

    assert exit_code == 0
    assert capsys.readouterr().out == "Blue sky.\n"


def test_main_requires_a_question(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([])

    assert exc_info.value.code == 2
    assert "usage:" in capsys.readouterr().err


def raise_error(error: Exception):
    async def fake_ask(question: str, settings: Settings) -> None:
        raise error

    return fake_ask


def test_main_explains_unreachable_server(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request = httpx2.Request("POST", "http://localhost:11434/v1/chat/completions")
    error = openai.APIConnectionError(request=request)
    monkeypatch.setattr(ask_module, "ask", raise_error(error))

    exit_code = main(["hi"])

    err = capsys.readouterr().err
    assert exit_code == 1
    assert "ollama serve" in err
    assert "Traceback" not in err


def test_main_explains_missing_model(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LLM_MODEL", "no-such-model")
    request = httpx2.Request("POST", "http://localhost:11434/v1/chat/completions")
    response = httpx2.Response(404, request=request)
    error = openai.NotFoundError("model not found", response=response, body=None)
    monkeypatch.setattr(ask_module, "ask", raise_error(error))

    exit_code = main(["hi"])

    assert exit_code == 1
    assert "ollama pull no-such-model" in capsys.readouterr().err
