"""HTTP client for Spring AiDbReadonlyController /sql/describe."""

from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urlparse, urlunparse

import httpx

from app.config.graph_settings import GraphSettings

logger = logging.getLogger(__name__)


class SpringDescribeError(RuntimeError):
    pass


def derive_spring_describe_url(spring_sql_url: str | None) -> str | None:
    """Map .../sql/query-readonly-raw → .../sql/describe."""
    if not spring_sql_url or not str(spring_sql_url).strip():
        return None
    raw = str(spring_sql_url).strip().rstrip("/")
    if raw.endswith("/sql/describe"):
        return raw
    if raw.endswith("/sql/query-readonly-raw"):
        return raw[: -len("/sql/query-readonly-raw")] + "/sql/describe"
    if raw.endswith("/sql/query-readonly"):
        return raw[: -len("/sql/query-readonly")] + "/sql/describe"
    parsed = urlparse(raw)
    path = parsed.path.rstrip("/")
    if path.endswith("/api/v1/ai/db"):
        new_path = path + "/sql/describe"
    else:
        new_path = path + "/sql/describe" if "/sql/" not in path else path.rsplit("/sql/", 1)[0] + "/sql/describe"
    return urlunparse(parsed._replace(path=new_path))


class SpringDescribeClient:
    def __init__(
        self,
        settings: GraphSettings,
        *,
        client: httpx.Client | None = None,
    ) -> None:
        url = derive_spring_describe_url(settings.spring_sql_url)
        if not url:
            raise ValueError("SPRING_SQL_URL required to derive describe endpoint")
        self._url = url
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

    def describe(
        self,
        object_name: str,
        *,
        correlation_id: str | None = None,
        bearer_token: str | None = None,
    ) -> dict[str, Any]:
        payload = {"object_name": object_name.strip()}
        req_headers: dict[str, str] = {}
        if bearer_token and bearer_token.strip():
            req_headers["Authorization"] = f"Bearer {bearer_token.strip()}"
        elif self._settings.spring_sql_bearer_token:
            req_headers["Authorization"] = f"Bearer {self._settings.spring_sql_bearer_token.strip()}"
        if correlation_id and correlation_id.strip():
            req_headers["X-Correlation-Id"] = correlation_id.strip()
        started = time.perf_counter()
        try:
            resp = self._client.post(self._url, json=payload, headers=req_headers)
        except httpx.TimeoutException as exc:
            raise SpringDescribeError("[timeout] spring describe timed out") from exc
        except httpx.RequestError as exc:
            raise SpringDescribeError("[transport] spring describe request failed") from exc
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        if resp.status_code >= 400:
            logger.warning("spring describe failure status=%s duration_ms=%s", resp.status_code, elapsed_ms)
            raise SpringDescribeError(f"spring describe HTTP {resp.status_code}")
        try:
            data = resp.json()
        except ValueError as exc:
            raise SpringDescribeError("[malformed] describe response is not JSON") from exc
        if not isinstance(data, dict):
            raise SpringDescribeError("[malformed] describe response must be object")
        err = data.get("error")
        if err:
            raise SpringDescribeError(str(err))
        return data


def build_spring_describe_client(settings: GraphSettings) -> SpringDescribeClient | None:
    if settings.sql_executor_mode != "http_spring":
        return None
    if not derive_spring_describe_url(settings.spring_sql_url):
        return None
    return SpringDescribeClient(settings)
