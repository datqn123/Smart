from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.auth import get_jwt_validator
from app.tts.service import TtsService, get_tts_service
from main import app


class _ValidatorBypass:
    def validate_authorization_header(self, authorization: str | None) -> dict:  # noqa: ANN001
        return {"auth_dev_bypass": True}


class _MockTtsService:
    def __init__(self, *, available: bool = True) -> None:
        self._available = available

    @property
    def available(self) -> bool:
        return self._available

    @property
    def default_voice(self) -> str:
        return "std_kimngan"

    def synthesize(self, text: str, *, voice: str | None = None) -> bytes:  # noqa: ARG002
        if not self._available:
            raise RuntimeError("TTS is not configured.")
        return b"RIFF" + b"\x00" * 40


def _client_with_tts(tts: TtsService) -> TestClient:
    app.dependency_overrides[get_jwt_validator] = lambda: _ValidatorBypass()
    app.dependency_overrides[get_tts_service] = lambda: tts
    return TestClient(app)


def test_synthesize_ok() -> None:
    client = _client_with_tts(_MockTtsService())
    res = client.post(
        "/api/v1/ai/chat/synthesize",
        json={"text": "xin chào"},
        headers={"X-Correlation-Id": "cid-tts-1", "Authorization": "Bearer x"},
    )
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("audio/")
    assert len(res.content) > 0
    app.dependency_overrides.clear()


def test_synthesize_unavailable() -> None:
    client = _client_with_tts(_MockTtsService(available=False))
    res = client.post(
        "/api/v1/ai/chat/synthesize",
        json={"text": "xin chào"},
        headers={"X-Correlation-Id": "cid-tts-2", "Authorization": "Bearer x"},
    )
    assert res.status_code == 503
    app.dependency_overrides.clear()
