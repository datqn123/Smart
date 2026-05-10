"""INTENT_HANDLERS — TASK-LG-07 (extensible registry metadata).

Routing thực tế nằm trong :func:`app.graph.nodes.intent.route_after_intent`.
"""

from __future__ import annotations

INTENT_HANDLERS_V1: dict[str, str] = {
    "general_chat": "chat_normal",
    "system_data_query": "sql_branch",
}


def normalize_intent(raw: str | None) -> str:
    if raw == "system_data_query":
        return "system_data_query"
    return "general_chat"
