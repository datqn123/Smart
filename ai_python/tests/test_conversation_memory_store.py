from __future__ import annotations

from app.harness.memory_store import (
    ConversationContext,
    ConversationMemoryStore,
    InMemoryConversationMemoryStore,
    MemoryTurnRecord,
)


def _ctx():
    from app.harness.tool_registry import TurnContext
    return TurnContext(
        tenant_id="t1", user_id="u1",
        thread_id="th1",
        correlation_id="corr-1",
        bearer_token=None, schema_version=None,
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


import json
import tempfile


def test_sqlite_append_and_get_context() -> None:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        from app.harness.memory_store import SqliteConversationMemoryStore
        store = SqliteConversationMemoryStore(db_path)
        t1 = MemoryTurnRecord(
            thread_id="th1", turn_index=1,
            user_message="doanh thu", ai_answer="10 tỷ",
            tool_names=["sql_query"], intent_type="data_query",
        )
        store.append_turn("th1", t1)
        ctx = store.get_context("th1")
        assert len(ctx.recent_turns) == 1
        assert ctx.recent_turns[0].user_message == "doanh thu"
        assert ctx.summary == ""

        store.compact("th1", "compacted text")
        ctx2 = store.get_context("th1")
        assert ctx2.summary == "compacted text"

        store.close()
    finally:
        import os
        os.unlink(db_path)


def test_sqlite_delete_thread() -> None:
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        from app.harness.memory_store import SqliteConversationMemoryStore
        store = SqliteConversationMemoryStore(db_path)
        store.append_turn("th1", MemoryTurnRecord(
            thread_id="th1", turn_index=1,
            user_message="q", ai_answer="a",
        ))
        store.delete_thread("th1")
        ctx = store.get_context("th1")
        assert ctx.recent_turns == []
        assert ctx.summary == ""
        store.close()
    finally:
        os.unlink(db_path)


def test_orchestrator_accepts_memory_store() -> None:
    from app.harness.memory_store import InMemoryConversationMemoryStore
    from app.harness.orchestrator import HarnessOrchestrator
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.tool_registry import ToolRegistry
    from app.config.graph_settings import GraphSettings

    store = InMemoryConversationMemoryStore()
    orch = HarnessOrchestrator(
        llm_registry=None,
        tool_registry=ToolRegistry(),
        policy=HarnessPolicy(),
        settings=GraphSettings(),
        harness=AgentHarness(enabled=False),
        memory_store=store,
    )
    assert orch._memory_store is store


import pytest


@pytest.mark.asyncio
async def test_memory_enriches_scratchpad_at_dispatch() -> None:
    """When memory_store has prior turns, a SystemMessage is prepended to scratchpad."""
    from app.harness.memory_store import InMemoryConversationMemoryStore, MemoryTurnRecord
    from app.harness.orchestrator import HarnessOrchestrator
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.scratchpad import TurnScratchpad
    from app.harness.tool_registry import ToolRegistry
    from app.config.graph_settings import GraphSettings
    from langchain_core.messages import HumanMessage, SystemMessage

    store = InMemoryConversationMemoryStore()
    store.append_turn("th1", MemoryTurnRecord(
        thread_id="th1", turn_index=1,
        user_message="sản phẩm tokboki", ai_answer="Đây là sản phẩm A",
        tool_names=["sql_query"], intent_type="data_query",
    ))

    orch = HarnessOrchestrator(
        llm_registry=None,
        tool_registry=ToolRegistry(),
        policy=HarnessPolicy(),
        settings=GraphSettings(),
        harness=AgentHarness(enabled=False),
        memory_store=store,
    )
    scratchpad = TurnScratchpad(
        messages=[HumanMessage(content="tốc độ bán hết bao lâu?")],
    )
    # Simulate the enrichment that happens at _dispatch start
    ctx = _ctx()
    ctx = orch._enrich_from_memory(ctx, scratchpad)

    assert any(
        isinstance(m, SystemMessage) and "sản phẩm tokboki" in (m.content or "")
        for m in scratchpad.messages
    ), "Memory context should be prepended as SystemMessage"


class _FakeLlmClient:
    last_usage = type("Usage", (), {"prompt_tokens": 10, "completion_tokens": 5, "cost_usd": 0.001})()

    async def astructured_predict(self, messages, schema, **kwargs):
        return schema(action="final_answer", final_answer="Đã xử lý.")


class _FakeRegistry:
    def __init__(self, client=None):
        self._client = client or _FakeLlmClient()

    def get(self, role: str):
        return self._client


@pytest.mark.asyncio
async def test_memory_saves_turn_after_dispatch() -> None:
    """After _dispatch completes, the turn should be saved to memory_store."""
    from app.harness.memory_store import InMemoryConversationMemoryStore
    from app.harness.orchestrator import (
        FinalAnswerEvent, HarnessOrchestrator,
    )
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.scratchpad import TurnScratchpad
    from app.harness.tool_registry import ToolRegistry
    from app.config.graph_settings import GraphSettings
    from langchain_core.messages import HumanMessage

    store = InMemoryConversationMemoryStore()
    orch = HarnessOrchestrator(
        llm_registry=_FakeRegistry(),
        tool_registry=ToolRegistry(),
        policy=HarnessPolicy(),
        settings=GraphSettings(),
        harness=AgentHarness(enabled=False),
        memory_store=store,
    )

    events = [
        event
        async for event in orch.run(
            TurnScratchpad(messages=[HumanMessage(content="test question")]),
            _ctx(),
        )
    ]

    assert any(isinstance(e, FinalAnswerEvent) for e in events)
    ctx2 = store.get_context("th1")
    assert len(ctx2.recent_turns) >= 1
    assert ctx2.recent_turns[-1].user_message == "test question"
