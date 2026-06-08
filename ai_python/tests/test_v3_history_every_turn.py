"""MEDIUM-2 fix: K15 history is appended after EVERY turn with the right status.

Previously history was recorded only inside v3 plan mode, so reactive turns,
clarify, and HITL-pending outcomes never produced a K15 event (FR-9.1/9.5).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from langchain_core.messages import HumanMessage

from app.harness.history_store import (
    STATUS_CLARIFY_PENDING,
    STATUS_FAILURE,
    STATUS_SUCCESS,
    InMemoryIntentHistoryStore,
)
from app.harness.orchestrator import HarnessOrchestrator
from app.harness.policy import HarnessPolicy
from app.harness.runtime import AgentHarness
from app.harness.scratchpad import TurnScratchpad
from app.harness.tool_registry import (
    ClarifyRequest,
    DecisionSchema,
    ToolCall,
    ToolManifest,
    ToolRegistry,
    ToolResult,
    TurnContext,
)


def _settings(**overrides):
    base = dict(
        harness_max_steps=4,
        harness_planner_role="harness_planner",
        harness_token_budget=0,
        harness_cost_budget_usd=0.0,
        harness_wallclock_timeout_s=0.0,
        agentic_trace_enabled=False,
        agentic_intent_object_enabled=False,
        agentic_plan_dag_enabled=False,
        working_memory_pairs=0,
        agentic_model_routing_enabled=False,
        agentic_semantic_cache_enabled=False,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _ctx():
    return TurnContext(
        tenant_id="t1", user_id="u1", thread_id="th1", correlation_id="cid",
        bearer_token=None, schema_version=None, role="owner", permissions=("data_read",),
    )


class _DecisionClient:
    def __init__(self, decisions):
        from app.llm.openai_compatible import InvokeUsage

        self._decisions = list(decisions)
        self._i = 0
        self.last_usage = InvokeUsage(prompt_tokens=1, completion_tokens=1, cost_usd=0.0)

    async def astructured_predict(self, messages, schema, **kwargs):  # noqa: ANN001
        decision = self._decisions[self._i]
        self._i += 1
        return decision


class _Registry:
    def __init__(self, client):
        self.client = client

    def get(self, role):  # noqa: ANN001
        return self.client


def _orchestrator(decisions, history, *, tool_registry=None):
    return HarnessOrchestrator(
        llm_registry=_Registry(_DecisionClient(decisions)),
        tool_registry=tool_registry or ToolRegistry(),
        policy=HarnessPolicy(),
        settings=_settings(),
        harness=AgentHarness(enabled=False),
        history_store=history,
    )


async def _drain(orchestrator):
    return [
        e async for e in orchestrator.run(TurnScratchpad(messages=[HumanMessage(content="doanh thu")]), _ctx())
    ]


# --- reactive success records K15 with the tools called -------------------

@pytest.mark.asyncio
async def test_reactive_success_records_history_with_tools():
    class SqlTool:
        async def invoke(self, args, ctx):  # noqa: ANN001
            return ToolResult(ok=True, output={"rows": [{"v": 1}]}, observation_text="rows")

    registry = ToolRegistry()
    registry.register(ToolManifest(name="sql_query", description="SQL", args_schema="{}", capability="data_read"), SqlTool())

    decisions = [
        DecisionSchema(action="call_tool", tool_call=ToolCall(tool_name="sql_query", args={})),
        DecisionSchema(action="final_answer", final_answer="Xong."),
    ]
    history = InMemoryIntentHistoryStore()
    await _drain(_orchestrator(decisions, history, tool_registry=registry))

    summary = history.summary("doanh thu")
    assert summary.total == 1
    assert summary.success == 1
    events = history.all()
    assert events[0].plan["tools"] == ["sql_query"]
    assert events[0].plan["plan_hash"].startswith("reactive:")


# --- clarify turn records clarify_pending ---------------------------------

@pytest.mark.asyncio
async def test_clarify_turn_records_clarify_pending():
    decisions = [
        DecisionSchema(action="clarify", clarify=ClarifyRequest(questions=["Khoảng thời gian?"])),
    ]
    history = InMemoryIntentHistoryStore()
    await _drain(_orchestrator(decisions, history))

    summary = history.summary("doanh thu")
    assert summary.total == 1
    assert summary.clarify_pending == 1
    assert summary.success == 0


# --- failure turn records failure -----------------------------------------

@pytest.mark.asyncio
async def test_failure_turn_records_failure():
    decisions = [
        DecisionSchema(action="call_tool", tool_call=None),  # invalid -> ErrorEvent
    ]
    history = InMemoryIntentHistoryStore()
    await _drain(_orchestrator(decisions, history))

    summary = history.summary("doanh thu")
    assert summary.total == 1
    assert summary.failure == 1


# --- no history store wired -> no crash -----------------------------------

@pytest.mark.asyncio
async def test_no_history_store_is_noop():
    decisions = [DecisionSchema(action="final_answer", final_answer="ok")]
    orchestrator = HarnessOrchestrator(
        llm_registry=_Registry(_DecisionClient(decisions)),
        tool_registry=ToolRegistry(),
        policy=HarnessPolicy(),
        settings=_settings(),
        harness=AgentHarness(enabled=False),
    )
    events = await _drain(orchestrator)
    assert events  # ran fine without a history store
