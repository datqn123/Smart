"""Answer composer harness tool."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.harness.tool_registry import ToolManifest, ToolResult, TurnContext


class AnswerComposerOutput(BaseModel):
    answer_markdown: str
    assumptions: list[str] = Field(default_factory=list)
    follow_ups: list[str] = Field(default_factory=list)


class AnswerComposerTool:
    manifest = ToolManifest(
        name="answer_composer",
        description="Compose a Vietnamese final answer from tool observations.",
        args_schema='{"observations":"list","assumptions":"list[str]"}',
    )

    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
        _ = ctx
        observations = args.get("observations") or []
        assumptions = [str(item) for item in (args.get("assumptions") or []) if str(item).strip()]
        rows = _first_rows(observations)
        if not rows:
            answer = (
                "Không tìm thấy dữ liệu phù hợp với yêu cầu hiện tại. "
                "Bạn có thể hỏi lại cụ thể hơn, ví dụ: doanh thu tháng này hoặc tồn kho của một sản phẩm cụ thể."
            )
        else:
            answer = f"Tôi đã tổng hợp được {len(rows)} dòng dữ liệu phù hợp. Điểm chính: {_summarize_first_row(rows[0])}."
        if assumptions:
            answer += "\n\nGiả định: " + "; ".join(assumptions)
        follow_ups = [
            "Bạn có muốn xem chi tiết theo thời gian không?",
            "Bạn có muốn so sánh với kỳ trước không?",
        ]
        answer += "\n\nGợi ý tiếp theo:\n" + "\n".join(f"- {item}" for item in follow_ups)
        output = AnswerComposerOutput(
            answer_markdown=answer,
            assumptions=assumptions,
            follow_ups=follow_ups,
        )
        return ToolResult(
            ok=True,
            output=output.model_dump(mode="json"),
            observation_text=answer,
            sse_payload={"_event": "delta_full", "text": answer},
        )


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


def _summarize_first_row(row: dict[str, Any]) -> str:
    parts = [f"{key}={value}" for key, value in list(row.items())[:3]]
    return ", ".join(parts) if parts else "có dữ liệu"
