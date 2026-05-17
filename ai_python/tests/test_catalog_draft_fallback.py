"""Catalog draft fallback rows when LLM JSON fails."""

from __future__ import annotations

from app.graph.nodes.catalog_draft import (
    _display_name_from_slots_and_prompt,
    _fallback_catalog_rows,
)
from app.graph.nodes.draft_resolve import route_after_catalog_generate


def test_extract_supplier_name_from_prompt() -> None:
    name = _display_name_from_slots_and_prompt(
        "supplier",
        "tạo nhà cung cấp mới có tên là Claude",
        None,
    )
    assert name == "Claude"


def test_fallback_supplier_row_has_claude() -> None:
    rows = _fallback_catalog_rows(
        "supplier",
        count=1,
        question="tạo nhà cung cấp mới có tên là Claude",
        slots={"entity_type": "supplier", "supplier_query": "Claude"},
    )
    assert len(rows) == 1
    assert rows[0]["values"]["name"] == "Claude"
    assert rows[0]["values"]["supplierCode"]


def test_route_stops_when_no_payload() -> None:
    assert route_after_catalog_generate({"final_answer": "lỗi"}) == "stop"


def test_route_stops_when_empty_rows() -> None:
    assert (
        route_after_catalog_generate(
            {"catalog_draft_payload": {"rows": [], "entityType": "supplier"}}
        )
        == "stop"
    )


def test_route_continues_with_rows() -> None:
    assert (
        route_after_catalog_generate(
            {
                "catalog_draft_payload": {
                    "rows": [{"rowId": "r1", "values": {"name": "Claude"}}],
                }
            }
        )
        == "continue"
    )
