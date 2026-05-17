"""Defensive read-only checks before dispatching SQL to external executors."""

from __future__ import annotations

import re

_DDL_DML = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|UPSERT|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)
_TX = re.compile(r"\b(BEGIN|COMMIT|ROLLBACK|SAVEPOINT)\b", re.IGNORECASE)
_HAS_SELECT = re.compile(r"\bSELECT\b", re.IGNORECASE)


class SqlSafetyError(ValueError):
    """Raised when SQL fails executor-level defensive validation."""


def _strip_leading_line_comments(sql: str) -> str:
    """Remove full lines that are SQL `--` comments (simple heuristic)."""
    kept: list[str] = []
    for line in sql.splitlines():
        if line.strip().startswith("--"):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def _is_read_only_query_head(head: str) -> bool:
    """Allow SELECT and WITH ... SELECT (CTE calendar spine, etc.)."""
    h = head.lstrip()
    if not h:
        return False
    upper = h.upper()
    if upper.startswith("SELECT"):
        return True
    if upper.startswith("WITH"):
        return _HAS_SELECT.search(h) is not None
    return False


def enforce_read_only_sql(sql: str) -> None:
    """Reject DDL/DML, transaction control, and multi-statement payloads."""
    text = _strip_leading_line_comments((sql or "").strip())
    if not text:
        raise SqlSafetyError("empty sql")
    parts = [p.strip() for p in text.split(";") if p.strip()]
    if len(parts) != 1:
        raise SqlSafetyError("multi-statement sql is not allowed")
    head = parts[0].lstrip()
    if not _is_read_only_query_head(head):
        raise SqlSafetyError("only SELECT statements are allowed")
    if _DDL_DML.search(text):
        raise SqlSafetyError("ddl/dml keywords are not allowed")
    if _TX.search(text):
        raise SqlSafetyError("transaction control statements are not allowed")
