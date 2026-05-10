"""FastAPI entrypoint — AI / chatbot service (Python)."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.errors import register_error_handlers
from app.api.routes import router as chat_router
from app.config.settings import load_llm_settings, validate_llm_required
from app.graph.correlation import setup_correlation_logging


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Fail-fast when ``LLM_REQUIRED=1`` and credentials are missing."""
    setup_correlation_logging()
    validate_llm_required(load_llm_settings())
    yield


app = FastAPI(title="ai_python", version="0.1.0", lifespan=lifespan)
register_error_handlers(app)
app.include_router(chat_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "ai_python", "docs": "/docs"}
