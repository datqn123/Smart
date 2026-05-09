"""Artifact view-models for Task005 (summary-only — never persist DB rows)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.contracts.task005 import (
    MAX_COLUMNS,
    MAX_SMOKE_ROW_COUNT,
    MAX_SUMMARY_CHARS,
    ColumnMeta,
    SqlDescribeOut,
    SqlQueryReadonlyOut,
)


class SchemaCatalogEntry(BaseModel):
    """One catalog entry produced from `sql.describe` for an allowlisted object."""

    model_config = ConfigDict(extra="forbid")

    object_name: str
    columns: list[ColumnMeta] = Field(max_length=MAX_COLUMNS)
    summary: str = Field(max_length=MAX_SUMMARY_CHARS)


class SchemaCatalogArtifact(BaseModel):
    """`catalog.json` shape: corpus version + describe entries."""

    model_config = ConfigDict(extra="forbid")

    corpus_version: str
    correlation_id: str
    objects: list[SchemaCatalogEntry] = Field(default_factory=list)


class SmokeArtifactEntry(BaseModel):
    """One smoke status row — no rows / summary detail / params persisted."""

    model_config = ConfigDict(extra="forbid")

    template_id: str
    ok: bool
    row_count: int = Field(ge=0, le=MAX_SMOKE_ROW_COUNT)
    code: str | None

    @field_validator("template_id")
    @classmethod
    def _strip_template_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("template_id must not be blank")
        return cleaned


class SmokeHealthArtifact(BaseModel):
    """`health.json` shape: corpus version + per-template status (no rows)."""

    model_config = ConfigDict(extra="forbid")

    corpus_version: str
    correlation_id: str
    smoke: list[SmokeArtifactEntry] = Field(default_factory=list)


def catalog_entry_from_describe(out: SqlDescribeOut) -> SchemaCatalogEntry:
    """Project a describe response into a catalog entry."""

    return SchemaCatalogEntry(
        object_name=out.object_name,
        columns=list(out.columns),
        summary=out.summary,
    )


def smoke_entry_from_success(
    out: SqlQueryReadonlyOut, *, template_id: str
) -> SmokeArtifactEntry:
    """Project a successful smoke response into a status entry (drops `rows`)."""

    return SmokeArtifactEntry(
        template_id=template_id,
        ok=True,
        row_count=out.row_count,
        code=None,
    )


def smoke_entry_from_failure(
    *, template_id: str, code: str, row_count: int = 0
) -> SmokeArtifactEntry:
    """Build a smoke status entry for a failed template (no rows)."""

    return SmokeArtifactEntry(
        template_id=template_id,
        ok=False,
        row_count=row_count,
        code=code,
    )
