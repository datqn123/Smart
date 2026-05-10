from __future__ import annotations

import json
from typing import Any

from fastapi.testclient import TestClient

from app.api.auth import get_jwt_validator, load_auth_settings
from app.api.runtime import get_graph_runtime
from main import app


class _MockRuntime:
    def invoke(self, request: Any, *, correlation_id: str) -> dict[str, Any]:
        return {
            "intent": "general_chat",
            "final_answer": f"echo:{request.message}",
            "correlation_id": correlation_id,
        }

    def stream(self, request: Any, *, correlation_id: str):  # noqa: ANN001
        yield {"chat_normal": {"delta": "a"}}
        yield {"chat_normal": {"final_answer": f"done:{request.message}"}}


def _build_client(monkeypatch, *, auth_dev_bypass: str = "1") -> TestClient:  # noqa: ANN001
    monkeypatch.setenv("AUTH_DEV_BYPASS", auth_dev_bypass)
    if auth_dev_bypass == "1":
        monkeypatch.delenv("JWT_ISSUER", raising=False)
        monkeypatch.delenv("JWT_AUDIENCE", raising=False)
        monkeypatch.delenv("JWT_JWKS_URL", raising=False)
        monkeypatch.delenv("JWT_PUBLIC_KEY_PEM", raising=False)
    load_auth_settings.cache_clear()
    get_jwt_validator.cache_clear()
    return TestClient(app)


def test_invoke_metadata_validation_422(monkeypatch) -> None:  # noqa: ANN001
    client = _build_client(monkeypatch, auth_dev_bypass="1")
    app.dependency_overrides[get_graph_runtime] = lambda: _MockRuntime()

    res = client.post(
        "/api/v1/ai/chat/invoke",
        headers={"X-Correlation-Id": "cid-422"},
        json={
            "message": "hello",
            "metadata": {"tenant_id": "t-1"},
        },
    )

    assert res.status_code == 422
    body = res.json()
    assert body["error"]["code"] == "AI_VALIDATION_FAILED"
    app.dependency_overrides.clear()


def test_invoke_rejects_jwt_401(monkeypatch) -> None:  # noqa: ANN001
    client = _build_client(monkeypatch, auth_dev_bypass="0")

    res = client.post(
        "/api/v1/ai/chat/invoke",
        headers={
            "X-Correlation-Id": "cid-401",
            "Authorization": "Bearer invalid-token",
        },
        json={
            "message": "hello",
            "metadata": {"tenant_id": "t-1", "user_id": "u-1"},
        },
    )

    assert res.status_code == 401
    assert res.json()["error"]["code"] == "AI_AUTH_INVALID"


def test_invoke_happy_path_with_mock_runtime(monkeypatch) -> None:  # noqa: ANN001
    client = _build_client(monkeypatch, auth_dev_bypass="1")
    app.dependency_overrides[get_graph_runtime] = lambda: _MockRuntime()

    res = client.post(
        "/api/v1/ai/chat/invoke",
        headers={"X-Correlation-Id": "cid-happy"},
        json={
            "message": "xin chao",
            "metadata": {"tenant_id": "t-1", "user_id": "u-1", "thread_id": "th-1"},
        },
    )

    assert res.status_code == 200
    body = res.json()
    assert body["correlation_id"] == "cid-happy"
    assert body["thread_id"] == "th-1"
    assert body["final_answer"] == "echo:xin chao"
    assert body["error"] is None
    app.dependency_overrides.clear()


def test_stream_emits_single_terminal_event(monkeypatch) -> None:  # noqa: ANN001
    client = _build_client(monkeypatch, auth_dev_bypass="1")
    app.dependency_overrides[get_graph_runtime] = lambda: _MockRuntime()

    res = client.post(
        "/api/v1/ai/chat/stream",
        headers={"X-Correlation-Id": "cid-stream"},
        json={
            "message": "abc",
            "metadata": {"tenant_id": "t-1", "user_id": "u-1"},
        },
    )

    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/event-stream")

    events = [
        json.loads(line[len("data: ") :])
        for line in res.text.splitlines()
        if line.startswith("data: ")
    ]
    terminal_events = [e for e in events if e.get("is_terminal")]
    assert len(terminal_events) == 1
    assert terminal_events[0]["event_type"] in ("final_answer", "error")
    app.dependency_overrides.clear()
