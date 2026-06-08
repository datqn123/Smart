from __future__ import annotations

from app.harness.memory_store import (
    ConversationContext,
    InMemoryConversationMemoryStore,
    MemoryTurnRecord,
)


def test_inmemory_append_and_get_context() -> None:
    store = InMemoryConversationMemoryStore()

    t1 = MemoryTurnRecord(
        thread_id="th1", turn_index=1,
        user_message="doanh thu tháng này", ai_answer="10 tỷ",
        tool_names=["sql_query"], intent_type="data_query",
    )
    store.append_turn("th1", t1)

    ctx = store.get_context("th1")
    assert ctx.recent_turns == [t1]
    assert ctx.summary == ""


def test_inmemory_get_context_empty_thread() -> None:
    store = InMemoryConversationMemoryStore()
    ctx = store.get_context("unknown")
    assert ctx.recent_turns == []
    assert ctx.summary == ""


def test_inmemory_compact_keeps_recent() -> None:
    store = InMemoryConversationMemoryStore(max_turns=3)
    for i in range(5):
        store.append_turn("th1", MemoryTurnRecord(
            thread_id="th1", turn_index=i,
            user_message=f"q{i}", ai_answer=f"a{i}",
        ))
    store.compact("th1", "Summary of turns 0-1")
    ctx = store.get_context("th1")
    assert ctx.summary == "Summary of turns 0-1"
    assert len(ctx.recent_turns) == 3  # turns 2,3,4 kept
    assert ctx.recent_turns[0].turn_index == 2
