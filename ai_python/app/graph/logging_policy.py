"""Mask / truncate SQL in logs (TASK-LG-14)."""

from __future__ import annotations

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
