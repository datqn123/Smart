"""Compact table catalog snippet for chart brief (registry text only)."""

from __future__ import annotations

from app.config.graph_settings import GraphSettings
from app.graph.schema_tools import format_catalog_for_prompt, list_tables


def chart_catalog_snippet(settings: GraphSettings) -> str:
    max_n = int(getattr(settings, "chart_brief_catalog_max_tables", 40) or 40)
    catalog, err = list_tables(settings)
    if err or not catalog:
        return ""
    return format_catalog_for_prompt(catalog, max_tables=max(1, max_n))
