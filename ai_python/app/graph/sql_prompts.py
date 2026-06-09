"""Exploration / exploitation SQL prompt builders (Task007)."""

from __future__ import annotations

from typing import Literal

from app.graph.chart_calendar import MonthCalendarSpec, calendar_spine_prompt_block
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
        line = f"- {t.name}({col_names})"
        if t.distinct_values:
            dv_preview = "; ".join(
                f"{k}=[{', '.join(str(v) for v in vs[:5])}]"
                for k, vs in t.distinct_values.items()
            )
            line += f"\n  distinct: {dv_preview}"
        if t.sample_rows:
            row0 = {k: (str(v)[:40] if v is not None else "NULL") for k, v in t.sample_rows[0].items()}
            line += f"\n  sample: {row0}"
        lines.append(line)
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
        if t.relationship_hints:
            head += "\nRelationships:\n" + "\n".join(f"  {h}" for h in t.relationship_hints)
        if t.distinct_values:
            dv_lines = []
            for col_name, vals in t.distinct_values.items():
                preview = ", ".join(str(v) for v in vals[:8])
                more = f" … and {len(vals) - 8} more" if len(vals) > 8 else ""
                dv_lines.append(f"  {col_name}: [{preview}{more}]")
            if dv_lines:
                head += "\nKnown distinct values:\n" + "\n".join(dv_lines)
        if t.sample_rows:
            sample_lines = []
            for i, row in enumerate(t.sample_rows[:3]):
                truncated = {k: (str(v)[:80] if v is not None else "NULL") for k, v in row.items()}
                sample_lines.append(f"  row{i+1}: {truncated}")
            if sample_lines:
                head += "\nSample rows:\n" + "\n".join(sample_lines)
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
    chart_thread_context: str | None = None,
    allowed_tables_line: str | None = None,
    month_calendar: MonthCalendarSpec | None = None,
    domain_context_block: str | None = None,
    business_scope_block: str | None = None,
    data_context_block: str | None = None,
    query_table_mode: bool = False,
    retry_rewrite_block: str | None = None,
) -> str:
    domain_block = (domain_context_block or "").strip()
    if domain_block:
        domain_block = f"ERP domain context (canonical terms — follow for filters/entities):\n{domain_block}\n\n"
    tail = (dialog_tail or "").strip()
    dialog_block = (
        "Recent conversation (resolve pronouns like đơn đó / tháng đó; "
        "use only to narrow filters — do not invent columns or numbers not in schema / DB):\n"
        f"{tail}\n\n"
        if tail
        else ""
    )
    chart_ctx_block = ""
    ctx = (chart_thread_context or "").strip()
    if ctx:
        chart_ctx_block = (
            "Chart thread context (stay consistent with prior answer in this thread):\n"
            f"{ctx}\n\n"
        )
    planner_block = ""
    pj = (planner_data_request_json or "").strip()
    if pj:
        ts_hint = (
            "time_series: use month calendar spine (generate_series + LEFT JOIN) when "
            "include_zero_months is true; otherwise GROUP BY time/category."
            if month_calendar
            else "time_series needs multiple buckets or calendar spine when include_zero_months is true."
        )
        planner_block = (
            "Chart/data planning brief (JSON from Agent_Idea — satisfy this read-only SELECT; "
            f"{ts_hint} "
            "Do not add Retail/channel filters unless the brief says so; "
            "map to allowed tables/columns only):\n"
            f"{pj}\n\n"
        )
    calendar_block = calendar_spine_prompt_block(month_calendar) + "\n\n" if month_calendar else ""
    plan_block = _schema_plan_block(schema_plan)
    allow_block = ""
    al = (allowed_tables_line or "").strip()
    if al:
        allow_block = f"{al}\n\n"
    scope_block = (business_scope_block or "").strip()
    if scope_block:
        scope_block = f"{scope_block}\n\n"
    data_block = (data_context_block or "").strip()
    if data_block:
        data_block = f"{data_block}\n\n"
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
    query_table_block = ""
    if query_table_mode:
        query_table_block = (
            "Data-table UI mode: the user will see a wide editable grid — SELECT **6–12 useful "
            "business columns**, not a minimal 2–3 column answer.\n"
            "- List columns explicitly (no SELECT *).\n"
            "- Omit `id` and `category_id` from the SELECT list (use them only in JOIN/WHERE if needed).\n"
            "- `products` listing: prefer "
            "sku_code, barcode, name, description, weight, status, created_at, updated_at.\n"
            "- Filter by **giá vốn / cost_price**: use table **`productpricehistory`** "
            "(exact name) joined to `products`; filter `pph.cost_price`. "
            "Prefer latest price per product via `JOIN productunits` + `LATERAL` "
            "or `DISTINCT ON (p.id)` — table name is **not** `product_price_history`.\n"
            "- `stockreceipts` / `stockdispatches`: include codes, dates, amounts, status — not only counts.\n"
            "- Use schema snake_case names (sku_code, not SKU_CODE).\n\n"
        )
    retry_block = (retry_rewrite_block or "").strip()
    if retry_block:
        retry_block = f"{retry_block}\n\n"
    if mode == "explore":
        return (
            f"{persona}\n\n"
            f"{retry_block}"
            f"{domain_block}"
            f"{dialog_block}"
            f"{chart_ctx_block}"
            f"{planner_block}"
            f"{calendar_block}"
            f"{plan_block}"
            f"{allow_block}"
            f"{scope_block}"
            f"{data_block}"
            f"{query_table_block}"
            f"Schema (allowlist tables):\n{schema_block}\n\n"
            f"Prior feedback (only buckets with content):\n{feedback_render}\n\n"
            f"User question: {user_q}\n\n"
            "Hard rules: Your entire reply must be that ONE SELECT only (PostgreSQL). "
            "No Vietnamese/English sentences, no markdown except optional ```sql fences around the query. "
            "If unsure, still output a valid SELECT using ONLY tables listed above, never prose.\n"
            "Match the Agent_Idea brief for filters: add order_channel = 'Retail' only when the brief explicitly "
            "targets retail/POS/bán lẻ; for company-wide monthly order counts, omit channel filter unless the brief "
            "says all channels still need a breakdown (then GROUP BY order_channel, month).\n\n"
            f"Include a LIMIT clause (≤ {sql_limit_max})."
        )
    seed = (seed_sql or "").strip()
    seed_block = seed[:8000] if seed else "(no previous SQL — treat as fresh generation)"
    return (
        f"{persona} Do not invent columns outside the schema block or the seed SQL.\n\n"
        f"{retry_block}"
        f"{domain_block}"
        f"{dialog_block}"
        f"{chart_ctx_block}"
        f"{planner_block}"
        f"{calendar_block}"
        f"{plan_block}"
        f"{allow_block}"
        f"{scope_block}"
        f"{data_block}"
        f"{query_table_block}"
        f"Schema (allowlist tables):\n{schema_block}\n\n"
        f"Seed SQL (starting point):\n{seed_block}\n\n"
        f"Prior feedback:\n{feedback_render}\n\n"
        f"User question: {user_q}\n\n"
        "Hard rules: Your entire reply must be that ONE SELECT only (PostgreSQL). "
        "No natural-language explanations. No prose instead of SQL.\n"
        "Apply every [sql_fix] instruction; change FROM/JOIN/GROUP BY/WHERE vs the seed SQL.\n"
        "Respect the Agent_Idea brief for channel filters (Retail vs all channels) like explore mode.\n\n"
        f"Include a LIMIT clause (≤ {sql_limit_max})."
    )


def build_retry_rewrite_block(
    *,
    attempt: int,
    prior_sql: str | None,
    feedback_render: str,
    duplicate_warning: bool = False,
) -> str:
    """Mandatory rewrite section injected into gen_sql on retries."""
    if attempt <= 1 or not feedback_render.strip():
        return ""
    parts = [
        "## MANDATORY SQL REWRITE",
        f"Attempt {attempt}: the previous SELECT was rejected. Follow all fix instructions below.",
        feedback_render,
    ]
    seed = (prior_sql or "").strip()
    if seed:
        parts.append(
            "Rejected SQL (starting reference only — you must change structure, not echo verbatim):\n"
            f"```sql\n{seed[:6000]}\n```"
        )
    if duplicate_warning:
        parts.append(
            "Your last output matched a prior attempt. Use different tables, joins, or GROUP BY columns."
        )
    return "\n".join(parts)
