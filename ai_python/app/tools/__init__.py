from __future__ import annotations


def memory_block(state) -> str:
    """Khoi boi canh hoi thoai cho prompt tool. Rong khi khong co summary —
    chi summary ngan xuong tool, KHONG nhet 10 luot verbatim (spec)."""
    summary = state.get("memory_summary")
    if not summary:
        return ""
    return f"[Boi canh hoi thoai truoc]: {summary}\n"
