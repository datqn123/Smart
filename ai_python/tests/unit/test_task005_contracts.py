"""Unit-T005-1 — pydantic contracts (job context, MCP I/O, error model)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.contracts.task005 import (
    ColumnMeta,
    CorpusJobContext,
    McpToolError,
    SqlColumn,
    SqlDescribeIn,
    SqlDescribeOut,
    SqlQueryReadonlyIn,
    SqlQueryReadonlyOut,
)

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "task005"


def _load_task005_fixture(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


# AC: AC4
# AC: AC6
def test_mcp_tool_error_minimal_fields() -> None:
    err = McpToolError(
        code="DB_TIMEOUT",
        message="upstream took too long",
        retryable=True,
        correlation_id="corr_001",
    )
    assert err.code == "DB_TIMEOUT"
    assert err.retryable is True
    assert err.details is None
    dumped = err.model_dump()
    assert dumped["correlation_id"] == "corr_001"
    assert dumped["details"] is None


# AC: AC4
def test_mcp_tool_error_blank_correlation_rejected() -> None:
    with pytest.raises(ValidationError):
        McpToolError(
            code="DB_TIMEOUT",
            message="x",
            retryable=False,
            correlation_id="   ",
        )


# AC: AC1
# AC: AC4
def test_sql_describe_request_fixture_matches_contract() -> None:
    payload = _load_task005_fixture("sql_describe_request.json")
    model = SqlDescribeIn.model_validate(payload)
    assert model.object_name == "reporting.sales_by_day_v1"


# AC: AC1
def test_sql_describe_in_strips_object_name() -> None:
    payload = SqlDescribeIn(object_name="  reporting.sales_by_day_v1  ")
    assert payload.object_name == "reporting.sales_by_day_v1"


# AC: AC1
def test_sql_describe_in_rejects_blank_object_name() -> None:
    with pytest.raises(ValidationError):
        SqlDescribeIn(object_name="")


# AC: AC1
def test_sql_describe_out_round_trip() -> None:
    out = SqlDescribeOut(
        object_name="reporting.sales_by_day_v1",
        columns=[ColumnMeta(name="day", type="date", nullable=False)],
        summary="cols=1 object=reporting.sales_by_day_v1",
        correlation_id="corr_desc_001",
    )
    raw = out.model_dump()
    again = SqlDescribeOut.model_validate(raw)
    assert again == out


# AC: AC1
def test_sql_describe_response_fixture_round_trip() -> None:
    raw = _load_task005_fixture("sql_describe_response.json")
    out = SqlDescribeOut.model_validate(raw)
    again = SqlDescribeOut.model_validate(out.model_dump())
    assert again.object_name == "reporting.sales_by_day_v1"


# AC: AC2
# AC: AC4
def test_sql_query_readonly_request_fixture_matches_contract() -> None:
    payload = _load_task005_fixture("sql_query_readonly_request.json")
    model = SqlQueryReadonlyIn.model_validate(payload)
    assert model.template_id == "sales_by_day_v1"
    assert model.params["channel"] is None


# AC: AC2
def test_sql_query_readonly_in_requires_template_id() -> None:
    with pytest.raises(ValidationError):
        SqlQueryReadonlyIn(template_id="", params={})


# AC: AC2
def test_sql_query_readonly_in_accepts_dict_params() -> None:
    payload = SqlQueryReadonlyIn(
        template_id="sales_by_day_v1",
        params={"date_from": "2026-04-01", "channel": None},
    )
    assert payload.params["channel"] is None


# AC: AC2
def test_sql_query_readonly_response_fixture_round_trip() -> None:
    raw = _load_task005_fixture("sql_query_readonly_response.json")
    out = SqlQueryReadonlyOut.model_validate(raw)
    assert out.row_count == 1
    assert len(out.columns) == 2


# AC: AC2
def test_sql_query_readonly_out_with_columns() -> None:
    out = SqlQueryReadonlyOut(
        columns=[
            SqlColumn(name="day", type="date"),
            SqlColumn(name="revenue", type="number"),
        ],
        rows=[["2026-04-01", 1230000]],
        row_count=1,
        summary="1 row(s); smoke OK.",
        correlation_id="corr_smoke_001",
    )
    assert out.row_count == 1
    assert out.columns[1].name == "revenue"


# AC: AC4
# AC: AC6
def test_corpus_job_context_defaults_describe_results_empty() -> None:
    ctx = CorpusJobContext(
        correlation_id="corr_run_abc",
        corpus_version="2026-05-09T12:00:00Z",
        run_started_at=datetime(2026, 5, 9, 12, 0, tzinfo=UTC),
        objects_allowlist=["reporting.sales_by_day_v1"],
    )
    assert ctx.describe_results == {}
    assert ctx.smoke_templates_tried == []
    assert ctx.run_finished_at is None


# AC: AC4
def test_corpus_job_context_describe_results_value_validation() -> None:
    with pytest.raises(ValidationError):
        CorpusJobContext(
            correlation_id="corr_run_abc",
            corpus_version="v1",
            run_started_at=datetime(2026, 5, 9, 12, 0, tzinfo=UTC),
            objects_allowlist=["a"],
            describe_results={"a": "weird"},  # type: ignore[arg-type]
        )


# AC: AC4
# AC: AC6
def test_corpus_job_context_smoke_failed_records_code_only() -> None:
    ctx = CorpusJobContext(
        correlation_id="corr_run_abc",
        corpus_version="v1",
        run_started_at=datetime(2026, 5, 9, 12, 0, tzinfo=UTC),
        objects_allowlist=["a"],
        smoke_templates_failed=[
            {"template_id": "inventory_snapshot_v1", "code": "DB_TIMEOUT"}
        ],
    )
    assert ctx.smoke_templates_failed[0].template_id == "inventory_snapshot_v1"
    assert ctx.smoke_templates_failed[0].code == "DB_TIMEOUT"


# AC: AC4
def test_mcp_tool_error_fixture_round_trip() -> None:
    raw = _load_task005_fixture("mcp_tool_error.json")
    err = McpToolError.model_validate(raw)
    assert err.code == "DB_QUERY_REJECTED"
    assert err.correlation_id == "corr_err_001"


# AC: AC4
def test_corpus_job_context_no_pii_rows_field() -> None:
    """Audit invariant: job context must not carry full SQL row payloads."""

    fields = set(CorpusJobContext.model_fields.keys())
    assert "rows" not in fields
    assert "data" not in fields
