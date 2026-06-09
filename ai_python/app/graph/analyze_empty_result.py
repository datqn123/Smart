"""Heuristic analysis for empty SQL results — distinguishes legitimate no-data from wrong SQL."""

from __future__ import annotations

import json
import logging
import re
from datetime import date
from typing import Any

from app.graph.deps import GraphDeps
from app.graph.state import AgentState

logger = logging.getLogger(__name__)

_NAME_COLUMNS = frozenset({
    "name", "category_name", "supplier_name", "customer_name",
    "display_name", "full_name", "product_name", "warehouse_name",
})


def _detect_year_mismatch(sql: str, user_q: str) -> str | None:
    """Check if years in SQL date filters differ from years in user question.

    Returns a warning string or None.
    """
    sql_years = set(re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", sql))
    user_years = set(re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", user_q))

    if not sql_years or not user_years:
        return None

    if not sql_years & user_years:
        return (
            f"Năm trong câu SQL ({', '.join(sorted(sql_years))}) "
            f"không khớp với năm bạn hỏi ({', '.join(sorted(user_years))}). "
            "Có thể câu SQL đang lọc sai năm."
        )

    return None


def _detect_exact_name_match(sql: str) -> str | None:
    """Detect WHERE name = '...' instead of WHERE name ILIKE '...'.

    Returns a warning string or None.
    """
    pattern = (
        r"\bWHERE\s+.*?\b("
        + "|".join(re.escape(col) for col in _NAME_COLUMNS)
        + r")\s*=\s*'([^']+)'"
    )
    m = re.search(pattern, sql, re.IGNORECASE)
    if m:
        col = m.group(1)
        val = m.group(2)
        return (
            f"Cột '{col}' đang dùng dấu '=' với giá trị '{val}' "
            f"thay vì 'ILIKE'. Có thể không tìm thấy dữ liệu do sai kiểu chữ hoa/thường."
        )
    return None


def _detect_future_dates(sql: str) -> str | None:
    """Detect date filters that reference future dates.

    Returns a warning string or None.
    """
    today = date.today()
    dates = re.findall(r"(\d{4})-(\d{2})-(\d{2})", sql)
    for yr_str, mo_str, dy_str in dates:
        try:
            d = date(int(yr_str), int(mo_str), int(dy_str))
            if d > today:
                return f"Câu SQL lọc dữ liệu từ ngày {d.isoformat()} (trong tương lai) — kết quả rỗng là hợp lệ."
        except ValueError:
            continue
    return None


_DOMAIN_FACT_TABLES: dict[str, str] = {
    "inventory": "inventory",
    "receipt": "stockreceipts",
    "dispatch": "stockdispatches",
    "ledger": "financeledger",
    "catalog_price": "products",
}


def _detect_fact_table(sql: str) -> str | None:
    m = re.search(r'\b(?:FROM|JOIN)\s+(\w+)', sql, re.IGNORECASE)
    return m.group(1).lower() if m else None


def _analyze_empty_heuristic(sql: str, user_q: str, domain: str) -> dict[str, Any]:
    """Run heuristic checks on an empty SQL result.

    Returns dict with keys: verdict, reason, warning.
    """
    warnings: list[str] = []

    yr_warn = _detect_year_mismatch(sql, user_q)
    if yr_warn:
        warnings.append(yr_warn)

    name_warn = _detect_exact_name_match(sql)
    if name_warn:
        warnings.append(name_warn)

    # Domain fact-table check
    expected_fact = _DOMAIN_FACT_TABLES.get(domain)
    if expected_fact:
        actual_fact = _detect_fact_table(sql)
        if actual_fact and actual_fact != expected_fact:
            warnings.append(
                f"Miền '{domain}' yêu cầu bảng fact '{expected_fact}' "
                f"nhưng SQL dùng '{actual_fact}'. Có thể sai bảng chính."
            )

    future_warn = _detect_future_dates(sql)
    if future_warn:
        return {
            "verdict": "legitimate",
            "reason": future_warn,
            "warning": future_warn,
        }

    if warnings:
        return {
            "verdict": "suspicious",
            "reason": "; ".join(warnings),
            "warning": "; ".join(warnings),
        }

    return {
        "verdict": "legitimate",
        "reason": "No suspicious patterns detected in empty result.",
        "warning": "",
    }


_ANALYSIS_ENABLED = True


def _load_agent_prompt(name: str) -> str:
    import os
    prompt_path = os.path.join(
        os.path.dirname(__file__), "..", "prompts", "agents", f"{name}.md"
    )
    try:
        with open(prompt_path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("Prompt file not found: %s", prompt_path)
        return ""


def _build_llm_analyze_prompt(sql: str, domain: str, user_q: str) -> str:
    return (
        f"User question: {user_q}\n"
        f"Domain: {domain}\n"
        f"SQL (returned 0 rows): {sql}\n\n"
        "Analyze this empty result. Return JSON with keys: verdict, confidence, reason, warning, suggested_fix"
    )


def _last_user_question(state: dict[str, Any]) -> str:
    """Extract the last human message from state."""
    from langchain_core.messages import HumanMessage
    msgs = state.get("messages", [])
    if isinstance(msgs, list):
        for m in reversed(msgs):
            if isinstance(m, HumanMessage):
                content = m.content
                return content if isinstance(content, str) else ""
    return str(state.get("intent") or "")


def make_analyze_empty_result_node(deps: GraphDeps):
    def analyze_empty_result(state: AgentState) -> dict[str, Any]:
        logger.info("node=analyze_empty_result action=start")

        sql = str(state.get("generated_sql") or "")
        qr = state.get("query_result")
        domain = str(state.get("sql_query_domain") or "generic")

        if not sql or qr is None:
            return {
                "empty_verdict": "legitimate",
                "empty_reason": "No SQL or query result to analyze",
                "empty_warning": "",
            }

        rows = qr.get("rows") if isinstance(qr, dict) else None
        if rows is not None and len(rows) > 0:
            return {
                "empty_verdict": "legitimate",
                "empty_reason": "Result has rows, no analysis needed",
                "empty_warning": "",
            }

        # Run heuristic analysis
        user_q = _last_user_question(state)
        result = _analyze_empty_heuristic(sql, user_q, domain)

        # Try LLM analysis if available
        reg = getattr(deps, "llm_registry", None)
        if reg is not None and _ANALYSIS_ENABLED:
            client = None
            try:
                client = reg.get("default")
            except KeyError:
                client = None
            if client is not None:
                prompt = _build_llm_analyze_prompt(sql, domain, user_q)
                system = _load_agent_prompt("analyze_empty_result")
                if system:
                    try:
                        raw = client.invoke_text(prompt, system=system)
                        parsed = json.loads(raw)
                        if parsed.get("confidence") == "high":
                            result = parsed
                    except Exception as exc:
                        logger.warning("analyze_empty_result LLM failed: %s", exc)

        return {
            "empty_verdict": result.get("verdict", "legitimate"),
            "empty_reason": result.get("reason", ""),
            "empty_warning": result.get("warning", ""),
        }

    return analyze_empty_result
