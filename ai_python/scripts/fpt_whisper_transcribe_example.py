"""Smoke test FPT Whisper STT (OpenAI-compatible transcriptions API).

    cd ai_python
    set LLM_API_KEY=...
    set LLM_BASE_URL=https://mkp-api.fptcloud.com
    python scripts/fpt_whisper_transcribe_example.py speech.wav
"""

from __future__ import annotations

import os
import sys

try:
    from openai import OpenAI
except ImportError as e:  # pragma: no cover
    raise SystemExit("Install OpenAI SDK: pip install openai") from e


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "speech.wav"
    base_url = (os.getenv("LLM_BASE_URL") or "https://mkp-api.fptcloud.com").rstrip("/")
    api_key = (os.getenv("LLM_API_KEY") or "").strip()
    model = (os.getenv("STT_MODEL") or "FPT.AI-whisper-medium").strip()
    language = (os.getenv("STT_LANGUAGE") or "vi").strip()

    if not api_key:
        print("Missing LLM_API_KEY.", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(path):
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=float(os.getenv("STT_HTTP_TIMEOUT_SECONDS", "45")))
    with open(path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model=model,
            file=(os.path.basename(path), audio_file, "audio/wav"),
            response_format="json",
            language=language,
        )
    print((getattr(response, "text", None) or "").strip())


if __name__ == "__main__":
    main()
