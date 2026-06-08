"""Unit tests for schema data introspection (sample rows + distinct values)."""

from __future__ import annotations

from app.graph.dbmeta import ColumnMeta, SchemaArtifact, TableMeta
from app.graph.pg_schema_context import _is_categorical_column
from app.graph.sql_prompts import format_schema_block


def test_is_categorical_column_varchar() -> None:
    col = ColumnMeta(name="status", type="varchar")
    assert _is_categorical_column(col) is True


def test_is_categorical_column_text() -> None:
    col = ColumnMeta(name="description", type="text")
    assert _is_categorical_column(col) is True


def test_is_categorical_column_char() -> None:
    col = ColumnMeta(name="flag", type="char(1)")
    assert _is_categorical_column(col) is True


def test_is_categorical_column_enum() -> None:
    col = ColumnMeta(name="direction", type="enum")
    assert _is_categorical_column(col) is True


def test_is_categorical_column_skips_id() -> None:
    col = ColumnMeta(name="id", type="bigint")
    assert _is_categorical_column(col) is False


def test_is_categorical_column_skips_created_at() -> None:
    col = ColumnMeta(name="created_at", type="timestamp")
    assert _is_categorical_column(col) is False


def test_is_categorical_column_skips_updated_at() -> None:
    col = ColumnMeta(name="updated_at", type="timestamptz")
    assert _is_categorical_column(col) is False


def test_is_categorical_column_skips_deleted_at() -> None:
    col = ColumnMeta(name="deleted_at", type="timestamp")
    assert _is_categorical_column(col) is False


def test_is_categorical_column_skips_array() -> None:
    col = ColumnMeta(name="tags", type="varchar[]")
    assert _is_categorical_column(col) is False


def test_is_categorical_column_numeric() -> None:
    col = ColumnMeta(name="amount", type="decimal")
    assert _is_categorical_column(col) is False


def test_is_categorical_column_no_type() -> None:
    col = ColumnMeta(name="status", type=None)
    assert _is_categorical_column(col) is False


def test_enriched_prompt_contains_known_distinct_values() -> None:
    artifact = SchemaArtifact(
        schema_version="test",
        tables=[
            TableMeta(
                name="orders",
                columns=[ColumnMeta(name="status", type="varchar")],
                distinct_values={"status": ["Completed", "Pending", "Cancelled"]},
            ),
        ],
    )
    block = format_schema_block(artifact, selected_tables=["orders"], enriched=True)
    assert "Known distinct values" in block
    assert "status" in block
    assert "Completed" in block
    assert "Pending" in block
    assert "Cancelled" in block


def test_enriched_prompt_contains_sample_rows() -> None:
    artifact = SchemaArtifact(
        schema_version="test",
        tables=[
            TableMeta(
                name="orders",
                columns=[ColumnMeta(name="status", type="varchar")],
                sample_rows=[{"id": 1, "status": "Completed"}],
            ),
        ],
    )
    block = format_schema_block(artifact, selected_tables=["orders"], enriched=True)
    assert "Sample rows" in block
    assert "row1" in block
    assert "Completed" in block


def test_enriched_prompt_omits_introspection_when_empty() -> None:
    artifact = SchemaArtifact(
        schema_version="test",
        tables=[
            TableMeta(
                name="orders",
                columns=[ColumnMeta(name="status", type="varchar")],
                sample_rows=[],
                distinct_values={},
            ),
        ],
    )
    block = format_schema_block(artifact, selected_tables=["orders"], enriched=True)
    assert "Known distinct values" not in block
    assert "Sample rows" not in block


def test_enriched_prompt_truncates_long_values() -> None:
    long_val = "x" * 200
    artifact = SchemaArtifact(
        schema_version="test",
        tables=[
            TableMeta(
                name="orders",
                columns=[ColumnMeta(name="note", type="text")],
                sample_rows=[{"note": long_val}],
            ),
        ],
    )
    block = format_schema_block(artifact, selected_tables=["orders"], enriched=True)
    assert "Sample rows" in block
    # value should be truncated to 80 chars
    assert ("x" * 81) not in block


def test_enriched_prompt_truncates_many_distinct_values() -> None:
    many_vals = [str(i) for i in range(20)]
    artifact = SchemaArtifact(
        schema_version="test",
        tables=[
            TableMeta(
                name="orders",
                columns=[ColumnMeta(name="status", type="varchar")],
                distinct_values={"status": many_vals},
            ),
        ],
    )
    block = format_schema_block(artifact, selected_tables=["orders"], enriched=True)
    assert "Known distinct values" in block
    assert "and 12 more" in block  # 20 - 8 = 12
