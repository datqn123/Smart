"""Execution harness: permission gating + lifecycle hooks for tool calls."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class ToolCallContext:
    tool_name: str
    correlation_id: str | None = None
    tenant_id: str | None = None
    thread_id: str | None = None


class HarnessPermissionError(RuntimeError):
    """Raised when a tool call is blocked by policy."""


class AgentHarness:
    """Minimal harness used as stable execution boundary for graph nodes."""

    def __init__(self, *, enabled: bool = True, audit_jsonl_path: str | None = None) -> None:
        self._enabled = bool(enabled)
        self._audit_path = Path(audit_jsonl_path).expanduser() if audit_jsonl_path else None

    def run_tool(
        self,
        *,
        tool_name: str,
        tool: Callable[[], Any],
        context: ToolCallContext | None = None,
    ) -> Any:
        ctx = context or ToolCallContext(tool_name=tool_name)
        if not self._enabled:
            return tool()
        self._before_tool_call(ctx)
        try:
            result = tool()
        except Exception as exc:
            self._after_tool_call(ctx, ok=False, error=str(exc))
            raise
        self._after_tool_call(ctx, ok=True, result=result)
        return result

    def _before_tool_call(self, ctx: ToolCallContext) -> None:
        if self._is_denied_tool(ctx.tool_name):
            raise HarnessPermissionError(f"tool blocked by harness policy: {ctx.tool_name}")
        self._audit(
            {
                "event": "before_tool_call",
                "tool": ctx.tool_name,
                "correlation_id": ctx.correlation_id,
                "tenant_id": ctx.tenant_id,
                "thread_id": ctx.thread_id,
            }
        )

    def _after_tool_call(
        self,
        ctx: ToolCallContext,
        *,
        ok: bool,
        result: Any | None = None,
        error: str | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "event": "after_tool_call",
            "tool": ctx.tool_name,
            "ok": ok,
            "correlation_id": ctx.correlation_id,
            "tenant_id": ctx.tenant_id,
            "thread_id": ctx.thread_id,
        }
        if ok:
            payload["result_type"] = type(result).__name__ if result is not None else "NoneType"
        else:
            payload["error"] = error or "unknown error"
        self._audit(payload)

    def _is_denied_tool(self, tool_name: str) -> bool:
        n = tool_name.lower().strip()
        denied_keywords = ("delete", "drop", "truncate", "exec_shell")
        return any(k in n for k in denied_keywords)

    def _audit(self, row: dict[str, Any]) -> None:
        row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            **row,
        }
        logger.info("harness_event=%s", json.dumps(row, ensure_ascii=False))
        if self._audit_path is None:
            return
        try:
            self._audit_path.parent.mkdir(parents=True, exist_ok=True)
            with self._audit_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except Exception:
            logger.warning("failed writing harness audit jsonl", exc_info=True)
