"""Build STT client from settings."""

from __future__ import annotations

from app.config.settings import LlmSettings, SttSettings, resolve_stt_credentials
from app.stt.fpt_whisper import FptWhisperClient
from app.stt.protocol import SttClient


def build_stt_client(stt: SttSettings, llm: LlmSettings) -> SttClient | None:
    creds = resolve_stt_credentials(llm, stt)
    if creds is None:
        return None
    return FptWhisperClient(creds)
