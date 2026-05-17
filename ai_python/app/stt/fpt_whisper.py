"""FPT Cloud Whisper via OpenAI-compatible audio transcriptions API."""

from __future__ import annotations

import logging

from openai import OpenAI

from app.config.settings import ResolvedSttCredentials

logger = logging.getLogger(__name__)

_ALLOWED_RESPONSE_FORMATS = frozenset({"json", "text", "verbose_json", "srt", "vtt"})


def mime_for_filename(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".mp3"):
        return "audio/mpeg"
    if lower.endswith(".webm"):
        return "audio/webm"
    if lower.endswith(".ogg"):
        return "audio/ogg"
    return "audio/wav"


class FptWhisperClient:
    def __init__(self, creds: ResolvedSttCredentials) -> None:
        self._creds = creds
        self._client = OpenAI(
            api_key=creds.api_key,
            base_url=creds.base_url,
            timeout=creds.http_timeout_seconds,
        )

    def transcribe(
        self,
        audio_bytes: bytes,
        *,
        filename: str = "recording.wav",
        language: str | None = None,
    ) -> str:
        if not audio_bytes:
            return ""
        lang = (language or self._creds.language or "vi").strip() or "vi"
        fmt = self._creds.response_format
        if fmt not in _ALLOWED_RESPONSE_FORMATS:
            fmt = "json"
        try:
            # FPT docs: pass raw bytes; gateway expects 16 kHz mono PCM WAV from clients.
            response = self._client.audio.transcriptions.create(
                model=self._creds.model,
                file=audio_bytes,
                response_format=fmt,  # type: ignore[arg-type]
                language=lang,
                timeout=self._creds.http_timeout_seconds,
            )
        except Exception as exc:
            logger.warning("STT transcription failed: %s", exc)
            raise RuntimeError(f"STT gateway error: {exc}") from exc

        text = getattr(response, "text", None)
        if text is None and isinstance(response, str):
            return response.strip()
        return (text or "").strip()
