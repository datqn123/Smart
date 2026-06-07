"""Harness capability policy for agentic tool calls."""

from __future__ import annotations

import re
from collections.abc import Sequence
from enum import Enum
from typing import Any

from app.harness.capability import CapabilityMatrix

POLICY_VERSION = "policy.v3.1"


class Capability(str, Enum):
    DATA_READ = "data_read"
    DRAFT_CREATE = "draft_create"
    CHAT = "chat"
    ARTIFACT_BUILD = "artifact_build"


TOOL_CAPABILITIES: dict[str, set[Capability]] = {
    "sql_query": {Capability.DATA_READ},
    "schema_explore": {Capability.DATA_READ},
    "catalog_draft": {Capability.DRAFT_CREATE},
    "inventory_draft": {Capability.DRAFT_CREATE},
    "data_validator": {Capability.DATA_READ},
    "answer_composer": {Capability.ARTIFACT_BUILD},
    "build_chart": {Capability.ARTIFACT_BUILD},
    "data_table_builder": {Capability.ARTIFACT_BUILD},
    "erp_guide": {Capability.CHAT},
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
        permissions: Sequence[str] | None = None,
        tenant_id: str | None = None,
        rbac_required: Sequence[str] = (),
        side_effect_class: str | None = None,
    ) -> None:
        _ = side_effect_class
        caps = TOOL_CAPABILITIES.get(tool_name, set())
        required_permissions = tuple(str(item).strip() for item in rbac_required if str(item).strip())
        if required_permissions:
            live_permissions = {str(item).strip() for item in (permissions or ()) if str(item).strip()}
            if not live_permissions:
                raise HarnessPolicyError("Bạn không có quyền thực hiện thao tác này.")
            missing = [item for item in required_permissions if item not in live_permissions]
            if missing:
                raise HarnessPolicyError("Bạn không có quyền thực hiện thao tác này.")
        for cap in caps:
            if cap == Capability.ARTIFACT_BUILD:
                continue
            if required_permissions and cap == Capability.DRAFT_CREATE:
                continue
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
