"""LangGraph state schema (TASK-LG-03)."""

from __future__ import annotations

from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """Merged across main graph and SQL subgraph."""

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
    sql_review_ok: bool | None
    sql_valid: bool | None
    result_ok: bool | None
    result_empty: bool | None
    error_payload: dict[str, Any] | None
    # Task007 — SQL-Factory-lite (optional keys; safe for old checkpoints)
    selected_tables: list[str] | None
    sql_allowlist_tables: list[str] | None
    sql_gen_mode: Literal["explore", "exploit"] | None
    sql_attempt_history: list[str] | None
    sql_local_pool: list[str] | None
    runtime_schema_artifact: dict[str, Any] | None
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
    # Ledger-first schema explorer (optional)
    schema_plan: dict[str, Any] | None
    ledger_metric_id: str | None
    schema_join_hints: list[str] | None
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
    business_scope: dict[str, Any] | None
    last_business_scope: dict[str, Any] | None
    last_data_answer: dict[str, Any] | None
    # Context compaction (conversation memory)
    conversation_summary: str | None
    context_compact_generation: int | None
    # SSE progress text shown to user during processing
    progress_text: str | None


def default_initial_state() -> AgentState:
    return {
        "context_compact_generation": 0,
        "sql_attempt_count": 0,
        "sql_repair_max_attempts": None,
        "route_source": None,
        "validation_feedback": {
            "intent_review": [],
            "policy": [],
            "exec": [],
            "result": [],
            "attempts": 0,
            "extras": None,
        },
    }
