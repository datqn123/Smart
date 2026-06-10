from __future__ import annotations
from dataclasses import dataclass
from fastapi import FastAPI, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from app.config.settings import get_settings
from app.config.llm_client import make_llm
from app.harness.auth import verify_jwt, AuthError
from app.harness.session import resolve_thread_id
from app.harness.turn_context import TurnContext
from app.harness.sse_emitter import sse_format
from app.graph.orchestrator import run_session
from app.graph.hitl import PendingStore
from app.sql.executor import PostgresRoExecutor, make_pg_connect


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
        pending_store=PendingStore(db_path=s.hitl_checkpoint_db))


def create_app() -> FastAPI:
    app = FastAPI(title="Agentic AI (ai_python)")

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.post("/chat")
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
        raw_require = body.get("raw_require", "")
        clarification = body.get("clarification_response")
        thread_id = resolve_thread_id(claims["sub"])
        ctx = TurnContext(raw_require=raw_require, user_id=claims["sub"],
                          thread_id=thread_id, clarification_response=clarification)

        resume_snapshot = None
        if clarification and deps.pending_store is not None:
            await deps.pending_store.init()
            resume_snapshot = await deps.pending_store.load(thread_id)
            if resume_snapshot:
                await deps.pending_store.clear(thread_id)

        async def stream():
            async for event in run_session(
                    ctx, llm_sm=deps.llm_sm, llm_tool=deps.llm_tool, deps=deps.deps,
                    max_steps=deps.max_steps, retry_cap=deps.retry_cap,
                    resume_snapshot=resume_snapshot, pending_store=deps.pending_store):
                yield sse_format(event["type"], event["data"])

        return StreamingResponse(stream(), media_type="text/event-stream")

    return app


app = create_app()
