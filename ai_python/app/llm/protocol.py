"""Port: LlmClient — implementations hide LangChain / HTTP details."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol, TypeVar

from langchain_core.messages import BaseMessage
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LlmClient(Protocol):
    """Minimal contract for Task 1; LangGraph nodes depend on this port."""

    def invoke_text(self, user: str, *, system: str | None = None) -> str:
        """Single-turn text completion (sync)."""
        ...

    def stream_text(self, user: str, *, system: str | None = None) -> Iterator[str]:
        """Stream plain-text deltas (sync iterator)."""
        ...

    def structured_predict(
        self,
        messages: Sequence[BaseMessage],
        schema: type[T],
        *,
        max_retries: int = 3,
    ) -> T:
        """Return a validated Pydantic model (native or JSON fallback)."""
        ...
