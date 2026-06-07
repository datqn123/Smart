"""Data table artifact builder for v3 planner-selected artifact flows."""

from __future__ import annotations

from typing import Any

from app.graph.tools._result_ref import rows_from_args_or_ref
from app.harness.tool_registry import ToolManifest, ToolResult, TurnContext


class DataTableBuilderTool:
    manifest = ToolManifest(
        name="data_table_builder",
        description="Build a frontend data-table artifact from rows or a Harness result_ref.",
        args_schema='{"rows":"list","result_ref":"string","title":"string"}',
        capability="data_table_build",
        output_schema='{"query_table_sse": "dict", "row_count": "int"}',
        output_artifact_types=("data_table",),
        when_to_use="User asks to list, inspect, compare, or browse row-level ERP data.",
        when_not_to_use="User needs a chart/trend visualization or only a short scalar answer.",
        risk_level="low",
        side_effect_class="read_only",
        consumes=("rows", "result_ref"),
        produces=("data_table",),
        result_ref_policy="result_ref",
        examples=("liệt kê sản phẩm sắp hết hàng", "danh sách đơn bán lẻ tháng này"),
    )

    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
        rows, error = rows_from_args_or_ref(args, ctx)
        if error:
            return ToolResult(ok=False, output={}, observation_text=error, error_message=error)
        title = str(args.get("title") or "Bảng dữ liệu").strip()
        payload = {"title": title, "rows": rows, "row_count": len(rows)}
        return ToolResult(
            ok=True,
            output={"query_table_sse": payload, "row_count": len(rows)},
            observation_text=f"Đã tạo bảng dữ liệu với {len(rows)} dòng.",
            sse_payload={"_event": "data_table", **payload},
        )
