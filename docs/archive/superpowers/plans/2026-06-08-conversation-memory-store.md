# Conversation Memory Store — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add turn-to-turn conversation memory to the Harness orchestrator so follow-up questions (e.g., "với tốc độ bán hiện tại thì bao lâu bán hết") retain context from prior turns (e.g., "sản phẩm tokboki").

**Architecture:** New `ConversationMemoryStore` protocol + InMemory/Sqlite variants following existing store pattern (`PendingHitlStore`, `IntentHistoryStore`). Store holds up to 10 recent Q&A turns per `thread_id`, with LLM-based compaction beyond that. Integrated into `HarnessOrchestrator._dispatch()` — enrich scratchpad at start, save turn at end. Harness-only, no legacy LangGraph changes.

**Tech Stack:** Python 3.12, Pydantic v2, sqlite3, existing `HarnessOrchestrator`, existing `TurnScratchpad`

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `ai_python/app/harness/memory_store.py` | **Create** | `MemoryTurnRecord`, `ConversationContext`, `ConversationMemoryStore` protocol, `InMemoryConversationMemoryStore`, `SqliteConversationMemoryStore` |
| `ai_python/tests/test_conversation_memory_store.py` | **Create** | Unit tests for store CRUD + compaction |
| `ai_python/app/config/graph_settings.py` | Modify | Add `conversation_memory_enabled`, `conversation_memory_store_path` |
| `ai_python/app/api/runtime.py` | Modify | Add `_build_conversation_memory_store()`, pass to orchestrator |
| `ai_python/app/harness/orchestrator.py` | Modify | Accept store in `__init__`, enrich scratchpad in `_dispatch`, save turn in `finally` |
| `ai_python/app/harness/__init__.py` | Modify | Export new types |
| `ai_python/tests/test_agentic_integration.py` | Modify | Add integration test for memory cross-turn |

---

### Task 1: Data models — `MemoryTurnRecord` and `ConversationContext`

**Files:**
- Create: `ai_python/app/harness/memory_store.py`

- [ ] **Step 1: Write the data model types**

Append to `ai_python/app/harness/memory_store.py`:

```python
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryTurnRecord:
    thread_id: str
    turn_index: int
    user_message: str
    ai_answer: str
    tool_names: list[str] = field(default_factory=list)
    intent_type: str = ""
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass
class ConversationContext:
    summary: str = ""
    recent_turns: list[MemoryTurnRecord] = field(default_factory=list)
```

- [ ] **Step 2: Run import check**

Run: `cd ai_python && .venv\Scripts\python.exe -c "from app.harness.memory_store import MemoryTurnRecord, ConversationContext; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add ai_python/app/harness/memory_store.py
git commit -m "feat(memory_store): add MemoryTurnRecord and ConversationContext data models"
```

---

### Task 2: `ConversationMemoryStore` protocol

**Files:**
- Modify: `ai_python/app/harness/memory_store.py` (append after data models)

- [ ] **Step 1: Write the protocol**

```python
from typing import Protocol


class ConversationMemoryStore(Protocol):
    def append_turn(self, thread_id: str, turn: MemoryTurnRecord) -> None: ...
    def get_context(self, thread_id: str) -> ConversationContext: ...
    def compact(self, thread_id: str, summary_text: str) -> None: ...
    def delete_thread(self, thread_id: str) -> None: ...
```

- [ ] **Step 2: Run import check**

Run: `cd ai_python && .venv\Scripts\python.exe -c "from app.harness.memory_store import ConversationMemoryStore; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add ai_python/app/harness/memory_store.py
git commit -m "feat(memory_store): add ConversationMemoryStore protocol"
```

---

### Task 3: `InMemoryConversationMemoryStore`

**Files:**
- Modify: `ai_python/app/harness/memory_store.py`

- [ ] **Step 1: Write the failing test**

Add to `ai_python/tests/test_conversation_memory_store.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_conversation_memory_store.py -v`
Expected: FAIL with `ModuleNotFoundError: cannot import name 'InMemoryConversationMemoryStore'`

- [ ] **Step 3: Write the implementation**

Append to `ai_python/app/harness/memory_store.py`:

```python
from collections import OrderedDict
from dataclasses import dataclass, field


class InMemoryConversationMemoryStore:
    def __init__(self, max_turns: int = 10) -> None:
        self._max_turns = max_turns
        self._turns: dict[str, list[MemoryTurnRecord]] = OrderedDict()
        self._summaries: dict[str, str] = {}

    def append_turn(self, thread_id: str, turn: MemoryTurnRecord) -> None:
        if thread_id not in self._turns:
            self._turns[thread_id] = []
        self._turns[thread_id].append(turn)

    def get_context(self, thread_id: str) -> ConversationContext:
        turns = self._turns.get(thread_id, [])
        return ConversationContext(
            summary=self._summaries.get(thread_id, ""),
            recent_turns=list(turns),
        )

    def compact(self, thread_id: str, summary_text: str) -> None:
        turns = self._turns.get(thread_id, [])
        if not turns:
            return
        keep_count = min(self._max_turns // 2, len(turns))
        keep_count = max(keep_count, 1)
        self._turns[thread_id] = turns[-keep_count:]
        self._summaries[thread_id] = summary_text

    def delete_thread(self, thread_id: str) -> None:
        self._turns.pop(thread_id, None)
        self._summaries.pop(thread_id, None)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_conversation_memory_store.py -v`
Expected: All 3 PASS

- [ ] **Step 5: Commit**

```bash
git add ai_python/app/harness/memory_store.py ai_python/tests/test_conversation_memory_store.py
git commit -m "feat(memory_store): add InMemoryConversationMemoryStore"
```

---

### Task 4: `SqliteConversationMemoryStore`

**Files:**
- Modify: `ai_python/app/harness/memory_store.py`
- Modify: `ai_python/tests/test_conversation_memory_store.py`

- [ ] **Step 1: Write the failing test**

Append to `ai_python/tests/test_conversation_memory_store.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_conversation_memory_store.py::test_sqlite_append_and_get_context -v`
Expected: FAIL with `cannot import name 'SqliteConversationMemoryStore'`

- [ ] **Step 3: Write the implementation**

Append to `ai_python/app/harness/memory_store.py`:

```python
import json
import sqlite3
from pathlib import Path


class SqliteConversationMemoryStore:
    def __init__(self, path: str, max_turns: int = 10) -> None:
        self._max_turns = max_turns
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_memory (
                thread_id TEXT NOT NULL,
                turn_index INTEGER NOT NULL,
                user_message TEXT NOT NULL,
                ai_answer TEXT,
                tool_names TEXT,
                intent_type TEXT,
                timestamp REAL NOT NULL,
                PRIMARY KEY (thread_id, turn_index)
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_thread (
                thread_id TEXT PRIMARY KEY,
                summary TEXT DEFAULT '',
                turn_count INTEGER NOT NULL DEFAULT 0
            )
        """)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def append_turn(self, thread_id: str, turn: MemoryTurnRecord) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO conversation_memory
               (thread_id, turn_index, user_message, ai_answer,
                tool_names, intent_type, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                thread_id, turn.turn_index,
                turn.user_message, turn.ai_answer,
                json.dumps(turn.tool_names, ensure_ascii=False),
                turn.intent_type, turn.timestamp,
            ),
        )
        self._conn.execute(
            """INSERT INTO conversation_thread (thread_id, turn_count, summary)
               VALUES (?, 1, '')
               ON CONFLICT(thread_id) DO UPDATE SET
                   turn_count = turn_count + 1""",
            (thread_id,),
        )
        self._conn.commit()

    def get_context(self, thread_id: str) -> ConversationContext:
        cursor = self._conn.execute(
            "SELECT summary FROM conversation_thread WHERE thread_id = ?",
            (thread_id,),
        )
        row = cursor.fetchone()
        summary = row[0] if row else ""

        cursor = self._conn.execute(
            """SELECT turn_index, user_message, ai_answer, tool_names, intent_type, timestamp
               FROM conversation_memory
               WHERE thread_id = ?
               ORDER BY turn_index ASC""",
            (thread_id,),
        )
        turns = []
        for row in cursor.fetchall():
            turns.append(MemoryTurnRecord(
                thread_id=thread_id,
                turn_index=row[0],
                user_message=row[1],
                ai_answer=row[2] or "",
                tool_names=json.loads(row[3]) if row[3] else [],
                intent_type=row[4] or "",
                timestamp=row[5],
            ))
        return ConversationContext(summary=summary, recent_turns=turns)

    def compact(self, thread_id: str, summary_text: str) -> None:
        cursor = self._conn.execute(
            "SELECT turn_index FROM conversation_memory WHERE thread_id = ? ORDER BY turn_index ASC",
            (thread_id,),
        )
        all_turns = [r[0] for r in cursor.fetchall()]
        if not all_turns:
            return
        keep_count = min(self._max_turns // 2, len(all_turns))
        keep_count = max(keep_count, 1)
        cutoff = all_turns[-keep_count]
        self._conn.execute(
            "DELETE FROM conversation_memory WHERE thread_id = ? AND turn_index < ?",
            (thread_id, cutoff),
        )
        self._conn.execute(
            "UPDATE conversation_thread SET summary = ? WHERE thread_id = ?",
            (summary_text, thread_id),
        )
        self._conn.commit()

    def delete_thread(self, thread_id: str) -> None:
        self._conn.execute(
            "DELETE FROM conversation_memory WHERE thread_id = ?",
            (thread_id,),
        )
        self._conn.execute(
            "DELETE FROM conversation_thread WHERE thread_id = ?",
            (thread_id,),
        )
        self._conn.commit()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_conversation_memory_store.py -v`
Expected: All 5 PASS

- [ ] **Step 5: Commit**

```bash
git add ai_python/app/harness/memory_store.py ai_python/tests/test_conversation_memory_store.py
git commit -m "feat(memory_store): add SqliteConversationMemoryStore"
```

---

### Task 5: GraphSettings — add configuration fields

**Files:**
- Modify: `ai_python/app/config/graph_settings.py`

- [ ] **Step 1: Add two fields to `GraphSettings` class**

Insert after `agentic_v3_template_promote_after` field (around line 431):

```python
    # --- Conversation memory (harness-only) ---
    conversation_memory_enabled: bool = Field(
        default=True,
        description="Enable turn-to-turn conversation memory in harness orchestrator.",
    )
    conversation_memory_store_path: str | None = Field(
        default=None,
        description="SQLite path for ConversationMemoryStore; None = in-memory.",
    )
```

- [ ] **Step 2: Add validators for the new fields**

Add `"conversation_memory_enabled"` to the existing `coerce_sql_factory_flags` validator's field list (the long `@field_validator` at line 498).

- [ ] **Step 3: Run import check**

Run: `cd ai_python && .venv\Scripts\python.exe -c "from app.config.graph_settings import GraphSettings; s=GraphSettings(); print(s.conversation_memory_enabled, s.conversation_memory_store_path)"`
Expected: `True None`

- [ ] **Step 4: Commit**

```bash
git add ai_python/app/config/graph_settings.py
git commit -m "feat(graph_settings): add conversation_memory_enabled and conversation_memory_store_path"
```

---

### Task 6: Builder function and wire into orchestrator construction

**Files:**
- Modify: `ai_python/app/api/runtime.py` (lines ~710-725)

- [ ] **Step 1: Add builder function after `_build_history_store`**

```python
def _build_conversation_memory_store(settings: Any) -> Any | None:
    if not bool(getattr(settings, "conversation_memory_enabled", True)):
        return None
    path = getattr(settings, "conversation_memory_store_path", None)
    if path:
        from app.harness.memory_store import SqliteConversationMemoryStore
        return SqliteConversationMemoryStore(str(path))
    from app.harness.memory_store import InMemoryConversationMemoryStore
    return InMemoryConversationMemoryStore()
```

- [ ] **Step 2: Pass store to orchestrator constructor**

In `get_graph_runtime()`, add `memory_store=_build_conversation_memory_store(deps.settings)` to the `HarnessOrchestrator(...)` call:

```python
    orchestrator = HarnessOrchestrator(
        llm_registry=deps.llm_registry,
        tool_registry=_build_tool_registry(deps),
        policy=HarnessPolicy(),
        settings=deps.settings,
        harness=deps.harness,
        plan_template_store=_build_plan_template_store(deps.settings),
        history_store=_build_history_store(deps.settings),
        memory_store=_build_conversation_memory_store(deps.settings),
    )
```

- [ ] **Step 3: Commit**

```bash
git add ai_python/app/api/runtime.py
git commit -m "feat(runtime): wire ConversationMemoryStore into HarnessOrchestrator"
```

---

### Task 7: Accept `memory_store` in `HarnessOrchestrator.__init__`

**Files:**
- Modify: `ai_python/app/harness/orchestrator.py` (lines 99-138)

- [ ] **Step 1: Write the failing test**

Append to `ai_python/tests/test_conversation_memory_store.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_conversation_memory_store.py::test_orchestrator_accepts_memory_store -v`
Expected: FAIL with `TypeError: HarnessOrchestrator.__init__() got an unexpected keyword argument 'memory_store'`

- [ ] **Step 3: Add `memory_store` parameter**

In `HarnessOrchestrator.__init__`, add `memory_store: Any | None = None` parameter and store it:

```python
    def __init__(
        self,
        *,
        llm_registry: LlmRegistry,
        tool_registry: ToolRegistry,
        policy: HarnessPolicy,
        settings: GraphSettings,
        harness: AgentHarness,
        plan_template_store: PlanTemplateStore | None = None,
        history_store: IntentHistoryStore | None = None,
        memory_store: Any | None = None,          # <-- add this line
    ) -> None:
```
Add body line after `self._history_store = history_store`:
```python
        self._memory_store = memory_store
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_conversation_memory_store.py::test_orchestrator_accepts_memory_store -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ai_python/app/harness/orchestrator.py ai_python/tests/test_conversation_memory_store.py
git commit -m "feat(orchestrator): accept memory_store parameter in __init__"
```

---

### Task 8: Enrich scratchpad at start of `_dispatch`

**Files:**
- Modify: `ai_python/app/harness/orchestrator.py`

- [ ] **Step 1: Write the failing test**

Append to `ai_python/tests/test_conversation_memory_store.py`:

```python
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
```

Also add `_ctx()` helper at top of test file if not already present:

```python
def _ctx():
    from app.harness.tool_registry import TurnContext
    return TurnContext(
        tenant_id="t1", user_id="u1",
        thread_id="th1",
        correlation_id="corr-1",
        bearer_token=None, schema_version=None,
    )
```

- [ ] **Step 2: Add `_enrich_from_memory` method to `HarnessOrchestrator`**

```python
    def _enrich_from_memory(
        self,
        ctx: TurnContext,
        scratchpad: TurnScratchpad,
    ) -> TurnContext:
        """Prepend conversation memory as a SystemMessage into scratchpad."""
        if self._memory_store is None:
            return ctx
        thread_id = ctx.thread_id or ctx.correlation_id
        if not thread_id:
            return ctx
        memory = self._memory_store.get_context(thread_id)
        blocks: list[str] = []
        if memory.summary:
            blocks.append(f"[Lịch sử hội thoại]\n{memory.summary}")
        if memory.recent_turns:
            turn_lines = []
            for t in memory.recent_turns:
                turn_lines.append(f"Người dùng: {t.user_message}")
                if t.ai_answer:
                    turn_lines.append(f"Trợ lý: {t.ai_answer}")
            blocks.append("[Các lượt gần đây]\n" + "\n".join(turn_lines))
        if not blocks:
            return ctx
        from langchain_core.messages import SystemMessage
        scratchpad.messages.insert(
            0,
            SystemMessage(content="\n\n".join(blocks)),
        )
        return ctx
```

- [ ] **Step 3: Call `_enrich_from_memory` at start of `_dispatch`**

Inside `_dispatch()`, insert after `WorkingMemory.attach()` (line ~216) and before `try:` (line ~217):

```python
        ctx = self._enrich_from_memory(ctx, scratchpad)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_conversation_memory_store.py::test_memory_enriches_scratchpad_at_dispatch -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ai_python/app/harness/orchestrator.py ai_python/tests/test_conversation_memory_store.py
git commit -m "feat(orchestrator): enrich scratchpad with conversation memory at _dispatch start"
```

---

### Task 9: Save turn at end of `_dispatch` (finally block)

**Files:**
- Modify: `ai_python/app/harness/orchestrator.py`

- [ ] **Step 1: Write the failing test**

Append to `ai_python/tests/test_conversation_memory_store.py`:

```python
@pytest.mark.asyncio
async def test_memory_saves_turn_after_dispatch() -> None:
    """After _dispatch completes, the turn should be saved to memory_store."""
    from app.harness.memory_store import InMemoryConversationMemoryStore, MemoryTurnRecord
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
        llm_registry=None,
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
```

- [ ] **Step 2: Write `_save_turn_to_memory` method**

```python
    def _save_turn_to_memory(
        self,
        ctx: TurnContext,
        scratchpad: TurnScratchpad,
    ) -> None:
        if self._memory_store is None:
            return
        thread_id = ctx.thread_id or ctx.correlation_id
        if not thread_id:
            return
        # Extract user question and AI answer from scratchpad
        user_msg = ""
        ai_answer = ""
        for m in reversed(scratchpad.messages):
            content = str(getattr(m, "content", "") or "")
            from langchain_core.messages import HumanMessage, AIMessage
            if not ai_answer and isinstance(m, AIMessage) and content:
                ai_answer = content
            if not user_msg and isinstance(m, HumanMessage) and content:
                user_msg = content
                if ai_answer:
                    break

        if not user_msg:
            return

        # Get existing turn count
        existing = self._memory_store.get_context(thread_id)
        turn_index = len(existing.recent_turns) + 1

        turn = MemoryTurnRecord(
            thread_id=thread_id,
            turn_index=turn_index,
            user_message=user_msg,
            ai_answer=ai_answer,
            tool_names=list(self._turn_tools),
            intent_type=str(getattr(self.last_metrics, "intent", "") or ""),
        )
        self._memory_store.append_turn(thread_id, turn)
```

- [ ] **Step 3: Call `_save_turn_to_memory` in `finally` block**

Inside `_dispatch()`'s `finally` block (after `_record_turn_history(...)` call, around line 380):

```python
            self._record_turn_history(...)  # existing
            self._save_turn_to_memory(ctx, scratchpad)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_conversation_memory_store.py::test_memory_saves_turn_after_dispatch -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ai_python/app/harness/orchestrator.py ai_python/tests/test_conversation_memory_store.py
git commit -m "feat(orchestrator): save turn to conversation memory in _dispatch finally block"
```

---

### Task 10: Export new types from `__init__.py`

**Files:**
- Modify: `ai_python/app/harness/__init__.py`

- [ ] **Step 1: Add imports and exports**

Add these imports to the top section:

```python
from app.harness.memory_store import (
    ConversationContext,
    ConversationMemoryStore,
    InMemoryConversationMemoryStore,
    MemoryTurnRecord,
    SqliteConversationMemoryStore,
)
```

Add to `__all__` list:

```python
    "ConversationContext",
    "ConversationMemoryStore",
    "InMemoryConversationMemoryStore",
    "MemoryTurnRecord",
    "SqliteConversationMemoryStore",
```

- [ ] **Step 2: Run import check**

Run: `cd ai_python && .venv\Scripts\python.exe -c "from app.harness import ConversationMemoryStore, InMemoryConversationMemoryStore, SqliteConversationMemoryStore, MemoryTurnRecord, ConversationContext; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add ai_python/app/harness/__init__.py
git commit -m "chore(harness): export conversation memory types"
```

---

### Task 11: Integration test — cross-turn context retention

**Files:**
- Modify: `ai_python/tests/test_agentic_integration.py`

- [ ] **Step 1: Write integration test**

Append to `ai_python/tests/test_agentic_integration.py`:

```python
@pytest.mark.asyncio
async def test_conversation_memory_cross_turn_context() -> None:
    """Verify that a follow-up question sees prior turn context in scratchpad."""
    from app.harness.memory_store import (
        InMemoryConversationMemoryStore,
        MemoryTurnRecord,
    )
    from app.harness.orchestrator import HarnessOrchestrator
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.scratchpad import TurnScratchpad
    from app.harness.tool_registry import ToolRegistry
    from app.config.graph_settings import GraphSettings
    from langchain_core.messages import HumanMessage, SystemMessage
    from tests.fake_llm import FakeLlmClient
    from tests.test_intent_confidence_thresholds import _ctx, _settings, _Registry

    store = InMemoryConversationMemoryStore()
    store.append_turn("th1", MemoryTurnRecord(
        thread_id="th1", turn_index=1,
        user_message="sản phẩm tokboki",
        ai_answer="sản phẩm tokboki mã SP001, tồn 50",
        tool_names=["sql_query"],
        intent_type="data_query",
    ))

    orch = HarnessOrchestrator(
        llm_registry=_Registry(FakeLlmClient(intent="data_query", intent_confidence=0.95)),
        tool_registry=ToolRegistry(),
        policy=HarnessPolicy(),
        settings=_settings(agentic_intent_object_enabled=True),
        harness=AgentHarness(enabled=False),
        memory_store=store,
    )

    # Turn 2 — follow-up question
    scratchpad = TurnScratchpad(
        messages=[HumanMessage(content="tốc độ bán hết bao lâu?")],
    )
    ctx = _ctx()
    # We override thread_id to match stored memory
    import dataclasses
    ctx = dataclasses.replace(ctx, thread_id="th1")
    ctx = orch._enrich_from_memory(ctx, scratchpad)

    # The scratchpad should now have a SystemMessage with prior context
    system_msgs = [
        m for m in scratchpad.messages
        if isinstance(m, SystemMessage)
    ]
    assert system_msgs, "Expected SystemMessage with memory context"
    combined = " ".join(str(m.content) for m in system_msgs)
    assert "tokboki" in combined, (
        f"Prior turn context 'tokboki' should appear in memory context, got: {combined[:200]}"
    )
```

- [ ] **Step 2: Run test**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_agentic_integration.py::test_conversation_memory_cross_turn_context -v`
Expected: PASS

- [ ] **Step 3: Run full integration suite**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_agentic_integration.py -v 2>&1 | Select-Object -Last 20`
Expected: All tests PASS (no pre-existing failures unless unrelated)

- [ ] **Step 4: Commit**

```bash
git add ai_python/tests/test_agentic_integration.py
git commit -m "test: add cross-turn conversation memory integration test"
```

---

### Task 12: Verify full test suite

- [ ] **Step 1: Run all memory store tests**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_conversation_memory_store.py -v`
Expected: All PASS

- [ ] **Step 2: Run broader test suite**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_agentic_integration.py tests/test_intent_confidence_thresholds.py tests/test_intent_object.py -v 2>&1 | Select-Object -Last 25`
Expected: All PASS

## Self-Review

**Spec coverage:**
- `MemoryTurnRecord` + `ConversationContext` data models — Task 1 ✅
- `ConversationMemoryStore` protocol — Task 2 ✅
- `InMemoryConversationMemoryStore` — Task 3 ✅
- `SqliteConversationMemoryStore` — Task 4 ✅
- GraphSettings fields — Task 5 ✅
- Builder function + wire into orchestrator — Tasks 6-7 ✅
- Enrich scratchpad at _dispatch start — Task 8 ✅
- Save turn at _dispatch end — Task 9 ✅
- Export types — Task 10 ✅
- Integration test — Task 11 ✅
- Verify full suite — Task 12 ✅

**Placeholder scan:** No TBD/TODO/placeholder patterns found.

**Type consistency:** `MemoryTurnRecord`, `ConversationContext`, `ConversationMemoryStore` protocol — consistent across all tasks. `InMemoryConversationMemoryStore` and `SqliteConversationMemoryStore` both implement the same `append_turn/get_context/compact/delete_thread` interface.
