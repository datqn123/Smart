from collections.abc import Iterator

from app.integrations.mkp.client import get_mkp_client


def stream_chat_deltas(prompt: str) -> Iterator[str]:
    """Yield delta text chunks from MKP (OpenAI-compatible Chat Completions, stream=True)."""
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
