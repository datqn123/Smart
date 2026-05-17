"""Build suggested question rewrite from terminology issues."""

from __future__ import annotations

import re
from typing import Any

from app.graph.erp_guide.slot_resolution import append_slot_hints_to_question
from app.llm.schemas import DomainIssue


def _collect_replacements(
    issues: list[DomainIssue],
    index: dict[str, Any] | None = None,
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for issue in issues:
        if issue.type != "term_mismatch":
            continue
        old = (issue.user_text or "").strip()
        new = (issue.canonical_vi or "").strip()
        if old and new and old.lower() != new.lower():
            pairs.append((old, new))
    if index:
        for m in index.get("global_misnomers") or []:
            if not isinstance(m, dict):
                continue
            old = str(m.get("phrase_vi", "")).strip()
            new = str(m.get("canonical_vi", "")).strip()
            if old and new:
                pairs.append((old, new))
    pairs.sort(key=lambda p: len(p[0]), reverse=True)
    seen_old: set[str] = set()
    out: list[tuple[str, str]] = []
    for old, new in pairs:
        key = old.lower()
        if key in seen_old:
            continue
        seen_old.add(key)
        out.append((old, new))
    return out


def apply_term_replacements(text: str, pairs: list[tuple[str, str]]) -> str:
    result = text
    for old, new in pairs:
        if not old:
            continue
        pattern = re.compile(re.escape(old), re.IGNORECASE)
        result = pattern.sub(new, result)
    return result.strip()


def build_suggested_rewrite(
    original: str,
    issues: list[DomainIssue],
    *,
    index: dict[str, Any] | None = None,
    missing_slots: list[str] | None = None,
) -> str:
    """Rewrite user question replacing known misnomers with canonical ERP terms."""
    pairs = _collect_replacements(issues, index)
    rewritten = apply_term_replacements(original, pairs) if pairs else original.strip()
    if missing_slots:
        rewritten = append_slot_hints_to_question(rewritten, missing_slots)
    return rewritten if rewritten else original.strip()


def resolve_suggested_rewrite(
    original: str,
    *,
    llm_normalized: str | None,
    issues: list[DomainIssue],
    index: dict[str, Any] | None = None,
    missing_slots: list[str] | None = None,
) -> str:
    """
    Prefer LLM rewrite when it differs from the original; otherwise apply rule-based replacements.
    """
    orig = original.strip()
    norm = (llm_normalized or "").strip()
    slots = list(missing_slots or [])

    if norm and norm.lower() != orig.lower():
        candidate = norm
    else:
        candidate = build_suggested_rewrite(orig, issues, index=index, missing_slots=slots)

    if candidate.lower() == orig.lower() and slots:
        candidate = append_slot_hints_to_question(
            build_suggested_rewrite(orig, issues, index=index, missing_slots=None),
            slots,
        )
    return candidate if candidate else orig
