import pytest
from app.graph.orchestrator import run_session
from app.harness.turn_context import TurnContext
from tests.conftest import FakeLLM


@pytest.mark.asyncio
async def test_e2e_require_to_sse_answer(stub_sql):  # done-condition happy path
    # MOT FakeLLM cho ca SM (tool_selects) lan tool (structured, theo thu tu
    # chay: SqlDraft -> SemanticCheck -> Verdict -> ComposerAnswer).
    llm = FakeLLM(
        tool_selects=[("sql_execute", {"reasoning": "lay data",
                                       "require": "liet ke 5 khach hang moi nhat"}),
                      ("data_validator", {"reasoning": "validate"}),
                      ("answer_composer", {"reasoning": "soan"})],
        structured=[{"sql": "SELECT id, name FROM customers LIMIT 5"},
                    {"ok": True},
                    {"verdict": "pass", "reason": "du data"},
                    {"answer": "Day la 5 khach hang.\nGợi ý: xem don hang?"}])
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
