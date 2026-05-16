"""Chart readiness: shape checks + optional LLM critic before agent_chart."""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.chart_data_profile import build_query_result_profile, profile_for_prompt
from app.graph.deps import GraphDeps
from app.graph.feedback import append_feedback
from app.graph.message_utils import latest_human_question
from app.graph.retry import can_regen_sql
from app.graph.state import AgentState
from app.llm.schemas import ChartReadinessOutput

logger = logging.getLogger(__name__)

_READINESS_SYSTEM = (
    "You judge whether SQL query results are adequate to draw the user's chart.\n"
    "You do NOT prescribe specific table names. Use the chart brief and the data profile only.\n"
    "If the user asked for a trend / multiple months / breakdown over time, results need multiple "
    "rows or clear categories — a single aggregate row is usually insufficient unless "
    "expected_result_shape is single_kpi.\n"
    "If results contradict the brief or prior assistant answer in context, set ok=false with retry_hint.\n"
    "warnings: non-fatal (e.g. only one month of data but chart can still render one bar)."
)

_READINESS_JSON_CONTRACT = (
    'Single JSON object with keys: "ok" (boolean), "issues" (array of strings), '
    '"retry_hint" (string, empty if ok), "warnings" (array of strings). No markdown fences.'
)


def _expected_shape(chart_brief: dict) -> str:
    dr = chart_brief.get("data_request")
    if isinstance(dr, dict):
        shape = dr.get("expected_result_shape") or dr.get("result_shape")
        if isinstance(shape, str) and shape.strip():
            return shape.strip().lower()
    return ""


def _heuristic_readiness(
    profile: dict,
    *,
    expected_shape: str,
) -> tuple[bool, list[str], list[str]]:
    """Lightweight shape checks — no table-name rules."""
    issues: list[str] = []
    warnings: list[str] = []
    rc = int(profile.get("row_count") or 0)
    if rc == 0:
        issues.append("query returned zero rows")
        return False, issues, warnings

    shape = expected_shape or ""
    if shape == "time_series" or shape == "breakdown":
        if rc < 2:
            issues.append(
                f"expected multiple rows for {shape}, got row_count={rc} "
                "(likely missing GROUP BY time/category)"
            )
        elif rc == 1:
            warnings.append("only one row/bucket — chart will be a single bar/point")
    elif shape == "single_kpi" and rc > 1:
        warnings.append("multiple rows but brief expected single_kpi — chart may pick one series")

    time_cols = profile.get("time_like_columns") or []
    if shape == "time_series" and rc >= 2 and not time_cols:
        warnings.append("no obvious time-like column in profile — verify x axis choice")

    return len(issues) == 0, issues, warnings


def make_chart_readiness_node(deps: GraphDeps):
    def chart_readiness(state: AgentState) -> dict:
        logger.info("node=chart_readiness action=start")
        if state.get("intent") != "system_data_chart":
            return {"chart_data_ok": True}

        if not deps.settings.chart_readiness_enabled:
            return {"chart_data_ok": True}

        brief = state.get("chart_brief")
        if not isinstance(brief, dict):
            brief = {
                "data_request": dict(state.get("idea_data_request") or {}),
                "chart_idea": dict(state.get("idea_chart_idea") or {}),
            }

        qr = state.get("query_result")
        profile = build_query_result_profile(qr)
        shape = _expected_shape(brief)
        ok_h, issues_h, warnings_h = _heuristic_readiness(profile, expected_shape=shape)

        issues = list(issues_h)
        warnings = list(warnings_h)
        retry_hint = ""
        ok = ok_h

        reg = deps.llm_registry
        use_critic = bool(deps.settings.chart_readiness_use_llm_critic and reg is not None)
        if use_critic and (not ok_h or warnings_h or shape in ("time_series", "breakdown")):
            user_q = latest_human_question(state.get("messages"))
            prior = (state.get("chart_thread_context") or "")[:2000]
            sql = (state.get("generated_sql") or "")[:3000]
            human = (
                f"User question:\n{user_q}\n\n"
                f"Chart brief (JSON):\n{json.dumps(brief, ensure_ascii=False)[:3000]}\n\n"
                f"Prior thread context:\n{prior or '(none)'}\n\n"
                f"Executed SQL:\n{sql or '(none)'}\n\n"
                f"Data profile:\n{profile_for_prompt(profile)}\n\n"
                f"Heuristic ok={ok_h}; issues={issues_h}; warnings={warnings_h}"
            )
            messages = [SystemMessage(content=_READINESS_SYSTEM), HumanMessage(content=human)]
            try:
                client = reg.get("chart_critic")
                out = client.structured_predict(
                    messages,
                    ChartReadinessOutput,
                    json_output_contract=_READINESS_JSON_CONTRACT,
                    max_retries=4,
                )
                ok = bool(out.ok)
                if out.issues:
                    issues = list(out.issues)
                if out.warnings:
                    warnings = list(dict.fromkeys([*warnings, *out.warnings]))
                retry_hint = (out.retry_hint or "").strip()
            except Exception:
                logger.warning("chart_readiness critic failed; using heuristics", exc_info=True)

        emit_agent_trace(
            logger,
            deps.settings,
            agent="chart_readiness",
            phase="Đánh giá dữ liệu cho biểu đồ",
            detail=f"ok={ok} row_count={profile.get('row_count')} shape={shape or '?'} issues={issues}",
        )

        upd: dict = {
            "chart_data_ok": ok,
            "chart_data_issues": issues,
            "chart_warnings": warnings,
            "chart_result_profile": profile,
        }
        if not ok and retry_hint:
            upd["chart_retry_hint"] = retry_hint
            syn: AgentState = dict(state)
            syn["validation_feedback"] = append_feedback(
                syn, "result", f"chart readiness: {retry_hint}"
            )
            upd["validation_feedback"] = syn["validation_feedback"]
        return upd

    return chart_readiness


def route_after_sql_subgraph_for_chart(state: AgentState) -> str:
    """Inside SQL subgraph: after validate_result, chart path visits readiness."""
    if state.get("intent") != "system_data_chart":
        return "done"
    if not state.get("result_ok") and not _has_usable_rows(state):
        return "done"
    return "chart_readiness"


def _has_usable_rows(state: AgentState) -> bool:
    qr = state.get("query_result")
    if not isinstance(qr, dict):
        return False
    rows = qr.get("rows")
    return isinstance(rows, list) and len(rows) > 0


def route_after_chart_readiness_in_sql(state: AgentState) -> str:
    if state.get("chart_data_ok"):
        return "done"
    if can_regen_sql(state):
        return "gen_sql"
    return "fail_max_attempts"
