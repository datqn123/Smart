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
