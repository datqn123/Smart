from __future__ import annotations

import struct

from app.stt.service import wav_is_unlikely_transcribable, wav_pcm_peak


def _pcm16_wav(*, seconds: float, peak: float, sample_rate: int = 16_000) -> bytes:
    import math

    n = max(1, int(sample_rate * seconds))
    samples = [int(32767 * peak * math.sin(2 * math.pi * 440 * i / sample_rate)) for i in range(n)]
    data = b"".join(struct.pack("<h", s) for s in samples)
    return (
        struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            36 + len(data),
            b"WAVE",
            b"fmt ",
            16,
            1,
            1,
            sample_rate,
            sample_rate * 2,
            2,
            16,
            b"data",
            len(data),
        )
        + data
    )


def test_silent_wav_rejected() -> None:
    wav = _pcm16_wav(seconds=1.0, peak=0.0)
    assert wav_pcm_peak(wav) == 0.0
    assert wav_is_unlikely_transcribable(wav) is not None


def test_short_wav_rejected() -> None:
    wav = _pcm16_wav(seconds=0.2, peak=0.5)
    assert wav_is_unlikely_transcribable(wav) is not None


def test_normal_wav_accepted() -> None:
    wav = _pcm16_wav(seconds=1.0, peak=0.3)
    assert wav_is_unlikely_transcribable(wav) is None
