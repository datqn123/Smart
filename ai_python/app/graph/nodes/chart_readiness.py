"""Chart readiness: shape checks + optional LLM critic before agent_chart."""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.chart_calendar import resolve_month_calendar
from app.graph.chart_data_profile import build_query_result_profile, profile_for_prompt
from app.graph.chart_sql_shape import sql_has_time_grouping
from app.graph.deps import GraphDeps
from app.graph.feedback import append_feedback
from app.graph.message_utils import latest_human_question
from app.graph.retry_policy import (
    RetryAction,
    chart_degrade_state_patch,
    decide_chart_readiness_retry,
)
from app.graph.state import AgentState
from app.llm.schemas import ChartReadinessOutput

logger = logging.getLogger(__name__)

_READINESS_SYSTEM = (
    "You judge whether SQL query results are adequate to draw the user's chart.\n"
    "You do NOT prescribe specific table names. Use the chart brief and the data profile only.\n"
    "If the brief requires include_zero_months / full month calendar, results must have one row per "
    "month in range (zeros allowed). If SQL used only fact GROUP BY without generate_series, set ok=false.\n"
    "If include_zero_months is false and SQL has time grouping with one row, set ok=true with warning "
    "(sparse data).\n"
    "Set ok=false with retry_hint only when SQL is clearly wrong (no time bucket, wrong metric, "
    "contradicts brief) — not merely because row_count is small.\n"
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
    generated_sql: str | None = None,
    expected_month_count: int | None = None,
) -> tuple[bool, list[str], list[str]]:
    """Lightweight shape checks — no table-name rules."""
    issues: list[str] = []
    warnings: list[str] = []
    rc = int(profile.get("row_count") or 0)
    if rc == 0:
        issues.append("query returned zero rows")
        return False, issues, warnings

    shape = expected_shape or ""
    time_cols = profile.get("time_like_columns") or []
    grouped = sql_has_time_grouping(generated_sql)
    if expected_month_count and expected_month_count > 1:
        if rc < expected_month_count:
            issues.append(
                f"include_zero_months requires {expected_month_count} month rows "
                f"(generate_series + LEFT JOIN + COALESCE); got row_count={rc}"
            )
        elif rc > expected_month_count:
            warnings.append(
                f"more rows ({rc}) than calendar months ({expected_month_count}) — verify grouping"
            )

    if shape == "time_series" or shape == "breakdown":
        if expected_month_count and expected_month_count > 1:
            pass
        elif rc == 1:
            if grouped or time_cols:
                warnings.append(
                    "only one time bucket in result — chart will be a single bar; "
                    "SQL grouping looks correct (sparse data)"
                )
            else:
                issues.append(
                    f"expected multiple rows for {shape}, got row_count=1 "
                    "(no time bucket in SQL — add GROUP BY period)"
                )
        elif rc < 2:
            issues.append(f"expected rows for {shape}, got row_count={rc}")
    elif shape == "single_kpi" and rc > 1:
        warnings.append("multiple rows but brief expected single_kpi — chart may pick one series")

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
        sql_text = state.get("generated_sql")
        user_q = latest_human_question(state.get("messages"))
        dr = brief.get("data_request") if isinstance(brief.get("data_request"), dict) else {}
        month_cal = resolve_month_calendar(user_q, dr)
        exp_months = month_cal.month_count if month_cal else None
        ok_h, issues_h, warnings_h = _heuristic_readiness(
            profile,
            expected_shape=shape,
            generated_sql=str(sql_text) if sql_text else None,
            expected_month_count=exp_months,
        )

        issues = list(issues_h)
        warnings = list(warnings_h)
        retry_hint = ""
        ok = ok_h

        reg = deps.llm_registry
        use_critic = bool(deps.settings.chart_readiness_use_llm_critic and reg is not None)
        # Critic only when heuristics fail — avoid overriding ok+warning for thin real data.
        if use_critic and not ok_h:
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
        if not ok:
            probe: AgentState = {**state, **upd}
            decision = decide_chart_readiness_retry(probe)
            if decision.action == RetryAction.CHART_DEGRADE:
                upd.update(chart_degrade_state_patch(probe, reason=decision.reason))
                upd["chart_data_issues"] = issues
            elif decision.action == RetryAction.REGEN_SQL and retry_hint:
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


def _state_for_chart_retry_route(state: AgentState) -> AgentState:
    """Exclude feedback appended in the same chart_readiness turn (budget is per regen_sql)."""
    fb = state.get("validation_feedback")
    if not isinstance(fb, dict):
        return state
    result = list(fb.get("result") or [])
    if not result or "chart readiness" not in str(result[-1]).lower():
        return state
    trimmed = {**fb, "result": result[:-1]}
    return {**state, "validation_feedback": trimmed}


def route_after_chart_readiness_in_sql(state: AgentState) -> str:
    if state.get("chart_data_ok"):
        return "done"
    route_state = _state_for_chart_retry_route(state)
    if decide_chart_readiness_retry(route_state).action == RetryAction.REGEN_SQL:
        return "gen_sql"
    return "fail_max_attempts"
