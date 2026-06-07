"""Three-tier memory primitives for harness tests and agentic wiring."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Protocol

from langchain_core.messages import BaseMessage


class WorkingMemory:
    def __init__(self, pairs: int = 6) -> None:
        self._message_cap = max(0, int(pairs)) * 2

    def attach(self, messages: list[BaseMessage]) -> list[BaseMessage]:
        if not self._message_cap:
            return []
        return list(messages[-self._message_cap :])


@dataclass
class EpisodicMemory:
    summary: str = ""


@dataclass
class SemanticRecord:
    user_id: str
    kind: str
    content: str


class SemanticStore(Protocol):
    async def upsert(self, rec: SemanticRecord) -> None:
        ...

    async def recall(self, user_id: str, query: str, k: int = 5) -> list[SemanticRecord]:
        ...


class InMemorySemanticStore:
    def __init__(self) -> None:
        self.records: list[SemanticRecord] = []

    async def upsert(self, rec: SemanticRecord) -> None:
        if _has_raw_pii(rec.content):
            return
        self.records.append(rec)

    async def recall(self, user_id: str, query: str, k: int = 5) -> list[SemanticRecord]:
        candidates = [rec for rec in self.records if rec.user_id == user_id]
        ranked = sorted(candidates, key=lambda rec: _score(query, rec.content), reverse=True)
        return ranked[:k]


def _score(query: str, content: str) -> float:
    q = " ".join((query or "").casefold().split())
    c = " ".join((content or "").casefold().split())
    q_terms = set(q.split())
    c_terms = set(c.split())
    overlap = len(q_terms & c_terms) / max(1, len(q_terms | c_terms))
    return max(overlap, SequenceMatcher(None, q, c).ratio())


def _has_raw_pii(text: str) -> bool:
    if re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text or ""):
        return True
    digits = re.sub(r"\D", "", text or "")
    return len(digits) >= 9
