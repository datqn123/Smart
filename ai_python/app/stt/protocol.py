"""STT client port."""

from __future__ import annotations

from typing import Protocol


class SttClient(Protocol):
    def transcribe(
        self,
        audio_bytes: bytes,
        *,
        filename: str = "recording.wav",
        language: str | None = None,
    ) -> str:
        """Transcribe audio bytes to plain text."""
