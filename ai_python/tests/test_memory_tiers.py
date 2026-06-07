from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage, HumanMessage


def test_working_memory_keeps_n_pairs() -> None:
    from app.harness.memory import WorkingMemory

    messages = []
    for idx in range(10):
        messages.append(HumanMessage(content=f"q{idx}"))
        messages.append(AIMessage(content=f"a{idx}"))

    kept = WorkingMemory(pairs=6).attach(messages)

    assert len(kept) == 12
    assert kept[0].content == "q4"
    assert kept[-1].content == "a9"


@pytest.mark.asyncio
async def test_semantic_store_recall_relevant() -> None:
    from app.harness.memory import InMemorySemanticStore, SemanticRecord

    store = InMemorySemanticStore()
    await store.upsert(SemanticRecord(user_id="u1", kind="preference", content="hay xem doanh thu"))
    await store.upsert(SemanticRecord(user_id="u1", kind="preference", content="quan tâm tồn kho"))

    recalled = await store.recall("u1", "doanh thu tháng này", k=1)

    assert recalled
    assert "doanh thu" in recalled[0].content


@pytest.mark.asyncio
async def test_semantic_store_no_raw_pii() -> None:
    from app.harness.memory import InMemorySemanticStore, SemanticRecord

    store = InMemorySemanticStore()
    await store.upsert(SemanticRecord(user_id="u1", kind="note", content="SĐT khách 0901234567"))

    assert store.records == []


def test_semantic_store_mode_memory_default() -> None:
    from app.config.graph_settings import GraphSettings

    assert GraphSettings().semantic_store_mode == "memory"
