"""Integration test for the pipeline orchestrator + CLI (Feature-T005-5)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.agents.task005_corpus_job import RunOutcome, run_corpus_job
from app.cli.task005_corpus_job import build_arg_parser, run_cli
from app.contracts.task005 import (
    McpToolError,
    SqlDescribeIn,
    SqlDescribeOut,
    SqlQueryReadonlyIn,
    SqlQueryReadonlyOut,
)
from app.mcp.db_readonly_port import (
    DescribeResult,
    McpTransportError,
    QueryReadonlyResult,
)
from app.tools.task005_corpus_fs import HEALTH_NAMESPACE, SCHEMA_NAMESPACE

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "task005"


def _load_task005_fixture(name: str) -> dict[str, Any]:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


class _FakeClient:
    def __init__(
        self,
        *,
        describes: dict[str, DescribeResult] | None = None,
        smokes: dict[str, QueryReadonlyResult] | None = None,
        transport_down: bool = False,
    ) -> None:
        self._describes = describes or {}
        self._smokes = smokes or {}
        self._transport_down = transport_down

    async def describe(self, payload: SqlDescribeIn) -> DescribeResult:
        if self._transport_down:
            raise McpTransportError("transport unavailable")
        return self._describes[payload.object_name]

    async def query_readonly(
        self, payload: SqlQueryReadonlyIn
    ) -> QueryReadonlyResult:
        if self._transport_down:
            raise McpTransportError("transport unavailable")
        return self._smokes[payload.template_id]


def _ok_describe(name: str) -> SqlDescribeOut:
    base = _load_task005_fixture("sql_describe_response.json")
    return SqlDescribeOut.model_validate(
        {
            **base,
            "object_name": name,
            "summary": f"cols=1 object={name}",
            "correlation_id": f"corr-{name}",
        }
    )


def _ok_smoke() -> SqlQueryReadonlyOut:
    return SqlQueryReadonlyOut.model_validate(
        _load_task005_fixture("sql_query_readonly_response.json")
    )


def _seed_config(tmp_path: Path) -> tuple[Path, Path]:
    objects_path = tmp_path / "objects.json"
    templates_path = tmp_path / "templates.json"
    objects_path.write_text(
        json.dumps(_load_task005_fixture("objects_allowlist.json")),
        encoding="utf-8",
    )
    templates_path.write_text(
        json.dumps(_load_task005_fixture("templates_registry_pipeline.json")),
        encoding="utf-8",
    )
    return objects_path, templates_path


# AC: AC1
# AC: AC2
# AC: AC3
# AC: AC5
# AC: AC6
async def test_run_corpus_job_happy_path_writes_artifacts(tmp_path: Path) -> None:
    client = _FakeClient(
        describes={"reporting.sales_by_day_v1": _ok_describe("reporting.sales_by_day_v1")},
        smokes={"sales_by_day_v1": _ok_smoke()},
    )
    objects_path, templates_path = _seed_config(tmp_path)
    corpus_root = tmp_path / "rag_corpus"

    outcome = await run_corpus_job(
        client=client,
        objects_path=objects_path,
        templates_path=templates_path,
        corpus_root=corpus_root,
        correlation_id="corr_run_happy",
    )

    assert isinstance(outcome, RunOutcome)
    assert outcome.exit_code == 0
    assert outcome.context.run_finished_at is not None
    assert outcome.context.describe_results == {"reporting.sales_by_day_v1": "ok"}
    assert outcome.context.smoke_templates_ok == ["sales_by_day_v1"]
    assert outcome.context.smoke_templates_failed == []

    catalog_files = list((corpus_root / SCHEMA_NAMESPACE).glob("catalog__*.json"))
    health_files = list((corpus_root / HEALTH_NAMESPACE).glob("health__*.json"))
    assert len(catalog_files) == 1
    assert len(health_files) == 1
    health_payload = json.loads(health_files[0].read_text(encoding="utf-8"))
    for entry in health_payload["smoke"]:
        assert "rows" not in entry
    assert outcome.index_chunks >= 2


# AC: AC1
# AC: AC5
# AC: AC6
async def test_run_corpus_job_partial_describe_failure_exits_non_zero(
    tmp_path: Path,
) -> None:
    client = _FakeClient(
        describes={
            "reporting.sales_by_day_v1": McpToolError(
                code="DB_TIMEOUT",
                message="x",
                retryable=True,
                correlation_id="corr",
            )
        },
        smokes={"sales_by_day_v1": _ok_smoke()},
    )
    objects_path, templates_path = _seed_config(tmp_path)
    corpus_root = tmp_path / "rag_corpus"

    outcome = await run_corpus_job(
        client=client,
        objects_path=objects_path,
        templates_path=templates_path,
        corpus_root=corpus_root,
        correlation_id="corr_run_partial",
    )

    assert outcome.exit_code != 0
    assert outcome.context.describe_results == {
        "reporting.sales_by_day_v1": "failed"
    }
    assert outcome.context.smoke_templates_ok == ["sales_by_day_v1"]


# AC: AC4
# AC: AC6
async def test_run_corpus_job_mcp_transport_down_exits_non_zero(
    tmp_path: Path,
) -> None:
    client = _FakeClient(transport_down=True)
    objects_path, templates_path = _seed_config(tmp_path)
    corpus_root = tmp_path / "rag_corpus"

    outcome = await run_corpus_job(
        client=client,
        objects_path=objects_path,
        templates_path=templates_path,
        corpus_root=corpus_root,
        correlation_id="corr_run_down",
    )

    assert outcome.exit_code != 0
    failed_codes = {
        failure.code for failure in outcome.describe_outcome.failures
    }
    assert "MCP_TRANSPORT_DOWN" in failed_codes


# AC: AC6
def test_cli_arg_parser_requires_paths() -> None:
    parser = build_arg_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


# AC: AC1
# AC: AC2
# AC: AC6
def test_cli_run_happy_path(tmp_path: Path) -> None:
    objects_path, templates_path = _seed_config(tmp_path)
    corpus_root = tmp_path / "rag_corpus"

    client = _FakeClient(
        describes={"reporting.sales_by_day_v1": _ok_describe("reporting.sales_by_day_v1")},
        smokes={"sales_by_day_v1": _ok_smoke()},
    )

    exit_code = run_cli(
        argv=[
            "--objects",
            str(objects_path),
            "--templates",
            str(templates_path),
            "--corpus-root",
            str(corpus_root),
            "--correlation-id",
            "corr_cli_happy",
        ],
        client=client,
    )

    assert exit_code == 0
