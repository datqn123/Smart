import json
import pytest
from app.graph.orchestrator import run_session
from app.harness.turn_context import TurnContext


class RoutingLLM:
    """FakeLLM that cho E2E: SM (role='sm') tra decision theo hang doi;
    tool (role='default') tra output dung schema theo skill dang nap."""
    def __init__(self, sm_decisions):
        self._sm = [json.dumps(d) for d in sm_decisions]

    def complete(self, *, system, user, role="default", temperature=None):
        if role == "sm":
            return self._sm.pop(0)
        if "Skill: sql_execute" in system:
            return json.dumps({"sql": "SELECT id, name FROM customers LIMIT 5"})
        if "Skill: answer_composer" in system:
            return json.dumps({"answer": "Day la 5 khach hang.\nGợi ý: xem don hang?"})
        raise AssertionError(f"role/tool khong nhan dien duoc:\n{system[:80]}")

    def complete_structured(self, *, system, user, output_model,
                            role="default", temperature=None):
        payloads = {
            "SqlDraft": {"sql": "SELECT id, name FROM customers LIMIT 5"},
            "SemanticCheck": {"ok": True},
            "ValidatorVerdict": {"verdict": "pass", "reason": "du data"},
            "ComposerAnswer": {"answer": "Day la 5 khach hang.\nGợi ý: xem don hang?"},
        }
        return output_model.model_validate(payloads[output_model.__name__])


@pytest.mark.asyncio
async def test_e2e_require_to_sse_answer(stub_sql):  # done-condition happy path
    llm = RoutingLLM([
        {"action": "call_tool", "tool_name": "sql_execute", "forward_data": {}, "reasoning": "lay data"},
        {"action": "call_tool", "tool_name": "data_validator", "forward_data": {"from": "sql_execute"}, "reasoning": "validate"},
        {"action": "call_tool", "tool_name": "answer_composer", "forward_data": {"from": "sql_execute"}, "reasoning": "soan"},
        {"action": "finish", "tool_name": None, "forward_data": {}, "reasoning": "xong"},
    ])
    ctx = TurnContext(raw_require="liet ke 5 khach hang moi nhat", user_id="u", thread_id="t")
    events = [e async for e in run_session(
        ctx, llm_sm=llm, llm_tool=llm,
        deps={"executor": stub_sql, "row_limit": 100}, max_steps=6, retry_cap=2)]

    tool_calls = [e["data"]["tool_name"] for e in events if e["type"] == "tool_call"]
    assert tool_calls == ["sql_execute", "data_validator", "answer_composer"]
    assert stub_sql.executed and stub_sql.executed[0].lower().startswith("select")
    answer = [e for e in events if e["type"] == "answer"][0]
    assert "Gợi ý:" in answer["data"]["text"]
    assert events[-1]["type"] == "done"
