"""K15 intent→tool success history (SRS-006 FR-9, OQ-4).

Append-only outcome history used as a first-class planner feedback signal and as
regression evidence. Privacy rules (FR-9.3, NFR-3): never store the raw question,
raw SQL, raw tenant id, user id, phone, email, or bearer token — only hashed keys
and safe scalars. Degraded/HITL/clarify outcomes are recorded distinctly so the
planner can down-weight them instead of treating any non-failure as good.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from typing import Any, Protocol

from pydantic import BaseModel, Field

# Distinct outcome statuses (FR-9.5).
STATUS_SUCCESS = "success"
STATUS_DEGRADED = "degraded"
STATUS_FAILURE = "failure"
STATUS_HITL_PENDING = "hitl_pending"
STATUS_CLARIFY_PENDING = "clarify_pending"

_CLEAN_SUCCESS = {STATUS_SUCCESS}


def _hash(value: str) -> str:
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()[:16]


class IntentHistoryEvent(BaseModel):
    event_id: str
    created_at: str
    schema_version: str = "1.0"
    context: dict[str, Any] = Field(default_factory=dict)
    intent: dict[str, Any] = Field(default_factory=dict)
    plan: dict[str, Any] = Field(default_factory=dict)
    outcome: dict[str, Any] = Field(default_factory=dict)
    asset_versions: dict[str, str] = Field(default_factory=dict)
    failure_detail: dict[str, Any] | None = None


def build_history_event(
    *,
    tenant_id: str | None,
    intent_key: str,
    plan_hash: str,
    tools: list[str],
    status: str,
    replan_count: int = 0,
    hitl_count: int = 0,
    latency_ms: int = 0,
    cost_usd: float = 0.0,
    budget_status: str = "ok",
    asset_versions: dict[str, str] | None = None,
    failure_kind: str | None = None,
) -> IntentHistoryEvent:
    """Build a privacy-safe K15 event. Raw question/SQL/PII are never accepted here."""
    return IntentHistoryEvent(
        event_id=uuid.uuid4().hex,
        created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        context={"tenant_hash": _hash(tenant_id or "")},
        intent={"intent_key_hash": _hash(intent_key)},
        plan={
            "plan_hash": plan_hash,
            "tools": list(tools),
            "replan_count": int(replan_count),
            "hitl_count": int(hitl_count),
        },
        outcome={
            "status": status,
            "latency_ms": int(latency_ms),
            "cost_usd": float(cost_usd),
            "budget_status": budget_status,
        },
        asset_versions=dict(asset_versions or {}),
        failure_detail={"kind": failure_kind} if failure_kind else None,
    )


class IntentHistorySummary(BaseModel):
    intent_key_hash: str
    total: int = 0
    success: int = 0
    degraded: int = 0
    failure: int = 0
    hitl_pending: int = 0
    clarify_pending: int = 0

    @property
    def clean_success_rate(self) -> float:
        return (self.success / self.total) if self.total else 0.0


class IntentHistoryStore(Protocol):
    def append(self, event: IntentHistoryEvent) -> None:
        ...

    def summary(self, intent_key: str) -> IntentHistorySummary:
        ...


def _summarize(events: list[IntentHistoryEvent], intent_key_hash: str) -> IntentHistorySummary:
    s = IntentHistorySummary(intent_key_hash=intent_key_hash)
    for e in events:
        status = str(e.outcome.get("status", ""))
        s.total += 1
        if status == STATUS_SUCCESS:
            s.success += 1
        elif status == STATUS_DEGRADED:
            s.degraded += 1
        elif status == STATUS_HITL_PENDING:
            s.hitl_pending += 1
        elif status == STATUS_CLARIFY_PENDING:
            s.clarify_pending += 1
        else:
            s.failure += 1
    return s


class InMemoryIntentHistoryStore:
    def __init__(self) -> None:
        self._events: list[IntentHistoryEvent] = []

    def append(self, event: IntentHistoryEvent) -> None:
        self._events.append(event)

    def all(self) -> list[IntentHistoryEvent]:
        return list(self._events)

    def summary(self, intent_key: str) -> IntentHistorySummary:
        key_hash = _hash(intent_key)
        matching = [e for e in self._events if e.intent.get("intent_key_hash") == key_hash]
        return _summarize(matching, key_hash)


_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS intent_history (
    event_id TEXT PRIMARY KEY,
    intent_key_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    event_json TEXT NOT NULL
)
"""


class SqliteIntentHistoryStore:
    def __init__(self, path: str) -> None:
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute(_CREATE_SQL)
        self._conn.commit()

    def append(self, event: IntentHistoryEvent) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO intent_history(event_id, intent_key_hash, status, event_json)"
            " VALUES (?,?,?,?)",
            (
                event.event_id,
                str(event.intent.get("intent_key_hash", "")),
                str(event.outcome.get("status", "")),
                event.model_dump_json(),
            ),
        )
        self._conn.commit()

    def summary(self, intent_key: str) -> IntentHistorySummary:
        key_hash = _hash(intent_key)
        cur = self._conn.execute(
            "SELECT event_json FROM intent_history WHERE intent_key_hash=?", (key_hash,)
        )
        events = [IntentHistoryEvent.model_validate_json(row[0]) for row in cur.fetchall()]
        return _summarize(events, key_hash)

    def close(self) -> None:
        self._conn.close()
