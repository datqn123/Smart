"""Task111 — query result table SSE payload builder."""

from __future__ import annotations

from app.graph.query_table_sse import MAX_DISPLAY_ROWS, build_query_table_sse


def _sample_qr(n: int) -> dict:
    return {
        "rows": [{"id": i, "name": f"item-{i}"} for i in range(n)],
        "meta": {
            "columns": [
                {"name": "id", "type": "int"},
                {"name": "name", "type": "text"},
            ],
        },
    }


def test_build_query_table_sse_basic() -> None:
    payload = build_query_table_sse(_sample_qr(3))
    assert payload is not None
    assert payload["rowCount"] == 3
    assert payload["truncated"] is False
    assert len(payload["rows"]) == 3
    assert len(payload["columns"]) == 1
    assert payload["columns"][0]["key"] == "name"
    assert payload["columns"][0]["label"] == "Tên"
    assert "id" not in payload["rows"][0]


def test_build_query_table_sse_hides_id_and_category_id() -> None:
    qr = {
        "rows": [
            {
                "id": 1,
                "category_id": 2,
                "sku_code": "UONG-COKE-24",
                "name": "Coca",
                "status": "Active",
            }
        ],
        "meta": {
            "columns": [
                {"name": "id", "type": "int"},
                {"name": "category_id", "type": "int"},
                {"name": "sku_code", "type": "text"},
                {"name": "name", "type": "text"},
                {"name": "status", "type": "text"},
            ],
        },
    }
    payload = build_query_table_sse(qr)
    assert payload is not None
    keys = {c["key"] for c in payload["columns"]}
    assert "id" not in keys
    assert "category_id" not in keys
    assert keys == {"sku_code", "name", "status"}
    assert "id" not in payload["rows"][0]
    assert payload["rows"][0]["sku_code"] == "UONG-COKE-24"


def test_build_query_table_sse_truncates_at_max() -> None:
    n = MAX_DISPLAY_ROWS + 50
    payload = build_query_table_sse(_sample_qr(n))
    assert payload is not None
    assert payload["rowCount"] == n
    assert payload["truncated"] is True
    assert len(payload["rows"]) == MAX_DISPLAY_ROWS


def test_build_query_table_sse_empty_returns_none() -> None:
    assert build_query_table_sse({"rows": []}) is None
    assert build_query_table_sse(None) is None
