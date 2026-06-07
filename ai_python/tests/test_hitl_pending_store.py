"""Tests for InMemoryPendingHitlStore and SqlitePendingHitlStore — Slice E (FR-5)."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from app.harness.hitl_store import (
    InMemoryPendingHitlStore,
    PendingHitlRecord,
    SqlitePendingHitlStore,
)


def _record(**kwargs) -> PendingHitlRecord:
    defaults = dict(
        tool_name="some_tool",
        payload={"k": "v"},
        tenant_id="t1",
        user_id="u1",
        thread_id="th1",
        created_at=time.time(),
    )
    defaults.update(kwargs)
    return PendingHitlRecord(**defaults)


# ---------------------------------------------------------------------------
# InMemoryPendingHitlStore
# ---------------------------------------------------------------------------

class TestInMemoryPendingHitlStore:
    def test_put_get_roundtrip(self):
        store = InMemoryPendingHitlStore()
        rec = _record()
        store.put("k1", rec)
        assert store.get("k1") == rec

    def test_get_missing_returns_none(self):
        store = InMemoryPendingHitlStore()
        assert store.get("nonexistent") is None

    def test_delete_removes_key(self):
        store = InMemoryPendingHitlStore()
        rec = _record()
        store.put("k1", rec)
        store.delete("k1")
        assert store.get("k1") is None

    def test_delete_nonexistent_is_noop(self):
        store = InMemoryPendingHitlStore()
        store.delete("ghost")  # should not raise

    def test_ttl_expiry_removes_record(self):
        store = InMemoryPendingHitlStore(ttl_seconds=60)
        past = time.time() - 120  # 2 minutes ago
        rec = _record(created_at=past)
        store.put("k1", rec)
        assert store.get("k1") is None  # expired

    def test_non_expired_record_returned(self):
        store = InMemoryPendingHitlStore(ttl_seconds=3600)
        rec = _record(created_at=time.time() - 10)
        store.put("k1", rec)
        assert store.get("k1") == rec

    def test_pending_hitl_property_accessible(self):
        store = InMemoryPendingHitlStore()
        rec = _record()
        store.put("k1", rec)
        assert "k1" in store._store


# ---------------------------------------------------------------------------
# SqlitePendingHitlStore
# ---------------------------------------------------------------------------

class TestSqlitePendingHitlStore:
    def test_put_get_roundtrip(self, tmp_path):
        db = str(tmp_path / "test.db")
        store = SqlitePendingHitlStore(path=db)
        try:
            rec = _record()
            store.put("k1", rec)
            result = store.get("k1")
            assert result is not None
            assert result.tool_name == rec.tool_name
            assert result.payload == rec.payload
            assert result.tenant_id == rec.tenant_id
            assert result.user_id == rec.user_id
            assert result.thread_id == rec.thread_id
        finally:
            store.close()

    def test_get_missing_returns_none(self, tmp_path):
        db = str(tmp_path / "test.db")
        store = SqlitePendingHitlStore(path=db)
        try:
            assert store.get("ghost") is None
        finally:
            store.close()

    def test_delete_removes_key(self, tmp_path):
        db = str(tmp_path / "test.db")
        store = SqlitePendingHitlStore(path=db)
        try:
            rec = _record()
            store.put("k1", rec)
            store.delete("k1")
            assert store.get("k1") is None
        finally:
            store.close()

    def test_ttl_expiry_removes_record(self, tmp_path):
        db = str(tmp_path / "test.db")
        store = SqlitePendingHitlStore(path=db, ttl_seconds=60)
        try:
            past = time.time() - 120
            rec = _record(created_at=past)
            store.put("k1", rec)
            assert store.get("k1") is None
        finally:
            store.close()

    def test_non_expired_record_survives(self, tmp_path):
        db = str(tmp_path / "test.db")
        store = SqlitePendingHitlStore(path=db, ttl_seconds=3600)
        try:
            rec = _record(created_at=time.time() - 5)
            store.put("k1", rec)
            result = store.get("k1")
            assert result is not None
            assert result.tool_name == rec.tool_name
        finally:
            store.close()

    def test_put_overwrites_existing(self, tmp_path):
        db = str(tmp_path / "test.db")
        store = SqlitePendingHitlStore(path=db)
        try:
            rec1 = _record(tool_name="tool_a")
            rec2 = _record(tool_name="tool_b")
            store.put("k1", rec1)
            store.put("k1", rec2)
            result = store.get("k1")
            assert result is not None
            assert result.tool_name == "tool_b"
        finally:
            store.close()

    def test_is_expired_helper(self):
        rec = PendingHitlRecord(
            tool_name="t",
            payload={},
            tenant_id=None,
            user_id=None,
            thread_id=None,
            created_at=time.time() - 200,
        )
        assert rec.is_expired(100) is True
        assert rec.is_expired(3600) is False
