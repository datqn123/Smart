"""In-memory semantic cache for deterministic harness tool outputs."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from typing import Any


DETERMINISTIC_TOOLS = {"sql_query", "schema_explore"}


class InMemorySemanticCache:
    def __init__(self) -> None:
        self._values: dict[str, Any] = {}
        self.last_event = "cache_miss"

    def is_cacheable(self, tool_name: str) -> bool:
        return tool_name in DETERMINISTIC_TOOLS

    def get(self, tool_name: str, args: dict[str, Any], tenant_id: str | None) -> Any | None:
        if not self.is_cacheable(tool_name):
            self.last_event = "cache_miss"
            return None
        key = self._key(tool_name, args, tenant_id)
        if key not in self._values:
            self.last_event = "cache_miss"
            return None
        self.last_event = "cache_hit"
        return self._values[key]

    def put(self, tool_name: str, args: dict[str, Any], tenant_id: str | None, value: Any) -> None:
        if not self.is_cacheable(tool_name):
            return
        self._values[self._key(tool_name, args, tenant_id)] = value

    def get_or_set(
        self,
        tool_name: str,
        args: dict[str, Any],
        tenant_id: str | None,
        factory: Callable[[], Any],
    ) -> Any:
        cached = self.get(tool_name, args, tenant_id)
        if self.last_event == "cache_hit":
            return cached
        value = factory()
        self.put(tool_name, args, tenant_id, value)
        return value

    @staticmethod
    def _key(tool_name: str, args: dict[str, Any], tenant_id: str | None) -> str:
        raw = json.dumps(
            {"tool": tool_name, "args": args, "tenant_id": tenant_id},
            sort_keys=True,
            ensure_ascii=False,
            default=str,
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
