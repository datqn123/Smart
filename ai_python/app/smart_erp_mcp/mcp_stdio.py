from __future__ import annotations

import json
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, cast

import mcp.types as mcp_types
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


def ai_python_root() -> Path:
    """Directory containing the ``app`` package (``ai_python/``)."""
    return Path(__file__).resolve().parent.parent.parent


def stdio_server_params() -> StdioServerParameters:
    cmd = os.getenv("SMART_ERP_MCP_COMMAND") or sys.executable
    extra = os.getenv("SMART_ERP_MCP_ARGS")
    args = extra.split() if extra else ["-m", "app.smart_erp_mcp"]
    env = dict(os.environ)
    root = str(ai_python_root())
    pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{root}{os.pathsep}{pp}" if pp else root
    env.setdefault("PYTHONUTF8", "1")
    return StdioServerParameters(
        command=cmd,
        args=args,
        env=env,
    )


def parse_call_tool_result(result: mcp_types.CallToolResult) -> dict[str, Any]:
    if result.isError:
        texts = [c.text for c in result.content if isinstance(c, mcp_types.TextContent)]
        return {"ok": False, "error": {"message": "mcp_tool_error", "details": texts}}
    for c in result.content:
        if isinstance(c, mcp_types.TextContent):
            return cast(dict[str, Any], json.loads(c.text))
    return {"ok": False, "error": {"message": "no_text_content"}}


@asynccontextmanager
async def mcp_client_session() -> AsyncIterator[ClientSession]:
    params = stdio_server_params()
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        yield session


async def call_tool_stdio(
    session: ClientSession, name: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    raw = await session.call_tool(name, arguments)
    return parse_call_tool_result(raw)
