from __future__ import annotations
from dataclasses import dataclass


@dataclass
class TurnContext:
    raw_require: str
    user_id: str
    thread_id: str
    clarification_response: str | None = None  # set khi resume HITL
