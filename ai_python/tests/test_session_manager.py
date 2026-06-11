import pytest
from app.config.llm_client import ToolCallError
from app.tools.session_manager import Decision, analyze
from app.graph.state import new_session_state
from tests.conftest import FakeLLM


def _st(require="R", history=None):
    st = new_session_state(raw_require=require, thread_id="t")
    if history:
        st["history"] = history
    return st


def test_toolcall_sql_execute_maps_to_call_tool(monkeypatch):  # fact-sm-decision
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "SM-SKILL")
    llm = FakeLLM(tool_selects=[("sql_execute",
                                 {"reasoning": "can data",
                                  "require": "doanh thu thang 6/2026"})])
    d = analyze(_st("doanh thu thang nay"), llm=llm)
    assert d.action == "call_tool" and d.tool_name == "sql_execute"
    assert d.resolved_require == "doanh thu thang 6/2026"
    assert llm.tool_select_calls[0]["role"] == "sm"
    # SM nhin thay du 5 API tools tu registry
    assert set(llm.tool_select_calls[0]["tools"]) == {
        "sql_execute", "data_validator", "answer_composer",
        "finish", "request_clarification"}


def test_same_tool_after_invalid_becomes_retry(monkeypatch):  # fact-sm-errorclass
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "S")
    hist = [{"action": "call_tool", "tool": "sql_execute", "valid": False,
             "output": {"error": "loi DB"}}]
    llm = FakeLLM(tool_selects=[("sql_execute", {"reasoning": "thu lai",
                                                 "require": "R"})])
    d = analyze(_st(history=hist), llm=llm)
    assert d.action == "retry_tool" and d.tool_name == "sql_execute"


def test_same_tool_after_valid_stays_call_tool(monkeypatch):
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "S")
    hist = [{"action": "call_tool", "tool": "sql_execute", "valid": True,
             "output": {"rows": []}}]
    llm = FakeLLM(tool_selects=[("sql_execute", {"reasoning": "cau hoi khac",
                                                 "require": "R2"})])
    d = analyze(_st(history=hist), llm=llm)
    assert d.action == "call_tool"


def test_finish_maps_message(monkeypatch):
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "S")
    llm = FakeLLM(tool_selects=[("finish", {"reasoning": "chao hoi",
                                            "message": "Chao ban!"})])
    d = analyze(_st("chao ban"), llm=llm)
    assert d.action == "finish" and d.message == "Chao ban!"


def test_clarify_maps_message(monkeypatch):
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "S")
    llm = FakeLLM(tool_selects=[("request_clarification",
                                 {"reasoning": "mo ho", "message": "Thang nao?"})])
    d = analyze(_st("cai do?"), llm=llm)
    assert d.action == "request_clarification" and d.message == "Thang nao?"


def test_unknown_tool_then_valid_uses_retry_attempt(monkeypatch):
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "S")
    llm = FakeLLM(tool_selects=[
        ("rm_rf_database", {"reasoning": "bia"}),                 # attempt 1 hong
        ("finish", {"reasoning": "ok", "message": "xong"})])      # attempt 2
    d = analyze(_st(), llm=llm)
    assert d.action == "finish"
    assert len(llm.tool_select_calls) == 2
    assert "[Loi attempt truoc" in llm.tool_select_calls[1]["user"]


def test_bad_args_two_attempts_falls_back_finish(monkeypatch):
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "S")
    llm = FakeLLM(tool_selects=[("finish", {"reasoning": "thieu message"}),
                                ("sql_execute", {"reasoning": "thieu require"})])
    d = analyze(_st(), llm=llm)
    assert d.action == "finish"
    assert "Xin loi" in (d.message or "")


def test_toolcall_error_falls_back(monkeypatch):
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "S")
    llm = FakeLLM(tool_selects=[ToolCallError("no tool"), ToolCallError("no tool")])
    d = analyze(_st(), llm=llm)
    assert d.action == "finish"


def test_analyze_reloads_skill_each_call(monkeypatch):  # fact-sm-reanalyze
    loads = []
    monkeypatch.setattr("app.tools.session_manager.load_skill",
                        lambda name: loads.append(name) or "SM-SKILL")
    llm = FakeLLM(tool_selects=[("finish", {"reasoning": "x", "message": "ok"}),
                                ("finish", {"reasoning": "x", "message": "ok"})])
    st = _st()
    analyze(st, llm=llm)
    analyze(st, llm=llm)
    assert loads == ["session_manager", "session_manager"]


def test_analyze_injects_memory_blocks(monkeypatch):
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "SM-SKILL")
    llm = FakeLLM(tool_selects=[("finish", {"reasoning": "x", "message": "ok"})])
    mem = {"summary": "User xem doanh thu thang 5/2026",
           "turns": [{"user": "doanh thu thang 5?", "answer": "15 trieu"}]}
    analyze(_st("con thang truoc thi sao?"), llm=llm, memory_context=mem)
    user = llm.tool_select_calls[0]["user"]
    assert "[Tom tat hoi thoai cu]: User xem doanh thu thang 5/2026" in user
    assert "[Cac luot gan nhat]:" in user
    assert "doanh thu thang 5?" in user


def test_analyze_no_memory_blocks_when_absent(monkeypatch):
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "SM-SKILL")
    llm = FakeLLM(tool_selects=[("finish", {"reasoning": "x", "message": "ok"})])
    analyze(_st("doanh thu quy 1"), llm=llm)
    user = llm.tool_select_calls[0]["user"]
    assert "[Tom tat hoi thoai cu]" not in user
    assert "[Cac luot gan nhat]" not in user


def test_resolved_require_used_when_no_require_field(monkeypatch):
    # validator/composer khong co field require — resolved_require van map.
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "S")
    llm = FakeLLM(tool_selects=[("data_validator",
                                 {"reasoning": "validate",
                                  "resolved_require": "doanh thu thang 4/2026"})])
    d = analyze(_st("con thang truoc?"), llm=llm)
    assert d.resolved_require == "doanh thu thang 4/2026"


def test_decision_rejects_unregistered_tool():  # fact-registry-static (luoi 2)
    with pytest.raises(Exception):
        Decision.model_validate({"action": "call_tool", "tool_name": "rm_rf",
                                 "reasoning": "r"})
