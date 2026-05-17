"""User-selected chat interaction mode → intent override (Task111)."""

from __future__ import annotations

from typing import Literal

InteractionMode = Literal[
    "auto",
    "data_query",
    "data_table",
    "chart",
    "catalog_draft",
    "inventory_draft",
]

VALID_INTERACTION_MODES = frozenset(
    {"auto", "data_query", "data_table", "chart", "catalog_draft", "inventory_draft"},
)

MODE_TO_INTENT: dict[str, str] = {
    "data_query": "system_data_query",
    "data_table": "system_data_query",
    "chart": "system_data_chart",
    "catalog_draft": "catalog_data_entry",
    "inventory_draft": "inventory_data_entry",
}


def normalize_interaction_mode(raw: str | None) -> str:
    if raw and raw in VALID_INTERACTION_MODES:
        return raw
    return "auto"


def resolve_mode_override(mode: str | None) -> dict[str, object] | None:
    """When mode is not ``auto``, return state patch for intent routing."""
    normalized = normalize_interaction_mode(mode)
    if normalized == "auto":
        return None
    intent = MODE_TO_INTENT.get(normalized)
    if not intent:
        return None
    return {
        "intent": intent,
        "show_query_table": normalized == "data_table",
    }


def should_route_query_table(state: dict) -> bool:
    if state.get("show_query_table"):
        return True
    return state.get("interaction_mode") == "data_table"
