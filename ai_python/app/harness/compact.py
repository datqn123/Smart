"""Harness compact subagent primitives."""

from __future__ import annotations

from langchain_core.messages import BaseMessage
from pydantic import BaseModel


class CompactOutput(BaseModel):
    compact_block: str


class CompactSubagent:
    def __init__(self, compact_context_ratio: float = 0.70) -> None:
        self._ratio = float(compact_context_ratio)

    def should_compact(self, *, token_count: int, context_window: int) -> bool:
        if context_window <= 0:
            return False
        return token_count >= context_window * self._ratio

    async def compact(self, messages: list[BaseMessage]) -> CompactOutput:
        contents = [str(getattr(message, "content", "") or "").strip() for message in messages]
        contents = [text for text in contents if text]
        return CompactOutput(compact_block="[COMPACT] " + " | ".join(contents[-6:]))
