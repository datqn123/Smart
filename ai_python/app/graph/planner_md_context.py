"""Curated markdown context for pre-intent planner (chatbot runtime only)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_ROOT_DIR = Path(__file__).resolve().parents[2]
_PROMPTS_DIR = _ROOT_DIR / "app" / "prompts" / "agents"
_GUIDE_DIR = _ROOT_DIR / "app" / "data" / "erp" / "guide_chunks"
_DOCS_DIR = _ROOT_DIR / "docs"

_BASE_DOCS: tuple[tuple[Path, int], ...] = (
    (_PROMPTS_DIR / "README.md", 1000),
    (_DOCS_DIR / "intent_registry_howto.md", 900),
    (_GUIDE_DIR / "09_ai_chat.md", 1000),
)

_KEYWORD_DOCS: tuple[tuple[tuple[str, ...], Path, int], ...] = (
    (("tồn kho", "kho", "nhập kho", "xuất kho", "inventory", "stock"), _GUIDE_DIR / "05_inventory.md", 700),
    (("sản phẩm", "danh mục", "nhà cung cấp", "khách hàng", "catalog", "product", "supplier", "customer"), _GUIDE_DIR / "06_catalog.md", 700),
    (("đơn hàng", "bán lẻ", "retail", "sales order", "order"), _GUIDE_DIR / "07_orders.md", 700),
    (("doanh thu", "chi phí", "sổ cái", "tài chính", "revenue", "expense", "ledger", "finance"), _GUIDE_DIR / "08_finance.md", 700),
)


@lru_cache(maxsize=64)
def _read_markdown_snippet(path: str, max_chars: int) -> str:
    p = Path(path)
    if not p.is_file():
        return ""
    text = p.read_text(encoding="utf-8").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n..."


def _matches_keywords(question: str, keywords: tuple[str, ...]) -> bool:
    q = (question or "").strip().lower()
    if not q:
        return False
    return any(k in q for k in keywords)


def _rel_ref(path: Path) -> str:
    try:
        return str(path.relative_to(_ROOT_DIR)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def build_planner_md_context(
    user_question: str,
    *,
    max_chars: int,
    enabled: bool,
) -> tuple[str, list[str]]:
    """Return (markdown_context, refs) for planner prompt grounding."""
    if not enabled or max_chars <= 0:
        return "", []

    selected: list[tuple[Path, int]] = list(_BASE_DOCS)
    for keywords, path, cap in _KEYWORD_DOCS:
        if _matches_keywords(user_question, keywords):
            selected.append((path, cap))

    refs: list[str] = []
    chunks: list[str] = []
    used = 0
    seen: set[str] = set()
    for path, cap in selected:
        ref = _rel_ref(path)
        if ref in seen:
            continue
        seen.add(ref)
        snippet = _read_markdown_snippet(str(path), cap).strip()
        if not snippet:
            continue
        block = f"### {ref}\n{snippet}"
        if used + len(block) > max_chars:
            remain = max_chars - used
            if remain <= 200:
                break
            block = block[:remain].rstrip() + "\n..."
        chunks.append(block)
        refs.append(ref)
        used += len(block)
        if used >= max_chars:
            break

    return "\n\n".join(chunks), refs

