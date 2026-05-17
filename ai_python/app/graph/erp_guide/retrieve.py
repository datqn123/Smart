"""Keyword retrieval over guide chunks (MVP, no embeddings)."""

from __future__ import annotations

import re
from typing import Any

from app.graph.erp_guide.load_index import chunks_dir, load_chunk_text, load_domain_index


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9à-ỹ]+", text.lower()) if len(t) > 1}


def _score_chunk(query_tokens: set[str], chunk_text: str, module: dict[str, Any]) -> float:
    chunk_tokens = _tokenize(chunk_text)
    overlap = len(query_tokens & chunk_tokens)
    score = float(overlap)
    for term in (module.get("user_terms_vi") or []) + (module.get("user_terms_en") or []):
        if term.lower() in " ".join(query_tokens):
            score += 2.0
    for m in (module.get("common_misnomers") or []):
        phrase = str(m.get("phrase_vi", "")).lower()
        if phrase and phrase in " ".join(query_tokens):
            score += 5.0
    return score


def retrieve_guide_snippets(
    question: str,
    *,
    data_dir: str | None = None,
    max_chunks: int = 3,
    max_chars_per_chunk: int = 3500,
) -> list[dict[str, str]]:
    index = load_domain_index(data_dir)
    modules = index.get("modules") or []
    if not modules or not question.strip():
        return []
    q_tokens = _tokenize(question)
    ranked: list[tuple[float, dict[str, Any]]] = []
    for mod in modules:
        chunk_file = mod.get("chunk_file")
        if not chunk_file:
            continue
        text = load_chunk_text(str(chunk_file), data_dir=data_dir)
        if not text:
            continue
        sc = _score_chunk(q_tokens, text, mod)
        if sc > 0:
            ranked.append((sc, mod))
    ranked.sort(key=lambda x: -x[0])
    out: list[dict[str, str]] = []
    for _, mod in ranked[:max_chunks]:
        chunk_file = str(mod.get("chunk_file", ""))
        text = load_chunk_text(chunk_file, data_dir=data_dir)
        if len(text) > max_chars_per_chunk:
            text = text[:max_chars_per_chunk] + "\n…"
        refs = ", ".join(mod.get("guide_refs") or [])
        out.append(
            {
                "module_id": str(mod.get("id", "")),
                "guide_ref": refs,
                "text": text,
            }
        )
    return out


def detect_heuristic_misnomers(question: str, index: dict[str, Any]) -> list[dict[str, Any]]:
    """Fast path: phrase match before LLM."""
    q = question.lower()
    hits: list[dict[str, Any]] = []
    all_m = list(index.get("global_misnomers") or [])
    for mod in index.get("modules") or []:
        all_m.extend(mod.get("common_misnomers") or [])
    for m in all_m:
        phrase = str(m.get("phrase_vi", "")).lower()
        if phrase and phrase in q:
            hits.append(
                {
                    "type": "term_mismatch",
                    "user_text": phrase,
                    "canonical_vi": m.get("canonical_vi"),
                    "canonical_en": m.get("canonical_en"),
                    "guide_ref": (m.get("module_id") or ""),
                    "severity": "block",
                }
            )
    return hits
