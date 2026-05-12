"""Pydantic schemas for structured LLM outputs (intent, SQL review)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class IntentOutput(BaseModel):
    intent: Literal["general_chat", "system_data_query", "system_data_chart"]


class SqlReviewOutput(BaseModel):
    ok: bool
    issues: list[str] = Field(default_factory=list)


class SqlTablePickOutput(BaseModel):
    """Structured output for optional table subset selection (Task007)."""

    tables: list[str] = Field(
        default_factory=list,
        description="Table names from the allowlist most relevant to the question.",
    )


class IdeaPlannerOutput(BaseModel):
    """Agent_Idea — brief for SQL + chart direction."""

    data_request: dict[str, Any] = Field(default_factory=dict)
    chart_idea: dict[str, Any] = Field(default_factory=dict)


class ChartSpecDraftOutput(BaseModel):
    """Agent_Chart — column keys before review."""

    chart_type: Literal["line", "bar"]
    x_key: str
    y_key: str
    title: str = ""


class ChartReviewOutput(BaseModel):
    """Agent_Review — aligned keys + summary."""

    chart_type: Literal["line", "bar"]
    x_key: str
    y_key: str
    title: str = ""
    final_answer: str = ""
