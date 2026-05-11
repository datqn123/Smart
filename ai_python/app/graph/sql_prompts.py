"""Exploration / exploitation SQL prompt builders (Task007)."""

from __future__ import annotations

from typing import Literal

from app.graph.dbmeta import ColumnMeta, SchemaArtifact

# Cap per-column registry text in enriched schema blocks (token control).
SCHEMA_COLUMN_DESCRIPTION_MAX_CHARS = 320


def _truncate_col_desc(text: str, *, max_chars: int = SCHEMA_COLUMN_DESCRIPTION_MAX_CHARS) -> str:
    t = (text or "").strip()
    if len(t) <= max_chars:
        return t
    if max_chars <= 1:
        return "…"
    return t[: max_chars - 1].rstrip() + "…"


def _format_enriched_column_line(c: ColumnMeta) -> str:
    typ = c.type or "?"
    base = f"{c.name} ({typ})"
    if c.description:
        return f"- {base}: {_truncate_col_desc(c.description)}"
    return f"- {base}"


def _lines_simple(artifact: SchemaArtifact, table_names: list[str] | None) -> list[str]:
    allow = {n.lower() for n in (table_names or [])}
    lines: list[str] = []
    for t in artifact.tables:
        if allow and t.name.lower() not in allow:
            continue
        col_names = ", ".join(c.name for c in t.columns)
        lines.append(f"- {t.name}({col_names})")
    return lines


def _lines_enriched(artifact: SchemaArtifact, table_names: list[str] | None) -> list[str]:
    allow = {n.lower() for n in (table_names or [])}
    blocks: list[str] = []
    for t in artifact.tables:
        if allow and t.name.lower() not in allow:
            continue
        col_lines = "\n".join(_format_enriched_column_line(c) for c in t.columns)
        head = f"### {t.name}\nColumns:\n{col_lines}"
        desc = getattr(t, "description", None)
        if desc:
            head += f"\nTable description: {desc}"
        if t.pk:
            head += f"\nPK: {', '.join(t.pk)}"
        if t.fks:
            fk_txt = "; ".join(
                f"{fk.get('column')} -> {fk.get('ref_table')}.{fk.get('ref_column')}"
                for fk in t.fks
                if fk.get("column") and fk.get("ref_table")
            )
            if fk_txt:
                head += f"\nFKs: {fk_txt}"
        blocks.append(head)
    return blocks


def format_schema_block(
    artifact: SchemaArtifact,
    *,
    selected_tables: list[str] | None,
    enriched: bool,
) -> str:
    names = selected_tables
    if enriched:
        body = "\n\n".join(_lines_enriched(artifact, names))
    else:
        body = "\n".join(_lines_simple(artifact, names))
    return body if body.strip() else "(no tables in selection)"


def build_gen_sql_user_prompt(
    *,
    mode: Literal["explore", "exploit"],
    schema_block: str,
    feedback_render: str,
    user_q: str,
    seed_sql: str | None,
    sql_limit_max: int,
) -> str:
    if mode == "explore":
        persona = (
            "You are a careful SQL author for a read-only analytics database. "
            "Prefer the simplest query that answers the question; use JOINs only when needed."
        )
        return (
            f"{persona}\n\n"
            f"Schema (allowlist tables):\n{schema_block}\n\n"
            f"Prior feedback (only buckets with content):\n{feedback_render}\n\n"
            f"User question: {user_q}\n\n"
            f"Respond with EXACTLY ONE SELECT statement. Include a LIMIT clause (≤ {sql_limit_max})."
        )
    seed = (seed_sql or "").strip()
    seed_block = seed[:8000] if seed else "(no previous SQL — treat as fresh generation)"
    return (
        "You revise a SQL query for a read-only database. A previous attempt exists; "
        "fix issues implied by feedback while staying faithful to allowed tables/columns. "
        "Do not invent columns outside the schema block or the seed SQL.\n\n"
        f"Schema (allowlist tables):\n{schema_block}\n\n"
        f"Seed SQL (starting point):\n{seed_block}\n\n"
        f"Prior feedback:\n{feedback_render}\n\n"
        f"User question: {user_q}\n\n"
        f"Respond with EXACTLY ONE SELECT statement. Include a LIMIT clause (≤ {sql_limit_max})."
    )
