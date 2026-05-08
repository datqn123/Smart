from collections.abc import Iterator

from app.integrations.mkp.streaming import stream_chat_deltas


def stream_chat_tool(prompt: str) -> Iterator[str]:
    yield from stream_chat_deltas(prompt)
