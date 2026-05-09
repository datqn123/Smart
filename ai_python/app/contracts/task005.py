"""Pydantic contracts for Task005 corpus pipeline (Option B).

Aligns with SRS §3 (CorpusJobContext) and §4 (MCP I/O for `db-readonly`).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

DescribeStatus = Literal["ok", "failed"]

MAX_COLUMNS = 512
MAX_SUMMARY_CHARS = 2000
MAX_SMOKE_ROW_COUNT = 50


def _strip_required(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{label} must not be blank")
    return cleaned


class McpToolError(BaseModel):
    """Shared error envelope for `db-readonly` MCP failures (SRS §4)."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, description="Machine-readable error code")
    message: str = Field(min_length=1, description="Human-readable description")
    retryable: bool
    details: dict[str, Any] | None = None
    correlation_id: str

    @field_validator("correlation_id")
    @classmethod
    def _correlation_id_not_blank(cls, value: str) -> str:
        return _strip_required(value, "correlation_id")


class ColumnMeta(BaseModel):
    """One column entry from `sql.describe`."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    type: str = Field(min_length=1)
    nullable: bool


class SqlDescribeIn(BaseModel):
    """`sql.describe` input — a single allowlisted object name."""

    model_config = ConfigDict(extra="forbid")

    object_name: str

    @field_validator("object_name")
    @classmethod
    def _strip_object_name(cls, value: str) -> str:
        return _strip_required(value, "object_name")


class SqlDescribeOut(BaseModel):
    """`sql.describe` response payload (column / summary caps per SRS §4.1)."""

    model_config = ConfigDict(extra="forbid")

    object_name: str
    columns: list[ColumnMeta] = Field(max_length=MAX_COLUMNS)
    summary: str = Field(max_length=MAX_SUMMARY_CHARS)
    correlation_id: str


class SqlColumn(BaseModel):
    """One projected column from `sql.query_readonly`."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    type: str = Field(min_length=1)


class SqlQueryReadonlyIn(BaseModel):
    """`sql.query_readonly` input (template-first; no raw SQL)."""

    model_config = ConfigDict(extra="forbid")

    template_id: str
    params: dict[str, Any] = Field(default_factory=dict)

    @field_validator("template_id")
    @classmethod
    def _strip_template_id(cls, value: str) -> str:
        return _strip_required(value, "template_id")


class SqlQueryReadonlyOut(BaseModel):
    """`sql.query_readonly` response payload (smoke surface).

    Slice persists only ``row_count`` + ``summary`` + ok/code; full ``rows`` is
    held only inside the response object and never written to corpus artifacts.
    """

    model_config = ConfigDict(extra="forbid")

    columns: list[SqlColumn]
    rows: list[list[Any]]
    row_count: int = Field(ge=0, le=MAX_SMOKE_ROW_COUNT)
    summary: str = Field(max_length=MAX_SUMMARY_CHARS)
    correlation_id: str


class SmokeTemplateFailure(BaseModel):
    """Recorded smoke failure entry — never carries row payloads."""

    model_config = ConfigDict(extra="forbid")

    template_id: str
    code: str


class CorpusJobContext(BaseModel):
    """Run-scoped state for the Task005 batch corpus job (SRS §3)."""

    model_config = ConfigDict(extra="forbid")

    correlation_id: str
    corpus_version: str
    run_started_at: datetime
    run_finished_at: datetime | None = None
    objects_allowlist: list[str] = Field(default_factory=list)
    describe_results: dict[str, DescribeStatus] = Field(default_factory=dict)
    smoke_templates_tried: list[str] = Field(default_factory=list)
    smoke_templates_ok: list[str] = Field(default_factory=list)
    smoke_templates_failed: list[SmokeTemplateFailure] = Field(default_factory=list)

    @field_validator("correlation_id", "corpus_version")
    @classmethod
    def _required_id(cls, value: str) -> str:
        return _strip_required(value, "value")
