"""Pydantic models for streamed / agent events (placeholder for later tasks)."""

from pydantic import BaseModel


class SSEEventStub(BaseModel):
    kind: str = "sse_stub"
