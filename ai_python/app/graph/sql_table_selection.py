"""Heuristic + optional LLM table subset selection (Task007)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.dbmeta import SchemaArtifact
from app.llm.schemas import SqlTablePickOutput

if TYPE_CHECKING:
    from app.graph.deps import GraphDeps

logger = logging.getLogger(__name__)


def expand_fk_neighbors(artifact: SchemaArtifact, seeds: list[str]) -> list[str]:
    """Add referenced tables from FK edges one hop from any seed table."""
    names_lower = {t.name.lower(): t.name for t in artifact.tables}
    cur: set[str] = {s for s in seeds if s}
    changed = True
    while changed:
        changed = False
        for t in artifact.tables:
            if t.name not in cur:
                continue
            for fk in t.fks or []:
                ref = fk.get("ref_table")
                if not ref or not isinstance(ref, str):
                    continue
                canonical = names_lower.get(ref.lower())
                if canonical and canonical not in cur:
                    cur.add(canonical)
                    changed = True
    return sorted(cur, key=lambda x: x.lower())


def _score_tables(user_q: str, artifact: SchemaArtifact) -> dict[str, float]:
    q = user_q.lower()
    scores: dict[str, float] = {}
    for t in artifact.tables:
        s = 0.0
        tl = t.name.lower()
        if tl in q:
            s += 10.0
        for c in t.columns:
            cl = c.name.lower()
            if len(cl) > 1 and cl in q:
                s += 2.0
        desc = getattr(t, "description", None) or ""
        if desc:
            for w in desc.lower().split():
                if len(w) > 3 and w in q:
                    s += 0.5
        scores[t.name] = s
    return scores


def heuristic_select_tables(
    user_q: str,
    artifact: SchemaArtifact,
    *,
    max_tables: int,
) -> list[str]:
    """Keyword overlap over table/column/description; fallback to all tables (capped)."""
    all_names = [t.name for t in artifact.tables]
    if not all_names:
        return []
    if len(all_names) <= max_tables:
        return all_names
    scores = _score_tables(user_q, artifact)
    ranked = sorted(all_names, key=lambda n: scores.get(n, 0.0), reverse=True)
    positive = [n for n in ranked if scores.get(n, 0.0) > 0.0]
    if not positive:
        return all_names[:max_tables]
    picked = positive[:max_tables]
    return expand_fk_neighbors(artifact, picked)[:max_tables]


def refine_tables_with_llm(
    *,
    deps: GraphDeps,
    user_q: str,
    artifact: SchemaArtifact,
    heuristic: list[str],
    max_tables: int,
) -> list[str]:
    """Structured pick intersected with artifact names; falls back to heuristic on error."""
    reg = deps.llm_registry
    if reg is None:
        return heuristic
    lines = []
    for t in artifact.tables:
        desc = (getattr(t, "description", None) or "").strip()
        extra = f" — {desc}" if desc else ""
        lines.append(f"- {t.name}{extra}")
    catalog = "\n".join(lines)
    sys = (
        "You choose which database tables are needed to answer the user question. "
        "Reply ONLY with JSON matching the schema: tables = array of table names. "
        "Every name MUST appear exactly as in the catalog list."
    )
    human = (
        f"Catalog:\n{catalog}\n\n"
        f"Heuristic shortlist (hint): {', '.join(heuristic) or '(none)'}\n\n"
        f"User question:\n{user_q}\n\n"
        f"Return at most {max_tables} tables."
    )
    try:
        client = reg.get("sql_table_pick")
        messages = [SystemMessage(content=sys), HumanMessage(content=human)]
        out = client.structured_predict(messages, SqlTablePickOutput)
    except Exception:
        logger.warning("sql_table_pick structured_predict failed; using heuristic", exc_info=True)
        return heuristic
    allowed = {t.name.lower(): t.name for t in artifact.tables}
    picked: list[str] = []
    for raw in out.tables or []:
        canon = allowed.get(str(raw).strip().lower())
        if canon and canon not in picked:
            picked.append(canon)
        if len(picked) >= max_tables:
            break
    if not picked:
        return heuristic
    return expand_fk_neighbors(artifact, picked)[:max_tables]


def select_tables_for_question(
    *,
    deps: GraphDeps,
    user_q: str,
    artifact: SchemaArtifact,
    max_tables: int,
    use_llm: bool,
    min_tables_for_llm: int,
) -> list[str]:
    """Main entry: heuristic, optional LLM refine, FK expansion, cap."""
    h = heuristic_select_tables(user_q, artifact, max_tables=max_tables)
    if (
        use_llm
        and deps.llm_registry is not None
        and len(artifact.tables) >= min_tables_for_llm
    ):
        return refine_tables_with_llm(
            deps=deps,
            user_q=user_q,
            artifact=artifact,
            heuristic=h,
            max_tables=max_tables,
        )
    return h
