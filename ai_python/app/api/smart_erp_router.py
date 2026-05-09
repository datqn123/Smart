from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..smart_erp_mcp.turn import run_smart_erp_turn

router = APIRouter(prefix="/v1/smart-erp", tags=["smart-erp"])


class SmartErpTurnIn(BaseModel):
    user_text: str = Field(min_length=1, max_length=4000)
    session_id: str = Field(default="", max_length=256)
    sql: str | None = Field(default=None, max_length=4000)


@router.post("/turn")
async def smart_erp_turn(body: SmartErpTurnIn) -> dict[str, Any]:
    """
    Một lượt: ``intent_analyze`` (MCP) → tool(s) theo intent (demo routing).

    - ``SMART_ERP_MCP_STDIO=1``: spawn MCP stdio ``python -m app.smart_erp_mcp`` (kết nối thật).
    - Mặc định / ``SMART_ERP_MCP_INLINE=1``: in-process (nhanh, dùng cho test/CI).
    """
    return await run_smart_erp_turn(body.user_text, body.session_id, body.sql)
