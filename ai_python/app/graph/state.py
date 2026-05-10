"""LangGraph state schema (TASK-LG-03)."""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """Merged across main graph and SQL subgraph."""

    messages: Annotated[list[BaseMessage], add_messages]
    intent: str | None
    schema_version: str | None
    generated_sql: str | None
    sql_attempt_count: int
    validation_feedback: dict[str, Any] | None
    query_result: Any | None
    final_answer: str | None
    correlation_id: str | None
    tenant_id: str | None
    sql_review_ok: bool | None
    sql_valid: bool | None
    result_ok: bool | None
    result_empty: bool | None
    error_payload: dict[str, Any] | None


def default_initial_state() -> AgentState:
    return {
        "sql_attempt_count": 0,
        "validation_feedback": {
            "intent_review": [],
            "policy": [],
            "exec": [],
            "result": [],
            "attempts": 0,
            "extras": None,
        },
    }
