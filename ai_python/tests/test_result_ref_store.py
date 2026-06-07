"""Slice B — result_ref store (SRS-006 FR-12.6/12.7, QA TC-B-002/003)."""

from __future__ import annotations

from app.harness.result_store import InMemoryResultRefStore, StoredResult
from app.harness.tool_registry import TurnContext


def _ctx(tenant_id: str | None = "t1") -> TurnContext:
    return TurnContext(
        tenant_id=tenant_id,
        user_id="u1",
        thread_id="th1",
        correlation_id="cid",
        bearer_token=None,
        schema_version=None,
    )


def test_put_get_roundtrip_same_tenant():
    store = InMemoryResultRefStore()
    ref = store.put(tool_name="sql_query", data={"rows": [{"id": 1}]}, ctx=_ctx("t1"))
    assert ref.startswith("rref_")
    got = store.get(ref, ctx=_ctx("t1"))
    assert isinstance(got, StoredResult)
    assert got.data["rows"] == [{"id": 1}]
    assert got.tenant_id == "t1"


def test_tenant_mismatch_cannot_resolve():
    store = InMemoryResultRefStore()
    ref = store.put(tool_name="sql_query", data={"rows": [{"secret": 1}]}, ctx=_ctx("t1"))
    got = store.get(ref, ctx=_ctx("t2"))
    assert got is None
    assert store.policy_blocks == 1


def test_get_missing_returns_none():
    store = InMemoryResultRefStore()
    assert store.get("rref_nope", ctx=_ctx("t1")) is None


def test_delete_removes_ref():
    store = InMemoryResultRefStore()
    ref = store.put(tool_name="sql_query", data={"rows": []}, ctx=_ctx("t1"))
    store.delete(ref)
    assert store.get(ref, ctx=_ctx("t1")) is None


def test_each_put_has_unique_ref():
    store = InMemoryResultRefStore()
    a = store.put(tool_name="t", data={"rows": []}, ctx=_ctx("t1"))
    b = store.put(tool_name="t", data={"rows": []}, ctx=_ctx("t1"))
    assert a != b
