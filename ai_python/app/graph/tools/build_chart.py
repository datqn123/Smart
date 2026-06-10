"""Chart harness tool adapter."""

from __future__ import annotations

import logging
import time
from typing import Any

from app.graph.nodes.chart_report import build_chart_spec_final
from app.graph.tools._result_ref import rows_from_args_or_ref
from app.harness.tool_registry import ToolManifest, ToolResult, TurnContext

logger = logging.getLogger(__name__)


class BuildChartTool:
    manifest = ToolManifest(
        name="build_chart",
        description="Build a frontend chart payload from rows.",
        args_schema='{"rows":"list","result_ref":"string"}',
        capability="chart_build",
        output_schema='{"chart_spec": "dict"}',
        output_artifact_types=("chart",),
        when_to_use="User wants a trend, comparison, or distribution visualization of fetched data.",
        when_not_to_use="Data is a single scalar or non-chartable shape (use answer_composer or data_table_builder).",
        risk_level="low",
        side_effect_class="read_only",
        consumes=("rows",),
        produces=("chart",),
        result_ref_policy="result_ref",
        examples=("biểu đồ doanh thu 12 tháng", "so sánh tồn kho theo kho"),
    )

    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
        _invoke_start = time.monotonic()
        logger.info("tool_invoke_start tool=build_chart rows=%s", len(args.get("rows", [])))
        rows, error = rows_from_args_or_ref(args, ctx)
        if error:
            _result = ToolResult(ok=False, output={}, observation_text=error, error_message=error)
            _latency_ms = (time.monotonic() - _invoke_start) * 1000
            logger.info("tool_invoke_end tool=build_chart ok=%s latency_ms=%.0f chart_type=%s",
                        _result.ok, _latency_ms, _result.output.get("chart_spec", {}).get("chart_type"))
            return _result
        chart_type, x_key, y_key = _infer_chart(rows)
        spec = build_chart_spec_final(rows, chart_type, x_key, y_key, args.get("title") or "Biểu đồ dữ liệu")
        _latency_ms = (time.monotonic() - _invoke_start) * 1000
        result = ToolResult(
            ok=True,
            output=spec,
            observation_text=f"Đã tạo biểu đồ {spec.get('chartType')}.",
            sse_payload={"_event": "chart", **spec},
        )
        logger.info("tool_invoke_end tool=build_chart ok=%s latency_ms=%.0f chart_type=%s",
                    result.ok, _latency_ms, result.output.get("chartType"))
        return result


def _infer_chart(rows: list[dict[str, Any]]) -> tuple[str, str, str]:
    if not rows:
        return "bar", "label", "value"
    keys = list(rows[0].keys())
    x_key = keys[0]
    y_key = keys[1] if len(keys) > 1 else keys[0]
    for key in keys:
        low = key.lower()
        if any(token in low for token in ("date", "time", "month", "day", "ngay", "thang")):
            x_key = key
            break
    for key in keys:
        if key != x_key and isinstance(rows[0].get(key), (int, float)):
            y_key = key
            break
    chart_type = "line" if x_key != keys[0] or any(t in x_key.lower() for t in ("date", "time", "month")) else "bar"
    return chart_type, x_key, y_key
