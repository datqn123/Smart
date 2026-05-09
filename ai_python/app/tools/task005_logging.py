"""Structured logging helpers for the Task005 batch job.

Each event line is a single JSON object on stderr/stdout to ease log
aggregation. We avoid sensitive payloads (no row dumps, no raw params).
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

LOGGER_NAME = "ai_python.task005"


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "task005_extra", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload, ensure_ascii=False, sort_keys=False)


def get_logger() -> logging.Logger:
    """Return the singleton Task005 logger configured with a JSON handler."""

    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(_JsonFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def log_event(
    logger: logging.Logger,
    *,
    event: str,
    correlation_id: str,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    """Emit a structured event (no sensitive payloads — caller responsibility)."""

    extra = {
        "event": event,
        "correlation_id": correlation_id,
        **fields,
    }
    logger.log(level, event, extra={"task005_extra": extra})
