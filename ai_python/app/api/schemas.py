"""Pydantic contracts for Task004 invoke/stream APIs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChatMetadata(BaseModel):
    user_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    thread_id: str | None = None
    schema_version: str = Field(default="v1", min_length=1)


class ChatOptions(BaseModel):
    stream: bool = False
    locale: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    metadata: ChatMetadata
    options: ChatOptions = Field(default_factory=ChatOptions)


class InvokeUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class ErrorObject(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class InvokeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    correlation_id: str
    thread_id: str | None = None
    intent: str | None = None
    final_answer: str | None = None
    chart_spec: dict[str, Any] | None = None
    usage: InvokeUsage | None = None
    error: ErrorObject | None = None


class ErrorEnvelope(BaseModel):
    correlation_id: str | None = None
    error: ErrorObject


class StreamEvent(BaseModel):
    correlation_id: str
    event_type: str
    delta: str | None = None
    data: dict[str, Any] | str | None = None
    is_terminal: bool
