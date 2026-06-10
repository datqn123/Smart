from __future__ import annotations
from typing import Any, Callable, Protocol
from app.sql.guard import assert_read_only


class SqlExecutor(Protocol):
    def run(self, sql: str, *, row_limit: int | None = None) -> dict[str, Any]: ...


class PostgresRoExecutor:
    """Executor read-only thang toi Postgres (R1).

    Read-only enforce o TANG KET NOI: connection mo transaction read-only
    (`SET TRANSACTION READ ONLY`) + dung role/DSN read-only. Guard sqlparse
    la lop thu hai, chay TRUOC khi gui query.
    """

    def __init__(self, *, connect: Callable[[], Any], row_limit: int = 100):
        self._connect = connect
        self._row_limit = row_limit

    def run(self, sql: str, *, row_limit: int | None = None) -> dict[str, Any]:
        assert_read_only(sql)                      # chan non-SELECT TRUOC khi chay
        limit = row_limit or self._row_limit
        with self._connect() as conn:
            result = conn.execute(sql)
            cols = list(result.keys())
            rows = [dict(zip(cols, r)) for r in result.fetchall()[:limit]]
        return {"columns": cols, "rows": rows}


def make_pg_connect(database_url_ro: str):
    """Factory connect() that cho production. Mo transaction READ ONLY o
    tang ket noi. Test KHONG dung ham nay (inject connect= gia)."""
    from sqlalchemy import create_engine, text

    engine = create_engine(database_url_ro, pool_pre_ping=True)

    def _connect():
        conn = engine.connect()
        conn.execute(text("SET TRANSACTION READ ONLY"))
        return conn

    return _connect
