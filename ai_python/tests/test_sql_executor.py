import pytest
from app.sql.executor import PostgresRoExecutor
from app.sql.guard import SqlGuardError


class _FakeConn:
    def __init__(self, rows): self.rows = rows; self.executed = []
    def execute(self, sql):
        self.executed.append(str(sql))
        class R:
            def __init__(s, rows): s._rows = rows
            def keys(s): return ["id", "name"]
            def fetchall(s): return s._rows
        return R(self.rows)
    def __enter__(self): return self
    def __exit__(self, *a): return False


def test_executor_blocks_non_select_before_running(monkeypatch):  # fact-sql-guard
    conn = _FakeConn([])
    ex = PostgresRoExecutor(connect=lambda: conn, row_limit=100)
    with pytest.raises(SqlGuardError):
        ex.run("DELETE FROM t")
    assert conn.executed == []   # KHONG cham DB


def test_executor_runs_select_and_returns_rows():  # fact-sql-execute
    conn = _FakeConn([(1, "Acme"), (2, "Beta")])
    ex = PostgresRoExecutor(connect=lambda: conn, row_limit=100)
    out = ex.run("SELECT id, name FROM customers")
    assert out["columns"] == ["id", "name"]
    assert out["rows"][0] == {"id": 1, "name": "Acme"}
    assert len(conn.executed) == 1


def test_executor_applies_row_limit():
    conn = _FakeConn([(i, f"c{i}") for i in range(10)])
    ex = PostgresRoExecutor(connect=lambda: conn, row_limit=3)
    out = ex.run("SELECT id, name FROM customers")
    assert len(out["rows"]) == 3


def test_executor_returns_json_safe_values():
    # Postgres tra datetime/date/Decimal/UUID — moi consumer downstream
    # (SM history, data_validator, answer_composer, HITL snapshot) deu
    # json.dumps ket qua nay, nen executor phai chuan hoa tai nguon.
    import datetime
    import decimal
    import json
    import uuid

    uid = uuid.uuid4()
    conn = _FakeConn([(datetime.datetime(2026, 5, 1, 9, 30),
                       datetime.date(2026, 5, 1)),
                      (decimal.Decimal("15000000.50"), uid)])
    ex = PostgresRoExecutor(connect=lambda: conn, row_limit=100)
    out = ex.run("SELECT id, name FROM t")
    json.dumps(out)   # khong duoc raise
    assert out["rows"][0] == {"id": "2026-05-01T09:30:00", "name": "2026-05-01"}
    assert out["rows"][1] == {"id": 15000000.5, "name": str(uid)}


def test_text_wrap_conn_wraps_raw_string():
    # SQLAlchemy 2.x: conn.execute("SELECT ...") raw string -> 'Not an
    # executable object'. _TextWrapConn phai boc text() truoc khi forward.
    from app.sql.executor import _TextWrapConn

    class _Inner:
        def __init__(self): self.received = []; self.closed = False
        def execute(self, stmt):
            assert not isinstance(stmt, str), "raw string phai duoc boc text()"
            self.received.append(stmt)
        def close(self): self.closed = True

    class _FakeText:
        def __init__(self, sql): self.sql = sql

    inner = _Inner()
    with _TextWrapConn(inner, _FakeText) as conn:
        conn.execute("SELECT 1 LIMIT 1")
    assert isinstance(inner.received[0], _FakeText)
    assert inner.received[0].sql == "SELECT 1 LIMIT 1"
    assert inner.closed is True
