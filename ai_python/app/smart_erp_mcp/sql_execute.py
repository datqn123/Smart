from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import Any

from .catalog import allowlist_lower, seed_demo_db
from .sql_validate import SqlValidationError, transpile_to_sqlite, validate_select

MAX_ROWS = 500


def sql_execute_read(sql: str) -> dict[str, Any]:
    """Validate against allowlist, run on ephemeral SQLite (demo)."""
    allowed = allowlist_lower()
    try:
        validate_select(sql, allowed)
        sqlite_sql = transpile_to_sqlite(sql)
    except SqlValidationError as e:
        return {"ok": False, "error": {"code": e.code, "message": e.message}}

    conn = sqlite3.connect(":memory:")
    try:
        seed_demo_db(conn)
        cur = conn.execute(sqlite_sql)
        cols = [d[0] for d in (cur.description or ())]
        rows = cur.fetchmany(MAX_ROWS + 1)
        if len(rows) > MAX_ROWS:
            return {
                "ok": False,
                "error": {
                    "code": "VALIDATION_FAILED",
                    "message": f"row cap exceeded ({MAX_ROWS})",
                },
            }
        data_as_of = datetime.now(UTC).isoformat()
        return {
            "ok": True,
            "columns": cols,
            "rows": [list(r) for r in rows],
            "row_count": len(rows),
            "data_as_of": data_as_of,
        }
    except sqlite3.Error as e:
        return {
            "ok": False,
            "error": {"code": "VALIDATION_FAILED", "message": f"sqlite: {e}"},
        }
    finally:
        conn.close()
