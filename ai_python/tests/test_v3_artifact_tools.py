"""SRS-006 artifact tools consume result_ref instead of planner-visible full rows."""

from __future__ import annotations

import pytest

from app.harness.result_store import InMemoryResultRefStore
from app.harness.tool_registry import TurnContext


def _ctx(store: InMemoryResultRefStore | None = None) -> TurnContext:
    return TurnContext(
        tenant_id="t1",
        user_id="u1",
        thread_id="th1",
        correlation_id="cid",
        bearer_token=None,
        schema_version=None,
        result_store=store,
    )


@pytest.mark.asyncio
async def test_chart_builder_resolves_full_rows_from_result_ref() -> None:
    from app.graph.tools.build_chart import BuildChartTool

    rows = [{"month": f"2026-{i:02d}", "revenue": i * 10} for i in range(1, 31)]
    store = InMemoryResultRefStore()
    ref = store.put(tool_name="sql_query", data={"rows": rows}, ctx=_ctx(store))

    result = await BuildChartTool().invoke({"result_ref": ref}, _ctx(store))

    assert result.ok is True
    assert len(result.output["data"]) == 30


@pytest.mark.asyncio
async def test_data_table_builder_resolves_result_ref_for_sse() -> None:
    from app.graph.tools.data_table_builder import DataTableBuilderTool

    rows = [{"id": i, "name": f"sp{i}"} for i in range(30)]
    store = InMemoryResultRefStore()
    ref = store.put(tool_name="sql_query", data={"rows": rows}, ctx=_ctx(store))

    result = await DataTableBuilderTool().invoke({"result_ref": ref, "title": "Sản phẩm"}, _ctx(store))

    assert result.ok is True
    assert result.sse_payload is not None
    assert result.sse_payload["_event"] == "data_table"
    assert len(result.sse_payload["rows"]) == 30


@pytest.mark.asyncio
async def test_plan_executor_v3_passes_result_ref_not_full_rows_to_child() -> None:
    from app.graph.tools.data_table_builder import DataTableBuilderTool
    from app.harness.plan_graph import PlanExecutor, PlanGraph, PlanNode
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.tool_registry import ToolManifest, ToolRegistry, ToolResult

    class SqlTool:
        async def invoke(self, args, ctx):  # noqa: ANN001
            rows = [{"id": i} for i in range(30)]
            return ToolResult(ok=True, output={"rows": rows}, observation_text="rows")

    registry = ToolRegistry()
    registry.register(
        ToolManifest(
            name="sql_query",
            description="SQL",
            args_schema="{}",
            capability="data_read",
            produces=("rows",),
            result_ref_policy="result_ref",
        ),
        SqlTool(),
    )
    registry.register(DataTableBuilderTool.manifest, DataTableBuilderTool())
    store = InMemoryResultRefStore()
    plan = PlanGraph(
        nodes=[
            PlanNode(id="src", tool="sql_query", input_spec={"query": "x"}, output_expect="rows"),
            PlanNode(
                id="tbl",
                tool="data_table_builder",
                needs=["src"],
                input_spec={"result_ref": "${src.result_ref}"},
                output_expect="data_table",
            ),
        ]
    )

    results = await PlanExecutor(
        tool_registry=registry,
        policy=HarnessPolicy(),
        harness=AgentHarness(enabled=False),
    ).execute(plan, _ctx(store), result_store=store)

    src = next(r for r in results if r.node_id == "src")
    tbl = next(r for r in results if r.node_id == "tbl")
    assert src.tool_result["result_ref"].startswith("rref_")
    assert "rows" not in src.tool_result
    assert tbl.ok is True
    assert len(tbl.tool_result["query_table_sse"]["rows"]) == 30


@pytest.mark.asyncio
async def test_answer_composer_uses_observation_summary_without_full_table() -> None:
    from app.graph.tools.answer_composer import AnswerComposerTool

    result = await AnswerComposerTool().invoke(
        {
            "observations": [
                {
                    "tool_name": "sql_query",
                    "row_count": 30,
                    "result_ref": "rref_demo",
                    "sample_rows": [{"id": 1, "name": "sp1"}],
                }
            ],
            "assumptions": [],
        },
        _ctx(),
    )

    assert result.ok is True
    assert "30" in result.observation_text
    assert "sp29" not in result.observation_text


@pytest.mark.asyncio
async def test_data_table_builder_fails_when_no_rows_or_ref_bound() -> None:
    """LOW-5: an unbound artifact node must fail (replan), not render an empty table."""
    from app.graph.tools.data_table_builder import DataTableBuilderTool

    result = await DataTableBuilderTool().invoke({"title": "Bảng"}, _ctx())
    assert result.ok is False
    assert result.error_message


@pytest.mark.asyncio
async def test_data_table_builder_allows_explicit_empty_rows() -> None:
    """An explicit empty rows key is a valid zero-row input, not a failure."""
    from app.graph.tools.data_table_builder import DataTableBuilderTool

    result = await DataTableBuilderTool().invoke({"rows": [], "title": "Bảng"}, _ctx())
    assert result.ok is True
    assert result.output["row_count"] == 0
