"""Compact table catalog snippet for chart brief (ranked + inferred, aligned with gen_sql)."""

from __future__ import annotations

from app.config.graph_settings import GraphSettings
from app.graph.chart_schema_merge import infer_tables_from_chart_context
from app.graph.pg_schema_context import list_registry_tables, rank_tables_for_question
from app.graph.schema_tools import format_catalog_for_prompt


def chart_catalog_snippet(settings: GraphSettings, user_q: str = "") -> str:
    max_n = int(getattr(settings, "chart_brief_catalog_max_tables", 40) or 40)
    if max_n <= 0:
        return ""
    rows, err = list_registry_tables(settings)
    if err or not rows:
        return ""
    ranked = rank_tables_for_question(user_q, rows, max_tables=max_n) if user_q.strip() else []
    extra = infer_tables_from_chart_context(user_q, None)
    desc_map = {r[0]: r[1] for r in rows}
    reg_lower = {r[0].lower(): r[0] for r in rows}
    names: list[str] = []
    for t in [*extra, *ranked]:
        canon = reg_lower.get(t.lower())
        if canon and canon not in names:
            names.append(canon)
    if not names:
        names = [r[0] for r in rows[:max_n]]
    catalog = [{"table_name": n, "description": desc_map.get(n, "")} for n in names[:max_n]]
    return format_catalog_for_prompt(catalog, max_tables=max_n)
