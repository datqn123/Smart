"""Build SSE payload for read-only SQL query result tables."""

from __future__ import annotations

from typing import Any

from app.graph.datetime_display import localize_query_result_for_display

MAX_DISPLAY_ROWS = 200


def _rows_from_query_result(qr: Any) -> list[dict[str, Any]]:
    if not isinstance(qr, dict):
        return []
    rows = qr.get("rows")
    if not isinstance(rows, list):
        return []
    return [dict(r) for r in rows if isinstance(r, dict)]


def _infer_column_type(values: list[Any]) -> str:
    for v in values[:50]:
        if v is None:
            continue
        if isinstance(v, bool):
            return "boolean"
        if isinstance(v, (int, float)):
            return "number"
        return "string"
    return "string"


def _column_defs(qr: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    meta = qr.get("meta") if isinstance(qr.get("meta"), dict) else {}
    cols_raw = meta.get("columns") or []
    keys: list[str] = []
    labels: dict[str, str] = {}
    types: dict[str, str] = {}
    for c in cols_raw:
        if isinstance(c, dict) and c.get("name") is not None:
            name = str(c["name"])
            keys.append(name)
            if c.get("label"):
                labels[name] = str(c["label"])
            if c.get("type"):
                types[name] = str(c["type"])
        elif isinstance(c, str):
            keys.append(c)
    if not keys and rows:
        keys = list(rows[0].keys())
    out: list[dict[str, str]] = []
    for key in keys:
        col_type = types.get(key) or _infer_column_type([r.get(key) for r in rows])
        out.append(
            {
                "key": key,
                "label": labels.get(key) or key,
                "type": col_type,
            }
        )
    return out


def build_query_table_sse(
    qr: Any,
    *,
    display_timezone: str | None = None,
    max_rows: int = MAX_DISPLAY_ROWS,
    title: str = "Kết quả truy vấn",
) -> dict[str, Any] | None:
    """Return UI payload or ``None`` when there is nothing tabular to show."""
    if not isinstance(qr, dict):
        return None
    localized = localize_query_result_for_display(qr, display_timezone)
    rows = _rows_from_query_result(localized)
    if not rows:
        return None
    total = len(rows)
    truncated = total > max_rows
    display_rows = rows[:max_rows]
    return {
        "title": title,
        "columns": _column_defs(localized, rows),
        "rows": display_rows,
        "rowCount": total,
        "truncated": truncated,
        "maxDisplayRows": max_rows,
    }
