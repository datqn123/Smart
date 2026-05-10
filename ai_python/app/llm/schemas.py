"""Pydantic schemas for structured LLM outputs (intent, SQL review)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class IntentOutput(BaseModel):
    intent: Literal["general_chat", "system_data_query"]


class SqlReviewOutput(BaseModel):
    ok: bool
    issues: list[str] = Field(default_factory=list)
