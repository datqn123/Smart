"""TASK-LG-09 — retry eligibility."""

from __future__ import annotations

from app.graph.constants import MAX_SQL_ATTEMPTS
from app.graph.state import AgentState


def can_regen_sql(state: AgentState) -> bool:
    return int(state.get("sql_attempt_count") or 0) < MAX_SQL_ATTEMPTS
