from __future__ import annotations

from types import SimpleNamespace

import pytest


def _ctx():
    from app.harness.tool_registry import TurnContext

    return TurnContext(
        tenant_id="t1",
        user_id="u1",
        thread_id="thread-1",
        correlation_id="corr-1",
        bearer_token=None,
        schema_version=None,
    )


def _settings(**overrides):  # noqa: ANN003
    values = {
        "harness_max_steps": 3,
        "harness_planner_role": "harness_planner",
        "harness_token_budget": 0,
        "harness_cost_budget_usd": 0.05,
        "harness_wallclock_timeout_s": 30.0,
        "agentic_intent_object_enabled": True,
        "intent_confidence_run": 0.9,
        "intent_confidence_hitl": 0.75,
        "entity_score_hitl": 0.6,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class _Registry:
    def __init__(self, client) -> None:  # noqa: ANN001
        self.client = client

    def get(self, role: str):  # noqa: ANN001
        return self.client


@pytest.mark.asyncio
async def test_intent_low_entity_score_clarifies() -> None:
    from app.harness.orchestrator import ClarifyEvent, HarnessOrchestrator
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.scratchpad import TurnScratchpad
    from app.harness.tool_registry import ToolRegistry
    from langchain_core.messages import HumanMessage
    from tests.fake_llm import FakeLlmClient

    orchestrator = HarnessOrchestrator(
        llm_registry=_Registry(FakeLlmClient(intent="data_query", intent_confidence=0.95, intent_entity_score=0.5)),
        tool_registry=ToolRegistry(),
        policy=HarnessPolicy(),
        settings=_settings(),
        harness=AgentHarness(enabled=False),
    )

    events = [
        event
        async for event in orchestrator.run(
            TurnScratchpad(messages=[HumanMessage(content="áo")]),
            _ctx(),
        )
    ]

    clarify = [event for event in events if isinstance(event, ClarifyEvent)]
    assert clarify
    assert clarify[0].questions
    assert "vui lòng" in clarify[0].questions[0].lower() or "bạn muốn" in clarify[0].questions[0].lower()


@pytest.mark.asyncio
async def test_intent_gate_clarify_emits_sse_clarify() -> None:
    from app.api.runtime import _event_to_stream_chunk
    from app.harness.orchestrator import ClarifyEvent, HarnessOrchestrator
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.scratchpad import TurnScratchpad
    from app.harness.tool_registry import ToolRegistry
    from langchain_core.messages import HumanMessage
    from tests.fake_llm import FakeLlmClient

    orchestrator = HarnessOrchestrator(
        llm_registry=_Registry(FakeLlmClient(intent="data_query", intent_missing=["time_period"])),
        tool_registry=ToolRegistry(),
        policy=HarnessPolicy(),
        settings=_settings(),
        harness=AgentHarness(enabled=False),
    )

    events = [
        event
        async for event in orchestrator.run(
            TurnScratchpad(messages=[HumanMessage(content="báo cáo bán hàng")]),
            _ctx(),
        )
    ]
    clarify = next(event for event in events if isinstance(event, ClarifyEvent))
    chunk = _event_to_stream_chunk(clarify)

    assert "domain_clarify_sse" in chunk["harness"]
    assert chunk["harness"]["domain_clarify_sse"]["questions"]


@pytest.mark.asyncio
async def test_intent_llm_error_fallback_heuristic() -> None:
    from app.harness.orchestrator import FinalAnswerEvent, HarnessOrchestrator
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.scratchpad import TurnScratchpad
    from app.harness.tool_registry import ToolRegistry
    from langchain_core.messages import HumanMessage

    class BrokenClient:
        last_usage = None

        async def astructured_predict(self, messages, schema, **kwargs):  # noqa: ANN001
            if schema.__name__ == "IntentObjectOutput":
                raise RuntimeError("intent llm failed")
            return schema(action="final_answer", final_answer="fallback ok")

    orchestrator = HarnessOrchestrator(
        llm_registry=_Registry(BrokenClient()),
        tool_registry=ToolRegistry(),
        policy=HarnessPolicy(),
        settings=_settings(),
        harness=AgentHarness(enabled=False),
    )

    events = [
        event
        async for event in orchestrator.run(
            TurnScratchpad(messages=[HumanMessage(content="doanh thu")]),
            _ctx(),
        )
    ]

    assert any(isinstance(event, FinalAnswerEvent) and event.text == "fallback ok" for event in events)
