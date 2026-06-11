import pytest
from app.graph.hitl import PendingStore


@pytest.mark.asyncio
async def test_save_and_load_pending_roundtrip(tmp_path):  # fact-validator-hitl
    store = PendingStore(db_path=str(tmp_path / "hitl.sqlite"))
    await store.init()
    snapshot = {"raw_require": "doanh thu", "tool_results": {"sql_execute": {"rows": []}},
                "history": [{"action": "call_tool"}],
                "pending_clarification": {"message": "Khi nao?"}}
    await store.save("thread-1", snapshot)
    loaded = await store.load("thread-1")
    assert loaded["raw_require"] == "doanh thu"
    assert loaded["pending_clarification"]["message"] == "Khi nao?"


@pytest.mark.asyncio
async def test_load_missing_returns_none(tmp_path):
    store = PendingStore(db_path=str(tmp_path / "hitl.sqlite"))
    await store.init()
    assert await store.load("nope") is None


@pytest.mark.asyncio
async def test_save_without_explicit_init(tmp_path):
    # Regression: production pause-lan-dau goi save() truoc khi bat ky
    # init() nao chay -> tung crash 'no such table: pending'.
    store = PendingStore(db_path=str(tmp_path / "hitl.sqlite"))
    await store.save("t1", {"raw_require": "liet ke di"})
    loaded = await store.load("t1")
    assert loaded["raw_require"] == "liet ke di"


@pytest.mark.asyncio
async def test_clear_removes_pending(tmp_path):
    store = PendingStore(db_path=str(tmp_path / "hitl.sqlite"))
    await store.init()
    await store.save("t", {"raw_require": "x"})
    await store.clear("t")
    assert await store.load("t") is None
