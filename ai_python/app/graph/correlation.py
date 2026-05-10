"""Correlation id for logs (TASK-LG-13 / LG-14)."""

from __future__ import annotations

import contextvars
import logging
from collections.abc import Iterator
from contextlib import contextmanager

_correlation_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id",
    default=None,
)


def get_correlation_id() -> str | None:
    return _correlation_id.get()


def set_correlation_id(cid: str | None) -> contextvars.Token[str | None]:
    return _correlation_id.set(cid)


def reset_correlation_id(token: contextvars.Token[str | None]) -> None:
    _correlation_id.reset(token)


@contextmanager
def correlation_scope(cid: str | None) -> Iterator[None]:
    token = set_correlation_id(cid)
    try:
        yield
    finally:
        reset_correlation_id(token)


class CorrelationFilter(logging.Filter):
    """Injects correlation id into LogRecord if missing."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not getattr(record, "correlation_id", None):
            record.correlation_id = get_correlation_id() or "-"
        return True


def setup_correlation_logging() -> None:
    """Attach :class:`CorrelationFilter` to root handlers (captures all propagated logs).

    Logger-level filters do not apply to child loggers' records in the stdlib; putting the
    filter on **handlers** ensures correlation_id is set before emission (incl. pytest caplog).
    """
    root = logging.getLogger()
    for h in root.handlers:
        if not any(isinstance(f, CorrelationFilter) for f in getattr(h, "filters", [])):
            h.addFilter(CorrelationFilter())
