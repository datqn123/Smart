from __future__ import annotations

import json
import logging
import sqlite3
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Protocol

logger = logging.getLogger(__name__)



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


class ConversationMemoryStore(Protocol):
    def append_turn(self, thread_id: str, turn: MemoryTurnRecord) -> None: ...
    def get_context(self, thread_id: str) -> ConversationContext: ...
    def compact(self, thread_id: str, summary_text: str) -> None: ...
    def delete_thread(self, thread_id: str) -> None: ...


class InMemoryConversationMemoryStore:
    def __init__(self, max_turns: int = 10) -> None:
        self._max_turns = max_turns
        self._turns: dict[str, list[MemoryTurnRecord]] = OrderedDict()
        self._summaries: dict[str, str] = {}

    def append_turn(self, thread_id: str, turn: MemoryTurnRecord) -> None:
        if thread_id not in self._turns:
            self._turns[thread_id] = []
        self._turns[thread_id].append(turn)
        logger.info("conv_memory_append thread=%s turn=%s intent=%s tools=%s", thread_id, turn.turn_index, turn.intent_type, len(turn.tool_names))

    def get_context(self, thread_id: str) -> ConversationContext:
        turns = self._turns.get(thread_id, [])
        context = ConversationContext(
            summary=self._summaries.get(thread_id, ""),
            recent_turns=list(turns),
        )
        logger.info("conv_memory_retrieve thread=%s turns=%s has_summary=%s", thread_id, len(context.recent_turns), bool(context.summary))
        return context

    def compact(self, thread_id: str, summary_text: str) -> None:
        turns = self._turns.get(thread_id, [])
        if not turns:
            return
        all_turns_count = len(turns)
        keep_count = min(self._max_turns, len(turns))
        keep_count = max(keep_count, 1)
        self._turns[thread_id] = turns[-keep_count:]
        self._summaries[thread_id] = summary_text
        logger.info("conv_memory_compact thread=%s deleted=%s kept=%s", thread_id, all_turns_count - keep_count, keep_count)

    def delete_thread(self, thread_id: str) -> None:
        removed = len(self._turns.get(thread_id, []))
        self._turns.pop(thread_id, None)
        self._summaries.pop(thread_id, None)
        logger.info("conv_memory_delete thread=%s turns_removed=%s", thread_id, removed)


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
        logger.info("conv_memory_append thread=%s turn=%s intent=%s tools=%s", thread_id, turn.turn_index, turn.intent_type, len(turn.tool_names))

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
        ctx = ConversationContext(summary=summary, recent_turns=turns)
        logger.info("conv_memory_retrieve thread=%s turns=%s has_summary=%s", thread_id, len(ctx.recent_turns), bool(ctx.summary))
        return ctx

    def compact(self, thread_id: str, summary_text: str) -> None:
        cursor = self._conn.execute(
            "SELECT turn_index FROM conversation_memory WHERE thread_id = ? ORDER BY turn_index ASC",
            (thread_id,),
        )
        all_turns = [r[0] for r in cursor.fetchall()]
        if not all_turns:
            return
        keep_count = min(self._max_turns, len(all_turns))
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
        logger.info("conv_memory_compact thread=%s deleted=%s kept=%s", thread_id, len(all_turns) - keep_count, keep_count)

    def delete_thread(self, thread_id: str) -> None:
        cursor = self._conn.execute(
            "SELECT COUNT(*) FROM conversation_memory WHERE thread_id = ?",
            (thread_id,),
        )
        removed = cursor.fetchone()[0]
        self._conn.execute(
            "DELETE FROM conversation_memory WHERE thread_id = ?",
            (thread_id,),
        )
        self._conn.execute(
            "DELETE FROM conversation_thread WHERE thread_id = ?",
            (thread_id,),
        )
        self._conn.commit()
        logger.info("conv_memory_delete thread=%s turns_removed=%s", thread_id, removed)
