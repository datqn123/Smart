"""Build a FAISS index from Task005 local chunk index + template registry chunks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from app.rag.task005_ingest import RagChunk, read_chunks
from app.registry.task005_templates import TemplateRegistry, load_registry_from_path
from app.tools.task005_corpus_fs import (
    DEFAULT_CORPUS_ROOT,
    HEALTH_NAMESPACE,
    SCHEMA_NAMESPACE,
    atomic_write_json,
)


TEMPLATE_NAMESPACE = "erp_templates"


@dataclass(frozen=True)
class IngestResult:
    corpus_version: str
    dim: int
    chunk_count: int
    index_path: Path
    meta_path: Path


def _latest_task005_index_version(corpus_root: Path) -> str | None:
    d = corpus_root / "index"
    if not d.is_dir():
        return None
    paths = sorted(d.glob("index__*.json"))
    if not paths:
        return None
    stem = paths[-1].stem
    prefix = "index__"
    return stem[len(prefix) :] if stem.startswith(prefix) else None


def _registry_chunks(reg: TemplateRegistry) -> list[RagChunk]:
    chunks: list[RagChunk] = []
    for tpl in reg.templates:
        text = (
            f"# template_id: {tpl.template_id}\n"
            f"intent: {tpl.intent}\n"
            f"description: {tpl.description}\n"
            f"params_example: {json.dumps(tpl.params, ensure_ascii=False)}\n"
            f"smoke_safe: {tpl.smoke_safe}\n"
        )
        chunks.append(
            RagChunk(
                namespace=TEMPLATE_NAMESPACE,
                chunk_id=f"{TEMPLATE_NAMESPACE}:{tpl.template_id}",
                text=text,
            )
        )
    return chunks


def _normalize(v: np.ndarray) -> np.ndarray:
    denom = np.linalg.norm(v, axis=1, keepdims=True) + 1e-12
    return v / denom


def build_faiss_index(
    *,
    corpus_root: Path | None = None,
    registry_path: Path | None = None,
    top_k_per_namespace: int = 0,
) -> IngestResult:
    """Create `faiss__<ver>.bin` + `meta__<ver>.json` under `<corpus_root>/index/`."""

    import faiss  # local import
    from sentence_transformers import SentenceTransformer

    root = (corpus_root or DEFAULT_CORPUS_ROOT).resolve()
    ver = _latest_task005_index_version(root)
    if not ver:
        raise RuntimeError("No Task005 local index found (run ingest_corpus first).")

    # Load chunks from the JSON local index (schema + health).
    schema = list(read_chunks(corpus_root=root, corpus_version=ver, namespace=SCHEMA_NAMESPACE))
    health = list(read_chunks(corpus_root=root, corpus_version=ver, namespace=HEALTH_NAMESPACE))

    # Load template registry chunks.
    reg_path = registry_path or (root.parent / "config" / "templates.json")
    reg = load_registry_from_path(reg_path)
    templates = _registry_chunks(reg)

    chunks: list[RagChunk] = [*schema, *health, *templates]
    texts = [c.text for c in chunks]
    if not texts:
        raise RuntimeError("No chunks to index.")

    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    model = SentenceTransformer(model_name)
    emb = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True).astype("float32")
    dim = int(emb.shape[1])

    index = faiss.IndexFlatIP(dim)
    index.add(emb)

    out_dir = root / "index"
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / f"faiss__{ver}.bin"
    meta_path = out_dir / f"meta__{ver}.json"

    faiss.write_index(index, str(index_path))
    meta_payload: dict[str, Any] = {
        "corpus_version": ver,
        "dim": dim,
        "embedding_model": model_name,
        "chunks": [c.to_payload() for c in chunks],
    }
    atomic_write_json(meta_path, meta_payload)

    return IngestResult(
        corpus_version=ver,
        dim=dim,
        chunk_count=len(chunks),
        index_path=index_path,
        meta_path=meta_path,
    )

