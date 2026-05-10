"""SqlExecutor port — Option C (stub | python_ro | http_spring)."""

from __future__ import annotations

import logging
from typing import Any, Protocol

from app.config.graph_settings import GraphSettings

logger = logging.getLogger(__name__)


class SqlExecutor(Protocol):
    def execute(self, sql: str, *, tenant_id: str | None) -> dict[str, Any]:
        """Return {'rows': [...], 'meta': {...}} or raise."""
        ...


class StubSqlExecutor:
    """Deterministic CI / unit tests."""

    def execute(self, sql: str, *, tenant_id: str | None) -> dict[str, Any]:
        return {"rows": [{"_stub": 1, "sql_ok": True}], "meta": {"mode": "stub"}}


class PythonRoSqlExecutor:
    """Optional read-only DB — requires DATABASE_URL_RO."""

    def __init__(self, url: str) -> None:
        self._url = url

    def execute(self, sql: str, *, tenant_id: str | None) -> dict[str, Any]:
        raise NotImplementedError(
            "python_ro executor: install sqlalchemy/psycopg and implement pool — Task 2 ships stub only.",
        )


class HttpSpringSqlExecutor:
    """Delegate to Spring — requires SPRING_SQL_URL + contract Task 3."""

    def __init__(self, url: str) -> None:
        self._url = url

    def execute(self, sql: str, *, tenant_id: str | None) -> dict[str, Any]:
        raise NotImplementedError(
            "http_spring executor: wire httpx client when Spring endpoint exists (Task 3).",
        )


def build_sql_executor(settings: GraphSettings) -> SqlExecutor:
    mode = settings.sql_executor_mode
    if mode == "stub":
        return StubSqlExecutor()
    if mode == "python_ro":
        if not settings.database_url_ro:
            raise ValueError("DATABASE_URL_RO required when SQL_EXECUTOR_MODE=python_ro")
        return PythonRoSqlExecutor(settings.database_url_ro)
    if mode == "http_spring":
        if not settings.spring_sql_url:
            raise ValueError("SPRING_SQL_URL required when SQL_EXECUTOR_MODE=http_spring")
        return HttpSpringSqlExecutor(settings.spring_sql_url)
    raise ValueError(f"Unknown SQL_EXECUTOR_MODE: {mode}")
