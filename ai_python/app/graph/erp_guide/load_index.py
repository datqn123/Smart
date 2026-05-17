"""Load erp_domain_index.json and guide chunks."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "erp"


@lru_cache(maxsize=1)
def load_domain_index(data_dir: str | None = None) -> dict[str, Any]:
    base = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
    path = base / "erp_domain_index.json"
    if not path.is_file():
        return {
            "version": "0",
            "modules": [],
            "global_misnomers": [],
            "global_out_of_scope": [],
            "ai_rules_summary": [],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def chunks_dir(data_dir: str | None = None) -> Path:
    base = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
    return base / "guide_chunks"


def load_chunk_text(chunk_file: str, data_dir: str | None = None) -> str:
    path = chunks_dir(data_dir) / chunk_file
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def format_index_for_prompt(index: dict[str, Any], *, max_modules: int = 20) -> str:
    """Compact module list for domain_guard LLM."""
    lines: list[str] = []
    for rule in index.get("ai_rules_summary") or []:
        lines.append(f"- AI rule: {rule}")
    lines.append("\n## Modules in Smart ERP")
    for mod in (index.get("modules") or [])[:max_modules]:
        mid = mod.get("id", "?")
        vi = mod.get("title_vi", "")
        en = mod.get("title_en", "")
        refs = ", ".join(mod.get("guide_refs") or [])
        vi_terms = ", ".join((mod.get("user_terms_vi") or [])[:8])
        lines.append(f"- [{mid}] {vi} / {en} ({refs}) terms_vi: {vi_terms or '—'}")
        for m in mod.get("common_misnomers") or []:
            lines.append(
                f"  misnomer: «{m.get('phrase_vi')}» → «{m.get('canonical_vi')}» ({m.get('note') or ''})"
            )
    lines.append("\n## Global misnomers")
    for m in index.get("global_misnomers") or []:
        lines.append(
            f"- «{m.get('phrase_vi')}» → «{m.get('canonical_vi')}» / {m.get('canonical_en', '')}"
        )
    oos = index.get("global_out_of_scope") or []
    if oos:
        lines.append("\n## Out of scope examples: " + ", ".join(oos[:12]))
    return "\n".join(lines)
