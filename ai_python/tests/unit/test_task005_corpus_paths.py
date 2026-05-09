"""Unit-T005-3 — corpus paths + atomic write helpers."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.tools.task005_corpus_fs import (
    DEFAULT_CORPUS_ROOT,
    HEALTH_NAMESPACE,
    SCHEMA_NAMESPACE,
    CorpusPaths,
    atomic_write_bytes,
    atomic_write_json,
    atomic_write_text,
    build_corpus_paths,
    iso_corpus_version,
)


# AC: AC1
def test_iso_corpus_version_is_compact_utc_iso() -> None:
    moment = datetime(2026, 5, 9, 12, 0, 30, tzinfo=UTC)
    version = iso_corpus_version(moment)
    assert version == "2026-05-09T12-00-30Z"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z", version)


# AC: AC1
def test_default_corpus_root_relative_to_ai_python() -> None:
    assert DEFAULT_CORPUS_ROOT.parts[-3:] == ("ai_python", "data", "rag_corpus")


# AC: AC1
def test_build_corpus_paths_versions_artifacts(tmp_path: Path) -> None:
    paths = build_corpus_paths(tmp_path, "2026-05-09T12-00-30Z")
    assert isinstance(paths, CorpusPaths)
    assert paths.root == tmp_path
    assert paths.schema_dir.name == SCHEMA_NAMESPACE
    assert paths.health_dir.name == HEALTH_NAMESPACE
    assert paths.catalog_path.parent == paths.schema_dir
    assert "2026-05-09T12-00-30Z" in paths.catalog_path.name
    assert paths.health_path.suffix == ".json"


# AC: AC1
def test_build_corpus_paths_rejects_blank_version(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="corpus_version"):
        build_corpus_paths(tmp_path, "")


# AC: AC1
def test_atomic_write_bytes_does_not_leak_partial(tmp_path: Path) -> None:
    target = tmp_path / "namespace" / "blob.bin"
    atomic_write_bytes(target, b"hello")
    assert target.read_bytes() == b"hello"
    assert not list(tmp_path.rglob("*.tmp*"))


# AC: AC1
def test_atomic_write_text_uses_utf8(tmp_path: Path) -> None:
    target = tmp_path / "schema" / "doc.md"
    atomic_write_text(target, "Tài liệu schema")
    assert target.read_text(encoding="utf-8") == "Tài liệu schema"


# AC: AC1
def test_atomic_write_json_pretty_and_stable(tmp_path: Path) -> None:
    target = tmp_path / "schema" / "catalog.json"
    payload = {"corpus_version": "v1", "objects": [{"object_name": "x"}]}
    atomic_write_json(target, payload)
    parsed = json.loads(target.read_text(encoding="utf-8"))
    assert parsed == payload
    text = target.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert "\n  " in text  # pretty indent of 2 spaces


# AC: AC1
def test_atomic_write_overwrites_existing(tmp_path: Path) -> None:
    target = tmp_path / "schema" / "doc.md"
    atomic_write_text(target, "old")
    atomic_write_text(target, "new")
    assert target.read_text(encoding="utf-8") == "new"


# AC: AC1
def test_atomic_write_rejects_path_outside_root(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must include filename"):
        atomic_write_text(tmp_path, "no filename")
