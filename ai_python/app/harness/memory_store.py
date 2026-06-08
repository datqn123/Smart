from __future__ import annotations

import time
from dataclasses import dataclass, field



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
