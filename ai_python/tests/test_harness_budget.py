from __future__ import annotations

import json
from types import SimpleNamespace

import pytest


class _Usage:
    def __init__(self, *, prompt_tokens: int = 50, completion_tokens: int = 50, cost_usd: float = 0.001) -> None:
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.cost_usd = cost_usd


class _BudgetClient:
    def __init__(self, *, usage: _Usage | None = None) -> None:
        self.calls = 0
        self.last_usage = usage or _Usage()

    async def astructured_predict(self, messages, schema, **kwargs):  # noqa: ANN001
        self.calls += 1
        return schema(
            action="call_tool",
            tool_call={
                "tool_name": "sql_query",
                "args": {"query": f"q-{self.calls}"},
                "reasoning": "budget test",
            },
        )


class _Registry:
    def __init__(self, client) -> None:  # noqa: ANN001
        self.client = client

    def get(self, role: str):  # noqa: ANN001
        return self.client


class _Tool:
    async def invoke(self, args, ctx):  # noqa: ANN001
        from app.harness.tool_registry import ToolResult

        return ToolResult(ok=True, output={"rows": []}, observation_text=f"obs {args['query']}")


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


def _orchestrator(client, settings):  # noqa: ANN001
    from app.harness.orchestrator import HarnessOrchestrator
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.tool_registry import ToolManifest, ToolRegistry

    registry = ToolRegistry()
    registry.register(ToolManifest(name="sql_query", description="SQL", args_schema="{}"), _Tool())
    return HarnessOrchestrator(
        llm_registry=_Registry(client),
        tool_registry=registry,
        policy=HarnessPolicy(),
        settings=settings,
        harness=AgentHarness(enabled=False),
    )


def _settings(**overrides):  # noqa: ANN003
    values = {
        "harness_max_steps": 10,
        "harness_planner_role": "harness_planner",
        "harness_token_budget": 0,
        "harness_cost_budget_usd": 99.0,
        "harness_wallclock_timeout_s": 30.0,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.asyncio
async def test_budget_cost_stops_loop() -> None:
    from app.harness.orchestrator import FinalAnswerEvent
    from app.harness.scratchpad import TurnScratchpad

    orchestrator = _orchestrator(
        _BudgetClient(usage=_Usage(cost_usd=0.001)),
        _settings(harness_cost_budget_usd=0.0025),
    )

    events = [event async for event in orchestrator.run(TurnScratchpad(messages=[]), _ctx())]

    assert sum(isinstance(event, FinalAnswerEvent) for event in events) == 1
    assert orchestrator._last_budget_hit == "cost"


@pytest.mark.asyncio
async def test_budget_token_stops_loop() -> None:
    from app.harness.orchestrator import FinalAnswerEvent
    from app.harness.scratchpad import TurnScratchpad

    orchestrator = _orchestrator(
        _BudgetClient(usage=_Usage(prompt_tokens=50, completion_tokens=50, cost_usd=0.0)),
        _settings(harness_token_budget=120),
    )

    events = [event async for event in orchestrator.run(TurnScratchpad(messages=[]), _ctx())]

    assert any(isinstance(event, FinalAnswerEvent) for event in events)
    assert orchestrator._last_budget_hit == "token"


@pytest.mark.asyncio
async def test_budget_wallclock_stops_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.harness.orchestrator import FinalAnswerEvent
    from app.harness.scratchpad import TurnScratchpad

    ticks = iter([100.0, 100.0, 100.0, 200.0])
    monkeypatch.setattr("app.harness.budget.time.monotonic", lambda: next(ticks, 200.0))
    orchestrator = _orchestrator(
        _BudgetClient(usage=_Usage(cost_usd=0.0)),
        _settings(harness_wallclock_timeout_s=10.0),
    )

    events = [event async for event in orchestrator.run(TurnScratchpad(messages=[]), _ctx())]

    assert any(isinstance(event, FinalAnswerEvent) for event in events)
    assert orchestrator._last_budget_hit == "wallclock"


@pytest.mark.asyncio
async def test_audit_records_tokens_cost_latency(tmp_path) -> None:  # noqa: ANN001
    from app.harness.runtime import AgentHarness, ToolCallContext

    audit_path = tmp_path / "harness.jsonl"
    harness = AgentHarness(enabled=True, audit_jsonl_path=str(audit_path))

    async def tool():
        return {"ok": True}

    await harness.arun_tool(
        tool_name="sql_query",
        tool=tool,
        context=ToolCallContext(tool_name="sql_query", correlation_id="corr-1"),
        tokens=123,
        cost_usd=0.004,
    )

    rows = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    after = [row for row in rows if row["event"] == "after_tool_call"][-1]
    assert after["tokens"] == 123
    assert after["cost_usd"] == 0.004
    assert isinstance(after["latency_ms"], (int, float))

