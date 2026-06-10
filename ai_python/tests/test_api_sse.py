import time, json, jwt
from fastapi.testclient import TestClient
from app.api.app import create_app, get_deps

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


def _client(monkeypatch):
    async def fake_run_session(ctx, **kw):
        yield {"type": "tool_call", "data": {"tool_name": "sql_execute"}}
        yield {"type": "answer", "data": {"text": "Doanh thu quy 1 la 100."}}
        yield {"type": "done", "data": {"thread_id": ctx.thread_id}}
    monkeypatch.setattr("app.api.app.run_session", fake_run_session)
    app = create_app()
    app.dependency_overrides[get_deps] = lambda: _FakeDeps()
    return TestClient(app)


def test_chat_streams_sse_nested_under_harness(monkeypatch):  # fact-sse + R6
    client = _client(monkeypatch)
    resp = client.post("/chat", json={"raw_require": "doanh thu quy 1"},
                       headers={"Authorization": f"Bearer {_token()}"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    lines = [l for l in resp.text.splitlines() if l.startswith("data: ")]
    first = json.loads(lines[0][len("data: "):])
    assert set(first.keys()) == {"harness"}
    assert first["harness"]["type"] == "tool_call"
    assert "Doanh thu quy 1" in resp.text


def test_chat_rejects_invalid_jwt(monkeypatch):  # fact-auth
    client = _client(monkeypatch)
    resp = client.post("/chat", json={"raw_require": "x"},
                       headers={"Authorization": "Bearer garbage"})
    assert resp.status_code == 401
