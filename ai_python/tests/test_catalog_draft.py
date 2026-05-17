"""Catalog draft schema and intent routing."""

from __future__ import annotations

from app.graph.catalog_draft_schema import normalize_rows, validate_draft_rows
from app.graph.nodes.intent import route_after_intent
from app.graph.registry import normalize_intent


def test_normalize_intent_catalog_data_entry() -> None:
    assert normalize_intent("catalog_data_entry") == "catalog_data_entry"


def test_route_after_intent_catalog() -> None:
    assert route_after_intent({"intent": "catalog_data_entry"}) == "catalog_draft_branch"


def test_validate_draft_rows_missing_required() -> None:
    rows = [{"rowId": "r1", "values": {"name": "Only name"}}]
    issues = validate_draft_rows("product", rows)
    assert any("skuCode" in i for i in issues)


def test_normalize_rows_caps() -> None:
    raw = [{"skuCode": f"S{i}", "name": f"N{i}"} for i in range(60)]
    out = normalize_rows(raw)
    assert len(out) == 50
    assert out[0]["rowId"] == "r1"
