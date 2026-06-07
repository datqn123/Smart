"""Durable HITL pending-state store — Slice E."""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class PendingHitlRecord:
    tool_name: str
    payload: dict[str, Any]
    tenant_id: str | None
    user_id: str | None
    thread_id: str | None
    created_at: float  # wall-clock (time.time()) — safe across process restarts

    def is_expired(self, ttl_seconds: float) -> bool:
        return (time.time() - self.created_at) >= ttl_seconds


class PendingHitlStore(Protocol):
    def put(self, key: str, record: PendingHitlRecord) -> None: ...
    def get(self, key: str) -> PendingHitlRecord | None: ...
    def delete(self, key: str) -> None: ...


class InMemoryPendingHitlStore:
    """Default dev / unit-test store."""

    def __init__(self, ttl_seconds: float = 1800.0) -> None:
        self._store: dict[str, PendingHitlRecord] = {}
        self._ttl = ttl_seconds

    def put(self, key: str, record: PendingHitlRecord) -> None:
        self._store[key] = record

    def get(self, key: str) -> PendingHitlRecord | None:
        record = self._store.get(key)
        if record is None:
            return None
        if record.is_expired(self._ttl):
            del self._store[key]
            return None
        return record

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS harness_pending_hitl (
    key        TEXT PRIMARY KEY,
    tool_name  TEXT NOT NULL,
    payload    TEXT NOT NULL,
    tenant_id  TEXT,
    user_id    TEXT,
    thread_id  TEXT,
    created_at REAL NOT NULL
)
"""


class SqlitePendingHitlStore:
    """SQLite-backed store for deterministic tests and single-instance deployments."""

    def __init__(self, path: str, ttl_seconds: float = 1800.0) -> None:
        self._ttl = ttl_seconds
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute(_CREATE_SQL)
        self._conn.commit()

    def put(self, key: str, record: PendingHitlRecord) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO harness_pending_hitl "
            "(key, tool_name, payload, tenant_id, user_id, thread_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                key,
                record.tool_name,
                json.dumps(record.payload, ensure_ascii=False),
                record.tenant_id,
                record.user_id,
                record.thread_id,
                record.created_at,
            ),
        )
        self._conn.commit()

    def get(self, key: str) -> PendingHitlRecord | None:
        cur = self._conn.execute(
            "SELECT tool_name, payload, tenant_id, user_id, thread_id, created_at "
            "FROM harness_pending_hitl WHERE key = ?",
            (key,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        tool_name, payload_json, tenant_id, user_id, thread_id, created_at = row
        try:
            payload: dict[str, Any] = json.loads(payload_json)
        except (json.JSONDecodeError, TypeError):
            payload = {}
        record = PendingHitlRecord(
            tool_name=tool_name,
            payload=payload,
            tenant_id=tenant_id,
            user_id=user_id,
            thread_id=thread_id,
            created_at=float(created_at),
        )
        if record.is_expired(self._ttl):
            self.delete(key)
            return None
        return record

    def delete(self, key: str) -> None:
        self._conn.execute("DELETE FROM harness_pending_hitl WHERE key = ?", (key,))
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
