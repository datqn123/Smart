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
                      validator_passed=True):
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
