from __future__ import annotations

import time
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
