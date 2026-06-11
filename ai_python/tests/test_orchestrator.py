import json
import pytest
from app.graph.orchestrator import run_session
from app.harness.turn_context import TurnContext


class ScriptLLM:
    def __init__(self, decisions):
        self._d = [json.dumps(x) for x in decisions]
    def complete(self, *, system, user, role="default", temperature=None):
        if role == "sm":
            return self._d.pop(0)
        return "{}"


async def _collect(gen):
    return [e async for e in gen]


def _deps_with_fake_dispatch(monkeypatch, results_by_tool):
    calls = []
    def fake_dispatch(tool_name, *, raw_require, upstream_data, llm, deps,
                      validator_passed=True, memory_summary=None):
        calls.append(tool_name)
        return results_by_tool[tool_name]
    monkeypatch.setattr("app.graph.orchestrator.dispatch", fake_dispatch)
    return calls


@pytest.mark.asyncio
async def test_happy_path_order_sql_validate_compose(monkeypatch):
    calls = _deps_with_fake_dispatch(monkeypatch, {
        "sql_execute": {"output": {"rows": [{"id": 1}]}, "valid": True, "validation_error": None},
        "data_validator": {"output": {"verdict": "pass", "reason": "ok"}, "valid": True, "validation_error": None},
        "answer_composer": {"output": {"answer": "Tra loi.\nGợi ý: tiep?"}, "valid": True, "validation_error": None},
    })
    llm = ScriptLLM([
        {"action": "call_tool", "tool_name": "sql_execute", "forward_data": {}, "reasoning": "r"},
        {"action": "call_tool", "tool_name": "data_validator", "forward_data": {"from": "sql_execute"}, "reasoning": "r"},
        {"action": "call_tool", "tool_name": "answer_composer", "forward_data": {"from": "sql_execute"}, "reasoning": "r"},
        {"action": "finish", "tool_name": None, "forward_data": {}, "reasoning": "done"},
    ])
    ctx = TurnContext(raw_require="liet ke khach hang", user_id="u", thread_id="t")
    events = await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={}, max_steps=6, retry_cap=2))
    assert calls == ["sql_execute", "data_validator", "answer_composer"]
    types = [e["type"] for e in events]
    assert "answer" in types and "done" in types


@pytest.mark.asyncio
async def test_validator_fail_triggers_clarify_and_pause(monkeypatch):
    _deps_with_fake_dispatch(monkeypatch, {
        "sql_execute": {"output": {"rows": []}, "valid": True, "validation_error": None},
        "data_validator": {"output": {"verdict": "fail", "reason": "rong"}, "valid": True, "validation_error": None},
    })
    llm = ScriptLLM([
        {"action": "call_tool", "tool_name": "sql_execute", "forward_data": {}, "reasoning": "r"},
        {"action": "call_tool", "tool_name": "data_validator", "forward_data": {"from": "sql_execute"}, "reasoning": "r"},
        {"action": "request_clarification", "tool_name": None, "forward_data": {}, "reasoning": "fail", "message": "Khoang thoi gian nao?"},
    ])
    ctx = TurnContext(raw_require="doanh thu", user_id="u", thread_id="t")
    events = await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={}, max_steps=6, retry_cap=2))
    clarify = [e for e in events if e["type"] == "clarify"]
    assert clarify and clarify[0]["data"]["message"] == "Khoang thoi gian nao?"


@pytest.mark.asyncio
async def test_budget_exhaustion_aborts_safely(monkeypatch):
    _deps_with_fake_dispatch(monkeypatch, {
        "sql_execute": {"output": {"rows": [{"id": 1}]}, "valid": True, "validation_error": None},
    })
    llm = ScriptLLM([{"action": "call_tool", "tool_name": "sql_execute",
                      "forward_data": {}, "reasoning": "loop"} for _ in range(20)])
    ctx = TurnContext(raw_require="x", user_id="u", thread_id="t")
    events = await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={}, max_steps=3, retry_cap=2))
    err = [e for e in events if e["type"] == "error"]
    assert err and "gioi han" in err[0]["data"]["message"].lower()


@pytest.mark.asyncio
async def test_resume_continues_from_snapshot(monkeypatch):  # fact-validator-hitl
    calls = _deps_with_fake_dispatch(monkeypatch, {
        "data_validator": {"output": {"verdict": "pass", "reason": "ok"}, "valid": True, "validation_error": None},
        "answer_composer": {"output": {"answer": "OK.\nGợi ý: tiep?"}, "valid": True, "validation_error": None},
    })
    llm = ScriptLLM([
        {"action": "call_tool", "tool_name": "data_validator", "forward_data": {"from": "sql_execute"}, "reasoning": "revalidate"},
        {"action": "call_tool", "tool_name": "answer_composer", "forward_data": {"from": "sql_execute"}, "reasoning": "compose"},
        {"action": "finish", "tool_name": None, "forward_data": {}, "reasoning": "done"},
    ])
    ctx = TurnContext(raw_require="doanh thu", user_id="u", thread_id="t",
                      clarification_response="Quy 1 nam 2026")
    snapshot = {"raw_require": "doanh thu", "thread_id": "t",
                "tool_results": {"sql_execute": {"rows": [{"rev": 100}]}},
                "history": [], "retry_counts": {},
                "pending_clarification": {"message": "Khi nao?"}}
    events = await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={},
                                        max_steps=6, retry_cap=2, resume_snapshot=snapshot))
    assert "sql_execute" in snapshot["tool_results"]   # data cu giu nguyen
    assert any(e["type"] == "answer" for e in events)


def test_build_upstream_overlay_keeps_rows_from_other_tools():
    # Regression: SM forward tu data_validator lam answer_composer mat
    # rows cua sql_execute -> tra loi 'khong co du lieu' du SQL co data.
    from app.graph.orchestrator import _build_upstream
    state = {"tool_results": {
        "sql_execute": {"rows": [{"name": "A", "tong_ton": 9}], "columns": ["name", "tong_ton"], "error": None},
        "data_validator": {"verdict": "pass", "reason": "ok"},
    }}
    up = _build_upstream(state, {"from": "data_validator"})
    assert up["rows"] == [{"name": "A", "tong_ton": 9}]   # rows van con
    assert up["verdict"] == "pass"                         # source overlay len tren


def test_build_upstream_named_source_wins_on_conflict():
    from app.graph.orchestrator import _build_upstream
    state = {"tool_results": {
        "tool_a": {"value": "old"},
        "tool_b": {"value": "new"},
    }}
    up = _build_upstream(state, {"from": "tool_b"})
    assert up["value"] == "new"


@pytest.mark.asyncio
async def test_dispatch_uses_resolved_require_and_memory_summary(monkeypatch):
    captured = {}

    def fake_dispatch(tool_name, *, raw_require, upstream_data, llm, deps,
                      validator_passed=True, memory_summary=None):
        captured["raw_require"] = raw_require
        captured["memory_summary"] = memory_summary
        return {"output": {"verdict": "pass", "reason": "ok"},
                "valid": True, "validation_error": None}

    monkeypatch.setattr("app.graph.orchestrator.dispatch", fake_dispatch)
    llm = ScriptLLM([
        {"action": "call_tool", "tool_name": "data_validator", "forward_data": {},
         "reasoning": "r", "resolved_require": "doanh thu thang 4/2026"},
        {"action": "finish", "tool_name": None, "forward_data": {}, "reasoning": "done"},
    ])
    ctx = TurnContext(raw_require="con thang truoc?", user_id="u", thread_id="t")
    mem = {"summary": "dang xem doanh thu thang 5/2026", "turns": []}
    await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={},
                               memory_context=mem))
    assert captured["raw_require"] == "doanh thu thang 4/2026"
    assert captured["memory_summary"] == "dang xem doanh thu thang 5/2026"


@pytest.mark.asyncio
async def test_done_event_contains_raw_require():
    llm = ScriptLLM([
        {"action": "finish", "tool_name": None, "forward_data": {},
         "reasoning": "x", "message": "tra loi"},
    ])
    ctx = TurnContext(raw_require="cau hoi goc", user_id="u", thread_id="t")
    events = await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={}))
    done = [e for e in events if e["type"] == "done"][0]
    assert done["data"]["raw_require"] == "cau hoi goc"


@pytest.mark.asyncio
async def test_resume_restores_raw_require_from_snapshot():
    llm = ScriptLLM([
        {"action": "finish", "tool_name": None, "forward_data": {},
         "reasoning": "x", "message": "ok"},
    ])
    ctx = TurnContext(raw_require="thang 4", user_id="u", thread_id="t",
                      clarification_response="thang 4")
    snap = {"raw_require": "doanh thu", "tool_results": {}, "history": [],
            "retry_counts": {}}
    events = await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={},
                                        resume_snapshot=snap))
    done = [e for e in events if e["type"] == "done"][0]
    assert done["data"]["raw_require"].startswith("doanh thu")
    assert "[Bo sung tu user]: thang 4" in done["data"]["raw_require"]
