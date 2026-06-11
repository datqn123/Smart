from __future__ import annotations
import asyncio
import json
import logging
import os
from dataclasses import dataclass
from fastapi import FastAPI, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from app.config.settings import get_settings
from app.config.llm_client import make_llm
from app.harness.auth import verify_jwt, AuthError
from app.harness.session import resolve_thread_id
from app.harness.turn_context import TurnContext
from app.harness.sse_emitter import sse_frontend
from app.graph.orchestrator import run_session
from app.graph.hitl import PendingStore
from app.memory import ConversationMemory, get_memory
from app.sql.executor import PostgresRoExecutor, make_pg_connect

log = logging.getLogger(__name__)

# Giu ref task compact fire-and-forget — tranh bi GC giua chung.
_bg_tasks: set[asyncio.Task] = set()


@dataclass
class Deps:
    llm_sm: object
    llm_tool: object
    deps: dict
    max_steps: int
    retry_cap: int
    jwt_secret: str
    jwt_issuer: str
    jwt_audience: str
    dev_bypass: bool
    pending_store: PendingStore
    memory: ConversationMemory


def get_deps() -> Deps:
    s = get_settings()
    executor = PostgresRoExecutor(connect=make_pg_connect(s.database_url_ro),
                                  row_limit=s.sql_row_limit)
    return Deps(
        llm_sm=make_llm(s, role="sm"),
        llm_tool=make_llm(s, role="default"),
        deps={"executor": executor, "row_limit": s.sql_row_limit},
        max_steps=s.harness_max_steps, retry_cap=s.tool_retry_cap,
        jwt_secret=s.jwt_hs256_secret, jwt_issuer=s.jwt_issuer,
        jwt_audience=s.jwt_audience, dev_bypass=s.auth_dev_bypass,
        pending_store=PendingStore(db_path=s.hitl_checkpoint_db),
        memory=get_memory())  # singleton module-level — KHONG reset moi request


def _to_frontend_sse(event: dict, *, thread_id: str) -> str | None:
    """Translate orchestrator event -> SSE string cho Spring relay / browser."""
    t = event["type"]
    d = event.get("data", {})
    if t == "tool_call":
        return sse_frontend("progress", f"Đang xử lý: {d.get('tool_name', '')}")
    if t == "tool_result":
        status = "Hoàn thành" if d.get("valid") else "Đang xem xét lại"
        return sse_frontend("progress", f"{d.get('tool_name', '')}: {status}")
    if t == "answer":
        return sse_frontend("delta_full", d.get("text", ""))
    if t == "clarify":
        payload = json.dumps({
            "clarifyId": thread_id,
            "clarifyKind": "agentic",
            "questions": [d.get("message", "")],
            "issues": [],
            "guideRefs": [],
        }, ensure_ascii=False)
        return sse_frontend("clarify", payload)
    if t == "done":
        return sse_frontend("done", "")
    if t == "error":
        return sse_frontend("error", d.get("message", "Lỗi không xác định"))
    return None


def _setup_logging() -> None:
    """Root logger mac dinh chi in WARNING+ (uvicorn --log-level khong ap cho
    app logger). Bat INFO/DEBUG cua app qua env LOG_LEVEL (mac dinh INFO)."""
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=level,
                        format="%(asctime)s %(levelname)-7s %(name)s %(message)s",
                        datefmt="%H:%M:%S")
    for noisy in ("httpx", "httpcore", "openai", "watchfiles", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def create_app() -> FastAPI:
    _setup_logging()
    app = FastAPI(title="Agentic AI (ai_python)")

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.post("/api/v1/ai/chat/stream")
    async def chat(request: Request, deps: Deps = Depends(get_deps),
                   authorization: str | None = Header(default=None)):
        token = None
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization[7:]
        try:
            claims = verify_jwt(token, secret=deps.jwt_secret, issuer=deps.jwt_issuer,
                                audience=deps.jwt_audience, dev_bypass=deps.dev_bypass)
        except AuthError as exc:
            raise HTTPException(status_code=401, detail=str(exc))

        body = await request.json()
        # Spring relay sends: {message, metadata:{thread_id,...}, options:{clarification:{clarify_id,...}}}
        raw_require = body.get("message") or body.get("raw_require", "")
        metadata = body.get("metadata") or {}
        options = body.get("options") or {}
        clarify_opts = options.get("clarification") or {}

        # Thread ID: Spring passes conversationId via metadata.thread_id; else derive from sub
        thread_id = metadata.get("thread_id") or resolve_thread_id(claims["sub"])

        # HITL resume: clarify_id = thread_id from previous clarify event
        clarification: str | None = None
        clarify_id = clarify_opts.get("clarify_id") or clarify_opts.get("clarifyId")
        if clarify_id:
            thread_id = clarify_id
            clarification = (clarify_opts.get("suggested_rewrite") or raw_require or "").strip() or None

        log.info("chat request user=%s thread=%s clarify_resume=%s raw=%.120s",
                 claims.get("sub"), thread_id, clarify_id is not None, raw_require)

        ctx = TurnContext(raw_require=raw_require, user_id=claims["sub"],
                          thread_id=thread_id, clarification_response=clarification)
        memory_context = deps.memory.get_context(thread_id)

        resume_snapshot = None
        if clarification and deps.pending_store is not None:
            await deps.pending_store.init()
            resume_snapshot = await deps.pending_store.load(thread_id)
            if resume_snapshot:
                log.info("HITL snapshot loaded for thread=%s", thread_id)
                await deps.pending_store.clear(thread_id)
            else:
                log.warning("HITL resume requested but no snapshot found thread=%s", thread_id)

        async def stream():
            answer_text = ""
            done_require: str | None = None
            try:
                async for event in run_session(
                        ctx, llm_sm=deps.llm_sm, llm_tool=deps.llm_tool, deps=deps.deps,
                        max_steps=deps.max_steps, retry_cap=deps.retry_cap,
                        resume_snapshot=resume_snapshot, pending_store=deps.pending_store,
                        memory_context=memory_context):
                    if event["type"] == "answer":
                        answer_text = event["data"].get("text", "")
                    elif event["type"] == "done":
                        done_require = event["data"].get("raw_require") or ctx.raw_require
                    sse = _to_frontend_sse(event, thread_id=ctx.thread_id)
                    if sse:
                        log.debug("SSE emit event=%s", event["type"])
                        yield sse
                # Chi ghi memory khi phien ket thuc co answer (sau done) —
                # clarify/aborted/error KHONG ghi (spec write path).
                if done_require is not None and answer_text:
                    deps.memory.append_turn(ctx.thread_id, done_require, answer_text)
                    if deps.memory.needs_compact(ctx.thread_id):
                        # fire-and-forget: user khong phai cho them 1 LLM call
                        task = asyncio.create_task(
                            deps.memory.compact(ctx.thread_id, llm=deps.llm_tool))
                        _bg_tasks.add(task)
                        task.add_done_callback(_bg_tasks.discard)
            except Exception as exc:
                log.error("stream error thread=%s: %s", ctx.thread_id, exc, exc_info=True)
                yield _to_frontend_sse({"type": "error", "data": {"message": "Lỗi hệ thống."}},
                                       thread_id=ctx.thread_id) or ""

        return StreamingResponse(stream(), media_type="text/event-stream")

    return app


app = create_app()
