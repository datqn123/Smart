"""One chat turn: lightweight intent + local RAG retrieve + optional Spring db-readonly."""

from __future__ import annotations

import asyncio
import os
import re
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from app.contracts.task005 import McpToolError, SqlQueryReadonlyOut, SqlQueryReadonlyIn
from app.mkp_client import stream_chat_deltas
from app.mcp.db_readonly_port import DbReadonlyMcpClient, McpTransportError
from app.mcp.spring_http_client import SpringHttpDbReadonlyClient
from app.mcp.task005_client_factory import build_db_readonly_client_from_env
from app.mcp.task005_unconfigured_client import UnconfiguredDbReadonlyClient
from app.rag.task005_ingest import RagChunk, read_chunks
from app.smart_erp_mcp.chat_reply import format_turn_as_chat_text
from app.tools.task005_corpus_fs import (
    DEFAULT_CORPUS_ROOT,
    HEALTH_NAMESPACE,
    SCHEMA_NAMESPACE,
)


def build_chat_db_client() -> DbReadonlyMcpClient:
    """Prefer ``SPRING_AI_DB_BASE_URL``, then ``TASK005_DB_READONLY_ADAPTER``."""
    url = os.environ.get("SPRING_AI_DB_BASE_URL", "").strip()
    if url:
        return SpringHttpDbReadonlyClient(
            base_url=url.rstrip("/"),
            timeout_s=float(os.environ.get("SPRING_AI_DB_TIMEOUT_SEC", "60")),
        )
    return build_db_readonly_client_from_env()


def latest_corpus_version(corpus_root: Path) -> str | None:
    index_dir = corpus_root / "index"
    if not index_dir.is_dir():
        return None
    paths = sorted(index_dir.glob("index__*.json"))
    if not paths:
        return None
    stem = paths[-1].stem
    prefix = "index__"
    return stem[len(prefix) :] if stem.startswith(prefix) else None


def load_rag_chunks(corpus_root: Path) -> list[RagChunk]:
    ver = latest_corpus_version(corpus_root)
    if not ver:
        return []
    schema = list(read_chunks(corpus_root=corpus_root, corpus_version=ver, namespace=SCHEMA_NAMESPACE))
    health = list(read_chunks(corpus_root=corpus_root, corpus_version=ver, namespace=HEALTH_NAMESPACE))
    return schema + health


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[0-9a-zA-ZÀ-ỹ_]+", text.lower()))


def _rag_retrieve(query: str, chunks: list[RagChunk]) -> dict[str, Any]:
    if not chunks:
        return {
            "ok": True,
            "chunks": [],
            "rag_stale_warning": "Chưa có index RAG (chạy job Task005 generate + ingest).",
        }
    qtok = _tokens(query)
    scored: list[tuple[float, RagChunk]] = []
    for ch in chunks:
        ctok = _tokens(ch.text)
        inter = len(qtok & ctok)
        score = inter / max(len(qtok), 1) if qtok else 0.0
        scored.append((score, ch))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [c for s, c in scored[:8] if s > 0]
    if not top:
        top = [c for _, c in scored[:4]]
    fmt = [
        {"id": c.chunk_id, "text": c.text, "source": {"namespace": c.namespace}, "score": 1.0}
        for c in top
    ]
    return {"ok": True, "chunks": fmt, "rag_stale_warning": None}


def _pick_template(message: str) -> tuple[str, dict[str, Any]] | None:
    m = message.lower()
    inv_kw = ["tồn", "inventory", "sku", "mã hàng", "hàng tồn", "kho"]
    sales_kw = ["đơn hàng", "sales", "đơn bán", "order", "bán hàng"]
    has_inv = any(k in m for k in inv_kw)
    has_sales = any(k in m for k in sales_kw)
    if has_inv and not has_sales:
        return ("inventory_by_sku_prefix_v1", {"sku_prefix": "DEMO-", "limit": 20})
    if has_sales:
        return ("recent_sales_orders_v1", {"limit": 15})
    return None


def _intent_local(msg: str) -> dict[str, Any]:
    low = msg.lower()
    if any(x in low for x in ["xóa ", "delete ", "truncate ", "drop table", "hack", "inject"]):
        return {
            "ok": True,
            "primary_intent": "refusal",
            "entities": {},
            "risk_flags": ["unsafe_language"],
            "hitl_required": False,
            "suggested_tools": [],
        }
    tpl = _pick_template(msg)
    if tpl:
        return {
            "ok": True,
            "primary_intent": "data_query",
            "entities": {},
            "risk_flags": [],
            "hitl_required": False,
            "suggested_tools": ["rag_retrieve", "sql_execute_read"],
        }
    if any(x in low for x in ["schema", "cột", "column", "bảng", "table", "postgres", "database"]):
        return {
            "ok": True,
            "primary_intent": "rag_qa",
            "entities": {},
            "risk_flags": [],
            "hitl_required": False,
            "suggested_tools": ["rag_retrieve"],
        }
    return {
        "ok": True,
        "primary_intent": "conversation",
        "entities": {},
        "risk_flags": [],
        "hitl_required": False,
        "suggested_tools": ["rag_retrieve"],
    }


def _map_sql_step(out: SqlQueryReadonlyOut | McpToolError) -> dict[str, Any]:
    if isinstance(out, SqlQueryReadonlyOut):
        return {
            "ok": True,
            "columns": [c.name for c in out.columns],
            "rows": out.rows,
            "data_as_of": None,
        }
    return {
        "ok": False,
        "error": {"message": out.message, "code": out.code},
        "columns": [],
        "rows": [],
    }


async def run_smart_erp_turn(user_message: str) -> dict[str, Any]:
    db = build_chat_db_client()
    try:
        steps: list[dict[str, Any]] = []
        intent = _intent_local(user_message)
        steps.append({"tool": "intent_analyze", "result": intent})

        if intent.get("primary_intent") == "refusal":
            return {"steps": steps}

        corpus_root = Path(os.environ.get("TASK005_CORPUS_ROOT", str(DEFAULT_CORPUS_ROOT))).resolve()
        rag = _rag_retrieve(user_message, load_rag_chunks(corpus_root))
        steps.append({"tool": "rag_retrieve", "result": rag})

        tpl = _pick_template(user_message)
        if tpl and not isinstance(db, UnconfiguredDbReadonlyClient):
            tid, params = tpl
            try:
                raw = await db.query_readonly(SqlQueryReadonlyIn(template_id=tid, params=params))
            except McpTransportError as e:
                raw = McpToolError(
                    code="MCP_TRANSPORT",
                    message=str(e),
                    retryable=True,
                    details=None,
                    correlation_id="local",
                )
            steps.append({"tool": "sql_execute_read", "result": _map_sql_step(raw)})
        elif tpl and isinstance(db, UnconfiguredDbReadonlyClient):
            steps.append(
                {
                    "tool": "sql_execute_read",
                    "result": {
                        "ok": False,
                        "error": {
                            "message": "DB read-only chưa cấu hình "
                            "(đặt SPRING_AI_DB_BASE_URL hoặc TASK005_DB_READONLY_ADAPTER=spring).",
                            "code": "NOT_CONFIGURED",
                        },
                        "columns": [],
                        "rows": [],
                    },
                }
            )

        return {"steps": steps}
    finally:
        if isinstance(db, SpringHttpDbReadonlyClient):
            await db.aclose()


def _chunk_text(text: str, *, size: int = 48) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)]


def _use_llm() -> bool:
    return os.getenv("SMART_ERP_CHAT_USE_LLM", "true").strip().lower() not in ("0", "false", "no")


def _collect_llm(prompt: str) -> str:
    return "".join(stream_chat_deltas(prompt))


async def stream_final_answer(user_message: str) -> AsyncIterator[str]:
    """Run agent turn then stream deltas (MKP synthesis or formatted fallback)."""

    turn = await run_smart_erp_turn(user_message)
    base_ctx = format_turn_as_chat_text(turn)

    if not _use_llm():
        for piece in _chunk_text(base_ctx):
            yield piece
        return

    augmented = (
        "Bạn là trợ lý Smart ERP.\n"
        "Dưới đây là kết quả công cụ (RAG nội bộ + truy vấn DB read-only qua template). "
        "Chỉ dùng số liệu có trong ngữ cảnh; không bịa.\n\n"
        f"{base_ctx}\n\nCâu hỏi người dùng:\n{user_message}\n\n"
        "Trả lời tiếng Việt, súc tích, có đối chiếu số nếu có."
    )
    try:
        full = await asyncio.to_thread(_collect_llm, augmented)
        if not full.strip():
            for piece in _chunk_text(base_ctx):
                yield piece
            return
        for piece in _chunk_text(full.strip()):
            yield piece
    except Exception:
        for piece in _chunk_text(base_ctx):
            yield piece
