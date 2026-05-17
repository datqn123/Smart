"""Build TTS client from settings."""

from __future__ import annotations

from app.config.settings import LlmSettings, TtsSettings, resolve_tts_credentials
from app.tts.fpt_vits import FptVitsClient
from app.tts.protocol import TtsClient


def build_tts_client(tts: TtsSettings, llm: LlmSettings) -> TtsClient | None:
    creds = resolve_tts_credentials(llm, tts)
    if creds is None:
        return None
    return FptVitsClient(creds)
