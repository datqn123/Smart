from fastapi import FastAPI

from app.api.routers import chat as chat_router
from app.api.routers import health as health_router

app = FastAPI(title="ai_python", version="0.1.0")
app.include_router(health_router.router)
app.include_router(chat_router.router)
