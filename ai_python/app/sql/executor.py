from __future__ import annotations
import datetime
import decimal
import uuid
from typing import Any, Callable, Protocol
from app.sql.guard import assert_read_only


def _jsonable(v: Any) -> Any:
    """Moi consumer downstream (SM history, validator/composer prompt, HITL
    snapshot) deu json.dumps ket qua query — chuan hoa 1 lan tai nguon."""
    if isinstance(v, (datetime.datetime, datetime.date, datetime.time)):
        return v.isoformat()
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, uuid.UUID):
        return str(v)
    if isinstance(v, (bytes, memoryview)):
        return bytes(v).hex()
    return v


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
            rows = [{c: _jsonable(v) for c, v in zip(cols, r)}
                    for r in result.fetchall()[:limit]]
        return {"columns": cols, "rows": rows}


class _TextWrapConn:
    """SQLAlchemy 2.x khong nhan raw string ('Not an executable object') ->
    boc text() o day de executor.run() giu interface execute(sql_str)
    chung voi test fake. text_fn inject de test khong can engine that."""

    def __init__(self, conn, text_fn):
        self._conn = conn
        self._text = text_fn

    def execute(self, sql):
        return self._conn.execute(self._text(sql) if isinstance(sql, str) else sql)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._conn.close()
        return False


def make_pg_connect(database_url_ro: str):
    """Factory connect() that cho production. Mo transaction READ ONLY o
    tang ket noi. Test KHONG dung ham nay (inject connect= gia)."""
    from sqlalchemy import create_engine, text

    engine = create_engine(database_url_ro, pool_pre_ping=True)

    def _connect():
        conn = engine.connect()
        conn.execute(text("SET TRANSACTION READ ONLY"))
        return _TextWrapConn(conn, text)

    return _connect
