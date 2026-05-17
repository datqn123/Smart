"""TTS service for API layer."""

from __future__ import annotations

from functools import lru_cache

from app.config.settings import (
    LlmSettings,
    ResolvedTtsCredentials,
    TtsSettings,
    load_llm_settings,
    load_tts_settings,
    resolve_tts_credentials,
)
from app.tts.factory import build_tts_client
from app.tts.protocol import TtsClient


class TtsService:
    def __init__(
        self,
        client: TtsClient | None,
        creds: ResolvedTtsCredentials | None,
    ) -> None:
        self._client = client
        self._creds = creds

    @property
    def available(self) -> bool:
        return self._client is not None and self._creds is not None

    @property
    def default_voice(self) -> str:
        if self._creds is None:
            return "std_kimngan"
        return self._creds.voice

    def synthesize(self, text: str, *, voice: str | None = None) -> bytes:
        if not self.available or self._client is None or self._creds is None:
            raise RuntimeError("TTS is not configured.")
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("Nội dung đọc không được để trống.")
        if len(cleaned) > self._creds.max_input_chars:
            raise ValueError(
                f"Văn bản quá dài (tối đa {self._creds.max_input_chars} ký tự)."
            )
        return self._client.synthesize(cleaned, voice=voice)


@lru_cache(maxsize=1)
def get_tts_service() -> TtsService:
    llm = load_llm_settings()
    tts = load_tts_settings()
    creds = resolve_tts_credentials(llm, tts)
    client = build_tts_client(tts, llm)
    return TtsService(client, creds)
