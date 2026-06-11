"""E2E memory: 2 request cung thread — run_session THAT, chi fake LLM + executor."""
import json
import time

import jwt
from fastapi.testclient import TestClient

from app.api.app import create_app, get_deps
from app.memory import ConversationMemory

SECRET = "test-secret"
CHAT_URL = "/api/v1/ai/chat/stream"


def _token():
    return jwt.encode({"sub": "user-1", "exp": int(time.time()) + 60},
                      SECRET, algorithm="HS256")


# Moi request: SM goi 3 lan (sql -> validator -> composer; sau composer valid
# orchestrator tu finish, khong goi SM nua).
_SM_SCRIPT = [
    {"action": "call_tool", "tool_name": "sql_execute", "forward_data": {},
     "reasoning": "can data", "message": None},
    {"action": "call_tool", "tool_name": "data_validator",
     "forward_data": {"from": "sql_execute"}, "reasoning": "validate", "message": None},
    {"action": "call_tool", "tool_name": "answer_composer",
     "forward_data": {"from": "sql_execute"}, "reasoning": "soan", "message": None},
]


class _LLM:
    def __init__(self):
        self._sm = [json.dumps(d) for d in _SM_SCRIPT]
        self.sm_prompts = []

    def complete(self, *, system, user, role="default", temperature=None):
        if role == "sm":
            self.sm_prompts.append(user)
            return self._sm.pop(0)
        if "Skill: sql_execute" in system:
            return json.dumps({"sql": "SELECT SUM(final_amount) AS doanh_thu FROM orders"})
        if "Skill: answer_composer" in system:
            return json.dumps(
                {"answer": "Doanh thu thang 5/2026 la 15 trieu.\nGợi ý: xem theo kenh?"})
        raise AssertionError(f"LLM call khong mong doi: {system[:80]}")

    def complete_structured(self, *, system, user, output_model,
                            role="default", temperature=None):
        # Route theo output model — on dinh khi cac tool lan luot chuyen sang
        # structured channel (Task 4-6 plan native tool-calling).
        payloads = {
            "SqlDraft": {"sql": "SELECT SUM(final_amount) AS doanh_thu FROM orders"},
            "SemanticCheck": {"ok": True},
            "ValidatorVerdict": {"verdict": "pass", "reason": "du data"},
            "ComposerAnswer": {"answer": "Doanh thu thang 5/2026 la 15 trieu."
                                         "\nGợi ý: xem theo kenh?"},
        }
        return output_model.model_validate(payloads[output_model.__name__])


class _StubExecutor:
    def run(self, sql, row_limit=100):
        return {"columns": ["doanh_thu"], "rows": [[15000000]]}


class _Deps:
    def __init__(self, llm, memory):
        self.llm_sm = llm
        self.llm_tool = llm
        self.deps = {"executor": _StubExecutor(), "row_limit": 100}
        self.max_steps = 6
        self.retry_cap = 2
        self.jwt_secret = SECRET
        self.jwt_issuer = ""
        self.jwt_audience = ""
        self.dev_bypass = False
        self.pending_store = None
        self.memory = memory


def test_two_requests_same_thread_share_memory():
    memory = ConversationMemory(window=10)
    app = create_app()
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token()}"}

    # --- Request 1 ---
    llm1 = _LLM()
    app.dependency_overrides[get_deps] = lambda: _Deps(llm1, memory)
    r1 = client.post(CHAT_URL,
                     json={"message": "doanh thu thang 5/2026",
                           "metadata": {"thread_id": "t-e2e"}},
                     headers=headers)
    assert r1.status_code == 200
    assert "Doanh thu thang 5/2026 la 15 trieu" in r1.text
    # request 1 KHONG co memory cu — khong co turn JSON nao duoc inject
    # (skill.md SM co nhac ten khoi "[Cac luot gan nhat]" nen khong assert ten khoi)
    assert all('"user": "' not in p for p in llm1.sm_prompts)
    # sau done: ghi dung 1 luot
    ctxm = memory.get_context("t-e2e")
    assert len(ctxm["turns"]) == 1
    assert ctxm["turns"][0]["user"] == "doanh thu thang 5/2026"
    assert "15 trieu" in ctxm["turns"][0]["answer"]

    # --- Request 2: cau noi tiep, cung thread ---
    llm2 = _LLM()
    app.dependency_overrides[get_deps] = lambda: _Deps(llm2, memory)
    r2 = client.post(CHAT_URL,
                     json={"message": "con thang truoc thi sao?",
                           "metadata": {"thread_id": "t-e2e"}},
                     headers=headers)
    assert r2.status_code == 200
    # SM cua request 2 thay lich su luot 1 (turn JSON inject vao prompt)
    assert any('"user": "doanh thu thang 5/2026"' in p for p in llm2.sm_prompts)
    assert any("15 trieu" in p for p in llm2.sm_prompts)
    # sau request 2: 2 luot trong memory
    assert len(memory.get_context("t-e2e")["turns"]) == 2


def test_other_thread_does_not_see_memory():
    memory = ConversationMemory(window=10)
    memory.append_turn("t-khac", "cau cu", "tra loi cu")
    app = create_app()
    client = TestClient(app)
    llm = _LLM()
    app.dependency_overrides[get_deps] = lambda: _Deps(llm, memory)
    r = client.post(CHAT_URL,
                    json={"message": "doanh thu thang 5/2026",
                          "metadata": {"thread_id": "t-moi"}},
                    headers={"Authorization": f"Bearer {_token()}"})
    assert r.status_code == 200
    assert all("cau cu" not in p for p in llm.sm_prompts)
