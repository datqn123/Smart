"""Rewrite exact name equality to ILIKE for Vietnamese display names (case-insensitive)."""

from __future__ import annotations

import re

# Display-name columns — not enum literals (those use fix_enum_literals_in_sql).
_NAME_EQ_PATTERN = re.compile(
    r"\b((?:[a-zA-Z_][\w]*\.)?)(name|category_name)\s*=\s*'([^']*)'",
    re.IGNORECASE,
)


def fix_name_equality_to_ilike(sql: str) -> tuple[str, list[str]]:
    """
    ``categories.name = 'Điện tử 1'`` → ``categories.name ILIKE 'Điện tử 1'``
    so it matches ``Điện Tử 1`` in PostgreSQL.
    """
    notes: list[str] = []

    def _repl(match: re.Match[str]) -> str:
        prefix = match.group(1) or ""
        col = match.group(2)
        val = match.group(3)
        notes.append(f"{prefix}{col}: '=' → ILIKE (case-insensitive) for '{val}'")
        return f"{prefix}{col} ILIKE '{val}'"

    fixed = _NAME_EQ_PATTERN.sub(_repl, sql)
    return fixed, notes
