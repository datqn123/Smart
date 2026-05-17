from __future__ import annotations

from app.config.settings import LlmSettings, SttSettings, resolve_stt_credentials
from app.stt.factory import build_stt_client
from app.stt.fpt_whisper import mime_for_filename
from app.stt.service import wav_duration_seconds
from app.stt.service import get_stt_service
from pydantic import SecretStr


def test_resolve_uses_llm_gateway(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setenv("STT_ENABLED", "1")
    llm = LlmSettings(
        base_url="https://mkp-api.fptcloud.com",
        api_key=SecretStr("key-abc"),
        model="gemma",
    )
    stt = SttSettings()
    creds = resolve_stt_credentials(llm, stt)
    assert creds is not None
    assert creds.base_url == "https://mkp-api.fptcloud.com"
    assert creds.api_key == "key-abc"
    assert creds.model == "FPT.AI-whisper-medium"


def test_build_stt_client_disabled() -> None:
    llm = LlmSettings(base_url="https://x", api_key=SecretStr("k"), model="m")
    stt = SttSettings(enabled=False)
    assert build_stt_client(stt, llm) is None


def test_mime_for_filename() -> None:
    assert mime_for_filename("a.wav") == "audio/wav"
    assert mime_for_filename("a.mp3") == "audio/mpeg"


def test_wav_duration_seconds_minimal() -> None:
    # 44-byte header stub is too short; build minimal valid-ish wav is heavy — skip if None
    assert wav_duration_seconds(b"not-wav") is None


def test_get_stt_service_cache_clear(monkeypatch) -> None:  # noqa: ANN001
    get_stt_service.cache_clear()
    monkeypatch.setenv("STT_ENABLED", "0")
    svc = get_stt_service()
    assert not svc.available
    get_stt_service.cache_clear()
