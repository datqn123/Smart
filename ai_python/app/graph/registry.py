"""INTENT_HANDLERS — TASK-LG-07 (extensible registry metadata).

Routing thực tế nằm trong :func:`app.graph.nodes.intent.route_after_intent`.
"""

from __future__ import annotations

INTENT_HANDLERS_V1: dict[str, str] = {
    "general_chat": "chat_normal",
    "system_data_query": "sql_branch",
    "system_data_chart": "agent_idea",
    "catalog_data_entry": "catalog_draft_branch",
    "inventory_data_entry": "inventory_draft_branch",
}


def normalize_intent(raw: str | None) -> str:
    if raw == "system_data_query":
        return "system_data_query"
    if raw == "system_data_chart":
        return "system_data_chart"
    if raw == "catalog_data_entry":
        return "catalog_data_entry"
    if raw == "inventory_data_entry":
        return "inventory_data_entry"
    return "general_chat"
