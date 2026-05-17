"""Resolve effective SQL table allowlists (selection + FK join partners).

Table selection caps the schema block for tokens, but validation must allow
1-hop FK neighbors required for JOINs — otherwise gen_sql passes sql_review yet
validate_sql fails with «table not in allowlist».
"""

from __future__ import annotations

from app.graph.dbmeta import SchemaArtifact


def cap_tables_priority(tables: list[str], max_tables: int) -> list[str]:
    """Keep table order; dedupe case-insensitively; stop at max_tables."""
    if max_tables < 1:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for t in tables:
        if not t or not str(t).strip():
            continue
        key = str(t).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(str(t).strip())
        if len(out) >= max_tables:
            break
    return out


def fk_closure_list_ordered(
    artifact: SchemaArtifact,
    seeds: list[str],
    *,
    max_hops: int | None = 1,
) -> list[str]:
    """Seeds first (input order), then FK ref_table neighbors up to max_hops.

    max_hops=None runs until fixpoint (legacy expand_fk_neighbors behavior).
    """
    names_lower = {t.name.lower(): t.name for t in artifact.tables}
    ordered: list[str] = []
    seen: set[str] = set()

    def add(name: str) -> None:
        canon = names_lower.get(name.lower())
        if not canon:
            return
        if canon.lower() in seen:
            return
        seen.add(canon.lower())
        ordered.append(canon)

    for s in seeds:
        add(str(s))

    frontier = list(ordered)
    hop = 0
    while frontier:
        if max_hops is not None and hop >= max_hops:
            break
        next_frontier: list[str] = []
        for tname in frontier:
            tmeta = next((t for t in artifact.tables if t.name.lower() == tname.lower()), None)
            if tmeta is None:
                continue
            for fk in tmeta.fks or []:
                ref = fk.get("ref_table")
                if not ref or not isinstance(ref, str):
                    continue
                before = len(ordered)
                add(ref)
                if len(ordered) > before:
                    next_frontier.append(names_lower[ref.lower()])
        frontier = next_frontier
        hop += 1
    return ordered


def resolve_sql_allowlist(
    artifact: SchemaArtifact,
    selected_tables: list[str] | None,
    *,
    fk_expand: bool = True,
    fk_hops: int = 1,
    max_tables: int | None = None,
) -> list[str] | None:
    """Effective allowlist: selected core tables + optional FK neighbors (capped)."""
    full = artifact.allowlist_table_names()
    if not selected_tables:
        if max_tables is not None and len(full) > max_tables:
            return cap_tables_priority(sorted(full, key=str.lower), max_tables)
        return sorted(full, key=str.lower) if full else None

    core = cap_tables_priority(
        [str(t).strip() for t in selected_tables if str(t).strip()],
        max_tables if max_tables is not None else 10_000,
    )
    if not core:
        return None

    if fk_expand:
        expanded = fk_closure_list_ordered(artifact, core, max_hops=fk_hops)
    else:
        expanded = core

    # Intersect with artifact; drop unknown names.
    known = {t.name.lower(): t.name for t in artifact.tables}
    expanded = [known[t.lower()] for t in expanded if t.lower() in known]

    if max_tables is not None:
        expanded = cap_tables_priority(expanded, max_tables)
    return expanded


def allowlist_tables_prompt_line(tables: list[str] | None, artifact: SchemaArtifact | None = None) -> str:
    """Prompt line listing ONLY tables the validator will accept."""
    if tables:
        names = sorted({t for t in tables if t})
    elif artifact is not None:
        names = sorted(artifact.allowlist_table_names())
    else:
        return ""
    if not names:
        return ""
    return "Allowed tables ONLY (use no other table names): " + ", ".join(names)


def validation_allowlist_from_state(
    artifact: SchemaArtifact,
    state: dict,
    *,
    fk_expand: bool,
    fk_hops: int,
    max_tables: int,
) -> set[str] | None:
    """Prefer sql_allowlist_tables from gen_sql; else rebuild from selected_tables."""
    eff = state.get("sql_allowlist_tables")
    if isinstance(eff, list) and eff:
        names = {str(x).strip().lower() for x in eff if str(x).strip()}
        full = artifact.allowlist_table_names()
        return names & full if names else None

    sel = state.get("selected_tables")
    if isinstance(sel, list) and sel:
        rebuilt = resolve_sql_allowlist(
            artifact,
            [str(x) for x in sel if str(x).strip()],
            fk_expand=fk_expand,
            fk_hops=fk_hops,
            max_tables=max_tables,
        )
        if rebuilt:
            return {t.lower() for t in rebuilt}
    return artifact.allowlist_table_names()
