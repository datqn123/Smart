"""Chart report pipeline: Agent_Idea → SQL → Agent_Chart → Agent_Review."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.chart_catalog import chart_catalog_snippet
from app.graph.chart_data_profile import build_query_result_profile, profile_for_prompt
from app.graph.chart_thread_context import format_prior_turns_for_chart
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
from app.prompts.load import load_agent_json_contract, load_agent_prompt

logger = logging.getLogger(__name__)

_IDEA_SYSTEM = load_agent_prompt("idea")
_CHART_SYSTEM = load_agent_prompt("chart")
_REVIEW_SYSTEM = load_agent_prompt("chart_review")


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


def _idea_json_contract() -> str:
    return load_agent_json_contract("idea") or ""


_CHART_JSON_CONTRACT = load_agent_json_contract("chart") or ""


_REVIEW_JSON_CONTRACT = load_agent_json_contract("chart_review") or ""


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
    ct = chart_type if chart_type in ("line", "bar", "pie") else "bar"
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
        user_q = latest_human_question(state.get("messages"))
        thread_ctx = format_prior_turns_for_chart(
            state.get("messages"),
            max_turns=int(deps.settings.chart_thread_context_max_turns),
            summary=state.get("conversation_summary"),
        )
        catalog = ""
        if deps.settings.chart_brief_catalog_max_tables > 0:
            catalog = chart_catalog_snippet(deps.settings, user_q)
        if reg is None:
            q = user_q
            dr = {"question_stub": True, "summary": q[:400], "expected_result_shape": "time_series"}
            payload = {
                "idea_data_request": dr,
                "idea_chart_idea": {"chartType": "bar", "title": "(stub idea)"},
                "chart_brief": {"data_request": dr, "chart_idea": {"chartType": "bar", "title": "(stub idea)"}},
                "chart_thread_context": thread_ctx or None,
            }
            emit_agent_trace(
                logger,
                deps.settings,
                agent="idea",
                phase="Stub (no LLM registry)",
                detail=json.dumps(payload["idea_data_request"], ensure_ascii=False)[:800],
            )
            return payload
        parts = [f"Câu hỏi / yêu cầu hiện tại:\n{user_q}"]
        if thread_ctx:
            parts.append(f"\nPrior thread (same topic — stay consistent):\n{thread_ctx}")
        if catalog:
            parts.append(f"\nTable catalog (hints only — pick via SQL author, do not invent tables):\n{catalog}")
        messages: list[BaseMessage] = [
            SystemMessage(content=_IDEA_SYSTEM),
            HumanMessage(content="\n".join(parts)),
        ]
        client = reg.get("idea")
        try:
            out = client.structured_predict(
                messages,
                IdeaPlannerOutput,
                json_output_contract=_idea_json_contract(),
                max_retries=4,
            )
            dr = dict(out.data_request)
            ci = dict(out.chart_idea)
            bundle = {
                "idea_data_request": dr,
                "idea_chart_idea": ci,
                "chart_brief": {"data_request": dr, "chart_idea": ci},
                "chart_thread_context": thread_ctx or None,
            }
        except Exception:
            logger.warning("agent_idea structured_predict failed", exc_info=True)
            bundle = {
                "idea_data_request": {"parse_error": True, "expected_result_shape": "time_series"},
                "idea_chart_idea": {"chartType": "bar", "title": ""},
                "chart_brief": None,
                "chart_thread_context": thread_ctx or None,
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
        profile = state.get("chart_result_profile") or build_query_result_profile(qr_raw)
        compact = compact_query_result_for_chart_prompt(qr_raw)
        brief = state.get("chart_brief") or {}
        idea = json.dumps(state.get("idea_chart_idea") or brief.get("chart_idea") or {}, ensure_ascii=False)[
            :2000
        ]
        warnings = state.get("chart_warnings") or []
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
            f"Chart brief (JSON):\n{json.dumps(brief, ensure_ascii=False)[:2500]}\n\n"
            f"Chart idea (JSON):\n{idea}\n\n"
            f"Column profile:\n{profile_for_prompt(profile)}\n\n"
            f"Query sample (JSON):\n{compact}\n\n"
            f"Warnings: {warnings or '(none)'}\n\n"
            "Return chart_type, x_key, y_key using actual column names from profile/sample."
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
        profile = state.get("chart_result_profile") or build_query_result_profile(qr_raw)
        warnings = state.get("chart_warnings") or []
        human = (
            f"Câu hỏi người dùng: {user_q}\n\n"
            f"Draft chart spec (JSON):\n{json.dumps(draft, ensure_ascii=False)}\n\n"
            f"Column profile:\n{profile_for_prompt(profile)}\n\n"
            f"Dữ liệu (cột + sample):\n{compact_query_result_for_chart_prompt(qr_raw)}\n\n"
            f"Warnings: {warnings or '(none)'}\n\n"
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


def make_chart_fail_message_node(deps: GraphDeps):
    def chart_fail_message(state: AgentState) -> dict:
        logger.info("node=chart_fail_message action=start")
        issues = state.get("chart_data_issues") or []
        hint = (state.get("chart_retry_hint") or "").strip()
        err = state.get("error_payload") if isinstance(state.get("error_payload"), dict) else {}
        if err.get("error") == "max_sql_attempts":
            msg = "Không tạo được biểu đồ: đã hết số lần thử SQL."
        elif issues:
            msg = "Không tạo được biểu đồ phù hợp: " + "; ".join(str(i) for i in issues[:3])
        elif hint:
            msg = f"Không tạo được biểu đồ: {hint}"
        else:
            msg = "Không tạo được biểu đồ từ dữ liệu hiện tại."
        fa = format_display_for_chat_ui(msg)
        emit_agent_trace(
            logger,
            deps.settings,
            agent="chart_fail",
            phase="Chart aborted",
            detail=msg[:800],
        )
        return {"final_answer": fa, "messages": [AIMessage(content=fa)]}

    return chart_fail_message


