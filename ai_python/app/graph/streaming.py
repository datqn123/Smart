"""Stream / events helpers (TASK-LG-13)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from app.graph.correlation import correlation_scope


def iter_graph_stream(
    compiled: Any,
    state: dict[str, Any],
    *,
    config: dict[str, Any] | None = None,
    correlation_id: str | None = None,
    stream_mode: str = "updates",
) -> Iterator[dict[str, Any] | Any]:
    """Sync iterator over graph stream (``stream_mode`` mặc định ``updates``)."""
    cfg = dict(config or {})
    with correlation_scope(correlation_id):
        yield from compiled.stream(state, cfg, stream_mode=stream_mode)
