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
import json
import logging
from pathlib import Path
from typing import TypedDict

log = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent / "compact_prompt.md"


def load_compact_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


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

    async def compact(self, thread_id: str, *, llm) -> None:
        """Gop cac luot tran ngoai window vao rolling summary (1 LLM call).

        Degrade an toan: LLM loi -> giu summary cu, VAN drop luot tran,
        khong raise (duoc goi fire-and-forget tu api/app.py)."""
        async with self._lock:
            mem = self._store.get(thread_id)
            if mem is None or len(mem["turns"]) <= self._window:
                return
            overflow = list(mem["turns"][:-self._window])
            prompt = load_compact_prompt()
            user = (f"[Summary cu]:\n{mem['summary'] or '(chua co)'}\n\n"
                    f"[Cac luot can gop]:\n{json.dumps(overflow, ensure_ascii=False)}")
            try:
                # llm.complete la sync (openai SDK) -> to_thread de khong block loop
                new_summary = await asyncio.to_thread(
                    llm.complete, system=prompt, user=user, role="default")
                mem["summary"] = new_summary.strip()[:self._summary_max_chars]
                log.info("memory compact thread=%s dropped=%d summary_len=%d",
                         thread_id, len(overflow), len(mem["summary"]))
            except Exception as exc:
                log.warning("memory compact failed thread=%s: %s — giu summary cu",
                            thread_id, exc)
            # Drop theo len(overflow) da chot truoc LLM call — luot append
            # trong luc LLM dang chay van duoc giu nguyen.
            mem["turns"] = mem["turns"][len(overflow):]


_memory: ConversationMemory | None = None


def get_memory() -> ConversationMemory:
    from app.config.settings import get_settings
    global _memory
    if _memory is None:
        s = get_settings()
        _memory = ConversationMemory(window=s.memory_window_turns,
                                     summary_max_chars=s.memory_summary_max_chars)
    return _memory
