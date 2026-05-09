"""Unit tests for the Task005 daily CLI shim."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from app.cli import task005_daily
from app.contracts.task005 import SqlDescribeIn, SqlQueryReadonlyIn
from app.mcp.db_readonly_port import McpTransportError
from app.mcp.task005_client_factory import build_db_readonly_client_from_env
from app.mcp.task005_unconfigured_client import UnconfiguredDbReadonlyClient


def test_build_db_readonly_client_stub_returns_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TASK005_DB_READONLY_ADAPTER", raising=False)
    client = build_db_readonly_client_from_env()
    assert isinstance(client, UnconfiguredDbReadonlyClient)


def test_daily_main_inserts_default_argv(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_cli(*, argv: list[str], client: object) -> int:
        captured["argv"] = list(argv)
        captured["client"] = client
        return 0

    monkeypatch.setattr(task005_daily, "run_cli", fake_run_cli)
    monkeypatch.setattr(sys, "argv", ["task005_daily"])
    with pytest.raises(SystemExit) as exc:
        task005_daily.main()
    assert exc.value.code == 0
    argv = captured["argv"]
    assert isinstance(argv, list)
    idx = argv.index("--objects")
    objects_path = Path(str(argv[idx + 1]))
    assert objects_path.name == "objects.json"


def test_build_db_readonly_unknown_adapter_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASK005_DB_READONLY_ADAPTER", "unknown_transport_xyz")
    with pytest.raises(RuntimeError, match="Unknown TASK005_DB_READONLY_ADAPTER"):
        build_db_readonly_client_from_env()


async def test_unconfigured_client_raises_transport_error() -> None:
    client = UnconfiguredDbReadonlyClient()
    with pytest.raises(McpTransportError):
        await client.describe(SqlDescribeIn(object_name="reporting.x"))
    with pytest.raises(McpTransportError):
        await client.query_readonly(
            SqlQueryReadonlyIn(template_id="t", params={})
        )
