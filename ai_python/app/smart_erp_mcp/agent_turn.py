"""One chat turn: lightweight intent + local RAG retrieve + optional Spring db-readonly."""

from __future__ import annotations

import asyncio
import json
import os
import re
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from app.contracts.task005 import McpToolError, SqlQueryReadonlyOut, SqlQueryReadonlyIn
from app.mkp_client import chat_text, stream_chat_deltas
from app.mcp.db_readonly_port import DbReadonlyMcpClient, McpTransportError
from app.mcp.spring_http_client import SpringHttpDbReadonlyClient
from app.mcp.task005_client_factory import build_db_readonly_client_from_env
from app.mcp.task005_unconfigured_client import UnconfiguredDbReadonlyClient
from app.rag.task005_ingest import RagChunk, read_chunks
from app.rag.vector_store import query as vector_query
from app.registry.task005_templates import load_registry_from_path
from app.smart_erp_mcp.chat_reply import format_turn_as_chat_text
from app.tools.task005_corpus_fs import (
    DEFAULT_CORPUS_ROOT,
    HEALTH_NAMESPACE,
    SCHEMA_NAMESPACE,
)

_MEM_TTL_SECONDS = 15 * 60
_MEMORY: dict[str, dict[str, Any]] = {}


def _now_s() -> float:
    return float(__import__("time").time())


def _mem_get(cid: str) -> dict[str, Any] | None:
    item = _MEMORY.get(cid)
    if not item:
        return None
    if _now_s() - float(item.get("_ts", 0)) > _MEM_TTL_SECONDS:
        _MEMORY.pop(cid, None)
        return None
    return item


def _mem_put(cid: str, payload: dict[str, Any]) -> None:
    payload["_ts"] = _now_s()
    _MEMORY[cid] = payload


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
    # Vector store is the primary RAG path (Plan: vector_store). Fallback to local chunk overlap.
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        emb = model.encode([query], normalize_embeddings=True, convert_to_numpy=True).astype("float32")
        picked = vector_query(query_embedding=emb[0], top_k=8)
        if picked:
            return {"ok": True, "chunks": picked, "rag_stale_warning": None}
        return {
            "ok": True,
            "chunks": [],
            "rag_stale_warning": "Vector index chưa sẵn sàng (hãy chạy `python -m app.cli.task005_vector_ingest`).",
        }
    except Exception:
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
        top = [c for s, c in scored[:8] if s > 0] or [c for _, c in scored[:4]]
        fmt = [
            {"id": c.chunk_id, "text": c.text, "source": {"namespace": c.namespace}, "score": 1.0}
            for c in top
        ]
        return {"ok": True, "chunks": fmt, "rag_stale_warning": "Đang dùng fallback retrieve (không vector store)."}


def _pick_template(message: str) -> tuple[str, dict[str, Any]] | None:
    # Deprecated: replaced by ToolPlanner (LLM + registry + RAG).
    return None


def _registry_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "config" / "templates.json"


def plan_tool_from_rag(*, user_message: str, rag_chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """LLM planner that maps question → template_id + params using registry + RAG context."""
    reg = load_registry_from_path(_registry_path())
    msg_lower = user_message.lower()
    # Deterministic routing for frequent ambiguous queries.
    # "bao nhiêu sản phẩm" usually means count of distinct products (not quantity sum).
    # Cover variants like: "trong kho ... bao nhiêu sản phẩm", "bao nhiêu sản phẩm còn hoạt động", ...
    has_inventory = ("tồn kho" in msg_lower) or ("trong kho" in msg_lower) or ("kho" in msg_lower)
    if has_inventory and "bao nhiêu" in msg_lower and "sản phẩm" in msg_lower:
        return {"action": "query", "template_id": "inventory_active_products_count_v1", "params": {"min_quantity": 0}}

    templates_brief = "\n".join(
        f"- {t.template_id}: {t.intent} — {t.description}; params_schema={json.dumps(t.params_schema, ensure_ascii=False)}"
        for t in reg.templates
    )
    rag_text = "\n\n".join(str(ch.get("text") or "")[:800] for ch in rag_chunks[:6])
    prompt = (
        "Bạn là ToolPlanner cho Smart ERP. Nhiệm vụ: chọn 0 hoặc 1 template_id phù hợp nhất và sinh params hợp lệ.\n"
        "Chỉ được chọn template_id trong danh sách bên dưới. Không được tạo SQL.\n\n"
        "QUY ƯỚC:\n"
        "- Nếu câu hỏi là 'bao nhiêu sản phẩm' / 'đếm sản phẩm' liên quan tồn kho → ưu tiên template đếm (count).\n"
        "- Nếu user hỏi danh sách SKU cụ thể → dùng template lọc theo sku_prefix.\n\n"
        "DANH SÁCH TEMPLATE (kèm params_schema JSON):\n"
        f"{templates_brief}\n\n"
        "NGỮ CẢNH RAG (schema/docs):\n"
        f"{rag_text}\n\n"
        "Hãy trả JSON THUẦN (không markdown) theo 1 trong 2 dạng:\n"
        "1) {\"action\":\"query\",\"template_id\":\"...\",\"params\":{...}}\n"
        "2) {\"action\":\"no_template\",\"reason\":\"...\"}\n\n"
        f"Câu hỏi: {user_message!r}\n"
    )
    raw = chat_text(prompt, max_tokens=300, temperature=0.0).strip()
    try:
        parsed = json.loads(raw)
    except Exception:
        return {"action": "no_template", "reason": "planner_parse_failed"}
    if not isinstance(parsed, dict):
        return {"action": "no_template", "reason": "planner_bad_shape"}
    action = str(parsed.get("action") or "")
    if action != "query":
        return {"action": "no_template", "reason": str(parsed.get("reason") or "no_template")}
    return {
        "action": "query",
        "template_id": str(parsed.get("template_id") or "").strip(),
        "params": parsed.get("params") if isinstance(parsed.get("params"), dict) else {},
    }


def plan_raw_sql_from_rag(*, user_message: str, rag_chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """Fallback: LLM generates guarded SELECT-only SQL based on RAG schema context."""
    rag_text = "\n\n".join(str(ch.get("text") or "")[:900] for ch in rag_chunks[:8])
    prompt = (
        "Bạn là DB Query Agent (read-only) cho Smart ERP.\n"
        "Hãy tạo 1 câu SQL SELECT duy nhất để trả lời câu hỏi.\n"
        "RÀNG BUỘC BẮT BUỘC:\n"
        "- Chỉ SELECT (không INSERT/UPDATE/DELETE/DROP/ALTER/CREATE)\n"
        "- Không có dấu ';'\n"
        "- Ưu tiên bảng/schema public.\n"
        "- Nếu có thể, dùng COUNT/SUM/AVG phù hợp.\n"
        "- Không cần LIMIT (server sẽ ép LIMIT nếu thiếu).\n\n"
        "NGỮ CẢNH RAG (schema/docs):\n"
        f"{rag_text}\n\n"
        "Trả JSON THUẦN: {\"action\":\"raw_sql\",\"query\":\"...\"} hoặc {\"action\":\"no_sql\",\"reason\":\"...\"}\n"
        f"Câu hỏi: {user_message!r}\n"
    )
    raw = chat_text(prompt, max_tokens=350, temperature=0.0).strip()
    try:
        parsed = json.loads(raw)
    except Exception:
        return {"action": "no_sql", "reason": "raw_sql_parse_failed"}
    if not isinstance(parsed, dict):
        return {"action": "no_sql", "reason": "raw_sql_bad_shape"}
    if str(parsed.get("action") or "") != "raw_sql":
        return {"action": "no_sql", "reason": str(parsed.get("reason") or "no_sql")}
    q = str(parsed.get("query") or "").strip()
    return {"action": "raw_sql", "query": q}


def _intent_guard_local(msg: str) -> dict[str, Any] | None:
    """Fast local guard for obvious unsafe requests to avoid spending tokens."""
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
    return None


def intent_analyze_via_agent_llm(msg: str) -> dict[str, Any]:
    """Always call MKP as the 'intent agent' to route the turn."""
    prompt = (
        "Bạn là Agent phân tích intent cho chat Smart ERP.\n"
        "Hãy phân loại tin nhắn người dùng thành 1 trong các intent sau:\n"
        "- greeting: chào hỏi / xã giao (hi, hello, xin chào, cảm ơn...)\n"
        "- general_chat: câu hỏi đời thường, không liên quan Smart ERP / dự án / database\n"
        "- project_db: câu hỏi liên quan Smart ERP, dự án, API, database, schema, tồn kho, SKU, đơn hàng, báo cáo\n"
        "- refusal: yêu cầu nguy hiểm (xóa dữ liệu, hack, inject, drop table, ...)\n\n"
        "Trả về JSON THUẦN, KHÔNG markdown, theo đúng schema:\n"
        "{"
        "\"ok\": true, "
        "\"primary_intent\": \"greeting|general_chat|project_db|refusal\", "
        "\"entities\": {}, "
        "\"risk_flags\": [], "
        "\"hitl_required\": false, "
        "\"suggested_tools\": [\"rag_retrieve\",\"sql_execute_read\"]"
        "}\n\n"
        f"Tin nhắn: {msg!r}\n"
    )
    raw = chat_text(prompt, max_tokens=200, temperature=0.0).strip()
    try:
        parsed = json.loads(raw)
    except Exception:
        return {
            "ok": True,
            "primary_intent": "general_chat",
            "entities": {},
            "risk_flags": ["intent_parse_failed"],
            "hitl_required": False,
            "suggested_tools": [],
        }
    if not isinstance(parsed, dict):
        return {
            "ok": True,
            "primary_intent": "general_chat",
            "entities": {},
            "risk_flags": ["intent_bad_shape"],
            "hitl_required": False,
            "suggested_tools": [],
        }
    primary = str(parsed.get("primary_intent") or "general_chat")
    if primary not in ("greeting", "general_chat", "project_db", "refusal"):
        primary = "general_chat"
    tools = parsed.get("suggested_tools")
    suggested_tools = tools if isinstance(tools, list) else []
    return {
        "ok": True,
        "primary_intent": primary,
        "entities": parsed.get("entities") if isinstance(parsed.get("entities"), dict) else {},
        "risk_flags": parsed.get("risk_flags") if isinstance(parsed.get("risk_flags"), list) else [],
        "hitl_required": bool(parsed.get("hitl_required", False)),
        "suggested_tools": suggested_tools,
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


async def run_smart_erp_turn(user_message: str, *, conversation_id: str | None) -> dict[str, Any]:
    db = build_chat_db_client()
    try:
        steps: list[dict[str, Any]] = []
        guard = _intent_guard_local(user_message)
        intent = guard or intent_analyze_via_agent_llm(user_message)
        steps.append({"tool": "intent_analyze", "result": intent})

        primary = intent.get("primary_intent")
        if primary == "refusal":
            return {"steps": steps}
        if primary in ("greeting", "general_chat"):
            # No tools; let LLM answer normally.
            return {"steps": steps}

        corpus_root = Path(os.environ.get("TASK005_CORPUS_ROOT", str(DEFAULT_CORPUS_ROOT))).resolve()
        rag = _rag_retrieve(user_message, load_rag_chunks(corpus_root))
        # Follow-up context: prepend last tool summary to help planner.
        if conversation_id:
            last = _mem_get(conversation_id)
            if last and isinstance(last.get("tool_summary"), str) and last["tool_summary"].strip():
                rag = dict(rag)
                rag["chunks"] = [
                    {
                        "id": "memory:last_tool_summary",
                        "text": f"(Kết quả lượt trước)\\n{last['tool_summary']}",
                        "source": {"namespace": "memory"},
                        "score": 1.0,
                    },
                    *list((rag.get("chunks") or [])),
                ]
        steps.append({"tool": "rag_retrieve", "result": rag})

        rag_chunks = list((rag or {}).get("chunks") or []) if isinstance(rag, dict) else []

        # Deterministic TOP-N routing for common inventory questions:
        # "sản phẩm nào ... nhiều nhất/cao nhất" should NOT hit count templates.
        msg_lower = user_message.lower()
        wants_top = any(k in msg_lower for k in ("nhiều nhất", "cao nhất", "top", "lớn nhất"))
        is_inventory = any(k in msg_lower for k in ("tồn kho", "trong kho", "kho", "inventory"))
        if wants_top and is_inventory and isinstance(db, SpringHttpDbReadonlyClient):
            # TOP 1 by total quantity (distinct SKU).
            query = (
                "SELECT p.sku_code AS sku_code, SUM(i.quantity) AS total_quantity "
                "FROM inventory i "
                "JOIN products p ON p.id = i.product_id "
                "WHERE p.status = 'Active' "
                "GROUP BY p.sku_code "
                "ORDER BY total_quantity DESC "
                "LIMIT 1"
            )
            raw_plan = {"action": "raw_sql", "query": query}
            steps.append({"tool": "raw_sql_plan", "result": raw_plan})
            raw = await db.query_readonly_raw(query=query, max_rows=5)
            steps.append({"tool": "sql_execute_read", "result": _map_sql_step(raw)})
            # Store minimal summary for follow-up (redacted; no raw rows persisted beyond runtime).
            if conversation_id:
                tool_summary = format_turn_as_chat_text({"steps": steps})
                _mem_put(conversation_id, {"tool_summary": tool_summary})
            return {"steps": steps}

        plan = plan_tool_from_rag(user_message=user_message, rag_chunks=rag_chunks)
        steps.append({"tool": "tool_plan", "result": plan})

        if plan.get("action") == "query" and not isinstance(db, UnconfiguredDbReadonlyClient):
            tid = str(plan.get("template_id") or "")
            params = plan.get("params") if isinstance(plan.get("params"), dict) else {}
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
        elif plan.get("action") == "query" and isinstance(db, UnconfiguredDbReadonlyClient):
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
        else:
            # Raw SQL fallback (guarded by Spring).
            if isinstance(db, SpringHttpDbReadonlyClient):
                raw_plan = plan_raw_sql_from_rag(user_message=user_message, rag_chunks=rag_chunks)
                steps.append({"tool": "raw_sql_plan", "result": raw_plan})
                if raw_plan.get("action") == "raw_sql":
                    raw = await db.query_readonly_raw(query=str(raw_plan.get("query") or ""), max_rows=50)
                    steps.append({"tool": "sql_execute_read", "result": _map_sql_step(raw)})

        # Store minimal summary for follow-up (redacted; no raw rows persisted beyond runtime).
        if conversation_id:
            tool_summary = format_turn_as_chat_text({"steps": steps})
            _mem_put(conversation_id, {"tool_summary": tool_summary})
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


async def stream_final_answer(user_message: str, *, conversation_id: str | None) -> AsyncIterator[str]:
    """Run agent turn then stream deltas (MKP synthesis or formatted fallback)."""

    turn = await run_smart_erp_turn(user_message, conversation_id=conversation_id)
    steps: list[dict[str, Any]] = list(turn.get("steps") or [])
    intent_step = next((s for s in steps if s.get("tool") == "intent_analyze"), None)
    intent_res = dict(intent_step.get("result") or {}) if isinstance(intent_step, dict) else {}
    primary = str(intent_res.get("primary_intent") or "general_chat")
    if primary in ("greeting", "general_chat"):
        # Let Gemma answer normally (no tool context).
        try:
            for delta in stream_chat_deltas(user_message):
                yield delta
            return
        except Exception:
            yield "Xin lỗi, hiện tại tôi chưa thể trả lời. Bạn thử lại giúp mình nhé."
            return

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
