"""Schema artifact loader (Task 3 / DBM) — YAML fixtures, no runtime DB."""

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


class TableMeta(BaseModel):
    name: str
    columns: list[ColumnMeta] = Field(default_factory=list)
    pk: list[str] = Field(default_factory=list)
    fks: list[dict[str, Any]] = Field(default_factory=list)


class SchemaArtifact(BaseModel):
    schema_version: str
    tables: list[TableMeta] = Field(default_factory=list)
    updated_at: str | None = None

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
        raw = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            raise ValueError(f"invalid schema YAML (expected mapping): {path}")
        return SchemaArtifact.model_validate(data)


def build_schema_loader(settings: GraphSettings) -> SchemaLoader:
    if settings.schema_dir:
        return FileSchemaLoader(settings.schema_dir)
    return FileSchemaLoader(None)
