from __future__ import annotations

import asyncio
from types import SimpleNamespace


def _request(message: str, *, thread_id: str = "thread-1", clarification=None):
    from app.api.schemas import ChatMetadata, ChatOptions, ChatRequest

    return ChatRequest(
        message=message,
        metadata=ChatMetadata(user_id="u1", tenant_id="t1", thread_id=thread_id, schema_version="v1"),
        options=ChatOptions(clarification=clarification),
    )


def _ctx():
    from app.harness.tool_registry import TurnContext

    return TurnContext(
        tenant_id="t1",
        user_id="u1",
        thread_id="thread-1",
        correlation_id="corr-1",
        bearer_token=None,
        schema_version="v1",
    )


class _FakeClient:
    def __init__(self, decision) -> None:
        self._decision = decision

    async def astructured_predict(self, messages, schema):  # noqa: ANN001
        return self._decision


def _orchestrator(decision):
    from app.harness.orchestrator import HarnessOrchestrator
    from app.harness.tool_registry import ToolRegistry

    return HarnessOrchestrator(
        llm_registry=SimpleNamespace(get=lambda role: _FakeClient(decision)),
        tool_registry=ToolRegistry(),
        policy=SimpleNamespace(check=lambda *a, **k: None),
        settings=SimpleNamespace(harness_max_steps=6, harness_planner_role="harness_planner"),
        harness=SimpleNamespace(_enabled=False),
    )


def test_clarify_action_emits_clarify_event() -> None:
    from app.harness.orchestrator import ClarifyEvent
    from app.harness.scratchpad import TurnScratchpad
    from app.harness.tool_registry import ClarifyRequest, DecisionSchema
    from langchain_core.messages import HumanMessage

    decision = DecisionSchema(
        action="clarify",
        clarify=ClarifyRequest(
            questions=["Bạn muốn xem doanh thu của khoảng thời gian nào?"],
            suggested_rewrite="Doanh thu tháng này là bao nhiêu?",
        ),
    )
    orch = _orchestrator(decision)
    scratchpad = TurnScratchpad(messages=[HumanMessage(content="doanh thu")])

    async def _collect():
        return [ev async for ev in orch.run(scratchpad, _ctx())]

    events = asyncio.run(_collect())
    clar = [e for e in events if isinstance(e, ClarifyEvent)]
    assert len(clar) == 1
    assert clar[0].questions == ["Bạn muốn xem doanh thu của khoảng thời gian nào?"]
    assert clar[0].suggested_rewrite == "Doanh thu tháng này là bao nhiêu?"
    assert clar[0].original_question == "doanh thu"


def test_clarify_without_questions_falls_back_to_final_answer() -> None:
    from app.harness.orchestrator import ClarifyEvent, FinalAnswerEvent
    from app.harness.scratchpad import TurnScratchpad
    from app.harness.tool_registry import ClarifyRequest, DecisionSchema
    from langchain_core.messages import HumanMessage

    decision = DecisionSchema(
        action="clarify",
        clarify=ClarifyRequest(questions=[], suggested_rewrite=""),
        final_answer="Bạn cần hỗ trợ gì?",
    )
    orch = _orchestrator(decision)
    scratchpad = TurnScratchpad(messages=[HumanMessage(content="x")])

    async def _collect():
        return [ev async for ev in orch.run(scratchpad, _ctx())]

    events = asyncio.run(_collect())
    assert not [e for e in events if isinstance(e, ClarifyEvent)]
    finals = [e for e in events if isinstance(e, FinalAnswerEvent)]
    assert finals and finals[0].text == "Bạn cần hỗ trợ gì?"


def test_clarify_event_maps_to_domain_clarify_sse_chunk() -> None:
    from app.api.runtime import _event_to_stream_chunk
    from app.harness.orchestrator import ClarifyEvent

    chunk = _event_to_stream_chunk(
        ClarifyEvent(
            questions=["Khoảng thời gian nào?"],
            suggested_rewrite="Doanh thu tháng này?",
            original_question="doanh thu",
        )
    )
    # Nested under "harness" so it survives routes._extract_partial_update flatten.
    assert "domain_clarify_sse" in chunk["harness"]
    sse = chunk["harness"]["domain_clarify_sse"]
    assert sse["clarifyKind"] == "harness_data_query"
    assert sse["questions"] == ["Khoảng thời gian nào?"]
    assert sse["suggestedRewrite"] == "Doanh thu tháng này?"
    assert sse["continuationContext"]["originalQuestion"] == "doanh thu"
    assert sse["clarifyId"] == sse["continuationContext"]["clarifyId"]


def test_resume_message_uses_suggested_rewrite_when_accepted() -> None:
    from app.api.runtime import _resume_scratchpad_message
    from app.api.schemas import ClarificationOptions

    req = _request(
        "Doanh thu tháng này?",
        clarification=ClarificationOptions(
            clarify_id="abc",
            clarify_kind="harness_data_query",
            suggested_rewrite="Doanh thu tháng này?",
            continuation_context={"clarifyKind": "harness_data_query", "originalQuestion": "doanh thu"},
        ),
    )
    assert _resume_scratchpad_message(req) == "Doanh thu tháng này?"


def test_resume_message_recombines_freeform_answer_with_original() -> None:
    from app.api.runtime import _resume_scratchpad_message
    from app.api.schemas import ClarificationOptions

    req = _request(
        "tháng này",
        clarification=ClarificationOptions(
            clarify_id="abc",
            clarify_kind="harness_data_query",
            continuation_context={"clarifyKind": "harness_data_query", "originalQuestion": "doanh thu"},
        ),
    )
    out = _resume_scratchpad_message(req)
    assert out.startswith("doanh thu")
    assert "tháng này" in out


def test_resume_message_untouched_for_non_clarify_requests() -> None:
    from app.api.runtime import _resume_scratchpad_message

    assert _resume_scratchpad_message(_request("doanh thu hôm nay")) == "doanh thu hôm nay"


def test_duplicate_tool_call_short_circuits_loop() -> None:
    """Repeating the same (tool, args) must stop the loop, not burn the budget."""
    from app.harness.orchestrator import FinalAnswerEvent, ProgressEvent
    from app.harness.scratchpad import TurnScratchpad
    from app.harness.tool_registry import DecisionSchema, ToolCall, ToolManifest, ToolResult
    from langchain_core.messages import HumanMessage

    decision = DecisionSchema(
        action="call_tool",
        tool_call=ToolCall(tool_name="sql_query", args={"query": "x"}),
    )

    class _Tool:
        manifest = ToolManifest(name="sql_query", description="d", args_schema="{}")
        calls = 0

        async def invoke(self, args, ctx):  # noqa: ANN001
            _Tool.calls += 1
            return ToolResult(ok=True, output={}, observation_text="SQL query returned 0 rows.")

    from app.harness.tool_registry import ToolRegistry

    registry = ToolRegistry()
    tool = _Tool()
    registry.register(tool.manifest, tool)

    from app.harness.orchestrator import HarnessOrchestrator

    orch = HarnessOrchestrator(
        llm_registry=SimpleNamespace(get=lambda role: _FakeClient(decision)),
        tool_registry=registry,
        policy=SimpleNamespace(check=lambda *a, **k: None),
        settings=SimpleNamespace(harness_max_steps=6, harness_planner_role="harness_planner"),
        harness=SimpleNamespace(_enabled=False),
    )
    scratchpad = TurnScratchpad(messages=[HumanMessage(content="liệt kê sản phẩm danh mục gia vị")])

    async def _collect():
        return [ev async for ev in orch.run(scratchpad, _ctx())]

    events = asyncio.run(_collect())
    # Tool runs once; the duplicate second decision short-circuits to a final answer.
    assert _Tool.calls == 1
    assert any(isinstance(e, FinalAnswerEvent) for e in events)
    steps = [e.text for e in events if isinstance(e, ProgressEvent)]
    assert len(steps) <= 2  # did not run all 6 steps


def test_empty_rows_observation_is_actionable_and_includes_sql() -> None:
    from app.graph.tools.sql_query import _format_rows_observation

    obs = _format_rows_observation([], sql="SELECT * FROM products WHERE c.name ILIKE 'gia vị'")
    assert "0 rows" in obs
    assert "Do NOT re-run" in obs
    assert "ILIKE 'gia vị'" in obs


def test_data_query_clarify_resume_runs_loop_not_hitl() -> None:
    """A clarification reply with no pending draft tool must re-run the loop."""
    from app.harness.orchestrator import FinalAnswerEvent
    from app.harness.scratchpad import TurnScratchpad
    from app.harness.tool_registry import DecisionSchema
    from langchain_core.messages import HumanMessage

    decision = DecisionSchema(action="final_answer", final_answer="Doanh thu tháng này là 100 triệu.")
    orch = _orchestrator(decision)
    scratchpad = TurnScratchpad(messages=[HumanMessage(content="doanh thu tháng này")])

    ctx = SimpleNamespace(
        clarification_response={"clarify_kind": "harness_data_query"},
        pending_hitl_tool=None,
        pending_hitl_payload=None,
    )

    async def _collect():
        return [ev async for ev in orch.run(scratchpad, ctx)]

    events = asyncio.run(_collect())
    finals = [e for e in events if isinstance(e, FinalAnswerEvent)]
    assert finals and "100 triệu" in finals[0].text
