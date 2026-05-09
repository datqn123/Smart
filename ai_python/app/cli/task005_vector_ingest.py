"""Build FAISS vector index from Task005 local index + registry.

Usage:
  cd ai_python
  python -m app.cli.task005_vector_ingest
"""

from __future__ import annotations

from pathlib import Path

from app.rag.vector_ingest import build_faiss_index
from app.tools.task005_corpus_fs import DEFAULT_CORPUS_ROOT


def main() -> None:
    try:
        res = build_faiss_index(corpus_root=Path(DEFAULT_CORPUS_ROOT))
    except ModuleNotFoundError as e:
        raise SystemExit(
            f"Missing dependency: {e}. Run: pip install -r requirements.txt"
        ) from e
    print(
        f"ok: corpus_version={res.corpus_version} dim={res.dim} chunks={res.chunk_count} "
        f"index={res.index_path.name} meta={res.meta_path.name}"
    )


if __name__ == "__main__":
    main()

