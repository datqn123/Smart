"""LangGraph state schema (TASK-LG-03)."""

from __future__ import annotations

from typing import Annotated, Any, NotRequired, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """Main graph AgentState — survives across turns."""

    messages: Annotated[list[BaseMessage], add_messages]
    intent: str | None
    route_source: str | None
    schema_version: str | None
    generated_sql: str | None
    sql_attempt_count: int
    sql_repair_max_attempts: int | None
    validation_feedback: dict[str, Any] | None
    query_result: Any | None
    final_answer: str | None
    correlation_id: str | None
    user_id: str | None
    tenant_id: str | None
    thread_id: str | None
    error_payload: dict[str, Any] | None
    # Task007 — SQL-Factory-lite (optional keys; safe for old checkpoints)
    # Chart pipeline (optional; safe for old checkpoints)
    idea_data_request: dict[str, Any] | None
    idea_chart_idea: dict[str, Any] | None
    chart_spec_draft: dict[str, Any] | None
    chart_spec_final: dict[str, Any] | None
    chart_brief: dict[str, Any] | None
    chart_thread_context: str | None
    chart_data_ok: bool | None
    chart_data_issues: list[str] | None
    chart_warnings: list[str] | None
    chart_retry_hint: str | None
    chart_result_profile: dict[str, Any] | None
    chart_degraded: bool | None

    # Catalog draft HITL (optional)
    catalog_entity_type: str | None
    catalog_row_count_hint: int | None
    catalog_draft_slots: dict[str, Any] | None
    catalog_draft_payload: dict[str, Any] | None
    catalog_draft_id: str | None
    catalog_draft_sse: dict[str, Any] | None
    catalog_draft_existing_data: list[dict[str, Any]] | None
    # Inventory document draft HITL (Task111)
    inventory_doc_type: str | None
    inventory_line_count_hint: int | None
    inventory_draft_slots: dict[str, Any] | None
    inventory_draft_payload: dict[str, Any] | None
    inventory_draft_id: str | None
    inventory_draft_sse: dict[str, Any] | None
    spring_bearer_token: str | None
    # Task111 — explicit UI interaction mode
    interaction_mode: str | None
    show_query_table: bool | None
    query_table_sse: dict[str, Any] | None
    # Task112 — ERP domain guard
    domain_guard_action: str | None
    normalized_user_question: str | None
    domain_context: dict[str, Any] | None
    domain_clarify_sse: dict[str, Any] | None
    pending_clarification: dict[str, Any] | None
    clarification_response: dict[str, Any] | None
    clarification_applied_context: dict[str, Any] | None
    business_scope: dict[str, Any] | None
    last_business_scope: dict[str, Any] | None
    last_data_answer: dict[str, Any] | None
    # Context compaction (conversation memory)
    conversation_summary: str | None
    context_compact_generation: int | None
    # Pre-intent planner (strategy routing)
    planning_mode: str | None
    planner_strategy: str | None
    planner_reason: str | None
    planner_confidence: float | None
    planner_doc_refs: list[str] | None
    # SSE progress text shown to user during processing
    progress_text: str | None
    # Entity resolution context (Task 3)
    entity_context: NotRequired[dict[str, Any]]


_TRANSIENT_KEYS = frozenset(
    {
        "query_result",
        "generated_sql",
        "final_answer",
        "error_payload",
        "intent",
        "route_source",
        "idea_data_request",
        "idea_chart_idea",
        "chart_spec_draft",
        "chart_spec_final",
        "chart_brief",
        "chart_thread_context",
        "chart_data_ok",
        "chart_data_issues",
        "chart_warnings",
        "chart_retry_hint",
        "chart_result_profile",
        "chart_degraded",
        "catalog_entity_type",
        "catalog_row_count_hint",
        "catalog_draft_slots",
        "catalog_draft_payload",
        "catalog_draft_id",
        "catalog_draft_sse",
        "catalog_draft_existing_data",
        "inventory_doc_type",
        "inventory_line_count_hint",
        "inventory_draft_slots",
        "inventory_draft_payload",
        "inventory_draft_id",
        "inventory_draft_sse",
        "domain_guard_action",
        "normalized_user_question",
        "domain_context",
        "domain_clarify_sse",
        "pending_clarification",
        "clarification_applied_context",
        "show_query_table",
        "query_table_sse",
        "planner_strategy",
        "planner_reason",
        "planner_confidence",
        "planner_doc_refs",
        "progress_text",
    }
)


def fresh_turn_overlay() -> dict[str, None]:
    return {key: None for key in _TRANSIENT_KEYS}


def default_initial_state() -> AgentState:
    return {
        "context_compact_generation": 0,
        "sql_attempt_count": 0,
        "sql_repair_max_attempts": None,
        "route_source": None,
        "planning_mode": "auto",
        "planner_strategy": None,
        "planner_reason": None,
        "planner_confidence": None,
        "planner_doc_refs": None,
        "validation_feedback": {
            "intent_review": [],
            "policy": [],
            "exec": [],
            "result": [],
            "attempts": 0,
            "extras": None,
        },
    }
