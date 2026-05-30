"""Schema explorer tools: list_tables, describe_table, artifact build."""

from __future__ import annotations

import logging
from typing import Any

from app.config.graph_settings import GraphSettings
from app.graph.dbmeta import ColumnMeta, SchemaArtifact
from app.graph.pg_schema_context import (
    build_schema_artifact_for_table_names,
    list_registry_tables,
)
from app.graph.spring_describe_client import SpringDescribeClient, SpringDescribeError

logger = logging.getLogger(__name__)

_CATALOG_DESC_MAX = 400


def list_tables(settings: GraphSettings) -> tuple[list[dict[str, str]], str | None]:
    """Tool: catalog from ai_table_description."""
    rows, err = list_registry_tables(settings)
    if err:
        return [], err
    out: list[dict[str, str]] = []
    for name, desc in rows:
        d = (desc or "").strip()
        if len(d) > _CATALOG_DESC_MAX:
            d = d[: _CATALOG_DESC_MAX - 1] + "…"
        out.append({"table_name": name, "description": d})
    return out, None


def describe_table(
    client: SpringDescribeClient | None,
    table_name: str,
    *,
    correlation_id: str | None = None,
    bearer_token: str | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    """Tool: column metadata via Spring /sql/describe (optional)."""
    if client is None:
        return [], "describe client unavailable (stub mode or missing SPRING_SQL_URL)"
    try:
        data = client.describe(
            table_name,
            correlation_id=correlation_id,
            bearer_token=bearer_token,
        )
    except SpringDescribeError as exc:
        return [], str(exc)
    cols_raw = data.get("columns") or []
    cols: list[dict[str, Any]] = []
    for c in cols_raw:
        if isinstance(c, dict) and c.get("name"):
            cols.append(
                {
                    "name": str(c["name"]),
                    "type": c.get("type"),
                    "nullable": c.get("nullable"),
                }
            )
    return cols, None


def merge_describe_into_artifact(artifact: SchemaArtifact, table_name: str, cols: list[dict[str, Any]]) -> None:
    """Overlay Spring describe types onto artifact columns when present."""
    t_lower = table_name.lower()
    for t in artifact.tables:
        if t.name.lower() != t_lower:
            continue
        by_name = {str(c["name"]).lower(): c for c in cols if c.get("name")}
        new_cols: list[ColumnMeta] = []
        for cm in t.columns:
            ext = by_name.get(cm.name.lower())
            if ext and ext.get("type"):
                new_cols.append(
                    cm.model_copy(
                        update={
                            "type": str(ext.get("type")),
                            "nullable": ext.get("nullable") if ext.get("nullable") is not None else cm.nullable,
                        }
                    )
                )
            else:
                new_cols.append(cm)
        t.columns = new_cols
        break


def build_artifact_for_tables(
    settings: GraphSettings,
    table_names: list[str],
    *,
    describe_client: SpringDescribeClient | None = None,
    correlation_id: str | None = None,
    bearer_token: str | None = None,
    describe_max: int = 6,
) -> tuple[SchemaArtifact | None, str | None]:
    """Build SchemaArtifact for selected tables; optional Spring describe overlay."""
    art, err = build_schema_artifact_for_table_names(settings, table_names)
    if art is None:
        return None, err
    if describe_client is None:
        return art, None
    n = 0
    for tname in table_names:
        if n >= describe_max:
            break
        cols, derr = describe_table(
            describe_client,
            tname,
            correlation_id=correlation_id,
            bearer_token=bearer_token,
        )
        if derr:
            logger.debug("describe_table %s skipped: %s", tname, derr)
            continue
        if cols:
            merge_describe_into_artifact(art, tname, cols)
            n += 1
    return art, None


def format_catalog_for_prompt(catalog: list[dict[str, str]], *, max_tables: int = 64) -> str:
    lines: list[str] = []
    for row in catalog[:max_tables]:
        name = row.get("table_name") or "?"
        desc = row.get("description") or ""
        lines.append(f"- {name}: {desc}")
    return "\n".join(lines) if lines else "(empty catalog)"
