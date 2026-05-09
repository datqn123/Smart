"""Integration test for the smoke runner (Feature-T005-3 SRS B3+B4)."""

from __future__ import annotations

from app.contracts.task005 import (
    McpToolError,
    SqlColumn,
    SqlDescribeIn,
    SqlQueryReadonlyIn,
    SqlQueryReadonlyOut,
)
from app.mcp.db_readonly_port import QueryReadonlyResult
from app.registry.task005_templates import TemplateRegistry, load_registry_from_dict
from app.tools.task005_smoke import run_smoke_loop


class _StubClient:
    def __init__(self, results: dict[str, QueryReadonlyResult]) -> None:
        self._results = results
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def describe(self, payload: SqlDescribeIn) -> object:  # pragma: no cover
        raise NotImplementedError

    async def query_readonly(
        self, payload: SqlQueryReadonlyIn
    ) -> QueryReadonlyResult:
        self.calls.append((payload.template_id, dict(payload.params)))
        return self._results[payload.template_id]


def _registry() -> TemplateRegistry:
    return load_registry_from_dict(
        {
            "templates": [
                {
                    "template_id": "sales_by_day_v1",
                    "intent": "report",
                    "description": "ok",
                    "params": {"date_from": "2026-04-01"},
                    "smoke_safe": True,
                },
                {
                    "template_id": "inventory_snapshot_v1",
                    "intent": "report",
                    "description": "ok",
                    "params": {},
                    "smoke_safe": True,
                },
                {
                    "template_id": "manual_only_v1",
                    "intent": "export",
                    "description": "skipped",
                    "params": {},
                    "smoke_safe": False,
                },
            ]
        }
    )


async def test_smoke_loop_records_ok_and_failure_summary_only() -> None:
    success = SqlQueryReadonlyOut(
        columns=[SqlColumn(name="day", type="date")],
        rows=[["2026-04-01"]],
        row_count=1,
        summary="1 row(s)",
        correlation_id="corr-ok",
    )
    failure = McpToolError(
        code="DB_TIMEOUT",
        message="timed out",
        retryable=True,
        correlation_id="corr-fail",
    )
    client = _StubClient(
        results={
            "sales_by_day_v1": success,
            "inventory_snapshot_v1": failure,
        }
    )

    outcome = await run_smoke_loop(
        client=client,
        registry=_registry(),
        correlation_id="corr_run_demo",
    )

    assert {call[0] for call in client.calls} == {
        "sales_by_day_v1",
        "inventory_snapshot_v1",
    }
    assert outcome.tried == ["sales_by_day_v1", "inventory_snapshot_v1"]
    assert outcome.passed == ["sales_by_day_v1"]
    assert len(outcome.failed) == 1
    assert outcome.failed[0].template_id == "inventory_snapshot_v1"
    assert outcome.failed[0].code == "DB_TIMEOUT"
    serialised = [entry.model_dump() for entry in outcome.entries]
    for row in serialised:
        assert "rows" not in row
    assert {row["template_id"] for row in serialised} == {
        "sales_by_day_v1",
        "inventory_snapshot_v1",
    }
    assert outcome.has_failures is True


async def test_smoke_loop_skips_non_smoke_safe_templates() -> None:
    success = SqlQueryReadonlyOut(
        columns=[SqlColumn(name="day", type="date")],
        rows=[],
        row_count=0,
        summary="ok",
        correlation_id="corr",
    )
    client = _StubClient(
        results={
            "sales_by_day_v1": success,
            "inventory_snapshot_v1": success,
        }
    )

    outcome = await run_smoke_loop(
        client=client,
        registry=_registry(),
        correlation_id="corr",
    )

    assert all(call[0] != "manual_only_v1" for call in client.calls)
    assert "manual_only_v1" not in outcome.tried
    assert outcome.has_failures is False
