"""FPT Cloud VITs TTS via OpenAI-compatible audio speech API."""

from __future__ import annotations

import logging

from openai import OpenAI

from app.config.settings import ResolvedTtsCredentials

logger = logging.getLogger(__name__)


class FptVitsClient:
    def __init__(self, creds: ResolvedTtsCredentials) -> None:
        self._creds = creds
        self._client = OpenAI(
            api_key=creds.api_key,
            base_url=creds.base_url,
            timeout=creds.http_timeout_seconds,
        )

    def synthesize(self, text: str, *, voice: str | None = None) -> bytes:
        if not text.strip():
            return b""
        use_voice = (voice or self._creds.voice).strip() or self._creds.voice
        try:
            response = self._client.audio.speech.create(
                model=self._creds.model,
                input=text,
                response_format=self._creds.response_format,  # type: ignore[arg-type]
                voice=use_voice,
                timeout=self._creds.http_timeout_seconds,
            )
        except Exception as exc:
            logger.warning("TTS synthesis failed: %s", exc)
            raise RuntimeError(f"TTS gateway error: {exc}") from exc

        if hasattr(response, "read"):
            data = response.read()
            return data if isinstance(data, bytes) else bytes(data)
        content = getattr(response, "content", None)
        if content is not None:
            return content if isinstance(content, bytes) else bytes(content)
        raise RuntimeError("TTS gateway returned empty audio.")
