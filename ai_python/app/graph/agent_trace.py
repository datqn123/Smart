"""Readable multi-line logs for agent steps (terminal / uvicorn).

Disable with ``AGENT_TERMINAL_TRACE=0`` (see :class:`app.config.graph_settings.GraphSettings`).
"""

from __future__ import annotations

import logging

from app.config.graph_settings import GraphSettings


def emit_agent_trace(
    logger: logging.Logger,
    settings: GraphSettings,
    *,
    agent: str,
    phase: str,
    detail: str,
) -> None:
    if not settings.agent_terminal_trace:
        return
    logger.info("[agent:%s] %s", agent, phase)
    body = detail.strip("\n") or "(empty)"
    for raw_line in body.splitlines():
        logger.info("[agent:%s]   %s", agent, raw_line)
