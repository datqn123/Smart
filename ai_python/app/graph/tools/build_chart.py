"""Chart harness tool adapter."""

from __future__ import annotations

from typing import Any

from app.graph.nodes.chart_report import build_chart_spec_final
from app.harness.tool_registry import ToolManifest, ToolResult, TurnContext


class BuildChartTool:
    manifest = ToolManifest(
        name="build_chart",
        description="Build a frontend chart payload from rows.",
        args_schema='{"rows":"list"}',
    )

    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
        _ = ctx
        rows = [row for row in (args.get("rows") or []) if isinstance(row, dict)]
        chart_type, x_key, y_key = _infer_chart(rows)
        spec = build_chart_spec_final(rows, chart_type, x_key, y_key, args.get("title") or "Biểu đồ dữ liệu")
        return ToolResult(
            ok=True,
            output=spec,
            observation_text=f"Đã tạo biểu đồ {spec.get('chartType')}.",
            sse_payload={"_event": "chart", **spec},
        )


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
