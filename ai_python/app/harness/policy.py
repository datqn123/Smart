"""Harness capability policy for agentic tool calls."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from app.harness.capability import CapabilityMatrix


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

    def __init__(self, capability_matrix: CapabilityMatrix | None = None) -> None:
        self._capability_matrix = capability_matrix or CapabilityMatrix()

    def check(
        self,
        tool_name: str,
        args: dict[str, Any],
        *,
        role: str | None = None,
        tenant_id: str | None = None,
    ) -> None:
        caps = TOOL_CAPABILITIES.get(tool_name, set())
        for cap in caps:
            if not self._capability_matrix.can(role, cap.value):
                raise HarnessPolicyError("Bạn không có quyền thực hiện thao tác này.")
        requested_tenant = args.get("tenant_id")
        if tenant_id and requested_tenant and str(requested_tenant) != str(tenant_id):
            raise HarnessPolicyError("Bạn không có quyền truy cập dữ liệu của tenant khác.")
        if Capability.DATA_READ not in caps:
            return

        sql_text = str(args.get("sql") or args.get("query") or "")
        if ";" in sql_text.strip().rstrip(";"):
            raise HarnessPolicyError("SQL multi-statement blocked")
        lowered = sql_text.lower()
        for keyword in DENIED_SQL_KEYWORDS:
            if re.search(rf"\b{re.escape(keyword)}\b", lowered):
                raise HarnessPolicyError(f"SQL write keyword blocked: {keyword}")
