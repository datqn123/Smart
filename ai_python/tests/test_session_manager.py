import json
import pytest
from app.tools.session_manager import Decision, analyze
from app.graph.state import new_session_state


class _LLM:
    def __init__(self, payload):
        self._p = payload; self.calls = []
    def complete(self, *, system, user, role="default", temperature=None):
        self.calls.append({"role": role, "system": system, "user": user})
        return self._p if isinstance(self._p, str) else json.dumps(self._p)


def test_decision_model_validates_action():  # fact-sm-decision
    d = Decision.model_validate({"action": "call_tool", "tool_name": "sql_execute",
                                 "forward_data": {}, "reasoning": "r"})
    assert d.action == "call_tool"
    with pytest.raises(Exception):
        Decision.model_validate({"action": "nuke", "reasoning": "r"})


def test_decision_rejects_unregistered_tool():  # fact-registry-static
    with pytest.raises(Exception):
        Decision.model_validate({"action": "call_tool", "tool_name": "rm_rf",
                                 "reasoning": "r"})


def test_analyze_reloads_skill_each_call(monkeypatch):  # fact-sm-reanalyze
    loads = []
    monkeypatch.setattr("app.tools.session_manager.load_skill",
                        lambda name: loads.append(name) or "SM-SKILL")
    llm = _LLM({"action": "call_tool", "tool_name": "sql_execute",
                "forward_data": {}, "reasoning": "r"})
    st = new_session_state(raw_require="R", thread_id="t")
    analyze(st, llm=llm)
    analyze(st, llm=llm)
    assert loads == ["session_manager", "session_manager"]
    assert llm.calls[0]["role"] == "sm"


def test_analyze_parses_into_decision():
    llm = _LLM({"action": "finish", "tool_name": None, "forward_data": {},
                "reasoning": "done", "message": "xong"})
    st = new_session_state(raw_require="R", thread_id="t")
    d = analyze(st, llm=llm)
    assert isinstance(d, Decision) and d.action == "finish"


def test_analyze_injects_memory_blocks():
    llm = _LLM({"action": "finish", "tool_name": None, "forward_data": {},
                "reasoning": "x", "message": "ok"})
    st = new_session_state(raw_require="con thang truoc thi sao?", thread_id="t")
    mem = {"summary": "User xem doanh thu thang 5/2026",
           "turns": [{"user": "doanh thu thang 5?", "answer": "15 trieu"}]}
    analyze(st, llm=llm, memory_context=mem)
    user = llm.calls[0]["user"]
    assert "[Tom tat hoi thoai cu]: User xem doanh thu thang 5/2026" in user
    assert "[Cac luot gan nhat]:" in user
    assert "doanh thu thang 5?" in user


def test_analyze_no_memory_blocks_when_absent():
    llm = _LLM({"action": "finish", "tool_name": None, "forward_data": {},
                "reasoning": "x", "message": "ok"})
    st = new_session_state(raw_require="doanh thu quy 1", thread_id="t")
    analyze(st, llm=llm)
    user = llm.calls[0]["user"]
    assert "[Tom tat hoi thoai cu]" not in user
    assert "[Cac luot gan nhat]" not in user


def test_decision_parses_resolved_require():
    llm = _LLM({"action": "call_tool", "tool_name": "sql_execute", "forward_data": {},
                "reasoning": "noi tiep", "message": None,
                "resolved_require": "doanh thu thang 4/2026"})
    st = new_session_state(raw_require="con thang truoc thi sao?", thread_id="t")
    d = analyze(st, llm=llm)
    assert d.resolved_require == "doanh thu thang 4/2026"


def test_decision_resolved_require_default_none():
    llm = _LLM({"action": "finish", "tool_name": None, "forward_data": {},
                "reasoning": "x", "message": "ok"})
    d = analyze(new_session_state(raw_require="x", thread_id="t"), llm=llm)
    assert d.resolved_require is None
