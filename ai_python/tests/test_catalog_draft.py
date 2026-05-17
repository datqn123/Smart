"""Catalog draft schema and intent routing."""

from __future__ import annotations

from app.graph.catalog_draft_schema import (
    enrich_catalog_draft_rows,
    normalize_rows,
    validate_draft_rows,
)
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


def test_enrich_product_rows_from_partial_llm() -> None:
    partial = [
        {"rowId": "r1", "values": {"salePrice": 50000}},
        {"rowId": "r2", "salePrice": 50000, "categoryName": "điện tử"},
        {"rowId": "r3", "values": {"categoryName": "Điện tử"}},
    ]
    rows = enrich_catalog_draft_rows(
        "product",
        normalize_rows(partial),
        user_prompt="Tạo 3 sản phẩm điện tử giá 50000",
    )
    assert len(rows) == 3
    assert rows[0]["values"]["name"]
    assert rows[1]["values"]["name"]
    assert rows[0]["values"]["skuCode"]
    assert rows[0]["values"]["salePrice"] == 50000
    assert rows[0]["values"]["baseUnitName"] == "Cái"
    issues = validate_draft_rows("product", rows)
    assert issues == []


def test_normalize_rows_caps() -> None:
    raw = [{"skuCode": f"S{i}", "name": f"N{i}"} for i in range(60)]
    out = normalize_rows(raw)
    assert len(out) == 50
    assert out[0]["rowId"] == "r1"
