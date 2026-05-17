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
    assert len(payload["columns"]) == 2
    assert payload["columns"][0]["key"] == "id"


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
