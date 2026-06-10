"""Answer composer harness tool."""

from __future__ import annotations

import logging
import time
from typing import Any

from pydantic import BaseModel, Field

from app.harness.tool_registry import ToolManifest, ToolResult, TurnContext

logger = logging.getLogger(__name__)


class AnswerComposerOutput(BaseModel):
    answer_markdown: str
    assumptions: list[str] = Field(default_factory=list)
    follow_ups: list[str] = Field(default_factory=list)


class AnswerComposerTool:
    manifest = ToolManifest(
        name="answer_composer",
        description="Compose a Vietnamese final answer from tool observations.",
        args_schema='{"observations":"list","assumptions":"list[str]"}',
        capability="answer_compose",
        output_schema='{"answer_markdown": "string", "assumptions": "list[str]"}',
        output_artifact_types=("answer",),
        when_to_use="Final step: summarize observations into a Vietnamese answer and reference emitted artifacts.",
        when_not_to_use="Data still needs to be fetched or validated, or the user needs a raw table/chart artifact only.",
        risk_level="low",
        side_effect_class="read_only",
        consumes=("observations", "rows"),
        produces=("answer",),
        examples=("tổng hợp kết quả thành câu trả lời", "trả lời kèm tham chiếu bảng/biểu đồ"),
    )

    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
        _invoke_start = time.monotonic()
        logger.info("tool_invoke_start tool=answer_composer observations_count=%s", len(args.get("observations", [])))
        _ = ctx
        observations = args.get("observations") or []
        assumptions = [str(item) for item in (args.get("assumptions") or []) if str(item).strip()]
        rows = _first_rows(observations)
        row_count = _total_row_count(observations)

        if not rows:
            answer = (
                "Không tìm thấy dữ liệu phù hợp với yêu cầu hiện tại. "
                "Bạn có thể hỏi lại cụ thể hơn, ví dụ: doanh thu tháng này hoặc tồn kho của một sản phẩm cụ thể."
            )
        else:
            answer = _build_answer(rows, row_count)

        if assumptions:
            answer += "\n\n**Giả định:** " + "; ".join(assumptions)
        follow_ups = [
            "Bạn có muốn xem chi tiết theo thời gian không?",
            "Bạn có muốn so sánh với kỳ trước không?",
        ]
        answer += "\n\n**Gợi ý tiếp theo:**\n" + "\n".join(f"- {item}" for item in follow_ups)
        output = AnswerComposerOutput(
            answer_markdown=answer,
            assumptions=assumptions,
            follow_ups=follow_ups,
        )
        _latency_ms = (time.monotonic() - _invoke_start) * 1000
        result = ToolResult(
            ok=True,
            output=output.model_dump(mode="json"),
            observation_text=answer,
            sse_payload={"_event": "delta_full", "text": answer},
        )
        logger.info("tool_invoke_end tool=answer_composer ok=%s latency_ms=%.0f answer_chars=%s",
                    result.ok, _latency_ms, len(result.output.get("answer_markdown", "")))
        return result


def _first_rows(observations: Any) -> list[dict[str, Any]]:
    if not isinstance(observations, list):
        return []
    for item in observations:
        if not isinstance(item, dict):
            continue
        rows = item.get("rows")
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def _total_row_count(observations: Any) -> int:
    if not isinstance(observations, list):
        return 0
    for item in observations:
        if not isinstance(item, dict):
            continue
        rc = item.get("row_count")
        if isinstance(rc, int):
            return rc
        rows = item.get("rows")
        if isinstance(rows, list):
            return len(rows)
    return 0


# Column-name heuristics for detecting common metrics.
_NAME_COLS = ("product_name", "name", "item_name", "customer_name", "ten", "tên")
_QTY_COLS = ("total_quantity_sold", "quantity", "total_qty", "qty", "so_luong", "sl")
_REVENUE_COLS = ("total_revenue", "revenue", "doanh_thu", "amount", "line_total", "tong_tien")
_STOCK_COLS = ("stock", "ton_kho", "available_qty", "inventory")


def _fmt_number(value: Any) -> str:
    try:
        n = float(value)
        if n == int(n):
            return f"{int(n):,}"
        return f"{n:,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _pick(row: dict[str, Any], candidates: tuple[str, ...]) -> Any:
    for key in candidates:
        if key in row:
            return row[key]
        # case-insensitive fallback
        for k in row:
            if k.lower() == key.lower():
                return row[k]
    return None


def _build_answer(rows: list[dict[str, Any]], row_count: int) -> str:
    total = row_count or len(rows)
    display_rows = rows[:10]

    lines: list[str] = []
    for i, row in enumerate(display_rows, 1):
        name = _pick(row, _NAME_COLS)
        qty = _pick(row, _QTY_COLS)
        revenue = _pick(row, _REVENUE_COLS)
        stock = _pick(row, _STOCK_COLS)

        if name is not None:
            label = f"**{i}. {name}**"
        else:
            # Generic row: render first 3 key=value pairs
            label = "**" + str(i) + ".** " + ", ".join(
                f"{k}: {v}" for k, v in list(row.items())[:3]
            )

        parts: list[str] = [label]
        if qty is not None:
            parts.append(f"Số lượng: {_fmt_number(qty)}")
        if revenue is not None:
            parts.append(f"Doanh thu: {_fmt_number(revenue)}đ")
        if stock is not None and qty is None and revenue is None:
            parts.append(f"Tồn kho: {_fmt_number(stock)}")

        lines.append(" — ".join(parts))

    header = f"Tìm được **{total}** bản ghi phù hợp."
    if total > len(display_rows):
        header += f" Hiển thị top {len(display_rows)}:"
    else:
        header += " Kết quả:"

    return header + "\n\n" + "\n\n".join(lines)
