"""Integration test for the RAG ingest stub (Feature-T005-4 / SRS B6)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.contracts.task005 import ColumnMeta
from app.rag.task005_ingest import (
    LocalRagIndex,
    ingest_corpus,
    read_chunks,
)
from app.tools.task005_artifacts import (
    SchemaCatalogArtifact,
    SchemaCatalogEntry,
    SmokeArtifactEntry,
    SmokeHealthArtifact,
)
from app.tools.task005_corpus_fs import (
    HEALTH_NAMESPACE,
    SCHEMA_NAMESPACE,
    atomic_write_json,
    build_corpus_paths,
    iso_corpus_version,
)


def _seed_corpus(root: Path) -> str:
    corpus_version = iso_corpus_version(datetime(2026, 5, 9, 12, 0, tzinfo=UTC))
    paths = build_corpus_paths(root, corpus_version)

    catalog = SchemaCatalogArtifact(
        corpus_version=corpus_version,
        correlation_id="corr_run_demo",
        objects=[
            SchemaCatalogEntry(
                object_name="reporting.sales_by_day_v1",
                columns=[
                    ColumnMeta(name="day", type="date", nullable=False),
                    ColumnMeta(name="revenue", type="number", nullable=True),
                ],
                summary="2 cols.",
            )
        ],
    )
    health = SmokeHealthArtifact(
        corpus_version=corpus_version,
        correlation_id="corr_run_demo",
        smoke=[
            SmokeArtifactEntry(
                template_id="sales_by_day_v1",
                ok=True,
                row_count=1,
                code=None,
            )
        ],
    )
    atomic_write_json(paths.catalog_path, catalog.model_dump())
    atomic_write_json(paths.health_path, health.model_dump())
    return corpus_version


def test_ingest_corpus_writes_index_with_two_namespaces(tmp_path: Path) -> None:
    corpus_version = _seed_corpus(tmp_path)

    index = ingest_corpus(corpus_root=tmp_path, corpus_version=corpus_version)

    assert isinstance(index, LocalRagIndex)
    assert {chunk.namespace for chunk in index.chunks} == {
        SCHEMA_NAMESPACE,
        HEALTH_NAMESPACE,
    }
    assert len(index.chunks) >= 2
    index_path = tmp_path / "index" / f"index__{corpus_version}.json"
    assert index_path.exists()
    parsed = json.loads(index_path.read_text(encoding="utf-8"))
    assert parsed["corpus_version"] == corpus_version
    assert any(chunk["namespace"] == SCHEMA_NAMESPACE for chunk in parsed["chunks"])


def test_read_chunks_returns_at_least_one_per_namespace(tmp_path: Path) -> None:
    corpus_version = _seed_corpus(tmp_path)
    ingest_corpus(corpus_root=tmp_path, corpus_version=corpus_version)

    schema_chunks = list(
        read_chunks(
            corpus_root=tmp_path,
            corpus_version=corpus_version,
            namespace=SCHEMA_NAMESPACE,
        )
    )
    health_chunks = list(
        read_chunks(
            corpus_root=tmp_path,
            corpus_version=corpus_version,
            namespace=HEALTH_NAMESPACE,
        )
    )

    assert len(schema_chunks) >= 1
    assert len(health_chunks) >= 1
    assert "reporting.sales_by_day_v1" in schema_chunks[0].text
    assert "sales_by_day_v1" in health_chunks[0].text


def test_ingest_corpus_skips_when_corpus_missing(tmp_path: Path) -> None:
    corpus_version = "2026-05-09T12-00-00Z"

    index = ingest_corpus(corpus_root=tmp_path, corpus_version=corpus_version)

    assert index.chunks == []
