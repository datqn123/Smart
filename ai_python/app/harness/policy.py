"""Harness capability policy for agentic tool calls."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any


class Capability(str, Enum):
    DATA_READ = "data_read"
    DRAFT_CREATE = "draft_create"
    CHAT = "chat"


TOOL_CAPABILITIES: dict[str, set[Capability]] = {
    "sql_query": {Capability.DATA_READ},
    "schema_explore": {Capability.DATA_READ},
    "catalog_draft": {Capability.DRAFT_CREATE},
    "inventory_draft": {Capability.DRAFT_CREATE},
    "chat_normal": {Capability.CHAT},
}

DENIED_SQL_KEYWORDS = frozenset(("delete", "update", "insert", "drop", "truncate", "alter", "create"))


class HarnessPolicyError(RuntimeError):
    """Raised when a tool call violates harness policy."""


class HarnessPolicy:
    """Capability guard that runs before any agentic tool execution."""

    def check(self, tool_name: str, args: dict[str, Any]) -> None:
        caps = TOOL_CAPABILITIES.get(tool_name, set())
        if Capability.DATA_READ not in caps:
            return

        sql_text = str(args.get("sql") or args.get("query") or "")
        lowered = sql_text.lower()
        for keyword in DENIED_SQL_KEYWORDS:
            if re.search(rf"\b{re.escape(keyword)}\b", lowered):
                raise HarnessPolicyError(f"SQL write keyword blocked: {keyword}")
