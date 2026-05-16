"""Chart report pipeline: Agent_Idea → SQL → Agent_Chart → Agent_Review."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.datetime_display import localize_query_result_for_display
from app.graph.deps import GraphDeps
from app.graph.display_format import format_display_for_chat_ui
from app.graph.message_utils import latest_human_question
from app.graph.state import AgentState
from app.llm.schemas import (
    ChartReviewOutput,
    ChartSpecDraftOutput,
    IdeaPlannerOutput,
)

logger = logging.getLogger(__name__)


def _rows_from_query_result(qr: Any) -> list[dict[str, Any]]:
    if not isinstance(qr, dict):
        return []
    rows = qr.get("rows")
    if not isinstance(rows, list):
        return []
    out: list[dict[str, Any]] = []
    for r in rows:
        if isinstance(r, dict):
            out.append(dict(r))
    return out


def compact_query_result_for_chart_prompt(
    qr: Any,
    *,
    max_rows: int = 12,
    max_chars: int = 3500,
    localize_for_llm: bool = False,
    display_timezone: str | None = None,
) -> str:
    """Build a JSON blob for chart LLM prompts.

    Default ``localize_for_llm=False``: keep timestamp/ISO values from SQL as-is.
    Localized ``dd/mm/yyyy`` strings confuse models (e.g. 01/05 read as January).
    """
    if localize_for_llm and display_timezone and str(display_timezone).strip():
        qr = localize_query_result_for_display(qr, display_timezone)
    rows = _rows_from_query_result(qr)
    if not rows:
        return "(no rows)"
    keys = list(rows[0].keys())
    sample = rows[: max(1, max_rows)]
    blob = json.dumps({"columns": keys, "sample_rows": sample}, ensure_ascii=False)
    if len(blob) <= max_chars:
        return blob
    return blob[: max_chars - 1] + "…"


_IDEA_SYSTEM = (
    "Bạn là Agent_Idea trong ERP đọc hiểu yêu cầu báo cáo / biểu đồ của người dùng.\n"
    "Doanh thu/chi phí/dòng tiền: data_request nên ghi source=financeledger và transaction_type phù hợp "
    "(SalesRevenue cho doanh thu), không dùng salesorders làm nguồn tổng hợp.\n"
    "Trả về JSON đúng schema: data_request (object) mô tả metric, dimension, khoảng thời gian, "
    "đơn vị thời gian (ngày/tuần/tháng), filter nghiệp vụ — không viết SQL, không đoán tên bảng DB.\n"
    "chart_idea (object): loại biểu đồ gợi ý (line|bar|area|pie), tiêu đề gợi ý, mô tả trục X/Y "
    "bằng ngôn ngữ nghiệp vụ.\n"
    "Phạm vi kênh (quan trọng): chỉ thu hẹp **bán lẻ / POS / walk-in / Retail / kênh lẻ** trong filter "
    "khi người dùng nói rõ các khái niệm đó. Nếu họ yêu cầu **so sánh theo từng tháng / xu hướng nhiều tháng** "
    "mà chỉ nói chung **đơn hàng** (không ghi bán lẻ/Retail/POS), đặt filter là **mọi kênh** hoặc mô tả "
    "\"tất cả đơn hàng\" — tránh ám chỉ Retail — vì đơn sỉ/wholesale có thể chiếm phần lớn theo tháng."
)


def _idea_json_contract() -> str:
    return (
        'Single JSON object with exactly two keys: "data_request" and "chart_idea". '
        "Both values must be JSON objects (possibly empty). No markdown fences, no other keys."
    )


_CHART_SYSTEM = (
    "Bạn là Agent_Chart. Đọc ý tưởng biểu đồ và mẫu dữ liệu (tiêu đề cột + vài dòng).\n"
    "Chọn chart_type là line hoặc bar. Chọn x_key và y_key là hai tên cột thật trong mẫu/kết quả "
    "(ASCII key names từ columns list)."
)


_CHART_JSON_CONTRACT = (
    'Single JSON object with keys: "chart_type" (exactly line or bar), "x_key" (string), '
    '"y_key" (string), "title" (string, may be empty). No markdown fences, no other keys.'
)


_REVIEW_SYSTEM = (
    "Bạn là Agent_Review. Căn chỉnh chart_type, x_key, y_key cho đúng với danh sách cột thật; "
    "viết final_answer ngắn tiếng Việt, chỉ dựa trên số liệu trong sample_rows (không bịa).\n"
    "Khi đọc giá trị trục thời gian (tháng): **bám đúng** chuỗi/ISO trong sample_rows (vd. 2026-05-01…). "
    "Không đổi sang \"tháng 1\" / \"tháng 4\" trừ khi bucket trong sample_rows thật sự là tháng đó — "
    "tránh hiểu nhầm định dạng ngày.\n"
    "Nếu chỉ có **một** bucket thời gian nhưng vẫn có số đếm, vẫn coi là đủ để vẽ một cột/điểm; "
    "final_answer ghi rõ đúng tháng/năm đó và số liệu, **không** nói \"không đủ dữ liệu\" chỉ vì ít hơn hai tháng "
    "trừ khi người dùng yêu cầu bắt buộc ≥2 tháng mới có ý nghĩa."
)


_REVIEW_JSON_CONTRACT = (
    'Single JSON object with keys: "chart_type" (line or bar), "x_key", "y_key", "title", '
    '"final_answer" (Vietnamese text). No markdown fences, no other keys.'
)


def _draft_to_dict(d: ChartSpecDraftOutput) -> dict[str, Any]:
    return {
        "chartType": d.chart_type,
        "xKey": d.x_key,
        "series": [{"dataKey": d.y_key, "name": d.title or "Giá trị"}],
        "title": d.title or "",
    }


def build_chart_spec_final(
    rows: list[dict[str, Any]],
    chart_type: str,
    x_key: str,
    y_key: str,
    title: str,
    *,
    row_limit: int = 200,
) -> dict[str, Any]:
    """Build Recharts-friendly payload with embedded data (truncated)."""
    ct = chart_type if chart_type in ("line", "bar") else "bar"
    if not rows:
        return {
            "chartType": ct,
            "xKey": x_key,
            "series": [{"dataKey": y_key, "name": title or "Giá trị"}],
            "title": title,
            "data": [],
        }
    keys0 = set(rows[0].keys())
    xk = x_key if x_key in keys0 else next(iter(keys0))
    yk = y_key if y_key in keys0 and y_key != xk else next((k for k in keys0 if k != xk), xk)
    slim: list[dict[str, Any]] = []
    for r in rows[:row_limit]:
        if isinstance(r, dict) and xk in r and yk in r:
            slim.append({str(xk): r.get(xk), str(yk): r.get(yk)})
    return {
        "chartType": ct,
        "xKey": xk,
        "series": [{"dataKey": yk, "name": title or "Giá trị"}],
        "title": title or "",
        "data": slim,
    }


def make_agent_idea_node(deps: GraphDeps):
    def agent_idea(state: AgentState) -> dict:
        logger.info("node=agent_idea action=start")
        reg = deps.llm_registry
        if reg is None:
            q = latest_human_question(state.get("messages"))
            payload = {
                "idea_data_request": {"question_stub": True, "summary": q[:400]},
                "idea_chart_idea": {"chartType": "bar", "title": "(stub idea)"},
            }
            emit_agent_trace(
                logger,
                deps.settings,
                agent="idea",
                phase="Stub (no LLM registry)",
                detail=json.dumps(payload["idea_data_request"], ensure_ascii=False)[:800],
            )
            return payload
        user_q = latest_human_question(state.get("messages"))
        messages: list[BaseMessage] = [
            SystemMessage(content=_IDEA_SYSTEM),
            HumanMessage(content=f"Câu hỏi / yêu cầu hiện tại:\n{user_q}"),
        ]
        client = reg.get("idea")
        try:
            out = client.structured_predict(
                messages,
                IdeaPlannerOutput,
                json_output_contract=_idea_json_contract(),
            )
            bundle = {"idea_data_request": dict(out.data_request), "idea_chart_idea": dict(out.chart_idea)}
        except Exception:
            logger.warning("agent_idea structured_predict failed", exc_info=True)
            bundle = {
                "idea_data_request": {"parse_error": True},
                "idea_chart_idea": {"chartType": "bar", "title": ""},
            }
        emit_agent_trace(
            logger,
            deps.settings,
            agent="idea",
            phase="Data brief + chart idea",
            detail=json.dumps(bundle["idea_data_request"], ensure_ascii=False)[:1200],
        )
        return bundle

    return agent_idea


def make_agent_chart_node(deps: GraphDeps):
    def agent_chart(state: AgentState) -> dict:
        logger.info("node=agent_chart action=start")
        reg = deps.llm_registry
        qr_raw = state.get("query_result")
        compact = compact_query_result_for_chart_prompt(qr_raw)
        idea = json.dumps(state.get("idea_chart_idea") or {}, ensure_ascii=False)[:2000]
        if reg is None:
            rows = _rows_from_query_result(qr_raw)
            keys = list(rows[0].keys()) if rows else ["x", "y"]
            xk, yk = keys[0], keys[min(1, len(keys) - 1)]
            draft = _draft_to_dict(
                ChartSpecDraftOutput(chart_type="bar", x_key=xk, y_key=yk, title="(stub chart)"),
            )
            emit_agent_trace(
                logger,
                deps.settings,
                agent="chart",
                phase="Stub spec (no LLM registry)",
                detail=json.dumps(draft, ensure_ascii=False)[:800],
            )
            return {"chart_spec_draft": draft}
        human = (
            f"Chart idea (JSON):\n{idea}\n\n"
            f"Query sample (JSON):\n{compact}\n\n"
            "Return chart_type, x_key, y_key using actual column names from sample."
        )
        messages: list[BaseMessage] = [SystemMessage(content=_CHART_SYSTEM), HumanMessage(content=human)]
        client = reg.get("chart")
        try:
            out = client.structured_predict(
                messages,
                ChartSpecDraftOutput,
                json_output_contract=_CHART_JSON_CONTRACT,
            )
            draft = _draft_to_dict(out)
        except Exception:
            logger.warning("agent_chart structured_predict failed", exc_info=True)
            rows = _rows_from_query_result(qr_raw)
            keys = list(rows[0].keys()) if rows else ["_stub", "sql_ok"]
            out = ChartSpecDraftOutput(chart_type="bar", x_key=keys[0], y_key=keys[min(1, len(keys) - 1)], title="")
            draft = _draft_to_dict(out)
        emit_agent_trace(
            logger,
            deps.settings,
            agent="chart",
            phase="Draft Recharts spec",
            detail=json.dumps(draft, ensure_ascii=False)[:1200],
        )
        return {"chart_spec_draft": draft}

    return agent_chart


def make_agent_review_node(deps: GraphDeps):
    def agent_review(state: AgentState) -> dict:
        logger.info("node=agent_review action=start")
        reg = deps.llm_registry
        qr_raw = state.get("query_result")
        rows = _rows_from_query_result(
            localize_query_result_for_display(qr_raw, deps.settings.ai_display_timezone),
        )
        draft = state.get("chart_spec_draft")
        if not isinstance(draft, dict):
            draft = {}
        user_q = latest_human_question(state.get("messages"))
        if reg is None:
            keys = list(rows[0].keys()) if rows else ["_stub", "sql_ok"]
            series = draft.get("series") if isinstance(draft.get("series"), list) else []
            ykey = keys[min(1, len(keys) - 1)]
            if series and isinstance(series[0], dict) and series[0].get("dataKey"):
                yk = str(series[0]["dataKey"])
                if rows and yk in rows[0]:
                    ykey = yk
            xkey = str(draft.get("xKey") or keys[0])
            if rows and xkey not in rows[0]:
                xkey = keys[0]
            title = str(draft.get("title") or "Biểu đồ")
            final = build_chart_spec_final(rows, str(draft.get("chartType") or "bar"), xkey, ykey, title)
            ans = f"Đã tạo biểu đồ ({final['chartType']}). " + (
                f"{len(rows)} dòng dữ liệu." if rows else "Không có dữ liệu."
            )
            fa = format_display_for_chat_ui(ans)
            emit_agent_trace(
                logger,
                deps.settings,
                agent="review",
                phase="Stub finalize",
                detail=json.dumps(final, ensure_ascii=False)[:800],
            )
            return {
                "chart_spec_final": final,
                "final_answer": fa,
                "messages": [AIMessage(content=fa)],
            }
        human = (
            f"Câu hỏi người dùng: {user_q}\n\n"
            f"Draft chart spec (JSON):\n{json.dumps(draft, ensure_ascii=False)}\n\n"
            f"Dữ liệu (cột + sample):\n{compact_query_result_for_chart_prompt(qr_raw)}\n\n"
            "Align x_key and y_key to real column names."
        )
        messages: list[BaseMessage] = [SystemMessage(content=_REVIEW_SYSTEM), HumanMessage(content=human)]
        client = reg.get("review")
        try:
            out = client.structured_predict(
                messages,
                ChartReviewOutput,
                json_output_contract=_REVIEW_JSON_CONTRACT,
            )
        except Exception:
            logger.warning("agent_review structured_predict failed", exc_info=True)
            keys = list(rows[0].keys()) if rows else ["x", "y"]
            out = ChartReviewOutput(
                chart_type="bar",
                x_key=keys[0],
                y_key=keys[min(1, len(keys) - 1)],
                title=str(draft.get("title") or ""),
                final_answer="Không thể hoàn tất rà soát biểu đồ.",
            )
        final = build_chart_spec_final(
            rows,
            out.chart_type,
            out.x_key,
            out.y_key,
            out.title or str(draft.get("title") or ""),
        )
        emit_agent_trace(
            logger,
            deps.settings,
            agent="review",
            phase="Final chart + answer",
            detail=(out.final_answer or "")[:1200],
        )
        fa = format_display_for_chat_ui(out.final_answer or "")
        return {
            "chart_spec_final": final,
            "final_answer": fa,
            "messages": [AIMessage(content=fa)],
        }

    return agent_review


def route_after_sql_branch(state: AgentState) -> str:
    if state.get("intent") == "system_data_chart":
        return "agent_chart"
    return "summarize_answer"
