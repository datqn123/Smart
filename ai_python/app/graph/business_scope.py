"""Business-scope contract for data query/chart turns.

This layer keeps business meaning stable across follow-ups (e.g. "liệt kê")
and injects deterministic constraints into SQL generation/review.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date
import re
from typing import Any

_DATA_INTENTS = frozenset({"system_data_query", "system_data_chart"})

_FOLLOW_UP_EXACT = frozenset(
    {
        "liệt kê",
        "liet ke",
        "chi tiết",
        "chi tiet",
        "chi tiết nhé",
        "chi tiet nhe",
        "xem chi tiết",
        "xem chi tiet",
        "chi tiet di",
        "chi tiết đi",
        "bảng",
        "bang",
        "vẽ biểu đồ",
        "ve bieu do",
        "biểu đồ",
        "bieu do",
        "theo tháng",
        "theo thang",
        "theo khách",
        "theo khach",
    }
)

_FOLLOW_UP_ACTION_HINTS = (
    "liệt kê",
    "liet ke",
    "chi tiết",
    "chi tiet",
    "xem",
    "bảng",
    "bang",
    "vẽ",
    "ve",
    "biểu đồ",
    "bieu do",
    "từng",
    "chi ra",
)

_ALL_STATUS_HINTS = (
    "mọi trạng thái",
    "moi trang thai",
    "tất cả trạng thái",
    "tat ca trang thai",
    "kể cả đã hủy",
    "ke ca da huy",
    "bao gồm hủy",
    "bao gom huy",
    "all statuses",
    "including cancelled",
)

_COMPLETED_ONLY_HINTS = (
    "đã hoàn thành",
    "da hoan thanh",
    "đã thu",
    "da thu",
    "thực thu",
    "thuc thu",
    "completed only",
)

_CASH_IN_HINTS = (
    "thu vào",
    "thu vao",
    "tổng thu",
    "tong thu",
    "thu tiền",
    "thu tien",
    "doanh thu",
    "revenue",
    "sales revenue",
)

_EXPENSE_HINTS = ("chi phí", "chi phi", "tổng chi", "tong chi", "expense", "cost")

_INVENTORY_VALUE_HINTS = ("giá trị tồn", "gia tri ton", "inventory value")

_TIME_HINTS = (
    "năm nay",
    "nam nay",
    "tháng này",
    "thang nay",
    "this year",
    "this month",
    "quý",
    "quarter",
    "tuần",
    "week",
    "hôm nay",
    "today",
)

_RAW_ALIAS_KEYS = frozenset({"coalesce", "sum", "count", "avg", "min", "max", "?column?"})

_RECONCILE_AMOUNT_HINTS = (
    "amount",
    "value",
    "revenue",
    "total",
    "price",
    "cost",
    "debt",
    "balance",
    "tien",
    "thu",
    "chi",
    "gia",
)
_RECONCILE_EXCLUDE_HINTS = (
    "id",
    "code",
    "count",
    "qty",
    "quantity",
    "month",
    "year",
    "day",
    "status",
)

_DETAIL_DIMENSION_HINTS = (
    "phiếu",
    "phieu",
    "receipt",
    "mã phiếu",
    "ma phieu",
    "khách",
    "khach",
    "customer",
    "mặt hàng",
    "mat hang",
    "sản phẩm",
    "san pham",
    "product",
    "theo khách",
    "theo khach",
    "theo phiếu",
    "theo phieu",
    "theo mặt hàng",
    "theo mat hang",
)

_DISTINCT_PRODUCT_HINTS = ("total_distinct_products_received", "distinct_product", "product_count")


def _norm(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().replace(",", "")
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None


def _has_follow_up_action(q: str) -> bool:
    return any(h in q for h in _FOLLOW_UP_ACTION_HINTS)


def _follow_up_action(q: str) -> str:
    if "biểu đồ" in q or "bieu do" in q or "vẽ" in q or "ve" in q:
        return "chart"
    if "bảng" in q or "bang" in q:
        return "table"
    if any(h in q for h in ("liệt kê", "liet ke", "chi tiết", "chi tiet", "xem", "từng")):
        return "detail"
    return "unknown"


def _mentions_scope_change(q: str) -> bool:
    if any(h in q for h in _TIME_HINTS):
        return True
    if any(h in q for h in _ALL_STATUS_HINTS):
        return True
    if any(h in q for h in _COMPLETED_ONLY_HINTS):
        return True
    return False


def _is_short_follow_up(question: str) -> bool:
    q = _norm(question)
    if not q:
        return False
    if q in _FOLLOW_UP_EXACT:
        return True
    words = re.findall(r"\w+", q)
    if len(words) <= 3 and any(k in q for k in ("liệt", "liet", "chi tiết", "chi tiet", "bảng", "bang", "biểu", "bieu")):
        return True
    if len(words) <= 8 and _has_follow_up_action(q):
        return True
    if len(q) <= 48 and _has_follow_up_action(q) and not _mentions_scope_change(q):
        return True
    return False


def _metric_from_question(q: str) -> str:
    if any(k in q for k in _CASH_IN_HINTS):
        return "cash_in"
    if any(k in q for k in _EXPENSE_HINTS):
        return "expense"
    if any(k in q for k in _INVENTORY_VALUE_HINTS):
        return "inventory_value"
    return "generic"


def _metric_label(metric: str) -> str:
    if metric == "cash_in":
        return "tổng tiền thu"
    if metric == "expense":
        return "tổng chi phí"
    if metric == "inventory_value":
        return "tổng giá trị tồn kho"
    return "kết quả"


def _detect_time_scope(q: str) -> dict[str, Any]:
    if "năm nay" in q or "nam nay" in q or "this year" in q:
        y = date.today().year
        return {"kind": "current_year", "from": f"{y}-01-01", "to": f"{y}-12-31"}
    if "tháng này" in q or "thang nay" in q or "this month" in q:
        today = date.today()
        return {"kind": "current_month", "year": today.year, "month": today.month}
    return {"kind": "unspecified"}


def _status_mode_from_question(q: str, metric: str) -> str:
    if any(k in q for k in _ALL_STATUS_HINTS):
        return "all_statuses"
    if any(k in q for k in _COMPLETED_ONLY_HINTS):
        return "completed_only"
    if metric == "cash_in":
        return "completed_only"
    return "unspecified"


def _source_preference(metric: str) -> list[str]:
    if metric == "cash_in":
        return ["financeledger", "cashtransactions"]
    if metric == "expense":
        return ["financeledger", "cashtransactions"]
    if metric == "inventory_value":
        return ["inventory", "products", "productpricehistory", "productunits"]
    return []


def _follow_up_effective_question(scope: dict[str, Any], original: str) -> str:
    metric = str(scope.get("metric") or "generic")
    label = _metric_label(metric)
    ts = scope.get("time_scope") if isinstance(scope.get("time_scope"), dict) else {}
    t_kind = str(ts.get("kind") or "unspecified")
    if t_kind == "current_year":
        suffix = "trong năm nay"
    elif t_kind == "current_month":
        suffix = "trong tháng này"
    else:
        suffix = ""
    status_scope = scope.get("status_scope") if isinstance(scope.get("status_scope"), dict) else {}
    mode = str(status_scope.get("mode") or "unspecified")
    if mode == "completed_only":
        status_text = " (chỉ các khoản đã hoàn thành)"
    elif mode == "all_statuses":
        status_text = " (mọi trạng thái)"
    else:
        status_text = ""
    q = _norm(original)
    action = _follow_up_action(q)
    follow = scope.get("followup") if isinstance(scope.get("followup"), dict) else {}
    contract = (
        follow.get("reconcile_contract")
        if isinstance(follow.get("reconcile_contract"), dict)
        else {}
    )
    dimension_kind = str(contract.get("dimension_kind") or "")
    if action == "chart":
        core = f"Vẽ biểu đồ {label} {suffix}".strip()
    elif action == "table":
        if dimension_kind == "product":
            core = f"Hiển thị bảng chi tiết theo từng sản phẩm {suffix}".strip()
        else:
            core = f"Hiển thị bảng chi tiết {label} {suffix}".strip()
    else:
        if dimension_kind == "product":
            core = f"Liệt kê chi tiết theo từng sản phẩm {suffix}".strip()
        else:
            core = f"Liệt kê chi tiết các khoản cấu thành {label} {suffix}".strip()
    return f"{core}{status_text}".strip()


def _scope_from_last_data_answer(last_data_answer: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(last_data_answer, dict):
        return None
    scope = last_data_answer.get("business_scope")
    if isinstance(scope, dict):
        return deepcopy(scope)
    return None


def _scalar_total_from_last_data_answer(last_data_answer: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(last_data_answer, dict):
        return None
    scalar = last_data_answer.get("scalar_total")
    if not isinstance(scalar, dict):
        return None
    val = _to_float(scalar.get("value"))
    if val is None:
        return None
    return {
        "value": val,
        "column": str(scalar.get("column") or ""),
        "label": str(scalar.get("label") or ""),
    }


def _reconcile_contract_from_last_data_answer(last_data_answer: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(last_data_answer, dict):
        return None
    contract = last_data_answer.get("reconcile_contract")
    if not isinstance(contract, dict):
        return None
    return deepcopy(contract)


def _detail_breakdown_wanted(scope: dict[str, Any] | None) -> bool:
    if not isinstance(scope, dict):
        return False
    follow = scope.get("followup") if isinstance(scope.get("followup"), dict) else {}
    if not follow.get("inherits_previous_scope"):
        return False
    return bool(follow.get("wants_detail_breakdown"))


def followup_detail_needs_clarify(
    scope: dict[str, Any] | None,
    *,
    raw_question: str,
) -> bool:
    """Whether a follow-up detail request is still ambiguous and should confirm with user."""
    if not _detail_breakdown_wanted(scope):
        return False
    if not isinstance(scope, dict):
        return False
    follow = scope.get("followup") if isinstance(scope.get("followup"), dict) else {}
    if not follow.get("has_previous_scalar_total"):
        return False
    q = _norm(raw_question)
    if not q:
        return False
    if any(h in q for h in _DETAIL_DIMENSION_HINTS):
        return False
    words = re.findall(r"\w+", q)
    if len(words) <= 10 and _has_follow_up_action(q):
        return True
    return len(q) <= 64 and _has_follow_up_action(q) and not _mentions_scope_change(q)


def build_followup_detail_clarify_advice(
    *,
    user_question: str,
    intent: str | None,
    previous_scope: dict[str, Any] | None,
    previous_data_answer: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Build clarify payload pieces for ambiguous detail follow-up."""
    scope = resolve_business_scope(
        user_question,
        intent=intent,
        previous_scope=previous_scope,
        previous_data_answer=previous_data_answer,
    )
    if not followup_detail_needs_clarify(scope, raw_question=user_question):
        return None
    metric = str(scope.get("metric") or "generic") if isinstance(scope, dict) else "generic"
    label = _metric_label(metric)
    ts = scope.get("time_scope") if isinstance(scope, dict) and isinstance(scope.get("time_scope"), dict) else {}
    t_kind = str(ts.get("kind") or "unspecified")
    if t_kind == "current_year":
        t_hint = "trong năm nay"
    elif t_kind == "current_month":
        t_hint = "trong tháng này"
    else:
        t_hint = "theo cùng mốc thời gian vừa tính"
    suggested = f"Liệt kê theo phiếu thu {t_hint} để tổng khớp {label} vừa trả."
    questions = [
        "Bạn muốn liệt kê theo phiếu, theo khách hàng, hay theo mặt hàng?",
        "Bạn muốn chỉ các khoản đã hoàn thành hay mọi trạng thái?",
    ]
    return {
        "suggested_rewrite": suggested,
        "questions": questions,
        "scope": scope,
    }


def resolve_business_scope(
    user_question: str,
    *,
    intent: str | None = None,
    previous_scope: dict[str, Any] | None = None,
    previous_data_answer: dict[str, Any] | None = None,
    force_followup_inherit: bool = False,
) -> dict[str, Any] | None:
    """Build a stable business scope for SQL/summarize from the current turn."""
    if intent and intent not in _DATA_INTENTS:
        return None
    raw_q = (user_question or "").strip()
    if not raw_q:
        if isinstance(previous_scope, dict):
            return deepcopy(previous_scope)
        return _scope_from_last_data_answer(previous_data_answer)
    q = _norm(raw_q)
    base_scope = deepcopy(previous_scope) if isinstance(previous_scope, dict) else None
    if base_scope is None:
        base_scope = _scope_from_last_data_answer(previous_data_answer)
    inherited = bool(base_scope) and (force_followup_inherit or _is_short_follow_up(raw_q))
    if inherited and isinstance(base_scope, dict):
        scope = deepcopy(base_scope)
        action = _follow_up_action(q)
        scalar_prev = _scalar_total_from_last_data_answer(previous_data_answer)
        scope["followup"] = {
            "is_followup": True,
            "inherits_previous_scope": True,
            "utterance": raw_q,
            "action": action,
            "wants_detail_breakdown": action in ("detail", "table"),
            "has_previous_scalar_total": scalar_prev is not None,
        }
        if scalar_prev is not None:
            scope["followup"]["previous_scalar_total"] = scalar_prev["value"]
        contract_prev = _reconcile_contract_from_last_data_answer(previous_data_answer)
        if isinstance(contract_prev, dict):
            scope["followup"]["reconcile_contract"] = contract_prev
        mode = _status_mode_from_question(q, str(scope.get("metric") or "generic"))
        if mode in ("completed_only", "all_statuses"):
            status_scope = scope.get("status_scope") if isinstance(scope.get("status_scope"), dict) else {}
            status_scope["mode"] = mode
            scope["status_scope"] = status_scope
        scope["effective_question"] = _follow_up_effective_question(scope, raw_q)
        scope["raw_user_question"] = raw_q
        return scope

    metric = _metric_from_question(q)
    status_mode = _status_mode_from_question(q, metric)
    status_scope = {
        "mode": status_mode,
        "included": ["Completed"] if status_mode == "completed_only" else [],
        "excluded": ["Pending", "Cancelled", "Draft"] if status_mode == "completed_only" else [],
    }
    scope = {
        "metric": metric,
        "business_meaning": "actual_received_amount" if metric == "cash_in" else metric,
        "source_preference": _source_preference(metric),
        "time_scope": _detect_time_scope(q),
        "status_scope": status_scope,
        "answer_policy": {
            "hide_raw_sql_alias": True,
            "must_explain_status_scope": status_mode == "all_statuses",
            "money_unit": "VND",
        },
        "followup": {
            "is_followup": False,
            "inherits_previous_scope": False,
            "utterance": raw_q,
            "action": "none",
            "wants_detail_breakdown": False,
        },
        "effective_question": raw_q,
        "raw_user_question": raw_q,
    }
    return scope


def scope_effective_question(user_question: str, scope: dict[str, Any] | None) -> str:
    if isinstance(scope, dict):
        t = str(scope.get("effective_question") or "").strip()
        if t:
            return t
    return user_question


def render_business_scope_sql_block(scope: dict[str, Any] | None) -> str:
    if not isinstance(scope, dict):
        return ""
    metric = str(scope.get("metric") or "generic")
    status_scope = scope.get("status_scope") if isinstance(scope.get("status_scope"), dict) else {}
    status_mode = str(status_scope.get("mode") or "unspecified")
    time_scope = scope.get("time_scope") if isinstance(scope.get("time_scope"), dict) else {}
    lines = [
        "Business scope contract (must follow):",
        f"- metric: {metric}",
    ]
    if metric == "cash_in":
        lines.append("- Prefer financeledger for totals; for financeledger revenue use transaction_type = 'SalesRevenue'.")
        lines.append("- If using cashtransactions, enforce status = 'Completed' unless user explicitly asks all statuses.")
    if status_mode == "completed_only":
        lines.append("- Status scope is completed_only: exclude Pending/Cancelled/Draft records.")
    elif status_mode == "all_statuses":
        lines.append("- Status scope is all_statuses: include status column and keep wording as 'ghi nhận', not 'đã thu'.")
    t_kind = str(time_scope.get("kind") or "unspecified")
    if t_kind == "current_year":
        y = date.today().year
        t_from = str(time_scope.get("from") or f"{y}-01-01")
        t_to = str(time_scope.get("to") or f"{y}-12-31")
        lines.append(
            f"- Time scope is the CURRENT year = {y} (NOT 2024 or any other year). "
            f"\"năm nay\"/\"this year\" means {y}. The full-year window is {t_from}..{t_to}. "
            f"If the user named specific months (e.g. tháng 2 đến tháng 5), keep year={y} "
            f"and build the date range from those months within {y} (e.g. {y}-02-01 .. {y}-05-31). "
            f"Never substitute a different year."
        )
    elif t_kind == "current_month":
        today = date.today()
        lines.append(
            f"- Time scope is the CURRENT month = {today.year}-{today.month:02d} "
            f"(NOT 2024). \"tháng này\"/\"this month\" means {today.year}-{today.month:02d}; "
            f"keep year={today.year}."
        )
    follow = scope.get("followup") if isinstance(scope.get("followup"), dict) else {}
    if follow.get("inherits_previous_scope"):
        lines.append("- This is a follow-up; keep metric/time/status scope from the previous data answer.")
    lines.append("- Aggregate SELECT columns must use explicit business aliases (e.g. total_revenue, total_received_amount).")
    return "\n".join(lines)


def render_last_data_answer_sql_block(
    last_data_answer: dict[str, Any] | None,
    scope: dict[str, Any] | None,
) -> str:
    if not isinstance(last_data_answer, dict):
        return ""
    if not _detail_breakdown_wanted(scope):
        return ""
    scalar = _scalar_total_from_last_data_answer(last_data_answer)
    lines = ["Previous answer context (must stay consistent):"]
    prev_q = str(
        last_data_answer.get("effective_question")
        or last_data_answer.get("user_question")
        or ""
    ).strip()
    if prev_q:
        lines.append(f"- previous_effective_question: {prev_q[:240]}")
    shape = str(last_data_answer.get("result_shape") or "unknown")
    lines.append(f"- previous_result_shape: {shape}")
    if scalar is not None:
        lines.append(f"- previous_scalar_total: {scalar['value']:.6f}")
        col = str(scalar.get("column") or "").strip()
        if col:
            lines.append(f"- previous_scalar_column: {col}")
        lines.append(
            "- For this follow-up detail query: keep the same business filters and make detail rows reconcile "
            "with previous_scalar_total (SUM(amount-like detail column) should match)."
        )
    return "\n".join(lines)


def build_last_data_answer_context(
    *,
    intent: str | None,
    user_question: str,
    effective_question: str,
    business_scope: dict[str, Any] | None,
    query_result: dict[str, Any] | None,
    generated_sql: str | None,
    reconcile_meta: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if intent and intent not in _DATA_INTENTS:
        return None
    qr = query_result if isinstance(query_result, dict) else {}
    rows = qr.get("rows") if isinstance(qr.get("rows"), list) else []
    row_count = len(rows)
    first = rows[0] if rows and isinstance(rows[0], dict) else {}
    col_keys = [str(k) for k in first.keys()][:24] if isinstance(first, dict) else []
    shape = "unknown"
    scalar_total: dict[str, Any] | None = None
    if row_count == 0:
        shape = "empty"
    elif isinstance(first, dict) and row_count == 1 and len(first) == 1:
        shape = "scalar"
        (col, raw_val), = first.items()
        num = _to_float(raw_val)
        if num is not None:
            scalar_total = {
                "value": num,
                "column": str(col),
                "label": scalar_label_from_scope(business_scope) or str(col),
            }
    elif row_count == 1 and isinstance(first, dict):
        shape = "single_row"
    else:
        shape = "table"
    out: dict[str, Any] = {
        "intent": str(intent or ""),
        "user_question": user_question,
        "effective_question": effective_question,
        "business_scope": deepcopy(business_scope) if isinstance(business_scope, dict) else None,
        "result_shape": shape,
        "row_count": row_count,
        "column_keys": col_keys,
        "generated_sql": (generated_sql or "")[:8000],
    }
    if scalar_total is not None:
        out["scalar_total"] = scalar_total
        col_norm = _norm(str(scalar_total.get("column") or "")).replace(" ", "_")
        sql_norm = _norm(generated_sql or "")
        if any(h in col_norm for h in _DISTINCT_PRODUCT_HINTS) or (
            "count(distinct" in sql_norm and ("product_id" in sql_norm or "products" in sql_norm)
        ):
            out["reconcile_contract"] = {
                "metric_class": "distinct_count",
                "dimension_kind": "product",
                "dimension_candidates": ["product_id", "sku_code", "name"],
                "expected_total": float(scalar_total["value"]),
            }
    if isinstance(reconcile_meta, dict) and reconcile_meta:
        out["reconcile"] = dict(reconcile_meta)
    return out


def _pick_reconcile_numeric_column(rows: list[dict[str, Any]]) -> tuple[str, float] | None:
    if not rows:
        return None
    sample = rows[0]
    if not isinstance(sample, dict):
        return None
    best_key = ""
    best_score = -1.0
    best_sum = 0.0
    min_hits = max(1, len(rows) // 2)
    for key in sample.keys():
        key_s = str(key)
        values: list[float] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            num = _to_float(row.get(key_s))
            if num is not None:
                values.append(num)
        if len(values) < min_hits:
            continue
        key_n = _norm(key_s).replace(" ", "_")
        score = float(len(values))
        if any(h in key_n for h in _RECONCILE_AMOUNT_HINTS):
            score += 5.0
        if any(h in key_n for h in _RECONCILE_EXCLUDE_HINTS):
            score -= 3.0
        if score > best_score:
            best_score = score
            best_key = key_s
            best_sum = float(sum(values))
    if not best_key:
        return None
    return best_key, best_sum


def reconcile_detail_rows_with_previous_total(
    *,
    scope: dict[str, Any] | None,
    previous_data_answer: dict[str, Any] | None,
    query_result: dict[str, Any] | None,
) -> tuple[bool, str | None, dict[str, Any]]:
    """Check detail follow-up rows reconcile with previous scalar total."""
    base_meta: dict[str, Any] = {"required": False, "ok": True}
    if not _detail_breakdown_wanted(scope):
        return True, None, base_meta
    prev_scalar = _scalar_total_from_last_data_answer(previous_data_answer)
    if prev_scalar is None:
        base_meta["reason"] = "no_previous_scalar_total"
        return True, None, base_meta
    rows = query_result.get("rows") if isinstance(query_result, dict) else None
    if not isinstance(rows, list) or not rows:
        return False, "reconcile: follow-up detail query returned no rows", {
            "required": True,
            "ok": False,
            "expected_total": prev_scalar["value"],
            "reason": "empty_rows",
        }
    contract = _reconcile_contract_from_last_data_answer(previous_data_answer)
    if isinstance(contract, dict) and str(contract.get("metric_class") or "") == "distinct_count":
        expected = float(contract.get("expected_total") or prev_scalar["value"])
        candidates_raw = contract.get("dimension_candidates")
        candidates = (
            [str(x) for x in candidates_raw if str(x).strip()]
            if isinstance(candidates_raw, list)
            else ["product_id", "sku_code", "name"]
        )
        chosen = next((c for c in candidates if any(isinstance(r, dict) and c in r for r in rows)), None)
        if chosen is None:
            return False, "reconcile: thiếu cột định danh để đối chiếu tổng số lượng không trùng", {
                "required": True,
                "ok": False,
                "expected_total": expected,
                "reason": "missing_dimension_column",
            }
        unique_vals = {
            str(r.get(chosen)).strip().lower()
            for r in rows
            if isinstance(r, dict) and r.get(chosen) is not None and str(r.get(chosen)).strip()
        }
        got = float(len(unique_vals))
        diff = abs(got - expected)
        meta = {
            "required": True,
            "ok": diff == 0.0,
            "dimension_column": chosen,
            "detail_distinct_count": got,
            "expected_total": expected,
            "difference": diff,
            "tolerance": 0.0,
            "metric_class": "distinct_count",
        }
        if diff > 0.0:
            detail = (
                f"reconcile mismatch: DISTINCT({chosen})={got:.0f} differs from previous total "
                f"{expected:.0f} (diff={diff:.0f})."
            )
            return False, detail, meta
        return True, None, meta
    picked = _pick_reconcile_numeric_column(rows)
    if picked is None:
        return False, "reconcile: cannot find amount/value column to match previous total", {
            "required": True,
            "ok": False,
            "expected_total": prev_scalar["value"],
            "reason": "no_amount_column",
        }
    col, got = picked
    expected = float(prev_scalar["value"])
    tolerance = max(1.0, abs(expected) * 0.01)
    diff = abs(got - expected)
    meta = {
        "required": True,
        "ok": diff <= tolerance,
        "column": col,
        "detail_sum": got,
        "expected_total": expected,
        "difference": diff,
        "tolerance": tolerance,
    }
    if diff > tolerance:
        detail = (
            f"reconcile mismatch: SUM({col})={got:.6f} differs from previous total {expected:.6f} "
            f"(diff={diff:.6f}, tolerance={tolerance:.6f})."
        )
        return False, detail, meta
    return True, None, meta


def merge_scope_reconcile_meta(
    scope: dict[str, Any] | None,
    reconcile_meta: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(scope, dict):
        return scope
    if not isinstance(reconcile_meta, dict):
        return scope
    out = deepcopy(scope)
    follow = out.get("followup") if isinstance(out.get("followup"), dict) else {}
    follow["detail_reconcile_required"] = bool(reconcile_meta.get("required"))
    follow["detail_reconcile_ok"] = bool(reconcile_meta.get("ok"))
    follow["detail_reconcile_meta"] = reconcile_meta
    out["followup"] = follow
    return out


def is_followup_detail_reconciled(scope: dict[str, Any] | None) -> bool:
    if not _detail_breakdown_wanted(scope):
        return True
    follow = scope.get("followup") if isinstance(scope.get("followup"), dict) else {}
    return bool(follow.get("detail_reconcile_ok"))


def ledger_metric_id_from_scope(scope: dict[str, Any] | None) -> str | None:
    if not isinstance(scope, dict):
        return None
    metric = str(scope.get("metric") or "")
    if metric == "cash_in":
        return "ledger_revenue"
    if metric == "expense":
        return "ledger_expense"
    return None


def scalar_label_from_scope(scope: dict[str, Any] | None) -> str | None:
    if not isinstance(scope, dict):
        return None
    metric = str(scope.get("metric") or "")
    status_scope = scope.get("status_scope") if isinstance(scope.get("status_scope"), dict) else {}
    mode = str(status_scope.get("mode") or "")
    if metric == "cash_in" and mode == "completed_only":
        return "tổng tiền thu đã hoàn thành"
    if metric == "cash_in":
        return "tổng tiền thu"
    if metric == "expense":
        return "tổng chi phí"
    if metric == "inventory_value":
        return "tổng giá trị tồn kho"
    return None


def is_raw_sql_alias(key: str) -> bool:
    return _norm(key).replace(" ", "_") in _RAW_ALIAS_KEYS


def check_sql_against_scope(sql: str | None, scope: dict[str, Any] | None) -> tuple[bool, str | None]:
    if not isinstance(scope, dict):
        return True, None
    s = _norm(sql or "")
    metric = str(scope.get("metric") or "")
    status_scope = scope.get("status_scope") if isinstance(scope.get("status_scope"), dict) else {}
    status_mode = str(status_scope.get("mode") or "")
    if metric == "cash_in" and "financeledger" in s:
        if "salesrevenue" not in s:
            return False, "policy: cash_in on financeledger should filter transaction_type = 'SalesRevenue'"
    if status_mode == "completed_only":
        if "cashtransactions" in s and "completed" not in s:
            return False, "policy: completed_only cashtransactions query must filter status = 'Completed'"
        if any(x in s for x in ("cancelled", "pending", "draft")) and "status" in s:
            return False, "policy: completed_only scope cannot include Pending/Cancelled/Draft rows"
    return True, None
