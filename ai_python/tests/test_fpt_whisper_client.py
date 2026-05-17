from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.config.settings import ResolvedSttCredentials
from app.stt.fpt_whisper import FptWhisperClient


def test_fpt_whisper_transcribe_returns_text() -> None:
    creds = ResolvedSttCredentials(
        base_url="https://mkp-api.fptcloud.com",
        api_key="k",
        model="FPT.AI-whisper-medium",
        language="vi",
        response_format="json",
        http_timeout_seconds=45.0,
        max_upload_bytes=10_485_760,
        max_audio_seconds=60,
    )
    mock_response = MagicMock()
    mock_response.text = "  xin chào  "
    mock_create = MagicMock(return_value=mock_response)

    with patch("app.stt.fpt_whisper.OpenAI") as mock_openai:
        mock_openai.return_value.audio.transcriptions.create = mock_create
        client = FptWhisperClient(creds)
        out = client.transcribe(b"wav-bytes", filename="a.wav", language="vi")

    assert out == "xin chào"
    mock_create.assert_called_once()
    call_kw = mock_create.call_args.kwargs
    assert call_kw["model"] == "FPT.AI-whisper-medium"
    assert call_kw["language"] == "vi"
    assert call_kw["file"] == b"wav-bytes"
