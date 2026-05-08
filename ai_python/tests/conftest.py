import pytest


@pytest.fixture(autouse=True)
def _task003_deterministic_synth(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid real MKP during tests — async stream is resolved at call time."""

    async def fake_stream(_prompt: str):
        yield "[SYNTH_STUB]"

    monkeypatch.delenv("TASK003_SYNTH_STUB", raising=False)
    monkeypatch.setattr("app.mkp_async.stream_chat_deltas_async", fake_stream)
