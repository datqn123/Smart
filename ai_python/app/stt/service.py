"""STT service for API layer (validation + transcribe)."""

from __future__ import annotations

import logging
import struct
from functools import lru_cache

from app.config.settings import (
    LlmSettings,
    ResolvedSttCredentials,
    SttSettings,
    load_llm_settings,
    load_stt_settings,
    resolve_stt_credentials,
)
from app.stt.factory import build_stt_client
from app.stt.protocol import SttClient

logger = logging.getLogger(__name__)

_ALLOWED_EXTENSIONS = frozenset({".wav", ".mp3", ".webm", ".ogg"})
_ALLOWED_MIME_PREFIXES = ("audio/wav", "audio/x-wav", "audio/mpeg", "audio/webm", "audio/ogg")


def _extension_ok(filename: str) -> bool:
    lower = filename.lower()
    return any(lower.endswith(ext) for ext in _ALLOWED_EXTENSIONS)


def _mime_ok(content_type: str | None) -> bool:
    if not content_type:
        return True
    ct = content_type.split(";")[0].strip().lower()
    return any(ct.startswith(p) for p in _ALLOWED_MIME_PREFIXES)


def wav_duration_seconds(audio_bytes: bytes) -> float | None:
    """Parse PCM WAV header for duration; None if not a standard WAV."""
    if len(audio_bytes) < 44 or audio_bytes[:4] != b"RIFF" or audio_bytes[8:12] != b"WAVE":
        return None
    try:
        channels = struct.unpack_from("<H", audio_bytes, 22)[0]
        sample_rate = struct.unpack_from("<I", audio_bytes, 24)[0]
        bits_per_sample = struct.unpack_from("<H", audio_bytes, 34)[0]
        if channels < 1 or sample_rate < 1 or bits_per_sample < 1:
            return None
        data_size = len(audio_bytes) - 44
        for i in range(12, min(len(audio_bytes) - 8, 128)):
            if audio_bytes[i : i + 4] == b"data":
                data_size = struct.unpack_from("<I", audio_bytes, i + 4)[0]
                break
        bytes_per_sec = channels * sample_rate * (bits_per_sample // 8)
        if bytes_per_sec <= 0:
            return None
        return data_size / bytes_per_sec
    except (struct.error, IndexError):
        return None


def wav_pcm_peak(audio_bytes: bytes) -> float | None:
    """Peak normalized amplitude 0..1 from PCM16 WAV; None if header not parsed."""
    if len(audio_bytes) < 44 or audio_bytes[:4] != b"RIFF":
        return None
    data_offset = 44
    data_size = len(audio_bytes) - data_offset
    for i in range(12, min(len(audio_bytes) - 8, 256)):
        if audio_bytes[i : i + 4] == b"data":
            data_offset = i + 8
            data_size = struct.unpack_from("<I", audio_bytes, i + 4)[0]
            break
    if data_size < 2:
        return 0.0
    end = min(len(audio_bytes), data_offset + data_size)
    peak = 0
    for off in range(data_offset, end - 1, 2):
        sample = struct.unpack_from("<h", audio_bytes, off)[0]
        peak = max(peak, abs(sample))
    return peak / 32768.0


def wav_is_unlikely_transcribable(audio_bytes: bytes) -> str | None:
    """Return user-facing reason when FPT Whisper would likely return HTTP 500."""
    duration = wav_duration_seconds(audio_bytes)
    if duration is not None and duration < 0.35:
        return "Ghi âm quá ngắn. Hãy giữ nút mic và nói ít nhất 1 giây."
    peak = wav_pcm_peak(audio_bytes)
    if peak is not None and peak < 0.008:
        return "Không phát hiện giọng nói. Hãy nói rõ hơn, gần microphone hơn."
    return None


class SttService:
    def __init__(
        self,
        client: SttClient | None,
        creds: ResolvedSttCredentials | None,
    ) -> None:
        self._client = client
        self._creds = creds

    @property
    def available(self) -> bool:
        return self._client is not None and self._creds is not None

    @property
    def default_language(self) -> str:
        if self._creds is None:
            return "vi"
        return self._creds.language

    def transcribe(
        self,
        audio_bytes: bytes,
        *,
        filename: str,
        content_type: str | None,
        language: str | None,
    ) -> str:
        if not self.available or self._client is None or self._creds is None:
            raise RuntimeError("STT is not configured.")
        if not _extension_ok(filename) and not _mime_ok(content_type):
            raise ValueError(
                "Định dạng audio không được hỗ trợ. Vui lòng gửi file WAV, MP3 hoặc WebM."
            )
        if len(audio_bytes) > self._creds.max_upload_bytes:
            raise ValueError(
                f"File audio quá lớn (tối đa {self._creds.max_upload_bytes // (1024 * 1024)} MB)."
            )
        duration = wav_duration_seconds(audio_bytes)
        if duration is not None and duration > self._creds.max_audio_seconds:
            raise ValueError(
                f"Ghi âm quá dài (tối đa {self._creds.max_audio_seconds} giây)."
            )
        if duration is None and filename.lower().endswith(".wav"):
            approx_max_bytes = self._creds.max_audio_seconds * 176_400
            if len(audio_bytes) > approx_max_bytes:
                raise ValueError(
                    f"Ghi âm quá dài (tối đa {self._creds.max_audio_seconds} giây)."
                )
        reject = wav_is_unlikely_transcribable(audio_bytes)
        if reject:
            raise ValueError(reject)
        lang = (language or self._creds.language).strip() or "vi"
        return self._client.transcribe(
            audio_bytes,
            filename=filename or "recording.wav",
            language=lang,
        )


@lru_cache(maxsize=1)
def get_stt_service() -> SttService:
    llm = load_llm_settings()
    stt = load_stt_settings()
    creds = resolve_stt_credentials(llm, stt)
    client = build_stt_client(stt, llm)
    return SttService(client, creds)
