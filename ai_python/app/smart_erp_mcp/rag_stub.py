from __future__ import annotations

from typing import Any

# Deterministic stub chunks (Plane A — not live DB truth).
CHUNKS: list[dict[str, Any]] = [
    {
        "id": "rag-products-1",
        "text": "Bảng `products` gồm các cột: id (PK), sku, qty — dùng cho tồn kho.",
        "source": {"doc": "erp-schema-stub.md", "section": "inventory"},
        "score": 0.91,
    },
    {
        "id": "rag-revenue-1",
        "text": (
            "Bảng `revenue_daily` gồm: d (ngày), amount — dùng cho báo cáo doanh thu theo ngày."
        ),
        "source": {"doc": "erp-schema-stub.md", "section": "finance"},
        "score": 0.88,
    },
    {
        "id": "rag-policy-1",
        "text": "Số liệu live phải lấy qua read/sql_execute_read; RAG có độ trễ index.",
        "source": {"doc": "ai-policy-stub.md"},
        "score": 0.85,
    },
]


def rag_retrieve(query: str, top_k: int = 5) -> dict[str, Any]:
    top_k = max(1, min(top_k, 10))
    q_tokens = {w for w in query.lower().split() if len(w) >= 2}

    def score(chunk: dict[str, Any]) -> float:
        text_l = chunk["text"].lower()
        if not q_tokens:
            return float(chunk["score"])
        hits = sum(1 for w in q_tokens if w in text_l)
        return float(chunk["score"]) + 0.01 * hits

    ranked = sorted(CHUNKS, key=score, reverse=True)[:top_k]
    return {
        "ok": True,
        "chunks": ranked,
        "rag_stale_warning": (
            "Stub RAG: không đại diện snapshot DB; "
            "dùng read_catalog_snapshot / sql_execute_read cho số live."
        ),
    }
