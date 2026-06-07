from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_hitl_resume_expired_returns_clear_error() -> None:
    from app.harness.orchestrator import ErrorEvent, HarnessOrchestrator
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.scratchpad import TurnScratchpad
    from app.harness.tool_registry import ToolRegistry, TurnContext

    class Registry:
        def get(self, role: str):  # noqa: ANN001
            raise AssertionError("expired HITL must not call LLM")

    orchestrator = HarnessOrchestrator(
        llm_registry=Registry(),
        tool_registry=ToolRegistry(),
        policy=HarnessPolicy(),
        settings=type("S", (), {"harness_max_steps": 3, "harness_planner_role": "harness_planner"})(),
        harness=AgentHarness(enabled=False),
    )
    ctx = TurnContext(
        tenant_id="t1",
        user_id="u1",
        thread_id="thread-1",
        correlation_id="corr-1",
        bearer_token=None,
        schema_version=None,
        clarification_response={"clarify_kind": "hitl_resume"},
        pending_hitl_tool=None,
        pending_hitl_payload=None,
    )

    events = [event async for event in orchestrator.run(TurnScratchpad(messages=[]), ctx)]

    errors = [event for event in events if isinstance(event, ErrorEvent)]
    assert errors and errors[0].code == "HITL_EXPIRED"
