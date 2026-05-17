"""Inventory draft schema and intent routing."""

from __future__ import annotations

from app.graph.inventory_draft_schema import (
    enrich_receipt_header,
    enrich_receipt_lines,
    normalize_lines,
    validate_receipt_draft,
)
from app.graph.nodes.intent import route_after_intent
from app.graph.registry import normalize_intent


def test_normalize_intent_inventory_data_entry() -> None:
    assert normalize_intent("inventory_data_entry") == "inventory_data_entry"


def test_route_after_intent_inventory() -> None:
    assert route_after_intent({"intent": "inventory_data_entry"}) == "inventory_draft_branch"


def test_enrich_receipt_single_line_quantity() -> None:
    header = enrich_receipt_header({}, user_prompt="Tạo phiếu nhập 10 máy tính từ NCC ABC")
    lines = enrich_receipt_lines(
        normalize_lines([{"values": {"skuCode": "PC-1"}}]),
        user_prompt="Tạo phiếu nhập 10 máy tính",
        header=header,
    )
    assert lines[0]["values"]["quantity"] == 10
    assert lines[0]["values"]["skuCode"]
    issues = validate_receipt_draft(header, lines)
    assert any("supplier" in i.lower() for i in issues) or header.get("supplierName")


def test_validate_receipt_requires_supplier() -> None:
    issues = validate_receipt_draft(
        {"receiptDate": "2026-05-17", "saveMode": "draft"},
        [{"lineId": "l1", "values": {"skuCode": "A", "quantity": 1, "costPrice": 0}}],
    )
    assert any("supplier" in i.lower() for i in issues)
