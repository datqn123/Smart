"""Format domain_context for downstream prompts."""

from __future__ import annotations

from typing import Any


def format_domain_context_block(ctx: dict[str, Any] | None, *, max_snippet_chars: int = 1200) -> str | None:
    if not ctx:
        return None
    lines: list[str] = []
    mods = ctx.get("matched_modules")
    if mods:
        lines.append("Matched modules: " + ", ".join(str(m) for m in mods))
    cov = ctx.get("coverage")
    if cov:
        lines.append(f"Coverage: {cov}")
    for s in ctx.get("guide_snippets") or []:
        if not isinstance(s, dict):
            continue
        ref = s.get("guide_ref", "")
        text = str(s.get("text", ""))[:max_snippet_chars]
        lines.append(f"Guide {ref}:\n{text}")
    if not lines:
        return None
    return "\n".join(lines)
