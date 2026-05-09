"""Local vector store (FAISS) for Task005 corpus + template registry.

Design goals:
- Local-first, no external DB.
- Deterministic persistence: `faiss__<ver>.bin` + `meta__<ver>.json`.
- Safe: stores only text chunks (schema/docs/templates), never DB rows.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.rag.task005_ingest import RagChunk
from app.tools.task005_corpus_fs import DEFAULT_CORPUS_ROOT


META_PREFIX = "meta__"
INDEX_PREFIX = "faiss__"


@dataclass(frozen=True)
class VectorStoreIndex:
    corpus_version: str
    dim: int
    index_path: Path
    meta_path: Path

    def load_meta(self) -> dict[str, Any]:
        return json.loads(self.meta_path.read_text(encoding="utf-8"))


def _index_dir(corpus_root: Path) -> Path:
    return corpus_root / "index"


def latest_vector_index(corpus_root: Path | None = None) -> VectorStoreIndex | None:
    root = (corpus_root or DEFAULT_CORPUS_ROOT).resolve()
    d = _index_dir(root)
    if not d.is_dir():
        return None
    metas = sorted(d.glob(f"{META_PREFIX}*.json"))
    if not metas:
        return None
    meta = metas[-1]
    ver = meta.stem[len(META_PREFIX) :] if meta.stem.startswith(META_PREFIX) else ""
    idx = d / f"{INDEX_PREFIX}{ver}.bin"
    if not ver or not idx.exists():
        return None
    payload = json.loads(meta.read_text(encoding="utf-8"))
    dim = int(payload.get("dim") or 0)
    return VectorStoreIndex(corpus_version=ver, dim=dim, index_path=idx, meta_path=meta)


def _chunks_from_meta(meta: dict[str, Any]) -> list[RagChunk]:
    chunks_payload = meta.get("chunks") or []
    out: list[RagChunk] = []
    for ch in chunks_payload:
        if not isinstance(ch, dict):
            continue
        out.append(
            RagChunk(
                namespace=str(ch.get("namespace") or ""),
                chunk_id=str(ch.get("chunk_id") or ""),
                text=str(ch.get("text") or ""),
            )
        )
    return out


def query(
    *,
    query_embedding: Any,
    top_k: int,
    corpus_root: Path | None = None,
) -> list[dict[str, Any]]:
    """Return top-k chunks with scores from the latest vector index."""

    root = (corpus_root or DEFAULT_CORPUS_ROOT).resolve()
    latest = latest_vector_index(root)
    if latest is None:
        return []

    import faiss  # local import: optional at import-time
    import numpy as np

    idx = faiss.read_index(str(latest.index_path))
    meta = latest.load_meta()
    chunks = _chunks_from_meta(meta)

    q = np.asarray(query_embedding, dtype="float32").reshape(1, -1)
    denom = np.linalg.norm(q, axis=1, keepdims=True) + 1e-12
    q = q / denom
    scores, ids = idx.search(q, int(top_k))
    picked: list[dict[str, Any]] = []
    for score, i in zip(scores[0].tolist(), ids[0].tolist(), strict=False):
        if i < 0 or i >= len(chunks):
            continue
        ch = chunks[i]
        picked.append(
            {
                "id": ch.chunk_id,
                "text": ch.text,
                "source": {"namespace": ch.namespace},
                "score": float(score),
            }
        )
    return picked

