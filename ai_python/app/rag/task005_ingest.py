"""Local RAG ingest stub for Task005 (Feature-T005-4).

Reads the catalog + health artifacts produced by the batch job, chunks them
into per-object/per-template entries, and writes a single ``index__<ver>.json``
that future readers can consume without invoking any Agent runtime (SRS B6 /
ADR §6 — implementation may be stub or production indexer).
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.tools.task005_artifacts import (
    SchemaCatalogArtifact,
    SmokeHealthArtifact,
)
from app.tools.task005_corpus_fs import (
    HEALTH_NAMESPACE,
    SCHEMA_NAMESPACE,
    atomic_write_json,
    build_corpus_paths,
)


@dataclass(frozen=True)
class RagChunk:
    """One indexed chunk, keyed by namespace + stable id."""

    namespace: str
    chunk_id: str
    text: str

    def to_payload(self) -> dict[str, str]:
        return {
            "namespace": self.namespace,
            "chunk_id": self.chunk_id,
            "text": self.text,
        }


@dataclass
class LocalRagIndex:
    """In-memory index produced by :func:`ingest_corpus`."""

    corpus_version: str
    chunks: list[RagChunk] = field(default_factory=list)


def _index_path(corpus_root: Path, corpus_version: str) -> Path:
    return corpus_root / "index" / f"index__{corpus_version}.json"


def _schema_chunks(catalog: SchemaCatalogArtifact) -> Iterator[RagChunk]:
    for entry in catalog.objects:
        column_lines = [
            f"- {col.name}: {col.type}{' (nullable)' if col.nullable else ''}"
            for col in entry.columns
        ]
        text_parts = [
            f"# {entry.object_name}",
            entry.summary,
            "Columns:",
            *column_lines,
        ]
        yield RagChunk(
            namespace=SCHEMA_NAMESPACE,
            chunk_id=f"{SCHEMA_NAMESPACE}:{entry.object_name}",
            text="\n".join(part for part in text_parts if part),
        )


def _health_chunks(health: SmokeHealthArtifact) -> Iterator[RagChunk]:
    for entry in health.smoke:
        status = "ok" if entry.ok else f"failed ({entry.code})"
        text = (
            f"Template `{entry.template_id}` smoke status: {status}; "
            f"row_count={entry.row_count}."
        )
        yield RagChunk(
            namespace=HEALTH_NAMESPACE,
            chunk_id=f"{HEALTH_NAMESPACE}:{entry.template_id}",
            text=text,
        )


def _maybe_load(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        return None
    return parsed


def ingest_corpus(*, corpus_root: Path, corpus_version: str) -> LocalRagIndex:
    """Read corpus artifacts and write a versioned local index."""

    paths = build_corpus_paths(corpus_root, corpus_version)
    chunks: list[RagChunk] = []

    catalog_payload = _maybe_load(paths.catalog_path)
    if catalog_payload is not None:
        catalog = SchemaCatalogArtifact.model_validate(catalog_payload)
        chunks.extend(_schema_chunks(catalog))

    health_payload = _maybe_load(paths.health_path)
    if health_payload is not None:
        health = SmokeHealthArtifact.model_validate(health_payload)
        chunks.extend(_health_chunks(health))

    if chunks:
        index_payload = {
            "corpus_version": corpus_version,
            "chunks": [chunk.to_payload() for chunk in chunks],
        }
        atomic_write_json(_index_path(corpus_root, corpus_version), index_payload)

    return LocalRagIndex(corpus_version=corpus_version, chunks=chunks)


def read_chunks(
    *, corpus_root: Path, corpus_version: str, namespace: str
) -> Iterable[RagChunk]:
    """Read chunks back from the persisted index for a given namespace."""

    path = _index_path(corpus_root, corpus_version)
    if not path.exists():
        return []
    parsed = json.loads(path.read_text(encoding="utf-8"))
    chunks_payload = parsed.get("chunks", [])
    return [
        RagChunk(
            namespace=str(chunk["namespace"]),
            chunk_id=str(chunk["chunk_id"]),
            text=str(chunk["text"]),
        )
        for chunk in chunks_payload
        if str(chunk.get("namespace")) == namespace
    ]
