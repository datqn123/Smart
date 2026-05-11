"""Task006 — SqlExecutor production client + DB metadata CLI."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import httpx
import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine

from app.config.graph_settings import GraphSettings
from app.graph.dbmeta import load_schema_yaml_path
from app.graph.dbmeta_scan import scan_engine_metadata
from app.graph.sql_executor import HttpSpringSqlExecutor, SqlExecutorError, build_sql_executor
from app.graph.sql_safety import SqlSafetyError, enforce_read_only_sql


def test_build_sql_executor_python_ro_is_deferred() -> None:
    s = GraphSettings(sql_executor_mode="python_ro", database_url_ro="postgresql://x:y@localhost/db")
    with pytest.raises(ValueError, match="python_ro"):
        build_sql_executor(s)


def test_http_spring_success() -> None:
    received: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        received["payload"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            200,
            json={
                "columns": [{"name": "n", "type": "text"}],
                "rows": [["ok"]],
                "row_count": 1,
                "summary": "test",
                "correlation_id": "c1",
                "meta": {"upstream": "spring"},
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    settings = GraphSettings(
        sql_executor_mode="http_spring",
        spring_sql_url="http://example.test/ro/exec",
        sql_executor_timeout_seconds=10,
        sql_executor_row_limit=100,
    )
    ex = HttpSpringSqlExecutor(settings, client=client)
    out = ex.execute("SELECT 1 AS n", tenant_id="t1", correlation_id="c1", schema_version="v1")
    assert out["rows"][0]["n"] == "ok"
    assert out["meta"]["mode"] == "http_spring"
    payload = received["payload"]
    assert isinstance(payload, dict)
    assert payload.get("query") == "SELECT 1 AS n"
    assert payload.get("max_rows") == 100


def test_http_spring_upstream_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={
                "error": {
                    "code": "DENY",
                    "message": "blocked",
                    "category": "policy",
                }
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    settings = GraphSettings(
        sql_executor_mode="http_spring",
        spring_sql_url="http://example.test/ro/exec",
        sql_executor_timeout_seconds=10,
        sql_executor_row_limit=100,
    )
    ex = HttpSpringSqlExecutor(settings, client=client)
    with pytest.raises(SqlExecutorError, match="policy"):
        ex.execute("SELECT 1", tenant_id=None)


def test_http_spring_rows_truncated_to_cap() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "columns": [{"name": "i", "type": "int"}],
                "rows": [[n] for n in range(300)],
                "row_count": 300,
                "summary": "big",
                "correlation_id": "x",
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    settings = GraphSettings(
        sql_executor_mode="http_spring",
        spring_sql_url="http://example.test/ro/exec",
        sql_executor_row_limit=50,
    )
    ex = HttpSpringSqlExecutor(settings, client=client)
    out = ex.execute("SELECT i FROM t", tenant_id=None)
    assert len(out["rows"]) == 50


def test_enforce_read_only_blocks_insert() -> None:
    with pytest.raises(SqlSafetyError):
        enforce_read_only_sql("INSERT INTO t VALUES (1)")


def test_scan_sqlite_memory() -> None:
    engine = create_engine("sqlite:///:memory:")
    md = MetaData()
    Table("widgets", md, Column("id", Integer, primary_key=True), Column("name", String))
    md.create_all(engine)
    try:
        art = scan_engine_metadata(engine, schema_version="mem-test")
    finally:
        engine.dispose()
    assert art.generated_at
    assert art.source_mode == "sqlalchemy_inspect"
    names = {t.name.lower() for t in art.tables}
    assert "widgets" in names


def test_load_schema_yaml_packaged_v1() -> None:
    root = pathlib.Path(__file__).resolve().parents[1] / "app" / "data" / "schema" / "v1.yaml"
    art = load_schema_yaml_path(root)
    assert art.schema_version == "v1"
    assert len(art.tables) >= 1


def test_dbmeta_cli_validate_module() -> None:
    root = pathlib.Path(__file__).resolve().parents[1]
    yaml_path = root / "app" / "data" / "schema" / "v1.yaml"
    proc = subprocess.run(
        [sys.executable, "-m", "app.cli.dbmeta_cli", "validate", str(yaml_path)],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
