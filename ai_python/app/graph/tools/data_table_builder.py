"""Data table artifact builder for v3 planner-selected artifact flows."""

from __future__ import annotations

import logging
import time
from typing import Any

from app.graph.tools._result_ref import rows_from_args_or_ref
from app.harness.tool_registry import ToolManifest, ToolResult, TurnContext

logger = logging.getLogger(__name__)


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
        _invoke_start = time.monotonic()
        logger.info("tool_invoke_start tool=data_table_builder rows=%s title=%s",
                    len(args.get("rows", [])), args.get("title", ""))
        rows, error = rows_from_args_or_ref(args, ctx)
        if error:
            _result = ToolResult(ok=False, output={}, observation_text=error, error_message=error)
            _latency_ms = (time.monotonic() - _invoke_start) * 1000
            logger.info("tool_invoke_end tool=data_table_builder ok=%s latency_ms=%.0f row_count=%s",
                        _result.ok, _latency_ms, _result.output.get("row_count"))
            return _result
        title = str(args.get("title") or "Bảng dữ liệu").strip()
        payload = {"title": title, "rows": rows, "row_count": len(rows)}
        _latency_ms = (time.monotonic() - _invoke_start) * 1000
        result = ToolResult(
            ok=True,
            output={"query_table_sse": payload, "row_count": len(rows)},
            observation_text=f"Đã tạo bảng dữ liệu với {len(rows)} dòng.",
            sse_payload={"_event": "data_table", **payload},
        )
        logger.info("tool_invoke_end tool=data_table_builder ok=%s latency_ms=%.0f row_count=%s",
                    result.ok, _latency_ms, result.output.get("row_count"))
        return result
