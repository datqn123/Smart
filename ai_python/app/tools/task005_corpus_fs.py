"""Filesystem helpers for the Task005 corpus pipeline.

Notes:
- Atomic write = write to ``<target>.tmp`` then ``os.replace`` onto target.
- Corpus version is a compact UTC ISO timestamp safe for filenames.
- Two namespaces: ``erp_schema`` (catalog/describe) and ``erp_template_health``
  (smoke status). They map to subdirectories under the corpus root.
"""

from __future__ import annotations

import contextlib
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_NAMESPACE = "erp_schema"
HEALTH_NAMESPACE = "erp_template_health"

DEFAULT_CORPUS_ROOT = (
    Path(__file__).resolve().parent.parent.parent / "data" / "rag_corpus"
)


def iso_corpus_version(now: datetime) -> str:
    """Render a UTC ISO timestamp safe for cross-platform filenames."""

    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return now.strftime("%Y-%m-%dT%H-%M-%SZ")


@dataclass(frozen=True)
class CorpusPaths:
    """Resolved filesystem layout for a single run."""

    root: Path
    schema_dir: Path
    health_dir: Path
    catalog_path: Path
    health_path: Path


def build_corpus_paths(root: Path, corpus_version: str) -> CorpusPaths:
    """Return canonical paths for catalog + health artifacts versioned by run."""

    if not corpus_version or not corpus_version.strip():
        raise ValueError("corpus_version must not be blank")

    cleaned = corpus_version.strip()
    schema_dir = root / SCHEMA_NAMESPACE
    health_dir = root / HEALTH_NAMESPACE
    catalog_path = schema_dir / f"catalog__{cleaned}.json"
    health_path = health_dir / f"health__{cleaned}.json"
    return CorpusPaths(
        root=root,
        schema_dir=schema_dir,
        health_dir=health_dir,
        catalog_path=catalog_path,
        health_path=health_path,
    )


def _ensure_filename(target: Path) -> None:
    if target.name == "" or target.is_dir():
        raise ValueError(f"target path must include filename: {target}")


def atomic_write_bytes(target: Path, data: bytes) -> None:
    """Write ``data`` to ``target`` atomically (temp + ``os.replace``)."""

    _ensure_filename(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f"{target.name}.tmp")
    try:
        with open(tmp, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            with contextlib.suppress(OSError):
                tmp.unlink()


def atomic_write_text(target: Path, text: str) -> None:
    """Atomic UTF-8 text write with no BOM."""

    atomic_write_bytes(target, text.encode("utf-8"))


def atomic_write_json(target: Path, payload: Any) -> None:
    """Atomic JSON write with stable indent and trailing newline."""

    text = json.dumps(payload, indent=2, sort_keys=False, ensure_ascii=False)
    atomic_write_text(target, text + "\n")
