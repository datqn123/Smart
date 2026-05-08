"""Structured audit logging + NFR-05 RAG ingest hooks."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ToolAuditRecord:
    user_id: str | None
    session_id: str | None
    tool_name: str
    correlation_id: str
    duration_ms: float


def log_tool_audit(rec: ToolAuditRecord, summary: str) -> None:
    logger.info(
        "mcp_tool",
        extra={
            "tool_name": rec.tool_name,
            "correlation_id": rec.correlation_id,
            "duration_ms": rec.duration_ms,
            "audit_summary": summary,
            "user_id": rec.user_id,
            "session_id": rec.session_id,
        },
    )


def rag_ingest_telemetry_best_effort(now_ts: float | None = None) -> None:
    """AC-5 / NFR-05: acknowledge last ingest timestamp or stale marker."""
    now = now_ts if now_ts is not None else time.time()
    raw = os.getenv("RAG_LAST_INGEST_UNIX")
    stale_flag = os.getenv("RAG_STALE_ACKNOWLEDGED", "").lower() in ("1", "true", "yes")
    if stale_flag:
        logger.info(
            "rag_stale_acknowledged",
            extra={"unix_ts_ack": now, "correlation_id": "telemetry"},
        )
        return
    if raw and raw.strip().isdigit():
        last = float(raw)
        age_h = max(0.0, (now - last) / 3600)
        payload = {"last_ingest_unix": last, "age_hours": age_h, "correlation_id": "telemetry"}
        if age_h > 24:
            logger.warning("rag_ingest_stale", extra=payload)
        else:
            logger.info("rag_ingest_ok", extra=payload)
        return
    logger.info("rag_ingest_unconfigured", extra={"correlation_id": "telemetry"})
