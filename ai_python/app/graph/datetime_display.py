"""Normalize timestamp strings in SQL payloads for user-facing prompts (UTC → display TZ)."""

from __future__ import annotations

import copy
import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger(__name__)


def _try_parse_offset_aware_instant(s: str) -> datetime | None:
    raw = s.strip()
    if len(raw) < 19:
        return None
    candidate = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
    try:
        dt = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return None
    return dt


def _format_local(dt: datetime) -> str:
    return dt.strftime("%d/%m/%Y %H:%M:%S")


def localize_value_tree(obj: Any, tz: ZoneInfo) -> Any:
    """Deep-copy tree and replace offset-aware ISO-8601 strings with local wall time in ``tz``."""
    if isinstance(obj, dict):
        return {k: localize_value_tree(v, tz) for k, v in obj.items()}
    if isinstance(obj, list):
        return [localize_value_tree(x, tz) for x in obj]
    if isinstance(obj, str):
        dt = _try_parse_offset_aware_instant(obj)
        if dt is None:
            return obj
        return _format_local(dt.astimezone(tz))
    return obj


def localize_query_result_for_display(payload: Any, tz_name: str | None) -> Any:
    """Return a copy of ``payload`` with timestamp strings localized, or ``payload`` if disabled / invalid tz."""
    if not tz_name or not str(tz_name).strip():
        return payload
    name = str(tz_name).strip()
    try:
        tz = ZoneInfo(name)
    except ZoneInfoNotFoundError:
        logger.warning("ai_display_timezone invalid %r — skipping localization.", name)
        return payload
    return localize_value_tree(copy.deepcopy(payload), tz)
