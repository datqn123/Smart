"""Harness-held result store (SRS-006 FR-12.6/12.7).

Full tool result data is held by the Harness and addressed by an opaque
``result_ref`` handle. The Planner only ever sees the bounded observation; only
downstream tools (chart/table builders) resolve the handle through the Harness,
under tenant/correlation scope. Full data never round-trips through the Planner.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class StoredResult:
    result_ref: str
    tool_name: str
    tenant_id: str | None
    correlation_id: str
    data: dict[str, Any]
    created_at: float


class ResultRefStore(Protocol):
    def put(self, *, tool_name: str, data: dict[str, Any], ctx: Any) -> str:
        ...

    def get(self, result_ref: str, *, ctx: Any) -> StoredResult | None:
        ...

    def delete(self, result_ref: str) -> None:
        ...


class InMemoryResultRefStore:
    """Default turn-scoped store for unit tests and single-process runtime."""

    def __init__(self) -> None:
        self._store: dict[str, StoredResult] = {}
        self.policy_blocks = 0

    def put(self, *, tool_name: str, data: dict[str, Any], ctx: Any) -> str:
        result_ref = f"rref_{uuid.uuid4().hex[:16]}"
        self._store[result_ref] = StoredResult(
            result_ref=result_ref,
            tool_name=tool_name,
            tenant_id=getattr(ctx, "tenant_id", None),
            correlation_id=getattr(ctx, "correlation_id", ""),
            data=dict(data),
            created_at=time.time(),
        )
        return result_ref

    def get(self, result_ref: str, *, ctx: Any) -> StoredResult | None:
        record = self._store.get(result_ref)
        if record is None:
            return None
        # Tenant scope: a different tenant must never resolve another tenant's data.
        if record.tenant_id != getattr(ctx, "tenant_id", None):
            self.policy_blocks += 1
            return None
        return record

    def delete(self, result_ref: str) -> None:
        self._store.pop(result_ref, None)
