"""Unit-T005-1 — pydantic contracts (job context, MCP I/O, error model)."""

from __future__ import annotations

from datetime import UTC, datetime

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


def test_mcp_tool_error_blank_correlation_rejected() -> None:
    with pytest.raises(ValidationError):
        McpToolError(
            code="DB_TIMEOUT",
            message="x",
            retryable=False,
            correlation_id="   ",
        )


def test_sql_describe_in_strips_object_name() -> None:
    payload = SqlDescribeIn(object_name="  reporting.sales_by_day_v1  ")
    assert payload.object_name == "reporting.sales_by_day_v1"


def test_sql_describe_in_rejects_blank_object_name() -> None:
    with pytest.raises(ValidationError):
        SqlDescribeIn(object_name="")


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


def test_sql_query_readonly_in_requires_template_id() -> None:
    with pytest.raises(ValidationError):
        SqlQueryReadonlyIn(template_id="", params={})


def test_sql_query_readonly_in_accepts_dict_params() -> None:
    payload = SqlQueryReadonlyIn(
        template_id="sales_by_day_v1",
        params={"date_from": "2026-04-01", "channel": None},
    )
    assert payload.params["channel"] is None


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


def test_corpus_job_context_describe_results_value_validation() -> None:
    with pytest.raises(ValidationError):
        CorpusJobContext(
            correlation_id="corr_run_abc",
            corpus_version="v1",
            run_started_at=datetime(2026, 5, 9, 12, 0, tzinfo=UTC),
            objects_allowlist=["a"],
            describe_results={"a": "weird"},  # type: ignore[arg-type]
        )


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


def test_corpus_job_context_no_pii_rows_field() -> None:
    """Audit invariant: job context must not carry full SQL row payloads."""

    fields = set(CorpusJobContext.model_fields.keys())
    assert "rows" not in fields
    assert "data" not in fields
