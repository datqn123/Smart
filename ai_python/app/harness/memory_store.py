from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Protocol



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
        keep_count = min(self._max_turns, len(turns))
        keep_count = max(keep_count, 1)
        self._turns[thread_id] = turns[-keep_count:]
        self._summaries[thread_id] = summary_text

    def delete_thread(self, thread_id: str) -> None:
        self._turns.pop(thread_id, None)
        self._summaries.pop(thread_id, None)
