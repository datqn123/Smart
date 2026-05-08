import os
from collections.abc import Iterator

from openai import OpenAI


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_mkp_client() -> tuple[OpenAI, str]:
    api_key = _get_required_env("FPT_MKP_API_KEY")
    base_url = os.getenv("FPT_MKP_BASE_URL", "https://mkp-api.fptcloud.com").rstrip("/")
    model = os.getenv("FPT_MKP_MODEL", "gemma-4-31B-it")
    return OpenAI(api_key=api_key, base_url=base_url), model


def stream_chat_deltas(prompt: str) -> Iterator[str]:
    """
    Yield delta text chunks from MKP (OpenAI-compatible Chat Completions, stream=True).
    """
    client, model = get_mkp_client()
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta is None:
            continue
        content = getattr(delta, "content", None)
        if content:
            yield content

