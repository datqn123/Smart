"""Mask / truncate SQL in logs (TASK-LG-14)."""

from __future__ import annotations

import json
import logging

from app.config.graph_settings import GraphSettings, load_graph_settings

logger = logging.getLogger(__name__)


def safe_log_sql(sql: str | None, *, settings: GraphSettings | None = None) -> str:
    """Return string safe for logs when MASK_SQL=1."""
    s = settings or load_graph_settings()
    if not sql:
        return ""
    if s.mask_sql:
        return "[SQL masked]"
    if len(sql) > 500:
        return sql[:500] + "…"
    return sql


def log_sql_debug(msg: str, sql: str | None, *, settings: GraphSettings | None = None) -> None:
    logger.debug("%s %s", msg, safe_log_sql(sql, settings=settings))


def safe_log_query_result(
    result: dict | None,
    *,
    max_preview_rows: int = 10,
    max_chars: int = 4000,
) -> str:
    """Format executor ``query_result`` for terminal trace (truncated JSON)."""
    if not result:
        return "rows=(none)"
    lines: list[str] = []
    meta = result.get("meta")
    if isinstance(meta, dict):
        rc = meta.get("row_count")
        if rc is not None:
            lines.append(f"row_count={rc}")
        cols = meta.get("columns")
        if cols is not None:
            try:
                col_txt = json.dumps(cols, ensure_ascii=False, default=str)
            except TypeError:
                col_txt = str(cols)
            if len(col_txt) > 500:
                col_txt = col_txt[:500] + "…"
            lines.append(f"columns={col_txt}")
    rows = result.get("rows")
    if not isinstance(rows, list):
        lines.append("rows=(missing or not a list)")
        return "\n".join(lines)
    if not rows:
        lines.append("rows=[]")
        return "\n".join(lines)
    preview = rows[: max(1, max_preview_rows)]
    try:
        body = json.dumps(preview, ensure_ascii=False, default=str)
    except TypeError:
        body = str(preview)
    if len(rows) > len(preview):
        body += f"\n… (+{len(rows) - len(preview)} more row(s))"
    if len(body) > max_chars:
        body = body[: max_chars - 1] + "…"
    lines.append(f"rows_preview:\n{body}")
    return "\n".join(lines)
