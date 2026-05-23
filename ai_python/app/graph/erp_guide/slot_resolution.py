"""Resolve missing_slots / noop issues before clarify vs proceed."""

from __future__ import annotations

import re
from datetime import datetime

from app.llm.schemas import DomainIssue

# User already gave a relative or absolute time window — do not ask "năm nào?"
_TIME_RANGE_PATTERNS = [
    r"từ\s+đầu\s+năm",
    r"đầu\s+năm\s+\d{4}",
    r"từ\s+đầu\s+năm\s+\d{4}",
    r"từ\s+tháng\s+\d",
    r"tháng\s+này",
    r"tháng\s+trước",
    r"quý\s+[1234]",
    r"năm\s+nay",
    r"năm\s+\d{4}",
    r"tới\s+giờ",
    r"đến\s+nay",
    r"hiện\s+tại",
    r"hôm\s+nay",
    r"tuần\s+này",
    r"trong\s+tháng",
    r"ytd",
]

_YEAR_SLOT_KEYWORDS = frozenset(
    {
        "year",
        "năm",
        "nam",
        "which year",
        "năm nào",
        "cho năm",
        "thời gian",
        "time period",
        "khoảng thời gian",
        "date range",
    }
)

_ORDER_STATUS_SLOT_KEYWORDS = frozenset(
    {
        "completed",
        "hoàn tất",
        "hoan tat",
        "trạng thái",
        "trang thai",
        "status",
        "đã hoàn",
        "da hoan",
    }
)

_ORDER_CHANNEL_SLOT_KEYWORDS = frozenset(
    {
        "order type",
        "order channel",
        "loại đơn",
        "kênh bán",
        "kênh",
        "bán lẻ",
        "ban le",
        "retail",
        "bán sỉ",
        "ban si",
        "wholesale",
        "pos",
        "đơn sỉ",
        "đơn bán",
    }
)

_FOLLOW_UP_MARKERS = (
    "chi tiết",
    "từng đơn",
    "các đơn",
    "mỗi đơn",
    "liệt kê",
    "danh sách",
    "tháng đó",
    "kỳ đó",
    "số đó",
    "đơn đó",
    "như trên",
    "tương tự",
)


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def has_time_range_in_question(question: str) -> bool:
    q = _norm(question)
    if not q:
        return False
    for pat in _TIME_RANGE_PATTERNS:
        if re.search(pat, q, re.IGNORECASE):
            return True
    if re.search(r"\b20\d{2}\b", q):
        return True
    return False


def _slot_mentions_year(slot: str) -> bool:
    s = _norm(slot)
    return any(k in s for k in _YEAR_SLOT_KEYWORDS)


def _slot_mentions_order_status(slot: str) -> bool:
    s = _norm(slot)
    return any(k in s for k in _ORDER_STATUS_SLOT_KEYWORDS)


def _slot_mentions_order_channel(slot: str) -> bool:
    s = _norm(slot).replace("_", " ")
    return any(k in s for k in _ORDER_CHANNEL_SLOT_KEYWORDS)


def has_order_channel_in_text(text: str) -> bool:
    t = _norm(text)
    if not t:
        return False
    if "bán lẻ" in t or "ban le" in t or "retail" in t or "pos" in t:
        return True
    if "bán sỉ" in t or "ban si" in t or "wholesale" in t or "đơn sỉ" in t:
        return True
    return False


def _is_elliptical_follow_up(question: str) -> bool:
    q = _norm(question)
    if not q or len(q) > 140:
        return False
    if any(m in q for m in _FOLLOW_UP_MARKERS):
        return True
    return bool(re.search(r"\b(từng|mỗi)\s+đơn\b", q))


def expand_elliptical_follow_up(question: str, context_text: str) -> str:
    """
    Expand short follow-ups using recent thread (e.g. «chi tiết từng đơn» after retail count).
    Returns original question when context is insufficient.
    """
    q = question.strip()
    ctx = (context_text or "").strip()
    if not q or not ctx or not _is_elliptical_follow_up(q):
        return q
    low_q = _norm(q)
    low_ctx = _norm(ctx)
    extras: list[str] = []

    if re.search(r"\bđơn\b", low_q) and not has_order_channel_in_text(q):
        if "bán lẻ" in low_ctx or "ban le" in low_ctx or "retail" in low_ctx:
            extras.append("đơn hàng bán lẻ")
        elif "bán sỉ" in low_ctx or "ban si" in low_ctx or "wholesale" in low_ctx:
            extras.append("đơn hàng bán sỉ")

    if ("tháng đó" in low_q or "kỳ đó" in low_q) and "tháng này" in low_ctx:
        extras.append("trong tháng này")
    elif "tháng này" in low_ctx and has_time_range_in_question(ctx) and not has_time_range_in_question(q):
        if re.search(r"\bđơn\b", low_q):
            extras.append("trong tháng này")

    if not extras:
        return q
    return f"{q} ({', '.join(extras)})"


def filter_resolved_missing_slots(
    question: str,
    missing_slots: list[str],
    *,
    dialog_tail: str = "",
) -> list[str]:
    """Drop slots already satisfied by the user message or recent thread."""
    if not missing_slots:
        return []
    has_time = has_time_range_in_question(question)
    combined = f"{question}\n{dialog_tail}"
    has_channel = has_order_channel_in_text(combined)
    kept: list[str] = []
    for slot in missing_slots:
        s = str(slot).strip()
        if not s:
            continue
        if has_time and _slot_mentions_year(s):
            continue
        if has_channel and _slot_mentions_order_channel(s):
            continue
        kept.append(s)
    return kept


def strip_noop_issues(issues: list[DomainIssue]) -> list[DomainIssue]:
    """Remove fake term fixes (canonical equals user phrase)."""
    out: list[DomainIssue] = []
    for i in issues:
        if i.type == "term_mismatch":
            u = _norm(i.user_text)
            c = _norm(i.canonical_vi or "")
            if u and c and u == c:
                continue
        out.append(i)
    return out


_CATALOG_MODULE_IDS = frozenset({"catalog"})

_CATEGORY_LABEL_CANONICALS = frozenset(
    {
        "loại sản phẩm",
        "danh mục",
        "danh mục sản phẩm",
        "nhóm hàng",
        "nhóm sản phẩm",
        "category",
    }
)

_PRODUCT_COLLOQUIAL_CANONICALS = frozenset(
    {
        "sản phẩm",
        "product",
        "hàng hóa",
    }
)


def _mentions_category_assignment(question: str) -> bool:
    q = question.lower()
    return "danh mục" in q or "danh muc" in q or "category" in q


def is_catalog_write_intent(question: str) -> bool:
    """User is creating/updating catalog master data (product, category, …)."""
    q = question.lower()
    if not re.search(r"\b(thêm|tạo|thêm mới|cho mình|giúp)\b", q):
        return False
    return bool(re.search(r"\b(sản phẩm|món|sku|hàng)\b", q))


def catalog_module_matched(matched_modules: list[str] | None) -> bool:
    for raw in matched_modules or []:
        mid = _norm(str(raw)).strip("[]")
        if mid in _CATALOG_MODULE_IDS:
            return True
    return False


def strip_catalog_draft_misnomers(issues: list[DomainIssue], question: str) -> list[DomainIssue]:
    """Do not block catalog drafts on valid category names or colloquial «món»."""
    catalog_ctx = is_catalog_write_intent(question) or _mentions_category_assignment(question)
    if not catalog_ctx:
        return issues
    q_lower = question.lower()
    out: list[DomainIssue] = []
    for i in issues:
        if i.type != "term_mismatch":
            out.append(i)
            continue
        ut = (i.user_text or "").strip().lower()
        canon = (i.canonical_vi or "").strip().lower()
        if _mentions_category_assignment(question) and ut and ut in q_lower:
            if canon in _CATEGORY_LABEL_CANONICALS:
                continue
        if is_catalog_write_intent(question) and ut == "món" and canon in _PRODUCT_COLLOQUIAL_CANONICALS:
            continue
        out.append(i)
    return out


def should_proceed_after_repeated_clarify(
    *,
    question: str,
    matched_modules: list[str] | None,
    identical_human_turns: int,
) -> bool:
    """User resent the same catalog request after clarify — stop looping."""
    if identical_human_turns < 2:
        return False
    if not catalog_module_matched(matched_modules):
        return False
    return is_catalog_write_intent(question) or _mentions_category_assignment(question)


def has_blocking_issues(issues: list[DomainIssue]) -> bool:
    return any(i.severity == "block" and i.type == "term_mismatch" for i in issues)


def append_slot_hints_to_question(question: str, missing_slots: list[str]) -> str:
    """Light defaults for optional slots when we still clarify."""
    q = question.strip()
    if not q:
        return q
    extras: list[str] = []
    for slot in missing_slots:
        s = _norm(slot)
        if _slot_mentions_order_status(s) and "hoàn tất" not in _norm(q) and "đã" not in _norm(q):
            extras.append("đơn đã hoàn tất")
    if not extras:
        return q
    if not q.endswith("?"):
        q = q + "?"
    return f"{q.rstrip('?')} ({', '.join(extras)})?"


def default_normalized_for_proceed(question: str) -> str:
    """Normalize time phrase for SQL-friendly wording when proceeding."""
    q = question.strip()
    year = datetime.now().year
    if re.search(r"từ\s+đầu\s+năm(?!\s+\d{4})", q, re.IGNORECASE):
        q = re.sub(
            r"từ\s+đầu\s+năm",
            f"từ đầu năm {year}",
            q,
            count=1,
            flags=re.IGNORECASE,
        )
    return q
