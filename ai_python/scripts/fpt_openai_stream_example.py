"""Minimal FPT OpenAI-compatible streaming example (same stack as mini-erp / LangGraph).

Uses ``LLM_MODEL`` (default ``gemma-4-31B-it``), not Qwen3.6-27B.
Set ``LLM_API_KEY`` (and optionally ``LLM_BASE_URL``) — e.g. from ``ai_python/.env``.

Run from repo root or ``ai_python``:

    cd ai_python
    set LLM_API_KEY=...   # Windows
    python scripts/fpt_openai_stream_example.py
"""

from __future__ import annotations

import os
import sys

try:
    from openai import OpenAI
except ImportError as e:  # pragma: no cover
    raise SystemExit("Install OpenAI SDK: pip install openai") from e


def main() -> None:
    base_url = (os.getenv("LLM_BASE_URL") or "https://mkp-api.fptcloud.com").rstrip("/")
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model_name = (os.getenv("LLM_MODEL") or "gemma-4-31B-it").strip()

    if not api_key:
        print("Missing LLM_API_KEY in environment.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=base_url)

    extra: dict = {}
    if os.getenv("LLM_SEND_TOP_K", "").strip() in ("1", "true", "True", "yes"):
        extra["top_k"] = int(os.getenv("LLM_TOP_K", "40"))

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": "Can you tell me about the creation of black holes?",
            }
        ],
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1024")),
        top_p=float(os.getenv("LLM_TOP_P", "1")),
        presence_penalty=0,
        frequency_penalty=0,
        stream=True,
        **extra,
    )

    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()


if __name__ == "__main__":
    main()
