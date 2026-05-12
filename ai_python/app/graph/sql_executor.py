"""SqlExecutor port — stub | http_spring (Phase 1); python_ro deferred."""

from __future__ import annotations

import logging
import time
from typing import Any, Protocol

import httpx

from app.config.graph_settings import GraphSettings
from app.graph.sql_safety import enforce_read_only_sql

logger = logging.getLogger(__name__)


class SqlExecutor(Protocol):
    def execute(
        self,
        sql: str,
        *,
        tenant_id: str | None,
        correlation_id: str | None = None,
        schema_version: str | None = None,
    ) -> dict[str, Any]:
        """Return {'rows': [...], 'meta': {...}} or raise."""
        ...


class SqlExecutorError(RuntimeError):
    """Upstream / transport failure mapped for graph feedback (no secrets)."""

    def __init__(self, message: str, *, category: str = "exec") -> None:
        self.category = category
        super().__init__(message)


class StubSqlExecutor:
    """Deterministic CI / unit tests."""

    def execute(
        self,
        sql: str,
        *,
        tenant_id: str | None,
        correlation_id: str | None = None,
        schema_version: str | None = None,
    ) -> dict[str, Any]:
        _ = tenant_id, correlation_id, schema_version
        return {"rows": [{"_stub": 1, "sql_ok": True}], "meta": {"mode": "stub"}}


class HttpSpringSqlExecutor:
    """Delegate read-only SQL execution to Spring via HTTP."""

    def __init__(
        self,
        settings: GraphSettings,
        *,
        client: httpx.Client | None = None,
    ) -> None:
        url = settings.spring_sql_url
        if not url:
            raise ValueError("SPRING_SQL_URL required when SQL_EXECUTOR_MODE=http_spring")
        self._url = url.rstrip("/")
        self._settings = settings
        timeout = float(settings.sql_executor_timeout_seconds)
        self._timeout = httpx.Timeout(timeout, connect=min(5.0, timeout))
        headers: dict[str, str] = {"Content-Type": "application/json"}
        token = settings.spring_sql_bearer_token
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=self._timeout, headers=headers)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def execute(
        self,
        sql: str,
        *,
        tenant_id: str | None,
        correlation_id: str | None = None,
        schema_version: str | None = None,
    ) -> dict[str, Any]:
        enforce_read_only_sql(sql)
        row_cap = self._settings.sql_executor_row_limit
        # Wire shape matches Spring `SqlQueryReadonlyRawHttpRequest` (see `AiDbReadonlyController`).
        payload: dict[str, Any] = {
            "query": sql,
            "max_rows": row_cap,
        }
        started = time.perf_counter()
        req_headers: dict[str, str] = {}
        if correlation_id and correlation_id.strip():
            req_headers["X-Correlation-Id"] = correlation_id.strip()
        try:
            resp = self._client.post(self._url, json=payload, headers=req_headers)
        except httpx.TimeoutException as exc:
            logger.warning(
                "http_spring timeout mode=http_spring correlation_id=%s",
                correlation_id or "-",
            )
            raise SqlExecutorError(
                "[timeout] spring sql execution timed out",
                category="timeout",
            ) from exc
        except httpx.RequestError as exc:
            logger.warning(
                "http_spring transport mode=http_spring correlation_id=%s",
                correlation_id or "-",
            )
            raise SqlExecutorError(
                "[transport] spring sql request failed",
                category="transport",
            ) from exc

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        if resp.status_code >= 400:
            body = _safe_parse_json(resp)
            msg = _failure_message(body) or f"spring returned HTTP {resp.status_code}"
            logger.warning(
                "http_spring upstream_failure status=%s category=%s correlation_id=%s duration_ms=%s",
                resp.status_code,
                _failure_category(body),
                correlation_id or "-",
                elapsed_ms,
            )
            raise SqlExecutorError(msg, category=_failure_category(body))

        data = _safe_parse_json(resp)
        if not isinstance(data, dict):
            raise SqlExecutorError("[malformed] spring response is not a JSON object")

        err_obj = data.get("error")
        if err_obj:
            msg = _failure_message(data) or "spring execution rejected"
            logger.warning(
                "http_spring policy_failure correlation_id=%s duration_ms=%s",
                correlation_id or "-",
                elapsed_ms,
            )
            raise SqlExecutorError(msg, category=_failure_category(data))

        rows_out = _spring_rows_as_dicts(data)[:row_cap]
        row_count = data.get("row_count")
        if row_count is None:
            row_count = len(rows_out)
        elif isinstance(row_count, int) and row_count > len(rows_out):
            row_count = len(rows_out)

        meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
        execution_ms = data.get("execution_ms", elapsed_ms)
        meta = {
            **meta,
            "mode": "http_spring",
            "execution_ms": execution_ms,
            "row_count": row_count,
            "columns": data.get("columns"),
            "summary": data.get("summary"),
            "spring_correlation_id": data.get("correlation_id"),
            "client_duration_ms": elapsed_ms,
        }
        logger.info(
            "http_spring ok correlation_id=%s duration_ms=%s row_count=%s",
            correlation_id or "-",
            elapsed_ms,
            row_count,
        )
        return {"rows": rows_out, "meta": meta}


def _spring_rows_as_dicts(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Spring `SqlQueryReadonlyHttpResponse` uses matrix rows; graph expects row dicts."""
    cols_raw = data.get("columns") or []
    names: list[str] = []
    for c in cols_raw:
        if isinstance(c, dict) and c.get("name") is not None:
            names.append(str(c["name"]))
        elif isinstance(c, str):
            names.append(c)
    raw_rows = data.get("rows")
    if raw_rows is None:
        return []
    if not isinstance(raw_rows, list):
        raise SqlExecutorError("[malformed] spring rows must be a list")
    if not raw_rows:
        return []
    if isinstance(raw_rows[0], dict):
        return raw_rows  # already object rows (SRS-style)
    out: list[dict[str, Any]] = []
    for row in raw_rows:
        if not isinstance(row, list):
            raise SqlExecutorError("[malformed] spring matrix row must be a list")
        d: dict[str, Any] = {}
        for i, name in enumerate(names):
            if i < len(row):
                d[name] = row[i]
        out.append(d)
    return out


def _safe_parse_json(resp: httpx.Response) -> Any:
    try:
        return resp.json()
    except ValueError:
        return None


def _failure_message(body: Any) -> str | None:
    if not isinstance(body, dict):
        return None
    err = body.get("error")
    if isinstance(err, dict):
        code = err.get("code") or "ERROR"
        msg = err.get("message") or "upstream error"
        cat = err.get("category") or "upstream"
        return f"[{cat}] {code}: {msg}"
    if isinstance(err, str):
        return err
    code = body.get("code")
    msg = body.get("message")
    if isinstance(code, str) and isinstance(msg, str):
        return f"{code}: {msg}"
    return None


def _failure_category(body: Any) -> str:
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict) and isinstance(err.get("category"), str):
            return str(err["category"])
        code = body.get("code")
        if isinstance(code, str) and code.startswith("DB_"):
            return "policy"
    return "upstream"


def build_sql_executor(settings: GraphSettings) -> SqlExecutor:
    mode = settings.sql_executor_mode
    if mode == "stub":
        logger.info(
            "SQL_EXECUTOR_MODE=stub: results are synthetic. "
            "Use http_spring + SPRING_SQL_URL for Spring smart-erp read-only SQL."
        )
        return StubSqlExecutor()
    if mode == "python_ro":
        raise ValueError(
            "SQL_EXECUTOR_MODE=python_ro is deferred (post–Task006 Phase 1). "
            "Use stub for dev/test or http_spring for production delegation to Spring.",
        )
    if mode == "http_spring":
        if not settings.spring_sql_url:
            raise ValueError("SPRING_SQL_URL required when SQL_EXECUTOR_MODE=http_spring")
        return HttpSpringSqlExecutor(settings)
    raise ValueError(f"Unknown SQL_EXECUTOR_MODE: {mode}")
