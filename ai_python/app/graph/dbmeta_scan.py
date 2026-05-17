"""Offline DB introspection → SchemaArtifact (CLI / operators)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

from app.graph.dbmeta import ColumnMeta, SchemaArtifact, TableMeta


def scan_engine_metadata(
    engine: Engine,
    *,
    schema_version: str,
    source_mode: str = "sqlalchemy_inspect",
) -> SchemaArtifact:
    """Reflect tables via SQLAlchemy inspector (read-only introspection)."""
    inspector = inspect(engine)
    tables_out: list[TableMeta] = []
    for table_name in inspector.get_table_names():
        cols_raw = inspector.get_columns(table_name)
        cols: list[ColumnMeta] = []
        for c in cols_raw:
            ctype = c.get("type")
            type_str = str(ctype) if ctype is not None else None
            cols.append(
                ColumnMeta(
                    name=str(c["name"]),
                    type=type_str,
                    nullable=bool(c["nullable"]) if c.get("nullable") is not None else None,
                )
            )
        pk_info = inspector.get_pk_constraint(table_name)
        pk_cols = list(pk_info.get("constrained_columns") or [])
        tables_out.append(TableMeta(name=table_name, columns=cols, pk=pk_cols))

    generated_at = datetime.now(tz=UTC).isoformat()
    return SchemaArtifact(
        schema_version=schema_version,
        tables=sorted(tables_out, key=lambda t: t.name.lower()),
        generated_at=generated_at,
        source_mode=source_mode,
    )


def scan_database_url(url: str, *, schema_version: str, source_mode: str = "sqlalchemy_inspect") -> SchemaArtifact:
    engine = create_engine(url)
    try:
        return scan_engine_metadata(engine, schema_version=schema_version, source_mode=source_mode)
    finally:
        engine.dispose()
