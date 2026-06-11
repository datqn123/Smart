import time, json, jwt
from fastapi.testclient import TestClient
from app.api.app import create_app, get_deps
from app.memory import ConversationMemory

SECRET = "test-secret"


def _token():
    return jwt.encode({"sub": "user-1", "exp": int(time.time()) + 60}, SECRET, algorithm="HS256")


class _FakeDeps:
    def __init__(self):
        self.llm_sm = self.llm_tool = None
        self.deps = {}
        self.max_steps = 6
        self.retry_cap = 2
        self.jwt_secret = SECRET
        self.jwt_issuer = ""
        self.jwt_audience = ""
        self.dev_bypass = False
        self.pending_store = None
        self.memory = ConversationMemory(window=10)


def _client(monkeypatch):
    async def fake_run_session(ctx, **kw):
        yield {"type": "tool_call", "data": {"tool_name": "sql_execute"}}
        yield {"type": "answer", "data": {"text": "Doanh thu quy 1 la 100."}}
        yield {"type": "done", "data": {"thread_id": ctx.thread_id}}
    monkeypatch.setattr("app.api.app.run_session", fake_run_session)
    app = create_app()
    app.dependency_overrides[get_deps] = lambda: _FakeDeps()
    return TestClient(app)


CHAT_URL = "/api/v1/ai/chat/stream"


def test_chat_streams_sse_with_event_fields(monkeypatch):  # Spring relay compat: event: + data: lines
    client = _client(monkeypatch)
    resp = client.post(CHAT_URL, json={"message": "doanh thu quy 1"},
                       headers={"Authorization": f"Bearer {_token()}"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    event_lines = [l for l in resp.text.splitlines() if l.startswith("event: ")]
    assert any("progress" in l for l in event_lines)      # tool_call -> progress
    assert any("delta_full" in l for l in event_lines)    # answer -> delta_full
    assert any("done" in l for l in event_lines)
    assert "Doanh thu quy 1" in resp.text


def test_chat_rejects_invalid_jwt(monkeypatch):  # fact-auth
    client = _client(monkeypatch)
    resp = client.post(CHAT_URL, json={"message": "x"},
                       headers={"Authorization": "Bearer garbage"})
    assert resp.status_code == 401


def test_chat_accepts_spring_metadata_thread_id(monkeypatch):  # Spring relay body contract
    client = _client(monkeypatch)
    resp = client.post(CHAT_URL,
                       json={"message": "test", "metadata": {"thread_id": "t-abc", "user_id": "u1"}},
                       headers={"Authorization": f"Bearer {_token()}"})
    assert resp.status_code == 200


def _client_with_deps(monkeypatch, fake_run_session):
    monkeypatch.setattr("app.api.app.run_session", fake_run_session)
    app = create_app()
    deps = _FakeDeps()
    app.dependency_overrides[get_deps] = lambda: deps
    return TestClient(app), deps


def test_chat_writes_memory_after_done(monkeypatch):
    async def fake_run_session(ctx, **kw):
        yield {"type": "answer", "data": {"text": "Doanh thu la 100."}}
        yield {"type": "done", "data": {"thread_id": ctx.thread_id,
                                        "raw_require": ctx.raw_require}}
    client, deps = _client_with_deps(monkeypatch, fake_run_session)
    client.post(CHAT_URL,
                json={"message": "doanh thu", "metadata": {"thread_id": "t-mem"}},
                headers={"Authorization": f"Bearer {_token()}"})
    assert deps.memory.get_context("t-mem")["turns"] == [
        {"user": "doanh thu", "answer": "Doanh thu la 100."}]


def test_chat_clarify_does_not_write_memory(monkeypatch):
    async def fake_run_session(ctx, **kw):
        yield {"type": "clarify", "data": {"message": "thang nao?",
                                           "thread_id": ctx.thread_id}}
    client, deps = _client_with_deps(monkeypatch, fake_run_session)
    client.post(CHAT_URL,
                json={"message": "doanh thu", "metadata": {"thread_id": "t-mem2"}},
                headers={"Authorization": f"Bearer {_token()}"})
    assert deps.memory.get_context("t-mem2")["turns"] == []


def test_chat_passes_memory_context_to_run_session(monkeypatch):
    seen = {}

    async def fake_run_session(ctx, **kw):
        seen["memory_context"] = kw.get("memory_context")
        yield {"type": "done", "data": {"thread_id": ctx.thread_id,
                                        "raw_require": ctx.raw_require}}
    client, deps = _client_with_deps(monkeypatch, fake_run_session)
    deps.memory.append_turn("t-mem3", "cau 1", "tra loi 1")
    client.post(CHAT_URL,
                json={"message": "cau 2", "metadata": {"thread_id": "t-mem3"}},
                headers={"Authorization": f"Bearer {_token()}"})
    assert seen["memory_context"]["turns"][0]["user"] == "cau 1"
