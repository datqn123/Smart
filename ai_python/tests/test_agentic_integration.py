"""Integration tests that exercise the wired features THROUGH HarnessOrchestrator.

These differ from the per-module unit tests: they flip the real settings flags and
assert behaviour observed at the orchestrator boundary (events / tool invocation),
proving the P1-P8 modules are actually reachable in the live loop — not just defined.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.harness.orchestrator import (
    FinalAnswerEvent,
    HarnessOrchestrator,
    SsePayloadEvent,
)
from app.harness.policy import HarnessPolicy
from app.harness.runtime import AgentHarness
from app.harness.scratchpad import TurnScratchpad
from app.harness.tool_registry import (
    ToolManifest,
    ToolRegistry,
    ToolResult,
    TurnContext,
)
from app.llm.openai_compatible import InvokeUsage


def _settings(**overrides):
    base = dict(
        harness_max_steps=4,
        harness_planner_role="harness_planner",
        harness_token_budget=0,
        harness_cost_budget_usd=0.05,
        harness_wallclock_timeout_s=30.0,
        agentic_trace_enabled=True,
        agentic_intent_object_enabled=False,
        working_memory_pairs=6,
        intent_confidence_run=0.9,
        intent_confidence_hitl=0.75,
        entity_score_hitl=0.6,
        agentic_plan_dag_enabled=False,
        plan_replan_max=2,
        agentic_model_routing_enabled=False,
        opt_escalate_replan_count=2,
        agentic_semantic_cache_enabled=False,
        agentic_answer_composer_enabled=False,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _ctx(role: str | None = None):
    return TurnContext(
        tenant_id="t1",
        user_id="u1",
        thread_id="th1",
        correlation_id="c1",
        bearer_token=None,
        schema_version=None,
        role=role,
    )


class _MultiClient:
    """Returns the right schema per call; tracks which schemas were requested."""

    def __init__(self, *, intent_type="data_query", confidence=0.95, plan_nodes=None) -> None:
        self.last_usage = InvokeUsage(prompt_tokens=10, completion_tokens=5, cost_usd=0.001)
        self._intent_type = intent_type
        self._confidence = confidence
        self._plan_nodes = plan_nodes
        self.schemas: list[str] = []

    async def astructured_predict(self, messages, schema, **kwargs):  # noqa: ANN001
        name = schema.__name__
        self.schemas.append(name)
        if name == "IntentAnalysisResult":
            return schema(goal="doanh thu", intent_type=self._intent_type, required_data=["revenue"], confidence=self._confidence)
        if name == "PlanGraphOutput":
            return schema(nodes=self._plan_nodes or [])
        if name == "DecisionSchema":
            return schema(action="final_answer", final_answer="Đã xử lý.")
        raise NotImplementedError(name)


class _Registry:
    def __init__(self, client, extra=None) -> None:  # noqa: ANN001
        self._client = client
        self._extra = extra or {}

    def get(self, role: str):  # noqa: ANN001
        if role in self._extra:
            return self._extra[role]
        return self._client


class _RecordingSqlTool:
    """Fake sql_query tool that records calls and returns maskable rows + data_table SSE."""

    manifest = ToolManifest(name="sql_query", description="SQL", args_schema="{}")

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def invoke(self, args, ctx):  # noqa: ANN001
        self.calls.append(dict(args))
        rows = [{"name": "Áo", "cost_price": 100, "sale_price": 150}]
        return ToolResult(
            ok=True,
            output={"rows": rows, "query_table_sse": {"rows": rows}},
            observation_text="rows",
            sse_payload={"_event": "data_table", "rows": rows},
        )


# --------------------------------------------------------------------------- #
# P8 — trace metrics are produced for a real turn through the orchestrator.
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_trace_metrics_populated_through_orchestrator():
    client = _MultiClient()
    orchestrator = HarnessOrchestrator(
        llm_registry=_Registry(client),
        tool_registry=ToolRegistry(),
        policy=HarnessPolicy(),
        settings=_settings(agentic_trace_enabled=True),
        harness=AgentHarness(enabled=False),
    )
    events = [e async for e in orchestrator.run(TurnScratchpad(messages=[]), _ctx())]
    assert any(isinstance(e, FinalAnswerEvent) for e in events)
    assert orchestrator.last_metrics is not None
    assert orchestrator.last_metrics.tokens == 15
    assert orchestrator.last_metrics.cost_usd == pytest.approx(0.001)


# --------------------------------------------------------------------------- #
# P7 — model routing picks a tier role through _decide.
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_model_routing_uses_tier_role():
    planner_client = _MultiClient()
    sonnet_client = _MultiClient()
    registry = _Registry(planner_client, extra={"sonnet": sonnet_client})
    orchestrator = HarnessOrchestrator(
        llm_registry=registry,
        tool_registry=ToolRegistry(),
        policy=HarnessPolicy(),
        settings=_settings(agentic_model_routing_enabled=True),
        harness=AgentHarness(enabled=False),
    )
    _ = [e async for e in orchestrator.run(TurnScratchpad(messages=[]), _ctx())]
    # planner-class work routes to the "sonnet" tier client, not the default.
    assert sonnet_client.schemas == ["DecisionSchema"]
    assert planner_client.schemas == []


# --------------------------------------------------------------------------- #
# P7 — deterministic cache short-circuits the second identical sql_query.
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_semantic_cache_hits_through_orchestrator():
    cache_settings = _settings(agentic_semantic_cache_enabled=True)
    tool = _RecordingSqlTool()
    registry = ToolRegistry()
    registry.register(tool.manifest, tool)
    orchestrator = HarnessOrchestrator(
        llm_registry=_Registry(_MultiClient()),
        tool_registry=registry,
        policy=HarnessPolicy(),
        settings=cache_settings,
        harness=AgentHarness(enabled=False),
    )
    args = {"query": "doanh thu"}
    inp = _tool_input("sql_query", args, _ctx())
    first = await orchestrator._run_tool_cached(inp)
    second = await orchestrator._run_tool_cached(inp)
    assert first.ok and second.ok
    assert len(tool.calls) == 1  # second served from cache
    # tenant isolation: different tenant misses the cache.
    third = await orchestrator._run_tool_cached(_tool_input("sql_query", args, _ctx_other_tenant()))
    assert len(tool.calls) == 2


# --------------------------------------------------------------------------- #
# P2 — plan-DAG mode runs through the orchestrator and fans out to both tools.
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_plan_dag_mode_fans_out_and_answers():
    plan_nodes = [
        {"id": "rev", "tool": "sql_query", "needs": [], "input_spec": {"query": "revenue"}, "output_expect": "rows"},
        {"id": "inv", "tool": "sql_query", "needs": [], "input_spec": {"query": "inventory"}, "output_expect": "rows"},
    ]
    client = _MultiClient(intent_type="data_query", confidence=0.95, plan_nodes=plan_nodes)
    tool = _RecordingSqlTool()
    registry = ToolRegistry()
    registry.register(tool.manifest, tool)
    orchestrator = HarnessOrchestrator(
        llm_registry=_Registry(client),
        tool_registry=registry,
        policy=HarnessPolicy(),
        settings=_settings(agentic_intent_object_enabled=True, agentic_plan_dag_enabled=True),
        harness=AgentHarness(enabled=False),
    )
    events = [e async for e in orchestrator.run(TurnScratchpad(messages=[]), _ctx())]
    # Both independent nodes reached the tool (fan-out through the orchestrator).
    assert {c["query"] for c in tool.calls} == {"revenue", "inventory"}
    # A data_table SSE was reconstructed from node output, and a final answer produced.
    assert any(isinstance(e, SsePayloadEvent) and e.event_name == "data_table" for e in events)
    assert any(isinstance(e, FinalAnswerEvent) for e in events)
    assert "PlanGraphOutput" in client.schemas


# --------------------------------------------------------------------------- #
# P2 — PlanExecutor pipes a parent node's output into a dependent child node.
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_plan_executor_pipes_parent_rows_to_child():
    from app.harness.plan_graph import PlanExecutor, PlanGraph, PlanNode

    captured: dict = {}

    class _SqlTool:
        async def invoke(self, args, ctx):  # noqa: ANN001
            return ToolResult(ok=True, output={"rows": [{"a": 1}, {"a": 2}]}, observation_text="rows")

    class _SinkTool:
        async def invoke(self, args, ctx):  # noqa: ANN001
            captured["rows"] = args.get("rows")
            return ToolResult(ok=True, output={"answer_markdown": "ok"}, observation_text="done")

    registry = ToolRegistry()
    registry.register(ToolManifest(name="sql_query", description="sql", args_schema="{}"), _SqlTool())
    registry.register(ToolManifest(name="answer_composer", description="compose", args_schema="{}"), _SinkTool())
    plan = PlanGraph(
        nodes=[
            PlanNode(id="src", tool="sql_query", needs=[], input_spec={"query": "x"}, output_expect="rows"),
            PlanNode(
                id="ans",
                tool="answer_composer",
                needs=["src"],
                input_spec={"rows": "${src.rows}"},  # data-flow binding
                output_expect="answer",
            ),
        ]
    )
    results = await PlanExecutor(
        tool_registry=registry,
        policy=HarnessPolicy(),
        harness=AgentHarness(enabled=False),
    ).execute(plan, _ctx())

    # The child received the PARENT's actual rows, not a literal "${src.rows}" string.
    assert captured["rows"] == [{"a": 1}, {"a": 2}]
    assert all(r.ok for r in results)


@pytest.mark.asyncio
async def test_plan_executor_static_input_spec_unchanged():
    """A node with no refs keeps its literal input_spec (backward compatible)."""
    from app.harness.plan_graph import PlanExecutor, PlanGraph, PlanNode

    seen: dict = {}

    class _Tool:
        async def invoke(self, args, ctx):  # noqa: ANN001
            seen.update(args)
            return ToolResult(ok=True, output={"rows": [1]}, observation_text="x")

    registry = ToolRegistry()
    registry.register(ToolManifest(name="sql_query", description="sql", args_schema="{}"), _Tool())
    plan = PlanGraph(nodes=[PlanNode(id="n", tool="sql_query", input_spec={"query": "literal"}, output_expect="rows")])
    await PlanExecutor(tool_registry=registry, policy=HarnessPolicy(), harness=AgentHarness(enabled=False)).execute(
        plan, _ctx()
    )
    assert seen == {"query": "literal"}


# --------------------------------------------------------------------------- #
# P6 — sensitive-column masking applied at SqlQueryTool OUTPUT (real tool).
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_sql_tool_masks_sensitive_columns_for_staff():
    from app.graph.tools.sql_query import SqlQueryTool

    rows = [{"name": "Áo", "cost_price": 100, "sale_price": 150}]

    class _Compiled:
        def invoke(self, state, config):  # noqa: ANN001
            return {"result_ok": True, "query_result": {"rows": rows}, "query_table_sse": {"rows": rows}, "generated_sql": "SELECT *"}

    deps = SimpleNamespace(settings=_settings(agentic_capability_guard_enabled=True))
    tool = SqlQueryTool(deps, compiled=_Compiled())

    staff = await tool.invoke({"query": "x"}, _ctx(role="staff"))
    owner = await tool.invoke({"query": "x"}, _ctx(role="owner"))

    assert "cost_price" not in (staff.sse_payload or {}).get("rows", [{}])[0]
    assert "cost_price" not in staff.observation_text
    assert owner.sse_payload["rows"][0]["cost_price"] == 100


# --------------------------------------------------------------------------- #
# P3/P4 — new tools are registered (reachable by the planner) when flags on.
# --------------------------------------------------------------------------- #
def test_new_tools_registered_when_flags_on():
    from app.api.runtime import _build_tool_registry

    deps = SimpleNamespace(
        settings=_settings(agentic_data_validator_enabled=True, agentic_answer_composer_enabled=True),
        llm_registry=None,
        sql_executor=None,
        harness=AgentHarness(enabled=False),
    )
    # SqlQueryTool/etc. need a compiled subgraph; patch build to avoid heavy deps.
    import app.graph.tools.sql_query as sq
    import app.graph.tools.schema_explore as se
    import app.graph.tools.catalog_draft as cd
    import app.graph.tools.inventory_draft as iv

    manifest_text = _safe_manifest(deps, sq, se, cd, iv)
    for name in ("data_validator", "answer_composer", "build_chart", "data_table_builder", "erp_guide"):
        assert name in manifest_text


def test_new_tools_absent_when_flags_off():
    deps = SimpleNamespace(
        settings=_settings(),
        llm_registry=None,
        sql_executor=None,
        harness=AgentHarness(enabled=False),
    )
    import app.graph.tools.sql_query as sq
    import app.graph.tools.schema_explore as se
    import app.graph.tools.catalog_draft as cd
    import app.graph.tools.inventory_draft as iv

    manifest_text = _safe_manifest(deps, sq, se, cd, iv)
    for name in ("data_validator", "answer_composer", "build_chart", "data_table_builder", "erp_guide"):
        assert name not in manifest_text


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _tool_input(name, args, ctx):
    from app.harness.tool_registry import ToolInput

    return ToolInput(tool_name=name, args=args, context=ctx)


def _ctx_other_tenant():
    return TurnContext(
        tenant_id="t2",
        user_id="u1",
        thread_id="th1",
        correlation_id="c1",
        bearer_token=None,
        schema_version=None,
    )


def _safe_manifest(deps, sq, se, cd, iv):
    """Build the tool registry with heavy subgraph compilation stubbed out."""
    from app.api.runtime import _build_tool_registry

    orig = {
        "sql": sq.SqlQueryTool.__init__,
        "se": se.SchemaExploreTool.__init__,
        "cd": cd.CatalogDraftTool.__init__,
        "iv": iv.InventoryDraftTool.__init__,
    }

    def _noop_init(self, *a, **k):  # noqa: ANN001
        self.manifest = type(self).manifest

    sq.SqlQueryTool.__init__ = _noop_init
    se.SchemaExploreTool.__init__ = _noop_init
    cd.CatalogDraftTool.__init__ = _noop_init
    iv.InventoryDraftTool.__init__ = _noop_init
    try:
        registry = _build_tool_registry(deps)
        return registry.tools_manifest_text()
    finally:
        sq.SqlQueryTool.__init__ = orig["sql"]
        se.SchemaExploreTool.__init__ = orig["se"]
        cd.CatalogDraftTool.__init__ = orig["cd"]
        iv.InventoryDraftTool.__init__ = orig["iv"]
