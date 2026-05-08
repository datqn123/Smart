"""Async MKP chat streaming (OpenAI-compatible) per ADR async I/O mandate."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

from openai import AsyncOpenAI


def _env(name: str, default: str | None = None) -> str:
    v = os.getenv(name, default)
    if v is None or v.strip() == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return v


def build_async_openai() -> tuple[AsyncOpenAI, str]:
    api_key = _env("FPT_MKP_API_KEY")
    base_url = os.getenv("FPT_MKP_BASE_URL", "https://mkp-api.fptcloud.com").rstrip("/")
    model = os.getenv("FPT_MKP_MODEL", "gemma-4-31B-it")
    return AsyncOpenAI(api_key=api_key, base_url=base_url), model


async def stream_chat_deltas_async(prompt: str) -> AsyncIterator[str]:
    client, model = build_async_openai()
    stream = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1024,
        top_p=1,
        stream=True,
    )
    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta is None:
            continue
        content = getattr(delta, "content", None)
        if content:
            yield content
