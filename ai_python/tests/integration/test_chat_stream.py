from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def _stub_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_tool(_prompt: str) -> Iterator[str]:
        yield "Hi"
        yield " there"

    monkeypatch.setattr(
        "app.api.routers.chat.stream_chat_tool",
        fake_tool,
    )


@pytest.fixture(autouse=True)
def _unset_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FPT_MKP_API_KEY", raising=False)


def test_health_ok() -> None:
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_chat_stream_sse_delta_and_done() -> None:
    client = TestClient(app)
    with client.stream(
        "GET",
        "/v1/chat/stream",
        params={"q": "Hi"},
    ) as resp:
        assert resp.status_code == 200
        body = "".join(chunk.decode("utf-8") for chunk in resp.iter_bytes())

    assert "event: delta" in body
    assert "data: Hi" in body
    assert "event: delta" in body
    assert "data: there" in body or "data: Hi" in body
    assert "event: done" in body
    assert "data: [DONE]" in body
