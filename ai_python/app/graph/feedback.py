"""Structured-dict validation feedback (Task 3 / Trục β = C)."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from app.graph.state import AgentState

FeedbackSource = Literal["intent_review", "policy", "exec", "result", "sql_fix"]


class ValidationFeedback(TypedDict, total=False):
    intent_review: list[str]
    policy: list[str]
    exec: list[str]
    result: list[str]
    sql_fix: list[str]
    attempts: int
    extras: dict[str, Any] | None


def empty_feedback() -> ValidationFeedback:
    return {
        "intent_review": [],
        "policy": [],
        "exec": [],
        "result": [],
        "sql_fix": [],
        "attempts": 0,
        "extras": None,
    }


def append_feedback(state: AgentState, source: FeedbackSource, detail: str) -> ValidationFeedback:
    """Return a NEW feedback dict (immutable update for LangGraph state merge)."""
    prev = state.get("validation_feedback")
    if not isinstance(prev, dict):
        prev = empty_feedback()
    new: ValidationFeedback = {
        "intent_review": list(prev.get("intent_review", [])),
        "policy": list(prev.get("policy", [])),
        "exec": list(prev.get("exec", [])),
        "result": list(prev.get("result", [])),
        "sql_fix": list(prev.get("sql_fix", [])),
        "attempts": int(prev.get("attempts", 0)),
        "extras": prev.get("extras"),
    }
    new[source].append(detail)  # type: ignore[index]
    return new


def render_for_prompt(
    fb: ValidationFeedback | None,
    *,
    latest_only: bool = False,
    max_items_per_bucket: int | None = None,
) -> str:
    """Render only buckets with content — NFR token cost (ADR-003 §5.5)."""
    if not fb:
        return ""
    parts: list[str] = []
    for k in ("sql_fix", "intent_review", "policy", "exec", "result"):
        items = fb.get(k) or []
        if not items:
            continue
        if latest_only:
            slice_items = items[-1:]
        elif max_items_per_bucket is not None and max_items_per_bucket > 0:
            slice_items = items[-max_items_per_bucket:]
        else:
            slice_items = items
        if len(slice_items) == 1:
            parts.append(f"[{k}] {slice_items[0]}")
        else:
            parts.append(f"[{k}] " + "; ".join(slice_items))
    if fb.get("attempts"):
        parts.append(f"attempts={fb['attempts']}")
    return "\n".join(parts)


def render_for_retry_prompt(fb: ValidationFeedback | None) -> str:
    """Compact feedback for gen_sql retries: latest sql_fix + one line per other bucket."""
    if not fb:
        return ""
    parts: list[str] = []
    fixes = fb.get("sql_fix") or []
    if fixes:
        parts.append("[sql_fix — mandatory]\n" + fixes[-1])
    for k in ("intent_review", "policy", "exec", "result"):
        items = fb.get(k) or []
        if not items:
            continue
        parts.append(f"[{k}] {items[-1]}")
    if fb.get("attempts"):
        parts.append(f"attempts={fb['attempts']}")
    return "\n\n".join(parts)


def has_sql_fix_feedback(fb: ValidationFeedback | None) -> bool:
    return bool(fb and (fb.get("sql_fix") or []))


def bump_attempts(state: AgentState) -> ValidationFeedback:
    prev = state.get("validation_feedback")
    if not isinstance(prev, dict):
        base = empty_feedback()
    else:
        base = {
            "intent_review": list(prev.get("intent_review", [])),
            "policy": list(prev.get("policy", [])),
            "exec": list(prev.get("exec", [])),
            "result": list(prev.get("result", [])),
            "sql_fix": list(prev.get("sql_fix", [])),
            "attempts": int(prev.get("attempts", 0)),
            "extras": prev.get("extras"),
        }
    base["attempts"] = int(base.get("attempts", 0)) + 1
    return base
