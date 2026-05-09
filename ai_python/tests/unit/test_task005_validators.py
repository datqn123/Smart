"""Unit-T005-2 — caps validators + registry/catalog JSON shape."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.contracts.task005 import (
    MAX_COLUMNS,
    MAX_SMOKE_ROW_COUNT,
    MAX_SUMMARY_CHARS,
    ColumnMeta,
    SqlColumn,
    SqlDescribeOut,
    SqlQueryReadonlyOut,
)
from app.registry.task005_templates import (
    SmokeTemplate,
    TemplateRegistry,
    load_registry_from_dict,
)
from app.tools.task005_artifacts import (
    SchemaCatalogEntry,
    SmokeArtifactEntry,
    SmokeHealthArtifact,
    catalog_entry_from_describe,
    smoke_entry_from_failure,
    smoke_entry_from_success,
)

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "task005"


def _load_task005_fixture(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def _column(idx: int) -> ColumnMeta:
    return ColumnMeta(name=f"c{idx}", type="text", nullable=True)


# AC: AC1
def test_describe_out_rejects_too_many_columns() -> None:
    with pytest.raises(ValidationError):
        SqlDescribeOut(
            object_name="reporting.too_wide_v1",
            columns=[_column(i) for i in range(MAX_COLUMNS + 1)],
            summary="x",
            correlation_id="corr",
        )


# AC: AC1
def test_describe_out_accepts_max_columns() -> None:
    out = SqlDescribeOut(
        object_name="reporting.wide_v1",
        columns=[_column(i) for i in range(MAX_COLUMNS)],
        summary="ok",
        correlation_id="corr",
    )
    assert len(out.columns) == MAX_COLUMNS


# AC: AC1
def test_describe_out_summary_capped() -> None:
    with pytest.raises(ValidationError):
        SqlDescribeOut(
            object_name="reporting.summary_overflow_v1",
            columns=[_column(0)],
            summary="x" * (MAX_SUMMARY_CHARS + 1),
            correlation_id="corr",
        )


# AC: AC2
def test_query_readonly_out_smoke_row_count_capped() -> None:
    with pytest.raises(ValidationError):
        SqlQueryReadonlyOut(
            columns=[SqlColumn(name="day", type="date")],
            rows=[],
            row_count=MAX_SMOKE_ROW_COUNT + 1,
            summary="too many",
            correlation_id="corr",
        )


# AC: AC2
def test_query_readonly_out_negative_row_count_rejected() -> None:
    with pytest.raises(ValidationError):
        SqlQueryReadonlyOut(
            columns=[SqlColumn(name="day", type="date")],
            rows=[],
            row_count=-1,
            summary="bad",
            correlation_id="corr",
        )


# AC: AC2
# AC: AC4
def test_smoke_entry_from_success_strips_rows() -> None:
    entry = smoke_entry_from_success(
        SqlQueryReadonlyOut(
            columns=[SqlColumn(name="day", type="date")],
            rows=[["2026-04-01"]],
            row_count=1,
            summary="1 row(s); smoke OK.",
            correlation_id="corr_smoke_001",
        ),
        template_id="sales_by_day_v1",
    )
    dumped = entry.model_dump()
    assert dumped == {
        "template_id": "sales_by_day_v1",
        "ok": True,
        "row_count": 1,
        "code": None,
    }
    assert "rows" not in dumped


# AC: AC2
# AC: AC4
def test_smoke_entry_from_failure_records_code_only() -> None:
    entry = smoke_entry_from_failure(
        template_id="inventory_snapshot_v1",
        code="DB_TIMEOUT",
        row_count=0,
    )
    assert isinstance(entry, SmokeArtifactEntry)
    assert entry.ok is False
    assert entry.code == "DB_TIMEOUT"


# AC: AC1
def test_catalog_entry_from_describe_round_trip() -> None:
    out = SqlDescribeOut(
        object_name="reporting.sales_by_day_v1",
        columns=[
            ColumnMeta(name="day", type="date", nullable=False),
            ColumnMeta(name="revenue", type="number", nullable=True),
        ],
        summary="2 cols.",
        correlation_id="corr",
    )
    entry = catalog_entry_from_describe(out)
    assert isinstance(entry, SchemaCatalogEntry)
    assert entry.object_name == "reporting.sales_by_day_v1"
    assert entry.columns[1].nullable is True


# AC: AC2
def test_smoke_health_artifact_serialises_summary_only() -> None:
    artifact = SmokeHealthArtifact(
        corpus_version="2026-05-09T12:00:00Z",
        correlation_id="corr_run_abc",
        smoke=[
            SmokeArtifactEntry(
                template_id="sales_by_day_v1",
                ok=True,
                row_count=1,
                code=None,
            )
        ],
    )
    dumped = artifact.model_dump()
    assert "rows" not in dumped["smoke"][0]
    assert dumped["smoke"][0]["row_count"] == 1


# AC: AC2
def test_health_artifact_fixture_matches_smoke_health_model() -> None:
    raw = _load_task005_fixture("health_artifact.json")
    artifact = SmokeHealthArtifact.model_validate(raw)
    dumped = artifact.model_dump()
    for entry in dumped["smoke"]:
        assert "rows" not in entry


# AC: AC2
def test_template_registry_loads_smoke_templates() -> None:
    registry = load_registry_from_dict(
        _load_task005_fixture("templates_registry_validators.json")
    )
    assert isinstance(registry, TemplateRegistry)
    smoke = registry.smoke_safe_templates()
    assert len(smoke) == 1
    assert isinstance(smoke[0], SmokeTemplate)
    assert smoke[0].template_id == "sales_by_day_v1"


# AC: AC2
def test_template_registry_rejects_duplicate_template_ids() -> None:
    with pytest.raises(ValidationError):
        load_registry_from_dict(
            {
                "templates": [
                    {
                        "template_id": "dup_v1",
                        "intent": "x",
                        "description": "y",
                        "params": {},
                        "smoke_safe": True,
                    },
                    {
                        "template_id": "dup_v1",
                        "intent": "x",
                        "description": "y",
                        "params": {},
                        "smoke_safe": False,
                    },
                ]
            }
        )


# AC: AC2
def test_template_registry_rejects_blank_template_id() -> None:
    with pytest.raises(ValidationError):
        load_registry_from_dict(
            {
                "templates": [
                    {
                        "template_id": "",
                        "intent": "x",
                        "description": "y",
                        "params": {},
                        "smoke_safe": True,
                    }
                ]
            }
        )
