"""Task111 — interaction mode → intent override."""

from __future__ import annotations

from app.graph.interaction_mode import (
    normalize_interaction_mode,
    resolve_mode_override,
    should_route_query_table,
)


def test_normalize_interaction_mode_defaults_to_auto() -> None:
    assert normalize_interaction_mode(None) == "auto"
    assert normalize_interaction_mode("invalid") == "auto"
    assert normalize_interaction_mode("data_table") == "data_table"


def test_resolve_mode_override_auto_returns_none() -> None:
    assert resolve_mode_override("auto") is None
    assert resolve_mode_override(None) is None


def test_resolve_mode_override_maps_intents() -> None:
    assert resolve_mode_override("data_query") == {
        "intent": "system_data_query",
        "show_query_table": False,
    }
    assert resolve_mode_override("data_table") == {
        "intent": "system_data_query",
        "show_query_table": True,
    }
    assert resolve_mode_override("chart") == {
        "intent": "system_data_chart",
        "show_query_table": False,
    }
    assert resolve_mode_override("catalog_draft") == {
        "intent": "catalog_data_entry",
        "show_query_table": False,
    }
    assert resolve_mode_override("inventory_draft") == {
        "intent": "inventory_data_entry",
        "show_query_table": False,
    }


def test_should_route_query_table() -> None:
    assert should_route_query_table({"interaction_mode": "data_table"}) is True
    assert should_route_query_table({"show_query_table": True}) is True
    assert should_route_query_table({"interaction_mode": "data_query"}) is False
