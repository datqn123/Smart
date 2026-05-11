"""Lightweight SQL similarity for local pool dedup hints (Task007)."""

from __future__ import annotations

import re
from collections.abc import Sequence

import sqlparse

_WS_RE = re.compile(r"\s+")
_NON_IDENT_RE = re.compile(r"[^\w]+", re.UNICODE)


def _tokens(sql: str) -> set[str]:
    s = sql.upper().strip()
    s = _NON_IDENT_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return {t for t in s.split() if t}


def sim_tok(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def _ast_fingerprint(sql: str) -> frozenset[str]:
    """Very coarse structural fingerprint (statement + clause heads)."""
    try:
        stmts = sqlparse.parse(sql)
    except Exception:
        return frozenset()
    parts: set[str] = set()
    for stmt in stmts:
        if stmt is None:
            continue
        parts.add(f"type:{stmt.get_type()}")
        for tok in stmt.flatten():
            if tok.ttype is None:
                continue
            name = str(tok.ttype)
            if "Keyword" in name or "DML" in name:
                parts.add(f"kw:{tok.value.upper()}")
    return frozenset(parts)


def sim_ast(a: str, b: str) -> float:
    fa, fb = _ast_fingerprint(a), _ast_fingerprint(b)
    if not fa and not fb:
        return 1.0
    if not fa or not fb:
        return 0.0
    inter = len(fa & fb)
    union = len(fa | fb)
    return inter / union if union else 0.0


def hybrid_similarity(
    candidate: str,
    previous: str,
    *,
    token_weight: float,
) -> float:
    w = min(max(token_weight, 0.0), 1.0)
    return w * sim_tok(candidate, previous) + (1.0 - w) * sim_ast(candidate, previous)


def max_pool_similarity(candidate: str, pool: Sequence[str], *, token_weight: float) -> float:
    if not pool:
        return 0.0
    return max(hybrid_similarity(candidate, p, token_weight=token_weight) for p in pool)
