"""Schema artifact models + optional YAML loader for tests/CLI (SQL graph uses Postgres live schema)."""

from __future__ import annotations

import pathlib
from typing import Any, Protocol

import yaml
from pydantic import BaseModel, Field

from app.config.graph_settings import GraphSettings


class ColumnMeta(BaseModel):
    name: str
    type: str | None = None
    allowlist: bool = True
    nullable: bool | None = None
    description: str | None = Field(
        default=None,
        description="Optional business description from ai_column_description registry.",
    )


class TableMeta(BaseModel):
    name: str
    columns: list[ColumnMeta] = Field(default_factory=list)
    pk: list[str] = Field(default_factory=list)
    fks: list[dict[str, Any]] = Field(default_factory=list)
    description: str | None = Field(
        default=None,
        description="Business description merged from registry/YAML; omitted in prompts when absent.",
    )
    sample_rows: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Up to N sample rows for LLM to infer data format.",
    )
    distinct_values: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Column name -> distinct non-null values for enum-like text columns.",
    )
    relationship_hints: list[str] = Field(
        default_factory=list,
        description="Business descriptions of FK relationships, e.g. 'category_id → categories.id: Each product belongs to a category'.",
    )


class SchemaArtifact(BaseModel):
    schema_version: str
    tables: list[TableMeta] = Field(default_factory=list)
    updated_at: str | None = None
    generated_at: str | None = None
    source_mode: str | None = Field(
        default=None,
        description="How the artifact was produced, e.g. cli_scan or manual.",
    )

    def allowlist_table_names(self) -> set[str]:
        return {t.name.lower() for t in self.tables}

    def allowlist_columns(self, table: str) -> set[str]:
        t_lower = table.lower()
        for t in self.tables:
            if t.name.lower() == t_lower:
                return {c.name.lower() for c in t.columns}
        return set()

    def allowlist_columns_map(self) -> dict[str, set[str]]:
        """Lowercase table name → allowed column names (lowercase)."""
        return {t.name.lower(): {c.name.lower() for c in t.columns} for t in self.tables}


class SchemaLoader(Protocol):
    def load(self, schema_version: str) -> SchemaArtifact: ...


class FileSchemaLoader:
    """Load `<schema_version>.yaml` from a base directory."""

    def __init__(self, base_dir: pathlib.Path | str | None) -> None:
        if base_dir is None:
            root = pathlib.Path(__file__).resolve().parent.parent / "data" / "schema"
            self._base = root
        else:
            self._base = pathlib.Path(base_dir)

    def load(self, schema_version: str) -> SchemaArtifact:
        path = self._base / f"{schema_version}.yaml"
        if not path.is_file():
            raise FileNotFoundError(f"schema artifact not found: {path}")
        return load_schema_yaml_path(path)


def load_schema_yaml_bytes(data: bytes, *, source_label: str = "") -> SchemaArtifact:
    text = data.decode("utf-8")
    return load_schema_yaml_text(text, source_label=source_label)


def load_schema_yaml_text(text: str, *, source_label: str = "") -> SchemaArtifact:
    raw = yaml.safe_load(text)
    if not isinstance(raw, dict):
        raise ValueError(f"invalid schema YAML (expected mapping){': ' + source_label if source_label else ''}")
    return SchemaArtifact.model_validate(raw)


def load_schema_yaml_path(path: pathlib.Path | str) -> SchemaArtifact:
    p = pathlib.Path(path)
    raw_bytes = p.read_bytes()
    return load_schema_yaml_bytes(raw_bytes, source_label=str(p))


def build_schema_loader(settings: GraphSettings) -> SchemaLoader:
    if settings.schema_dir:
        return FileSchemaLoader(settings.schema_dir)
    return FileSchemaLoader(None)
