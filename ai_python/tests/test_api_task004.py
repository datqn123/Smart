from __future__ import annotations

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

    def stream(self, request: Any, *, correlation_id: str, bearer_token: str | None = None):  # noqa: ANN001
        yield {"chat_normal": {"final_answer": "partial"}}
        yield {"chat_normal": {"final_answer": f"done:{request.message}"}}


class _SqlFailThenSummarizeRuntime:
    """Mimic sql_branch error_payload then summarize_answer final_answer (answer quality path)."""

    def invoke(self, request: Any, *, correlation_id: str) -> dict[str, Any]:
        return {"final_answer": "enriched-user-reply", "error_payload": {"error": "max_sql_attempts"}}

    def stream(self, request: Any, *, correlation_id: str, bearer_token: str | None = None):  # noqa: ANN001
        yield {
            "sql_branch": {
                "error_payload": {"error": "max_sql_attempts", "attempts": 2},
            },
        }
        yield {
            "summarize_answer": {
                "final_answer": "enriched-user-reply",
            },
        }


class _StreamFailureRuntime:
    def invoke(self, request: Any, *, correlation_id: str) -> dict[str, Any]:
        return {
            "intent": "general_chat",
            "final_answer": f"echo:{request.message}",
            "correlation_id": correlation_id,
        }

    def stream(self, request: Any, *, correlation_id: str, bearer_token: str | None = None):  # noqa: ANN001
        yield {"chat_normal": {"final_answer": "x"}}
        raise RuntimeError("mock stream exploded")


class _NeverRunRuntime:
    def invoke(self, request: Any, *, correlation_id: str) -> dict[str, Any]:
        raise AssertionError("Runtime must not execute.")

    def stream(self, request: Any, *, correlation_id: str, bearer_token: str | None = None):  # noqa: ANN001
        raise AssertionError("Runtime must not execute.")


class _ValidatorWithClaims:
    def __init__(self, claims: dict[str, Any]) -> None:
        self._claims = claims

    def validate_authorization_header(self, authorization: str | None) -> dict[str, Any]:
        return self._claims


def _parse_sse_named_events(raw: str) -> list[tuple[str, str]]:
    """Parse SSE blocks with optional `event:` lines."""
    events: list[tuple[str, str]] = []
    for block in raw.split("\n\n"):
        if not block.strip():
            continue
        ev_name = ""
        data_lines: list[str] = []
        for line in block.split("\n"):
            if line.startswith("event:"):
                ev_name = line[len("event:") :].strip()
            elif line.startswith("data:"):
                chunk = line[len("data:") :]
                if chunk.startswith(" "):
                    chunk = chunk[1:]
                data_lines.append(chunk)
        if ev_name:
            events.append((ev_name, "\n".join(data_lines)))
    return events


def _build_client(monkeypatch, *, auth_dev_bypass: str = "1") -> TestClient:  # noqa: ANN001
    monkeypatch.setenv("AUTH_DEV_BYPASS", auth_dev_bypass)
    if auth_dev_bypass == "1":
        monkeypatch.delenv("JWT_ISSUER", raising=False)
        monkeypatch.delenv("JWT_AUDIENCE", raising=False)
        monkeypatch.delenv("JWT_JWKS_URL", raising=False)
        monkeypatch.delenv("JWT_PUBLIC_KEY_PEM", raising=False)
        monkeypatch.delenv("JWT_HS256_SECRET", raising=False)
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


def test_stream_emits_delta_then_done(monkeypatch) -> None:  # noqa: ANN001
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

    evs = _parse_sse_named_events(res.text)
    names = [e[0] for e in evs]
    assert "delta" in names
    assert names[-1] == "done"
    assert any("partial" in d for _, d in evs if _ == "delta")
    assert any("done:abc" in d for _, d in evs if _ == "delta")
    app.dependency_overrides.clear()


def test_stream_sql_fail_with_summarize_answer_skips_error_event(monkeypatch) -> None:  # noqa: ANN001
    client = _build_client(monkeypatch, auth_dev_bypass="1")
    app.dependency_overrides[get_graph_runtime] = lambda: _SqlFailThenSummarizeRuntime()

    res = client.post(
        "/api/v1/ai/chat/stream",
        headers={"X-Correlation-Id": "cid-sql-fail-enriched"},
        json={
            "message": "tồn kho",
            "metadata": {"tenant_id": "t-1", "user_id": "u-1"},
        },
    )

    assert res.status_code == 200
    evs = _parse_sse_named_events(res.text)
    names = [e[0] for e in evs]
    assert "error" not in names
    deltas = [d for n, d in evs if n == "delta"]
    assert any("enriched-user-reply" in d for d in deltas)
    assert names[-1] == "done"
    app.dependency_overrides.clear()


def test_stream_runtime_failure_emits_error_then_done(monkeypatch) -> None:  # noqa: ANN001
    client = _build_client(monkeypatch, auth_dev_bypass="1")
    app.dependency_overrides[get_graph_runtime] = lambda: _StreamFailureRuntime()

    res = client.post(
        "/api/v1/ai/chat/stream",
        headers={"X-Correlation-Id": "cid-stream-fail"},
        json={
            "message": "abc",
            "metadata": {"tenant_id": "t-1", "user_id": "u-1"},
        },
    )

    assert res.status_code == 200
    evs = _parse_sse_named_events(res.text)
    err = [e for e in evs if e[0] == "error"]
    assert len(err) == 1
    assert "mock stream exploded" in err[0][1]
    assert evs[-1][0] == "done"
    app.dependency_overrides.clear()


def test_invoke_rejects_claims_metadata_mismatch(monkeypatch) -> None:  # noqa: ANN001
    client = _build_client(monkeypatch, auth_dev_bypass="1")
    app.dependency_overrides[get_jwt_validator] = lambda: _ValidatorWithClaims(
        {"sub": "u-claims", "tenant_id": "t-claims"},
    )
    app.dependency_overrides[get_graph_runtime] = lambda: _NeverRunRuntime()

    res = client.post(
        "/api/v1/ai/chat/invoke",
        headers={
            "X-Correlation-Id": "cid-claims-mismatch",
            "Authorization": "Bearer any-token",
        },
        json={
            "message": "hello",
            "metadata": {"tenant_id": "t-body", "user_id": "u-body"},
        },
    )

    assert res.status_code == 403
    body = res.json()
    assert body["error"]["code"] == "AI_AUTH_FORBIDDEN"
    assert body["correlation_id"] == "cid-claims-mismatch"
    app.dependency_overrides.clear()
