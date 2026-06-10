"""Smart SQL/chart retry: classify failures, budgets, dedup, degrade."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Literal

from app.graph.chart_data_profile import build_query_result_profile
from app.graph.constants import MAX_SQL_ATTEMPTS
from app.graph.state import AgentState


def strip_trailing_semicolons(text: str) -> str:
    return re.sub(r";+\s*$", "", text)


def normalize_llm_sql_output(sql: str | None) -> str:
    if not sql:
        return ""
    return strip_trailing_semicolons(sql).strip()


def sql_has_time_grouping(sql: str) -> bool:
    low = sql.lower()
    return any(
        kw in low
        for kw in (
            "date_trunc",
            "to_char(",
            "extract(",
            "date_part",
            "generate_series",
        )
    )

FailureKind = Literal["policy", "intent_review", "exec", "result", "chart_shape"]

MAX_POLICY_RETRIES = 3
MAX_EXEC_RETRIES = 3
MAX_RESULT_RETRIES = 2
MAX_CHART_SHAPE_RETRIES = 1


class RetryAction(str, Enum):
    REGEN_SQL = "regen_sql"
    FAIL = "fail"
    CHART_DEGRADE = "chart_degrade"


@dataclass(frozen=True)
class RetryDecision:
    action: RetryAction
    reason: str
    failure_kind: FailureKind | None = None


def sql_fingerprint(sql: str | None) -> str:
    s = strip_trailing_semicolons(normalize_llm_sql_output(sql or "") or "")
    return re.sub(r"\s+", " ", s.lower()).strip()


def _feedback_bucket(state: AgentState, key: str) -> list[str]:
    fb = state.get("validation_feedback")
    if not isinstance(fb, dict):
        return []
    items = fb.get(key)
    return list(items) if isinstance(items, list) else []


def _failure_signatures(state: AgentState) -> list[str]:
    fb = state.get("validation_feedback")
    if not isinstance(fb, dict):
        return []
    extras = fb.get("extras")
    if not isinstance(extras, dict):
        return []
    items = extras.get("failure_signatures")
    return [str(x) for x in items] if isinstance(items, list) else []


def _chart_shape_retry_count(state: AgentState) -> int:
    return sum(1 for x in _feedback_bucket(state, "result") if "chart readiness" in x.lower())


def _has_query_rows(state: AgentState) -> bool:
    qr = state.get("query_result")
    if not isinstance(qr, dict):
        return False
    rows = qr.get("rows")
    if isinstance(rows, list) and len(rows) > 0:
        return True
    meta = qr.get("meta") if isinstance(qr.get("meta"), dict) else {}
    rc = meta.get("row_count")
    return isinstance(rc, int) and rc > 0


def sql_attempt_duplicate(state: AgentState) -> bool:
    """True if last two recorded SQL texts are identical (futile retry)."""
    hist = list(state.get("sql_attempt_history") or [])
    if len(hist) < 2:
        return False
    return sql_fingerprint(hist[-1]) == sql_fingerprint(hist[-2])


def sql_attempt_duplicate_same_failure(state: AgentState) -> bool:
    """True when both SQL fingerprint and latest failure signature repeat."""
    if not sql_attempt_duplicate(state):
        return False
    sig = _failure_signatures(state)
    if len(sig) < 2:
        return False
    return str(sig[-1]).strip() == str(sig[-2]).strip()


def chart_thin_data_sql_ok(state: AgentState) -> bool:
    """Chart time_series with one row but SQL already grouped — retry cannot add months."""
    if state.get("intent") != "system_data_chart":
        return False
    profile = build_query_result_profile(state.get("query_result"))
    rc = int(profile.get("row_count") or 0)
    if rc != 1:
        return False
    sql = str(state.get("generated_sql") or "")
    if not sql_has_time_grouping(sql):
        return False
    return bool(profile.get("time_like_columns"))


def chart_degrade_eligible(state: AgentState) -> bool:
    return state.get("intent") == "system_data_chart" and _has_query_rows(state)


def chart_degrade_state_patch(state: AgentState, *, reason: str) -> dict:
    warnings = list(state.get("chart_warnings") or [])
    msg = reason.strip() or "Dùng dữ liệu truy vấn cuối để vẽ biểu đồ."
    if msg not in warnings:
        warnings.append(msg)
    return {
        "chart_data_ok": True,
        "chart_warnings": warnings,
        "chart_degraded": True,
        "error_payload": None,
    }


def _global_attempts_left(state: AgentState) -> bool:
    cfg = state.get("sql_repair_max_attempts")
    try:
        cap = int(cfg) if cfg is not None else MAX_SQL_ATTEMPTS
    except (TypeError, ValueError):
        cap = MAX_SQL_ATTEMPTS
    if cap <= 0:
        cap = MAX_SQL_ATTEMPTS
    return int(state.get("sql_attempt_count") or 0) < cap


def _budget_left(state: AgentState, kind: FailureKind) -> bool:
    if kind == "intent_review":
        # One sql_review failure per gen_sql round — do not exhaust budget on issue count.
        return int(state.get("sql_attempt_count") or 0) < MAX_POLICY_RETRIES
    if kind == "policy":
        return len(_feedback_bucket(state, "policy")) < MAX_POLICY_RETRIES
    if kind == "exec":
        return len(_feedback_bucket(state, "exec")) < MAX_EXEC_RETRIES
    if kind == "result":
        return len(_feedback_bucket(state, "result")) < MAX_RESULT_RETRIES
    if kind == "chart_shape":
        return _chart_shape_retry_count(state) < MAX_CHART_SHAPE_RETRIES
    return False


def _maybe_degrade(state: AgentState, reason: str, kind: FailureKind | None) -> RetryDecision:
    if chart_degrade_eligible(state):
        return RetryDecision(RetryAction.CHART_DEGRADE, reason, kind)
    return RetryDecision(RetryAction.FAIL, reason, kind)


def decide_sql_retry(state: AgentState, *, kind: FailureKind) -> RetryDecision:
    if chart_thin_data_sql_ok(state):
        return _maybe_degrade(state, "sparse time data — SQL grouped correctly", kind)

    if not _global_attempts_left(state):
        return _maybe_degrade(state, "max sql attempts", kind)

    if sql_attempt_duplicate_same_failure(state):
        return _maybe_degrade(state, "duplicate SQL + duplicate failure signature", kind)

    if kind == "chart_shape" and sql_attempt_duplicate(state):
        return _maybe_degrade(state, "duplicate SQL retry blocked", kind)

    if not _budget_left(state, kind):
        return _maybe_degrade(state, f"{kind} retry budget exhausted", kind)

    return RetryDecision(RetryAction.REGEN_SQL, f"retry {kind}", kind)


def decide_chart_readiness_retry(state: AgentState) -> RetryDecision:
    if state.get("chart_data_ok"):
        return RetryDecision(RetryAction.CHART_DEGRADE, "readiness ok")

    if chart_thin_data_sql_ok(state):
        return RetryDecision(
            RetryAction.CHART_DEGRADE,
            "thin time_series with valid grouping",
            "chart_shape",
        )

    if sql_attempt_duplicate(state):
        if chart_degrade_eligible(state):
            return RetryDecision(
                RetryAction.CHART_DEGRADE,
                "duplicate SQL after chart readiness fail",
                "chart_shape",
            )
        return RetryDecision(RetryAction.FAIL, "duplicate SQL", "chart_shape")

    return decide_sql_retry(state, kind="chart_shape")


def can_regen_sql(state: AgentState) -> bool:
    """Backward-compatible: any failure kind may still regen."""
    return decide_sql_retry(state, kind="policy").action == RetryAction.REGEN_SQL
