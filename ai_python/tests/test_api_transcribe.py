from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.auth import get_jwt_validator
from app.stt.service import SttService, get_stt_service
from main import app


class _ValidatorBypass:
    def validate_authorization_header(self, authorization: str | None) -> dict:  # noqa: ANN001
        return {"auth_dev_bypass": True}


class _MockSttService:
    def __init__(self, *, available: bool = True, transcript: str = "xin chào") -> None:
        self._available = available
        self._transcript = transcript

    @property
    def available(self) -> bool:
        return self._available

    @property
    def default_language(self) -> str:
        return "vi"

    def transcribe(self, audio_bytes: bytes, *, filename: str, content_type: str | None, language: str | None) -> str:  # noqa: ARG002
        if not self._available:
            raise RuntimeError("STT is not configured.")
        return self._transcript


def _client_with_stt(stt: SttService) -> TestClient:
    app.dependency_overrides[get_jwt_validator] = lambda: _ValidatorBypass()
    app.dependency_overrides[get_stt_service] = lambda: stt
    return TestClient(app)


def test_transcribe_ok() -> None:
    client = _client_with_stt(_MockSttService())
    wav = b"RIFF" + b"\x00" * 40  # invalid but passes size checks
    res = client.post(
        "/api/v1/ai/chat/transcribe",
        files={"file": ("recording.wav", wav, "audio/wav")},
        data={"language": "vi"},
        headers={"X-Correlation-Id": "cid-1", "Authorization": "Bearer x"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["correlation_id"] == "cid-1"
    assert body["transcript"] == "xin chào"
    app.dependency_overrides.clear()


def test_transcribe_stt_unavailable() -> None:
    client = _client_with_stt(_MockSttService(available=False))
    res = client.post(
        "/api/v1/ai/chat/transcribe",
        files={"file": ("recording.wav", b"data", "audio/wav")},
        headers={"X-Correlation-Id": "cid-2", "Authorization": "Bearer x"},
    )
    assert res.status_code == 503
    app.dependency_overrides.clear()
