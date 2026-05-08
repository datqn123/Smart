from collections.abc import Iterator
from unittest.mock import MagicMock, patch

from app.integrations.mkp.streaming import stream_chat_deltas


def fake_chunk(content: str | None):
    delta = MagicMock()
    delta.content = content
    choice = MagicMock()
    choice.delta = delta
    chunk = MagicMock()
    chunk.choices = [choice]
    return chunk


def test_stream_chat_deltas_yields_text_from_mock_chunks() -> None:
    def fake_stream(*_args: object, **_kwargs: object) -> Iterator[object]:
        yield fake_chunk("hel")
        yield fake_chunk("")
        yield fake_chunk("lo")

    fake_client = MagicMock()
    fake_client.chat.completions.create.side_effect = fake_stream

    with patch(
        "app.integrations.mkp.streaming.get_mkp_client",
        return_value=(fake_client, "stub-model"),
    ):
        deltas = list(stream_chat_deltas("hi"))

    assert deltas == ["hel", "lo"]
    fake_client.chat.completions.create.assert_called_once()
