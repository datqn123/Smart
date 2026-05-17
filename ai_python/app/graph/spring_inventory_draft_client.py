"""POST inventory draft to Spring (Bearer from chat relay)."""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import httpx

from app.config.graph_settings import GraphSettings


def inventory_drafts_url(settings: GraphSettings) -> str:
    base = (settings.spring_api_base_url or "http://127.0.0.1:8080").rstrip("/")
    return urljoin(base + "/", "api/v1/ai/inventory-drafts")


def post_inventory_draft(
    settings: GraphSettings,
    *,
    bearer_token: str | None,
    entity_type: str,
    header: dict[str, Any],
    line_columns: list[dict[str, Any]],
    lines: list[dict[str, Any]],
    conversation_id: str | None,
    meta: dict[str, Any] | None = None,
    timeout_seconds: float = 15.0,
) -> dict[str, Any]:
    url = inventory_drafts_url(settings)
    headers: dict[str, str] = {"Content-Type": "application/json"}
    token = (bearer_token or settings.spring_sql_bearer_token or "").strip()
    if token:
        if not token.lower().startswith("bearer "):
            token = f"Bearer {token}"
        headers["Authorization"] = token
    body: dict[str, Any] = {
        "entityType": entity_type,
        "header": header,
        "lineColumns": line_columns,
        "lines": lines,
    }
    if conversation_id:
        body["conversationId"] = conversation_id
    if meta:
        body["meta"] = meta
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            resp = client.post(url, json=body, headers=headers)
    except httpx.TimeoutException as exc:
        raise RuntimeError("Spring inventory-drafts timeout") from exc
    except httpx.TransportError as exc:
        raise RuntimeError(f"Spring inventory-drafts transport error: {exc}") from exc
    if resp.status_code >= 400:
        detail = resp.text[:500] if resp.text else resp.status_code
        raise RuntimeError(f"Spring inventory-drafts HTTP {resp.status_code}: {detail}")
    data = resp.json()
    if not isinstance(data, dict):
        raise RuntimeError("Spring inventory-drafts response is not JSON object")
    inner = data.get("data")
    if isinstance(inner, dict):
        return inner
    return data


def validate_inventory_draft_references(
    settings: GraphSettings,
    *,
    bearer_token: str | None,
    entity_type: str,
    header: dict[str, Any],
    line_columns: list[dict[str, Any]],
    lines: list[dict[str, Any]],
    timeout_seconds: float = 15.0,
) -> list[str]:
    """POST /validate — returns issue messages; empty list when all FKs resolve."""
    url = urljoin(inventory_drafts_url(settings).rstrip("/") + "/", "validate")
    headers: dict[str, str] = {"Content-Type": "application/json"}
    token = (bearer_token or settings.spring_sql_bearer_token or "").strip()
    if token:
        if not token.lower().startswith("bearer "):
            token = f"Bearer {token}"
        headers["Authorization"] = token
    body = {
        "entityType": entity_type,
        "header": header,
        "lineColumns": line_columns,
        "lines": lines,
    }
    with httpx.Client(timeout=timeout_seconds) as client:
        resp = client.post(url, json=body, headers=headers)
    if resp.status_code >= 400:
        detail = resp.text[:500] if resp.text else resp.status_code
        raise RuntimeError(f"Spring inventory-drafts/validate HTTP {resp.status_code}: {detail}")
    data = resp.json()
    if not isinstance(data, dict):
        raise RuntimeError("validate response is not JSON object")
    inner = data.get("data")
    payload = inner if isinstance(inner, dict) else data
    if payload.get("ok") is True:
        return []
    issues = payload.get("issues")
    if isinstance(issues, list):
        return [str(x) for x in issues if x]
    return ["Không xác minh được tham chiếu phiếu kho."]
