"""Align chart brief / question with gen_sql allowlist (merge required tables into schema artifact)."""

from __future__ import annotations

import json
import re
from typing import Any

from app.config.graph_settings import GraphSettings
from app.graph.dbmeta import SchemaArtifact
from app.graph.pg_schema_context import build_schema_artifact_for_table_names


def _blob(*parts: str | None) -> str:
    return " ".join(p for p in parts if p).lower()


def infer_tables_from_chart_context(
    user_q: str,
    data_request: dict[str, Any] | None = None,
) -> list[str]:
    """
    Heuristic required tables from question + Agent_Idea brief (no rigid domain templates).
    Returns registry table names to force into the SQL schema allowlist.
    """
    dr = data_request if isinstance(data_request, dict) else {}
    try:
        dr_text = json.dumps(dr, ensure_ascii=False)
    except Exception:
        dr_text = str(dr)
    text = _blob(user_q, dr_text)

    out: list[str] = []

    def add(name: str) -> None:
        if name not in out:
            out.append(name)

    # Explicit table names in brief values
    for m in re.finditer(
        r"\b(salesorders|financeledger|stockdispatches|orderdetails|customers|products)\b",
        text,
        re.IGNORECASE,
    ):
        add(m.group(1).lower())

    order_phrases = (
        "đơn hàng",
        "don hang",
        "đơn bán",
        "don ban",
        "bán lẻ",
        "ban le",
        "retail",
        "pos",
        "order_channel",
        "kênh bán",
        "kenh ban",
        "nguồn",
        "nguon",
        "nguồn doanh thu",
        "nguon doanh thu",
        "revenue source",
    )
    if any(p in text for p in order_phrases) or dr.get("entity", "").lower() in (
        "orders",
        "order",
        "salesorders",
    ):
        add("salesorders")

    dispatch_phrases = ("xuất kho", "xuat kho", "dispatch", "giao hàng", "giao hang", "shipped")
    if any(p in text for p in dispatch_phrases):
        add("stockdispatches")

    ledger_phrases = (
        "financeledger",
        "sổ cái",
        "so cai",
        "doanh thu",
        "chi phí",
        "chi phi",
        "salesrevenue",
        "dòng tiền",
        "dong tien",
    )
    if any(p in text for p in ledger_phrases) or str(dr.get("source", "")).lower() == "financeledger":
        add("financeledger")

    metric = str(dr.get("metric", "")).lower()
    if "đơn" in metric or "order" in metric:
        add("salesorders")

    return out


def merge_tables_into_artifact(
    settings: GraphSettings,
    artifact: SchemaArtifact,
    extra_tables: list[str],
) -> SchemaArtifact:
    """Prepend required tables, rebuild artifact within sql_max_selected_tables cap."""
    if not extra_tables:
        return artifact
    cap = int(settings.sql_max_selected_tables)
    existing = [t.name for t in artifact.tables]
    merged: list[str] = []
    for t in [*extra_tables, *existing]:
        key = t.strip()
        if not key:
            continue
        canon = None
        for e in existing:
            if e.lower() == key.lower():
                canon = e
                break
        if canon is None:
            for x in merged:
                if x.lower() == key.lower():
                    canon = x
                    break
        name = canon or key
        if name not in merged:
            merged.append(name)
    merged = merged[:cap]
    if set(n.lower() for n in merged) == set(n.lower() for n in existing):
        return artifact
    new_art, err = build_schema_artifact_for_table_names(settings, merged)
    if new_art is not None:
        return new_art
    return artifact


def allowed_tables_prompt_line(artifact: SchemaArtifact) -> str:
    names = sorted(artifact.allowlist_table_names())
    return "Allowed tables ONLY (use no other table names): " + ", ".join(names)
