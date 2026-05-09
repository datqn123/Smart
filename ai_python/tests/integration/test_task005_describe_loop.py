"""Integration test for the describe runner (Feature-T005-2 SRS B1+B2)."""

from __future__ import annotations

from app.contracts.task005 import (
    ColumnMeta,
    McpToolError,
    SqlDescribeIn,
    SqlDescribeOut,
)
from app.mcp.db_readonly_port import DescribeResult
from app.tools.task005_describe import run_describe_loop


class _StubClient:
    def __init__(self, results: dict[str, DescribeResult]) -> None:
        self._results = results
        self.calls: list[str] = []

    async def describe(self, payload: SqlDescribeIn) -> DescribeResult:
        self.calls.append(payload.object_name)
        return self._results[payload.object_name]

    async def query_readonly(self, payload: object) -> object:  # pragma: no cover
        raise NotImplementedError


def _ok(name: str) -> SqlDescribeOut:
    return SqlDescribeOut(
        object_name=name,
        columns=[ColumnMeta(name="day", type="date", nullable=False)],
        summary=f"cols=1 object={name}",
        correlation_id=f"corr-{name}",
    )


async def test_describe_loop_records_partial_failures() -> None:
    client = _StubClient(
        results={
            "reporting.a_v1": _ok("reporting.a_v1"),
            "reporting.b_v1": McpToolError(
                code="DB_TIMEOUT",
                message="timed out",
                retryable=True,
                correlation_id="corr-b",
            ),
            "reporting.c_v1": _ok("reporting.c_v1"),
        }
    )

    outcome = await run_describe_loop(
        client=client,
        objects=("reporting.a_v1", "reporting.b_v1", "reporting.c_v1"),
        correlation_id="corr_run_demo",
    )

    assert client.calls == ["reporting.a_v1", "reporting.b_v1", "reporting.c_v1"]
    assert [entry.object_name for entry in outcome.catalog_entries] == [
        "reporting.a_v1",
        "reporting.c_v1",
    ]
    assert outcome.results == {
        "reporting.a_v1": "ok",
        "reporting.b_v1": "failed",
        "reporting.c_v1": "ok",
    }
    assert outcome.failures[0].object_name == "reporting.b_v1"
    assert outcome.failures[0].code == "DB_TIMEOUT"
    assert outcome.has_failures is True


async def test_describe_loop_all_ok_marks_no_failures() -> None:
    client = _StubClient(
        results={
            "reporting.a_v1": _ok("reporting.a_v1"),
            "reporting.b_v1": _ok("reporting.b_v1"),
        }
    )

    outcome = await run_describe_loop(
        client=client,
        objects=("reporting.a_v1", "reporting.b_v1"),
        correlation_id="corr",
    )

    assert outcome.has_failures is False
    assert outcome.failures == []
    assert all(status == "ok" for status in outcome.results.values())
