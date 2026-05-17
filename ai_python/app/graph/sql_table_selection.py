"""Heuristic + optional LLM table subset selection (Task007)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.dbmeta import SchemaArtifact
from app.graph.sql_allowlist import cap_tables_priority, fk_closure_list_ordered
from app.graph.sql_query_domain import (
    boost_table_scores_for_domain,
    default_tables_for_domain,
    detect_sql_query_domain,
)
from app.prompts.load import load_agent_json_contract, load_agent_prompt
from app.llm.schemas import SqlTablePickOutput

if TYPE_CHECKING:
    from app.graph.deps import GraphDeps

logger = logging.getLogger(__name__)

_STAFF_PHRASES = (
    "nhân viên",
    "nhan vien",
    "người tạo",
    "nguoi tao",
    "người lập",
    "nguoi lap",
    "staff",
    "nhân sự",
    "nhan su",
    "tạo phiếu",
    "tao phieu",
)

_RECEIPT_PHRASES = (
    "phiếu nhập",
    "phieu nhap",
    "nhập kho",
    "nhap kho",
    "stockreceipt",
)

# Dropped first when staff context needs users within table cap.
_DROP_WHEN_STAFF = (
    "partnerdebts",
    "productunits",
    "stockdispatchdetail",
    "stockdispatches",
    "warehouses",
)

_TABLE_PICK_SYSTEM = load_agent_prompt("sql_table_pick")
_TABLE_PICK_JSON_CONTRACT = load_agent_json_contract("sql_table_pick")


def expand_fk_neighbors(artifact: SchemaArtifact, seeds: list[str]) -> list[str]:
    """Add all FK ref_table neighbors (fixpoint); seeds keep priority order."""
    return fk_closure_list_ordered(artifact, seeds, max_hops=None)


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
    domain = detect_sql_query_domain(user_q)
    scores = boost_table_scores_for_domain(scores, domain)
    ranked = sorted(all_names, key=lambda n: scores.get(n, 0.0), reverse=True)
    positive = [n for n in ranked if scores.get(n, 0.0) > 0.0]
    if not positive:
        picked = default_tables_for_domain(domain) or all_names[:max_tables]
    else:
        picked = positive[:max_tables]
    return cap_tables_priority(expand_fk_neighbors(artifact, picked), max_tables)


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
    human = (
        f"Catalog:\n{catalog}\n\n"
        f"Heuristic shortlist (hint): {', '.join(heuristic) or '(none)'}\n\n"
        f"User question:\n{user_q}\n\n"
        f"Return at most {max_tables} tables."
    )
    try:
        client = reg.get("sql_table_pick")
        messages = [SystemMessage(content=_TABLE_PICK_SYSTEM), HumanMessage(content=human)]
        kwargs: dict = {}
        if _TABLE_PICK_JSON_CONTRACT:
            kwargs["json_output_contract"] = _TABLE_PICK_JSON_CONTRACT
        out = client.structured_predict(messages, SqlTablePickOutput, **kwargs)
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
    return cap_tables_priority(expand_fk_neighbors(artifact, picked), max_tables)


def question_needs_users_table(user_q: str) -> bool:
    q = user_q.lower()
    return any(p in q for p in _STAFF_PHRASES)


def ensure_context_tables_for_question(
    user_q: str,
    tables: list[str],
    *,
    max_tables: int,
    known_tables: set[str] | None = None,
) -> list[str]:
    """Inject users / receipt tables when question wording requires them (within cap)."""
    if not question_needs_users_table(user_q):
        return tables[:max_tables]

    known_lower = {t.lower() for t in known_tables} if known_tables else None
    cur = list(tables)
    seen = {t.lower() for t in cur}

    def can_add(name: str) -> bool:
        if known_lower is not None and name.lower() not in known_lower:
            return False
        return name.lower() not in seen

    def add(name: str) -> None:
        if can_add(name):
            cur.append(name)
            seen.add(name.lower())

    q = user_q.lower()
    if any(p in q for p in _RECEIPT_PHRASES):
        add("stockreceipts")
        add("suppliers")
    add("users")

    if len(cur) > max_tables:
        drop = {d.lower() for d in _DROP_WHEN_STAFF}
        priority = [t for t in cur if t.lower() not in drop]
        rest = [t for t in cur if t.lower() in drop]
        cur = priority + rest
    return cur[:max_tables]


def question_needs_cost_price(user_q: str) -> bool:
    q = user_q.lower()
    return any(
        p in q
        for p in (
            "giá vốn",
            "gia von",
            "giá bán",
            "gia ban",
            "cost price",
            "cost_price",
            "sale price",
            "sale_price",
        )
    )


def ensure_price_tables_for_question(
    user_q: str,
    tables: list[str],
    *,
    max_tables: int,
    known_tables: set[str] | None = None,
) -> list[str]:
    """Inject products + price history + base unit when filtering by cost/sale price."""
    if not question_needs_cost_price(user_q):
        return tables[:max_tables]
    known_lower = {t.lower() for t in known_tables} if known_tables else None
    cur = list(tables)
    seen = {t.lower() for t in cur}

    def add(name: str) -> None:
        if known_lower is not None and name.lower() not in known_lower:
            return
        if name.lower() not in seen:
            cur.insert(0, name)
            seen.add(name.lower())

    for t in ("productunits", "productpricehistory", "products"):
        add(t)
    return cur[:max_tables]


def ensure_domain_tables_for_question(
    user_q: str,
    tables: list[str],
    *,
    max_tables: int,
    known_tables: set[str] | None = None,
) -> list[str]:
    """Inject domain-required tables (inventory snapshot, receipts, …) within cap."""
    domain = detect_sql_query_domain(user_q)
    seeds = default_tables_for_domain(domain)
    if not seeds:
        return tables[:max_tables]
    known_lower = {t.lower() for t in known_tables} if known_tables else None
    cur = list(tables)
    seen = {t.lower() for t in cur}

    def add(name: str) -> None:
        if known_lower is not None and name.lower() not in known_lower:
            return
        if name.lower() not in seen:
            cur.insert(0, name)
            seen.add(name.lower())

    for t in reversed(seeds):
        add(t)
    return cur[:max_tables]


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
    known = {t.name for t in artifact.tables}
    h = heuristic_select_tables(user_q, artifact, max_tables=max_tables)
    if (
        use_llm
        and deps.llm_registry is not None
        and len(artifact.tables) >= min_tables_for_llm
    ):
        h = refine_tables_with_llm(
            deps=deps,
            user_q=user_q,
            artifact=artifact,
            heuristic=h,
            max_tables=max_tables,
        )
    h = cap_tables_priority(expand_fk_neighbors(artifact, h), max_tables)
    h = ensure_domain_tables_for_question(
        user_q, h, max_tables=max_tables, known_tables=known
    )
    h = ensure_context_tables_for_question(
        user_q, h, max_tables=max_tables, known_tables=known
    )
    h = ensure_price_tables_for_question(
        user_q, h, max_tables=max_tables, known_tables=known
    )
    return h[:max_tables]
