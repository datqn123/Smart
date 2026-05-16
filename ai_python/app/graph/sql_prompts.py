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


def _schema_plan_block(schema_plan: dict | None) -> str:
    if not schema_plan:
        return ""
    import json

    hints = schema_plan.get("sql_hints") or []
    joins = schema_plan.get("join_hints") or []
    amb = schema_plan.get("ambiguity_note")
    parts = [
        "Schema plan (from schema_explore — follow exactly):\n",
        json.dumps(
            {
                "metric_id": schema_plan.get("metric_id"),
                "tables": schema_plan.get("tables"),
                "dimensions": schema_plan.get("dimensions"),
            },
            ensure_ascii=False,
        ),
    ]
    if hints:
        parts.append("\nMetric SQL hints:\n" + "\n".join(f"- {h}" for h in hints))
    if joins:
        parts.append("\nRequired join paths when using dimension tables:\n" + "\n".join(f"- {j}" for j in joins))
    if amb:
        parts.append(f"\nAmbiguity note: {amb}")
    parts.append("\n\n")
    return "".join(parts)


def build_gen_sql_user_prompt(
    *,
    mode: Literal["explore", "exploit"],
    schema_block: str,
    feedback_render: str,
    user_q: str,
    seed_sql: str | None,
    sql_limit_max: int,
    dialog_tail: str | None = None,
    planner_data_request_json: str | None = None,
    schema_plan: dict | None = None,
    ledger_first: bool = False,
    multi_table_plan: bool = False,
) -> str:
    tail = (dialog_tail or "").strip()
    dialog_block = (
        "Recent conversation (resolve pronouns like đơn đó / tháng đó; "
        "use only to narrow filters — do not invent columns or numbers not in schema / DB):\n"
        f"{tail}\n\n"
        if tail
        else ""
    )
    planner_block = ""
    pj = (planner_data_request_json or "").strip()
    if pj:
        planner_block = (
            "Data planning brief (JSON from Agent_Idea — satisfy this read-only SELECT; "
            "do not expose or guess secrets; map to allowed tables/columns only):\n"
            f"{pj}\n\n"
        )
    plan_block = _schema_plan_block(schema_plan)
    if ledger_first:
        persona = (
            "You are a careful SQL author for a read-only ERP analytics database. "
            "Revenue, expense, and cashflow questions MUST use financeledger as the fact table "
            "(filter transaction_type; use transaction_date for time periods). "
            "Do not use salesorders alone for totals — join salesorders only for dimensions "
            "(channel, customer, SKU) via reference_type/reference_id from financeledger."
        )
        if multi_table_plan:
            persona += " Use JOINs per schema plan; do not collapse to a single-table shortcut."
    elif mode == "explore":
        persona = (
            "You are a careful SQL author for a read-only analytics database. "
            "Prefer the simplest query that answers the question; use JOINs only when needed."
        )
    else:
        persona = (
            "You revise a SQL query for a read-only database. A previous attempt exists; "
            "fix issues implied by feedback while staying faithful to allowed tables/columns."
        )
    if mode == "explore":
        return (
            f"{persona}\n\n"
            f"{dialog_block}"
            f"{planner_block}"
            f"{plan_block}"
            f"Schema (allowlist tables):\n{schema_block}\n\n"
            f"Prior feedback (only buckets with content):\n{feedback_render}\n\n"
            f"User question: {user_q}\n\n"
            "Hard rules: Your entire reply must be that ONE SELECT only (PostgreSQL). "
            "No Vietnamese/English sentences, no markdown except optional ```sql fences around the query. "
            "If unsure, still output a valid SELECT on the allowlist (aggregates/filters), never prose.\n"
            "Match the Agent_Idea brief for filters: add order_channel = 'Retail' only when the brief explicitly "
            "targets retail/POS/bán lẻ; for company-wide monthly order counts, omit channel filter unless the brief "
            "says all channels still need a breakdown (then GROUP BY order_channel, month).\n\n"
            f"Include a LIMIT clause (≤ {sql_limit_max})."
        )
    seed = (seed_sql or "").strip()
    seed_block = seed[:8000] if seed else "(no previous SQL — treat as fresh generation)"
    return (
        f"{persona} Do not invent columns outside the schema block or the seed SQL.\n\n"
        f"{dialog_block}"
        f"{planner_block}"
        f"{plan_block}"
        f"Schema (allowlist tables):\n{schema_block}\n\n"
        f"Seed SQL (starting point):\n{seed_block}\n\n"
        f"Prior feedback:\n{feedback_render}\n\n"
        f"User question: {user_q}\n\n"
        "Hard rules: Your entire reply must be that ONE SELECT only (PostgreSQL). "
        "No natural-language explanations. No prose instead of SQL.\n"
        "Respect the Agent_Idea brief for channel filters (Retail vs all channels) like explore mode.\n\n"
        f"Include a LIMIT clause (≤ {sql_limit_max})."
    )
