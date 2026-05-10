"""Helpers for streaming text deltas from an :class:`app.llm.protocol.LlmClient`."""

from __future__ import annotations

from collections.abc import Iterator

from app.llm.protocol import LlmClient


def iter_text_chunks(client: LlmClient, user: str, *, system: str | None = None) -> Iterator[str]:
    """Yield non-empty text fragments from ``client.stream_text``."""
    for delta in client.stream_text(user, system=system):
        if delta:
            yield delta


def join_stream(client: LlmClient, user: str, *, system: str | None = None) -> str:
    """Concatenate all deltas (convenience for tests / simple callers)."""
    return "".join(iter_text_chunks(client, user, system=system))
