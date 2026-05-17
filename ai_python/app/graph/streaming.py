"""Stream / events helpers (TASK-LG-13)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

def iter_graph_stream(
    compiled: Any,
    state: dict[str, Any],
    *,
    config: dict[str, Any] | None = None,
    correlation_id: str | None = None,
    stream_mode: str | list[str] | None = None,
) -> Iterator[dict[str, Any] | Any]:
    """Sync iterator: ``updates`` + ``custom`` (progress at node entry via stream writer)."""
    cfg = dict(config or {})
    modes: list[str] = (
        list(stream_mode)
        if isinstance(stream_mode, list)
        else [stream_mode or "updates", "custom"]
    )
    if "updates" not in modes:
        modes.insert(0, "updates")
    if "custom" not in modes:
        modes.append("custom")
    _ = correlation_id  # caller sets ContextVar at SSE boundary (routes)
    yield from compiled.stream(state, cfg, stream_mode=modes)
