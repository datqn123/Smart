"""TTS client protocol."""

from __future__ import annotations

from typing import Protocol


class TtsClient(Protocol):
    def synthesize(self, text: str, *, voice: str | None = None) -> bytes: ...
