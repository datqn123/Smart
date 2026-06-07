from __future__ import annotations

import pytest


class _FinalClient:
    async def astructured_predict(self, messages, schema, **kwargs):  # noqa: ANN001
        return schema(action="final_answer", final_answer="xong")


class _ToolThenFinalClient:
    def __init__(self) -> None:
        self.calls = 0

    async def astructured_predict(self, messages, schema, **kwargs):  # noqa: ANN001
        self.calls += 1
        if self.calls == 1:
            return schema(
                action="call_tool",
                tool_call={"tool_name": "schema_explore", "args": {"topic": "doanh thu"}, "reasoning": "need schema"},
            )
        if self.calls == 2:
            return schema(
                action="call_tool",
                tool_call={"tool_name": "sql_query", "args": {"query": "doanh thu"}, "reasoning": "query data"},
            )
        return schema(action="final_answer", final_answer="doanh thu là 100")


class _LoopForeverClient:
    async def astructured_predict(self, messages, schema, **kwargs):  # noqa: ANN001
        return schema(
            action="call_tool",
            tool_call={"tool_name": "sql_query", "args": {"query": "x"}, "reasoning": "continue"},
        )


class _Registry:
    def __init__(self, client) -> None:  # noqa: ANN001
        self.client = client

    def get(self, role: str):  # noqa: ANN001
        return self.client


class _Settings:
    harness_max_steps = 2
    harness_planner_role = "harness_planner"


@pytest.fixture
def ctx():
    from app.harness.tool_registry import TurnContext

    return TurnContext(
        tenant_id="t1",
        user_id="u1",
        thread_id="thread-1",
        correlation_id="corr-1",
        bearer_token=None,
        schema_version=None,
    )


def _orchestrator(client, *tools):  # noqa: ANN001
    from app.harness.orchestrator import HarnessOrchestrator
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.tool_registry import ToolManifest, ToolRegistry

    registry = ToolRegistry()
    for name, tool in tools:
        registry.register(
            ToolManifest(name=name, description=f"{name} tool", args_schema="{}"),
            tool,
        )
    return HarnessOrchestrator(
        llm_registry=_Registry(client),
        tool_registry=registry,
        policy=HarnessPolicy(),
        settings=_Settings(),
        harness=AgentHarness(enabled=False),
    )


@pytest.mark.asyncio
async def test_loop_stops_at_max_steps(ctx) -> None:  # noqa: ANN001
    from app.harness.orchestrator import FinalAnswerEvent, ProgressEvent
    from app.harness.scratchpad import TurnScratchpad
    from app.harness.tool_registry import ToolResult

    class Tool:
        async def invoke(self, args, ctx):  # noqa: ANN001
            return ToolResult(ok=True, output={}, observation_text="still working")

    orchestrator = _orchestrator(_LoopForeverClient(), ("sql_query", Tool()))
    events = [event async for event in orchestrator.run(TurnScratchpad(messages=[]), ctx)]

    assert len([event for event in events if isinstance(event, FinalAnswerEvent)]) == 1
    assert len([event for event in events if isinstance(event, ProgressEvent)]) == 2


@pytest.mark.asyncio
async def test_hitl_stops_loop_and_emits_payload(ctx) -> None:  # noqa: ANN001
    from app.harness.orchestrator import PendingHitlEvent, SsePayloadEvent
    from app.harness.scratchpad import TurnScratchpad
    from app.harness.tool_registry import HitlSpec, ToolResult

    class HitlClient:
        async def astructured_predict(self, messages, schema, **kwargs):  # noqa: ANN001
            return schema(
                action="call_tool",
                tool_call={"tool_name": "catalog_draft", "args": {"request": "new"}, "reasoning": "draft"},
            )

    class HitlTool:
        async def invoke(self, args, ctx):  # noqa: ANN001
            return ToolResult(
                ok=True,
                output={},
                observation_text="draft ready",
                sse_payload={"entity": "product"},
                pending_hitl=HitlSpec(event_name="draft", payload={"entity": "product"}, resume_token="thread-1"),
            )

    orchestrator = _orchestrator(HitlClient(), ("catalog_draft", HitlTool()))
    events = [event async for event in orchestrator.run(TurnScratchpad(messages=[]), ctx)]

    assert len([event for event in events if isinstance(event, SsePayloadEvent) and event.event_name == "draft"]) == 1
    assert len([event for event in events if isinstance(event, PendingHitlEvent)]) == 1


@pytest.mark.asyncio
async def test_two_tool_chain(ctx) -> None:  # noqa: ANN001
    from app.harness.orchestrator import FinalAnswerEvent
    from app.harness.scratchpad import TurnScratchpad
    from app.harness.tool_registry import ToolResult

    class Tool:
        def __init__(self, text: str) -> None:
            self.text = text

        async def invoke(self, args, ctx):  # noqa: ANN001
            return ToolResult(ok=True, output={}, observation_text=self.text)

    scratchpad = TurnScratchpad(messages=[])
    orchestrator = _orchestrator(
        _ToolThenFinalClient(),
        ("schema_explore", Tool("schema loaded")),
        ("sql_query", Tool("doanh thu là 100")),
    )
    events = [event async for event in orchestrator.run(scratchpad, ctx)]

    finals = [event for event in events if isinstance(event, FinalAnswerEvent)]
    assert len(finals) == 1
    assert "doanh thu là 100" in finals[0].text
    assert [obs.tool_name for obs in scratchpad.observations] == ["schema_explore", "sql_query"]
