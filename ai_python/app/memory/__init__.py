"""Conversation memory theo thread_id (in-memory — chap nhan mat khi restart).

Giu `window` luot (user -> answer) verbatim; qua window thi compact() gop
phan cu vao rolling summary bang LLM (prompt: compact_prompt.md).

Singleton module-level qua get_memory() — KHONG tao trong get_deps() vi
FastAPI Depends chay moi request se reset store (PendingStore song duoc vi
backed boi SQLite).
"""
from __future__ import annotations
import asyncio
import copy
import logging
from typing import TypedDict

log = logging.getLogger(__name__)


class ThreadMemory(TypedDict):
    turns: list[dict]      # [{"user": str, "answer": str}]
    summary: str | None    # rolling summary, None khi chua compact


class ConversationMemory:
    def __init__(self, *, window: int = 10, summary_max_chars: int = 2000):
        self._window = window
        self._summary_max_chars = summary_max_chars
        self._store: dict[str, ThreadMemory] = {}
        self._lock = asyncio.Lock()  # chi guard compact-vs-compact

    def get_context(self, thread_id: str) -> ThreadMemory:
        mem = self._store.get(thread_id)
        if mem is None:
            return ThreadMemory(turns=[], summary=None)
        return ThreadMemory(turns=copy.deepcopy(mem["turns"]), summary=mem["summary"])

    def append_turn(self, thread_id: str, user: str, answer: str) -> None:
        # Sync, khong await -> atomic tren event loop don, khong can lock.
        mem = self._store.setdefault(thread_id, ThreadMemory(turns=[], summary=None))
        mem["turns"].append({"user": user, "answer": answer})

    def needs_compact(self, thread_id: str) -> bool:
        mem = self._store.get(thread_id)
        return mem is not None and len(mem["turns"]) > self._window
