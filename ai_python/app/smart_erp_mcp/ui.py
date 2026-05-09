from __future__ import annotations

from typing import Any


def ui_build_form_spec(
    title: str,
    fields: list[dict[str, Any]],
    defaults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": True,
        "spec": {
            "kind": "form",
            "version": 1,
            "title": title,
            "fields": fields,
            "defaults": defaults or {},
        },
    }


def ui_build_table_spec(title: str, columns: list[str], rows: list[list[Any]]) -> dict[str, Any]:
    return {
        "ok": True,
        "spec": {
            "kind": "table",
            "version": 1,
            "title": title,
            "columns": columns,
            "rows": rows,
        },
    }


def viz_build_chart_spec(
    chart_type: str,
    labels: list[str],
    series: dict[str, list[float]],
) -> dict[str, Any]:
    return {
        "ok": True,
        "spec": {
            "kind": "chart",
            "version": 1,
            "chart_type": chart_type,
            "labels": labels,
            "series": series,
        },
    }
