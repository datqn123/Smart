"""HTTP adapter: Python ``DbReadonlyMcpClient`` → Spring Boot MCP-shaped endpoints."""

from __future__ import annotations

import uuid
from typing import Any

import httpx

from app.contracts.task005 import (
    McpToolError,
    SqlDescribeIn,
    SqlDescribeOut,
    SqlQueryReadonlyIn,
    SqlQueryReadonlyOut,
)
from app.mcp.db_readonly_port import DescribeResult, QueryReadonlyResult


class SpringHttpDbReadonlyClient:
    """Calls ``POST /api/v1/ai/db/sql/describe`` and ``sql/query-readonly`` on smart-erp."""

    def __init__(self, *, base_url: str, timeout_s: float = 30.0) -> None:
        self._http = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout_s,
        )

    async def describe(self, payload: SqlDescribeIn) -> DescribeResult:
        cid = str(uuid.uuid4())
        try:
            r = await self._http.post(
                "/api/v1/ai/db/sql/describe",
                json={"object_name": payload.object_name},
                headers={"X-Correlation-Id": cid},
            )
        except httpx.RequestError as e:
            return _transport_error(e, cid)
        body: dict[str, Any] = _safe_json(r)
        if r.is_success:
            return SqlDescribeOut.model_validate(body)
        return _as_tool_error(body, fallback_cid=cid)

    async def query_readonly(self, payload: SqlQueryReadonlyIn) -> QueryReadonlyResult:
        cid = str(uuid.uuid4())
        try:
            r = await self._http.post(
                "/api/v1/ai/db/sql/query-readonly",
                json={"template_id": payload.template_id, "params": payload.params},
                headers={"X-Correlation-Id": cid},
            )
        except httpx.RequestError as e:
            return _transport_error(e, cid)
        body = _safe_json(r)
        if r.is_success:
            return SqlQueryReadonlyOut.model_validate(body)
        return _as_tool_error(body, fallback_cid=cid)

    async def aclose(self) -> None:
        await self._http.aclose()


def _safe_json(r: httpx.Response) -> dict[str, Any]:
    try:
        data = r.json()
    except ValueError:
        return {
            "code": "HTTP_ERROR",
            "message": r.text[:2000] if r.text else r.reason_phrase,
            "retryable": False,
            "correlation_id": str(uuid.uuid4()),
        }
    if isinstance(data, dict):
        return data
    return {
        "code": "BAD_RESPONSE",
        "message": "Response JSON was not an object",
        "retryable": False,
        "correlation_id": str(uuid.uuid4()),
    }


def _transport_error(exc: httpx.RequestError, cid: str) -> McpToolError:
    return McpToolError(
        code="DB_UPSTREAM_ERROR",
        message=f"Không kết nối được Spring db-readonly: {exc}",
        retryable=True,
        details=None,
        correlation_id=cid,
    )


def _as_tool_error(body: dict[str, Any], *, fallback_cid: str) -> McpToolError:
    try:
        return McpToolError.model_validate(body)
    except ValueError:
        return McpToolError(
            code=str(body.get("code") or "HTTP_ERROR"),
            message=str(body.get("message") or "Spring db-readonly call failed"),
            retryable=bool(body.get("retryable", False)),
            details=None,
            correlation_id=str(body.get("correlation_id") or fallback_cid),
        )
