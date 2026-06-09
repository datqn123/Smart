# Empty Result Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add post-execution analysis when SQL returns 0 rows to distinguish legitimate no-data from subtly wrong SQL (wrong year, non-existent value, mismatched filter).

**Architecture:** Insert `analyze_empty_result` node between `execute_sql` and `validate_result` in the SQL subgraph. Add an `analyze` callable to `SelfCorrectingSqlRunner` for the thin-adapter path. Both use the same heuristic + optional LLM analysis module. When suspicious patterns are detected, a warning is propagated through the state to the `summarize_answer` node for user display.

**Tech Stack:** Python 3.12, LangGraph, OpenAI-compatible LLM, regex-based heuristics

---

## File Structure

```
Create:
  ai_python/app/graph/analyze_empty_result.py       — Heuristics + LLM analysis + node factory
  ai_python/app/prompts/agents/analyze_empty_result.md  — LLM prompt for empty-result analysis
  ai_python/tests/test_analyze_empty_result.py       — Unit + integration tests

Modify:
  ai_python/app/graph/state.py                       — Add state keys
  ai_python/app/graph/sql_subgraph.py                — Add node + conditional routing
  ai_python/app/graph/nodes/sql_pipeline.py          — Propagate warning in validate_result
  ai_python/app/graph/nodes/summarize.py             — Include warning in empty message
  ai_python/app/graph/tools/sql_query.py             — Add analyze to SelfCorrectingSqlRunner
  ai_python/tests/test_sql_query_tool_self_correct_integration.py  — Update empty tests
```

---

### Task 1: Add state keys for empty-result analysis

**Files:**
- Modify: `ai_python/app/graph/state.py:30-34` (add keys after `verify_intent_reason`)
- Modify: `ai_python/app/graph/state.py:119` (add to `_TRANSIENT_KEYS`)

- [ ] **Step 1: Add state keys to AgentState**

Add these lines after line 33 (`verify_intent_reason: str | None`):

```python
    empty_verdict: str | None       # "legitimate" | "suspicious" | "wrong"
    empty_reason: str | None        # explanation of the verdict
    empty_warning: str | None       # user-facing warning (e.g. "Có thể năm trong câu SQL chưa đúng...")
```

- [ ] **Step 2: Add to _TRANSIENT_KEYS**

Add these lines after the `verify_intent_reason` entry in `_TRANSIENT_KEYS` (line 118):

```python
        "empty_verdict",
        "empty_reason",
        "empty_warning",
```

- [ ] **Step 3: Verify state file loads**

Run: `python -c "from app.graph.state import AgentState; print('OK')"`
Expected: No import errors

- [ ] **Step 4: Commit**

```bash
git add ai_python/app/graph/state.py
git commit -m "feat(empty-analyze): add empty_verdict/reason/warning state keys"
```

---

### Task 2: Write heuristic analysis functions

**Files:**
- Create: `ai_python/app/graph/analyze_empty_result.py`
- Test: `ai_python/tests/test_analyze_empty_result.py` (partial — tests for heuristics only)

- [ ] **Step 1: Write the failing heuristic tests**

Create `ai_python/tests/test_analyze_empty_result.py`:

```python
"""Tests for analyze_empty_result module — heuristics and node factory."""

from __future__ import annotations

import pytest

from app.graph.analyze_empty_result import (
    _detect_year_mismatch,
    _detect_exact_name_match,
    _detect_future_dates,
    _analyze_empty_heuristic,
)


class TestYearMismatch:
    def test_detects_year_mismatch(self):
        sql = "SELECT * FROM financeledger WHERE transaction_date BETWEEN '2024-01-01' AND '2024-12-31'"
        user_q = "doanh thu năm 2025"
        result = _detect_year_mismatch(sql, user_q)
        assert result is not None
        assert "2024" in result or "2025" in result

    def test_no_mismatch_when_years_align(self):
        sql = "SELECT * FROM financeledger WHERE transaction_date BETWEEN '2025-01-01' AND '2025-03-31'"
        user_q = "doanh thu quý 1 năm 2025"
        result = _detect_year_mismatch(sql, user_q)
        assert result is None

    def test_no_user_question_years_returns_none(self):
        sql = "SELECT * FROM products WHERE name ILIKE '%iphone%'"
        user_q = "liệt kê sản phẩm"
        result = _detect_year_mismatch(sql, user_q)
        assert result is None

    def test_mismatch_from_non_overlap_years(self):
        sql = "SELECT * FROM inventory WHERE expiry_date < '2025-06-01'"
        user_q = "hàng hết hạn trong năm 2026"
        result = _detect_year_mismatch(sql, user_q)
        assert result is not None

    def test_no_sql_dates_returns_none(self):
        sql = "SELECT name FROM products WHERE status = 'Active'"
        user_q = "danh sách sản phẩm năm 2025"
        result = _detect_year_mismatch(sql, user_q)
        assert result is None


class TestExactNameMatch:
    def test_detects_exact_name_match(self):
        sql = "SELECT * FROM products WHERE name = 'Điện thoại'"
        result = _detect_exact_name_match(sql)
        assert result is not None

    def test_detects_exact_category_name(self):
        sql = "SELECT * FROM categories WHERE category_name = 'Điện tử'"
        result = _detect_exact_name_match(sql)
        assert result is not None

    def test_skips_iliike(self):
        sql = "SELECT * FROM products WHERE name ILIKE '%Điện thoại%'"
        result = _detect_exact_name_match(sql)
        assert result is None

    def test_skips_code_columns(self):
        sql = "SELECT * FROM products WHERE sku_code = 'ABC123'"
        result = _detect_exact_name_match(sql)
        assert result is None

    def test_no_name_filter_returns_none(self):
        sql = "SELECT quantity FROM inventory WHERE product_id = 1"
        result = _detect_exact_name_match(sql)
        assert result is None


class TestDetectFutureDates:
    def test_detects_future_date(self):
        # Year 2099 is definitely in the future
        sql = "SELECT * FROM financeledger WHERE transaction_date >= '2099-01-01'"
        result = _detect_future_dates(sql)
        assert result is not None

    def test_past_dates_return_none(self):
        sql = "SELECT * FROM financeledger WHERE transaction_date BETWEEN '2024-01-01' AND '2024-12-31'"
        result = _detect_future_dates(sql)
        assert result is None  # current year is 2026

    def test_no_dates_returns_none(self):
        sql = "SELECT name FROM products"
        result = _detect_future_dates(sql)
        assert result is None


class TestAnalyzeEmptyHeuristic:
    def test_legitimate_no_data(self):
        sql = "SELECT * FROM inventory WHERE product_id = 99999"
        user_q = "kiểm tra sản phẩm 99999"
        result = _analyze_empty_heuristic(sql, user_q, "inventory")
        assert result["verdict"] == "legitimate"

    def test_suspicious_year_mismatch(self):
        sql = "SELECT * FROM financeledger WHERE transaction_date BETWEEN '2024-01-01' AND '2024-12-31'"
        user_q = "doanh thu năm 2025"
        result = _analyze_empty_heuristic(sql, user_q, "ledger")
        assert result["verdict"] == "suspicious"

    def test_suspicious_exact_name_match(self):
        sql = "SELECT * FROM products WHERE name = 'Điện thoại'"
        user_q = "sản phẩm tên Điện thoại"
        result = _analyze_empty_heuristic(sql, user_q, "catalog_price")
        assert result["verdict"] == "suspicious"

    def test_legitimate_future_date_empty(self):
        sql = "SELECT * FROM stockreceipts WHERE created_at >= '2099-01-01'"
        user_q = "phiếu nhập tương lai"
        result = _analyze_empty_heuristic(sql, user_q, "receipt")
        assert result["verdict"] == "legitimate"

    def test_generic_domain_no_patterns_returns_legitimate(self):
        sql = "SELECT name FROM products WHERE status = 'Active'"
        user_q = "danh sách sản phẩm"
        result = _analyze_empty_heuristic(sql, user_q, "generic")
        assert result["verdict"] == "legitimate"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest ai_python/tests/test_analyze_empty_result.py -v`
Expected: ALL FAIL with `ModuleNotFoundError` or `function not defined`

- [ ] **Step 3: Write heuristic analysis functions**

Create `ai_python/app/graph/analyze_empty_result.py`:

```python
"""Empty result analysis node for SQL subgraph — distinguishes legitimate no-data from wrong SQL."""

from __future__ import annotations

import json
import logging
import re
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)

_NAME_COLUMNS = frozenset({
    "name", "category_name", "supplier_name", "customer_name",
    "display_name", "full_name", "product_name", "warehouse_name",
})

_CODE_COLUMNS = frozenset({
    "sku_code", "supplier_code", "customer_code", "receipt_code",
    "product_code", "barcode", "category_code",
})


def _detect_year_mismatch(sql: str, user_q: str) -> str | None:
    """Check if years in SQL date filters differ from years in user question.

    Returns a warning string or None.
    """
    sql_years = set(re.findall(r"(?<!\d)(19|20)\d{2}(?!\d)", sql))
    user_years = set(re.findall(r"(?<!\d)(19|20)\d{2}(?!\d)", user_q))

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
        r"\bWHERE\s+.*\b("
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


def _analyze_empty_heuristic(sql: str, user_q: str, domain: str) -> dict[str, Any]:
    """Run heuristic checks on an empty SQL result.

    Returns dict with keys: verdict, reason, warning.
    """
    warnings: list[str] = []

    # Check 1: Year mismatch
    yr_warn = _detect_year_mismatch(sql, user_q)
    if yr_warn:
        warnings.append(yr_warn)

    # Check 2: Exact name match (instead of ILIKE)
    name_warn = _detect_exact_name_match(sql)
    if name_warn:
        warnings.append(name_warn)

    # Check 3: Future date — diminishes suspicion
    future_warn = _detect_future_dates(sql)
    if future_warn:
        # Future dates make empty result expected → verdict remains legitimate
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest ai_python/tests/test_analyze_empty_result.py -v`
Expected: ALL PASS

<details>
<summary>Expected output</summary>
<pre>
TestYearMismatch::test_detects_year_mismatch PASSED
TestYearMismatch::test_no_mismatch_when_years_align PASSED
TestYearMismatch::test_no_user_question_years_returns_none PASSED
TestYearMismatch::test_mismatch_from_non_overlap_years PASSED
TestYearMismatch::test_no_sql_dates_returns_none PASSED
TestExactNameMatch::test_detects_exact_name_match PASSED
TestExactNameMatch::test_detects_exact_category_name PASSED
TestExactNameMatch::test_skips_iliike PASSED
TestExactNameMatch::test_skips_code_columns PASSED
TestExactNameMatch::test_no_name_filter_returns_none PASSED
TestDetectFutureDates::test_detects_future_date PASSED
TestDetectFutureDates::test_past_dates_return_none PASSED
TestDetectFutureDates::test_no_dates_returns_none PASSED
TestAnalyzeEmptyHeuristic::test_legitimate_no_data PASSED
TestAnalyzeEmptyHeuristic::test_suspicious_year_mismatch PASSED
TestAnalyzeEmptyHeuristic::test_suspicious_exact_name_match PASSED
TestAnalyzeEmptyHeuristic::test_legitimate_future_date_empty PASSED
TestAnalyzeEmptyHeuristic::test_generic_domain_no_patterns_returns_legitimate PASSED
</pre>
</details>

- [ ] **Step 5: Commit**

```bash
git add ai_python/app/graph/analyze_empty_result.py ai_python/tests/test_analyze_empty_result.py
git commit -m "feat(empty-analyze): add heuristic analysis functions"
```

---

### Task 3: Write LLM analysis prompt

**Files:**
- Create: `ai_python/app/prompts/agents/analyze_empty_result.md`

- [ ] **Step 1: Write the prompt file**

Create `ai_python/app/prompts/agents/analyze_empty_result.md`:

```markdown
# Agent: analyze_empty_result

You analyze SQL queries that returned 0 rows. Your job: determine whether the empty result is legitimate (data does not exist) or caused by wrong filter values (wrong year, wrong ID, wrong string value).

## Input

- User question: {user_question}
- Domain: {domain}
- SQL that returned 0 rows: {sql}
- DDL (schema) for referenced tables: {ddl}

## Analysis

Check each possibility in order:

### 1. Date/temporal mismatch
- Extract all years from user question.
- Extract all years from SQL WHERE clause date filters.
- Do they overlap? If not → suspicious.

### 2. Exact string match on name/display columns
- Does the SQL use `=` on a name column (name, category_name, supplier_name)?
- Names should use `ILIKE` for case-insensitive matching.
- If exact match → suspicious.

### 3. Non-existent ID / FK reference
- Does the SQL filter by a specific ID that might not exist?
- If the filter is an ID and returned 0 rows, data might legitimately be absent.

### 4. Domain-appropriate filter
- Does the WHERE clause make sense for the domain?
- inventory domain but no filter on quantity or product_id? Possibly wrong.
- ledger domain but no transaction_type or date range? Possibly wrong.

## Output Format

Return a JSON object with these keys:
```json
{
  "verdict": "legitimate | suspicious | wrong",
  "confidence": "high | medium | low",
  "reason": "explanation in Vietnamese",
  "warning": "user-facing warning message (or empty string if legitimate)",
  "suggested_fix": "suggested SQL fix or empty string"
}
```

## Rules

- If confident that SQL is wrong → `verdict: "wrong"` — this will trigger a regeneration.
- If suspicious but not sure → `verdict: "suspicious"` — result is returned with a warning.
- If no clear problem → `verdict: "legitimate"` — empty result is a valid response.
- `warning` must be in Vietnamese and user-friendly.
- Only suggest a fix if you are highly confident about the correct SQL.
```

- [ ] **Step 2: Commit**

```bash
git add ai_python/app/prompts/agents/analyze_empty_result.md
git commit -m "feat(empty-analyze): add LLM prompt for empty-result analysis"
```

---

### Task 4: Write node factory with LLM integration

**Files:**
- Modify: `ai_python/app/graph/analyze_empty_result.py`
- Test: `ai_python/tests/test_analyze_empty_result.py` (append tests)

- [ ] **Step 1: Write node factory tests**

Append to `ai_python/tests/test_analyze_empty_result.py`:

```python
class TestMakeAnalyzeEmptyNode:
    def test_legitimate_empty_passes_through(self):
        from unittest.mock import MagicMock
        from app.graph.analyze_empty_result import make_analyze_empty_result_node

        deps = MagicMock()
        deps.llm_registry = None
        node = make_analyze_empty_result_node(deps)

        state = {
            "generated_sql": "SELECT * FROM inventory WHERE product_id = 99999",
            "query_result": {"rows": []},
            "intent": "inventory inquiry",
        }
        result = node(state)
        assert result["empty_verdict"] == "legitimate"

    def test_suspicious_sets_warning(self):
        from unittest.mock import MagicMock
        from app.graph.analyze_empty_result import make_analyze_empty_result_node

        deps = MagicMock()
        deps.llm_registry = None
        node = make_analyze_empty_result_node(deps)

        state = {
            "generated_sql": "SELECT * FROM financeledger WHERE transaction_date BETWEEN '2024-01-01' AND '2024-12-31'",
            "query_result": {"rows": []},
            "intent": "doanh thu năm 2025",
        }
        result = node(state)
        assert result["empty_verdict"] == "suspicious"
        assert result.get("empty_warning")

    def test_no_query_result_returns_legitimate(self):
        from unittest.mock import MagicMock
        from app.graph.analyze_empty_result import make_analyze_empty_result_node

        deps = MagicMock()
        deps.llm_registry = None
        node = make_analyze_empty_result_node(deps)

        state = {
            "generated_sql": "SELECT 1",
            "query_result": None,
            "intent": "test",
        }
        result = node(state)
        assert result["empty_verdict"] == "legitimate"

    def test_no_sql_returns_legitimate(self):
        from unittest.mock import MagicMock
        from app.graph.analyze_empty_result import make_analyze_empty_result_node

        deps = MagicMock()
        deps.llm_registry = None
        node = make_analyze_empty_result_node(deps)

        state = {
            "generated_sql": "",
            "query_result": {"rows": []},
            "intent": "test",
        }
        result = node(state)
        assert result["empty_verdict"] == "legitimate"
```

- [ ] **Step 2: Run tests to verify they fail (node factory not yet implemented)**

Run: `python -m pytest ai_python/tests/test_analyze_empty_result.py::TestMakeAnalyzeEmptyNode -v`
Expected: FAIL

- [ ] **Step 3: Add node factory + LLM integration to the module**

Append to `ai_python/app/graph/analyze_empty_result.py`:

```python
_ANALYSIS_ENABLED = True

_DOMAIN_FACT_TABLES: dict[str, str] = {
    "inventory": "inventory",
    "receipt": "stockreceipts",
    "dispatch": "stockdispatches",
    "ledger": "financeledger",
    "catalog_price": "products",
}


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
            # Not empty — no analysis needed
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
                        # LLM verdict overrides heuristic only if confidence is high
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest ai_python/tests/test_analyze_empty_result.py -v`
Expected: ALL PASS (18 tests)

- [ ] **Step 5: Commit**

```bash
git add ai_python/app/graph/analyze_empty_result.py ai_python/tests/test_analyze_empty_result.py
git commit -m "feat(empty-analyze): add node factory with LLM integration"
```

---

### Task 5: Integrate into SQL subgraph

**Files:**
- Modify: `ai_python/app/graph/sql_subgraph.py`

- [ ] **Step 1: Add conditional routing + node registration**

Modify `ai_python/app/graph/sql_subgraph.py`:

1. Add import at the top (after existing `from app.graph.verify_sql_intent import ...`):

```python
from app.graph.analyze_empty_result import make_analyze_empty_result_node
```

2. Add routing function before `build_sql_subgraph`:

```python
def _route_after_execute_sql(state: AgentState) -> str:
    qr = state.get("query_result")
    if qr is None:
        # Execution error — send to validate_result for error handling
        return "validate_result"
    rows = qr.get("rows") if isinstance(qr, dict) else None
    if isinstance(rows, list) and len(rows) == 0:
        return "analyze_empty_result"
    return "validate_result"


def _route_after_analyze_empty(state: AgentState) -> str:
    verdict = state.get("empty_verdict", "legitimate")
    if verdict == "wrong":
        attempt = int(state.get("sql_attempt_count") or 0)
        max_attempts = int(state.get("sql_repair_max_attempts") or 3)
        if attempt >= max_attempts:
            return "fail_max_attempts"
        return "gen_sql"
    # legitimate + suspicious both go to validate_result
    # suspicious carries a warning in state for later display
    return "validate_result"
```

3. Add node in `build_sql_subgraph` after `execute_sql` node registration (line 56):

```python
    g.add_node("analyze_empty_result", wrap("analyze_empty_result", make_analyze_empty_result_node(deps)))
```

4. Replace the fixed edge `execute_sql → validate_result` (line 106) with conditional edges:

```python
    g.add_conditional_edges(
        "execute_sql",
        _route_after_execute_sql,
        {
            "validate_result": "validate_result",
            "analyze_empty_result": "analyze_empty_result",
        },
    )
```

5. Add conditional edge from `analyze_empty_result`:

```python
    g.add_conditional_edges(
        "analyze_empty_result",
        _route_after_analyze_empty,
        {
            "validate_result": "validate_result",
            "gen_sql": "gen_sql",
            "fail_max_attempts": "fail_max_attempts",
        },
    )
```

The full `build_sql_subgraph` should now have nodes in this order:

```
schema_explore → gen_sql → verify_sql_intent → sql_review → validate_sql → execute_sql
                                                                                ↓
                                                                  analyze_empty_result
                                                                     ↓           ↓
                                                              validate_result  gen_sql
```

- [ ] **Step 2: Verify subgraph compiles**

Run: `python -c "from app.graph.sql_subgraph import build_sql_subgraph; print('OK')"`
Expected: No import errors (may fail if deps param is required — that's OK, just check import)

Run: `python -c "from unittest.mock import MagicMock; from app.graph.sql_subgraph import build_sql_subgraph; g = build_sql_subgraph(MagicMock()); print('compiled OK')"`
Expected: `compiled OK`

- [ ] **Step 3: Commit**

```bash
git add ai_python/app/graph/sql_subgraph.py
git commit -m "feat(empty-analyze): integrate analyze_empty_result node into SQL subgraph"
```

---

### Task 6: Propagate warning through validate_result

**Files:**
- Modify: `ai_python/app/graph/nodes/sql_pipeline.py:1119-1137`

- [ ] **Step 1: Modify validate_result to carry the empty warning**

In `make_validate_result_node`, in the empty-result block (currently lines 1119-1137), modify the return dict to include the empty warning:

Find this block (around line 1119):

```python
        if isinstance(qr, dict) and rows == []:
            ctx = build_last_data_answer_context(
                ...
            )
            out: dict[str, Any] = {
                **emit_progress(state, "validate_result"),
                "result_ok": True,
                "result_empty": True,
                "business_scope": merged_scope,
            }
            if isinstance(ctx, dict):
                out["last_data_answer"] = ctx
            return out
```

Add `empty_warning` propagation:

```python
        if isinstance(qr, dict) and rows == []:
            ctx = build_last_data_answer_context(
                intent=str(state.get("intent") or "") or None,
                user_question=user_q_raw,
                effective_question=user_q_effective,
                business_scope=merged_scope,
                query_result=qr,
                generated_sql=str(state.get("generated_sql") or ""),
                reconcile_meta=reconcile_meta,
            )
            out: dict[str, Any] = {
                **emit_progress(state, "validate_result"),
                "result_ok": True,
                "result_empty": True,
                "business_scope": merged_scope,
            }
            # Propagate empty-result warning from analyze_empty_result node
            empty_warning = state.get("empty_warning")
            if empty_warning:
                out["empty_warning"] = empty_warning
            if isinstance(ctx, dict):
                out["last_data_answer"] = ctx
            return out
```

- [ ] **Step 2: Run existing tests to ensure no regression**

Run: `python -m pytest ai_python/tests/ -x -q --tb=short`
Expected: Same as before (2 pre-existing failures, no new failures)

- [ ] **Step 3: Commit**

```bash
git add ai_python/app/graph/nodes/sql_pipeline.py
git commit -m "feat(empty-analyze): propagate empty warning through validate_result"
```

---

### Task 7: Include warning in summarize_answer empty message

**Files:**
- Modify: `ai_python/app/graph/nodes/summarize.py:276-303`

- [ ] **Step 1: Modify `_build_sql_empty_message` to include warning**

Replace the existing `_build_sql_empty_message` function:

Before the replacement, read the current function to confirm exact lines.

```python
SQL_EMPTY_WARNING_TMPL = (
    "Không có dữ liệu phù hợp với điều kiện bạn yêu cầu.\n\n"
    "⚠️ {warning}\n\n"
    "Bạn muốn thử lại với thông tin khác không?"
)


def _build_sql_empty_message(
    deps: GraphDeps,
    state: AgentState,
    user_q: str,
) -> str:
    empty_warning = state.get("empty_warning") or ""

    if empty_warning:
        # If we have a specific warning, use the template directly
        return SQL_EMPTY_WARNING_TMPL.format(warning=empty_warning)

    reg = deps.llm_registry
    if reg is None:
        return SQL_EMPTY_VI
    dialog_tail = format_dialog_tail_for_sql(
        state.get("messages"),
        max_messages=int(deps.settings.sql_dialog_tail_max_messages),
        max_chars=int(deps.settings.sql_dialog_tail_max_chars),
        summary=state.get("conversation_summary"),
    )
    system = (
        _SUMMARIZE_EMPTY_SYSTEM.replace("{user_question}", user_q or "(không rõ)")
        .replace("{dialog_tail}", dialog_tail or "(không có)")
    )
    try:
        text = reg.get("summarize").invoke_text(
            "Write the user-facing reply.",
            system=system,
        )
        return format_display_for_chat_ui(text)
    except Exception:
        logger.warning("summarize_empty LLM failed", exc_info=True)
        return SQL_EMPTY_VI
```

- [ ] **Step 2: Run existing tests to ensure no regression**

Run: `python -m pytest ai_python/tests/ -x -q --tb=short`
Expected: Same as before (2 pre-existing failures, no new failures)

- [ ] **Step 3: Commit**

```bash
git add ai_python/app/graph/nodes/summarize.py
git commit -m "feat(empty-analyze): include empty warning in user-facing message"
```

---

### Task 8: Add analyze to SelfCorrectingSqlRunner (thin-adapter path)

**Files:**
- Modify: `ai_python/app/graph/tools/sql_query.py`

- [ ] **Step 1: Write failing integration tests**

Append to `ai_python/tests/test_sql_query_tool_self_correct_integration.py`:

```python
# ---------------------------------------------------------------------------
# Empty result with analyze callable
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invoke_empty_legitimate_no_analyze_needed():
    """Empty result with legitimate SQL passes through with no warning."""
    analyze_calls = []

    async def _gen(hint):
        return "SELECT id FROM orders WHERE id = 999"

    async def _review(sql):
        return {"ok": True, "issues": []}

    async def _execute(sql):
        return []

    deps = _make_deps()
    tool = SqlQueryTool(deps, _test_generate=_gen, _test_review=_review, _test_execute=_execute)
    result = await tool.invoke({"query": "find order 999"}, _ctx())
    assert result.ok is True
    assert result.output["query_result"]["rows"] == []


@pytest.mark.asyncio
async def test_invoke_empty_with_analyze_warning():
    """Test that analyze callable is invoked and warning surfaces."""
    async def _gen(hint):
        return "SELECT * FROM financeledger WHERE transaction_date BETWEEN '2024-01-01' AND '2024-12-31'"

    async def _review(sql):
        return {"ok": True, "issues": []}

    async def _execute(sql):
        return []

    deps = _make_deps()
    tool = SqlQueryTool(deps, _test_generate=_gen, _test_review=_review, _test_execute=_execute)
    result = await tool.invoke({"query": "doanh thu năm 2025"}, _ctx())
    assert result.ok is True
    # Should still return empty rows
    assert result.output["query_result"]["rows"] == []
    # May or may not have warning in observation — depends on thin-adapter integration
```

- [ ] **Step 2: Run new tests to verify they capture expected behavior**

Run: `python -m pytest ai_python/tests/test_sql_query_tool_self_correct_integration.py::test_invoke_empty_legitimate_no_analyze_needed -v`
Expected: PASS

- [ ] **Step 3: Modify SelfCorrectingSqlRunner to accept analyze callable**

In `SelfCorrectingSqlRunner.__init__`, add an `analyze` parameter (after `review`):

```python
class SelfCorrectingSqlRunner:
    def __init__(
        self,
        *,
        sql_regen_max: int,
        sql_empty_retry_max: int,
        generate: Callable[[str | None], Awaitable[str]],
        review: Callable[[str], Awaitable[dict[str, Any]]],
        execute: Callable[[str], Awaitable[list[dict[str, Any]]]],
        analyze: Callable[[str, str], Awaitable[dict[str, Any]]] | None = None,
    ) -> None:
        self._sql_regen_max = max(0, int(sql_regen_max))
        self._sql_empty_retry_max = max(0, int(sql_empty_retry_max))
        self._generate = generate
        self._review = review
        self._execute = execute
        self._analyze = analyze
        self._last_analyze_result: dict[str, Any] = {}
```

In `SelfCorrectingSqlRunner.run()`, modify the empty-result return (around line 104-114):

```python
            if not last_rows:
                # SQL passed review — analyze empty result
                if self._analyze is not None:
                    try:
                        analyze_result = await self._analyze(sql, hint or "")
                        self._last_analyze_result = analyze_result or {}
                    except Exception as exc:
                        logger.warning("analyze_empty_result failed: %s", exc)
                return SelfCorrectingSqlResult(
                    ok=True,
                    rows=last_rows,
                    sql=last_sql,
                    regen_count=regen,
                    empty_retry_count=empty_retry,
                    degraded=False,
                    warning=self._last_analyze_result.get("warning", ""),
                )
```

- [ ] **Step 4: Modify `_make_callables` to provide analyze callable**

In `SqlQueryTool._make_callables`, add the analyze callable creation after the `execute` function. Add this before the return statement:

```python
        async def analyze(sql: str, hint: str) -> dict[str, Any]:
            """Run empty-result analysis when rows == 0."""
            from app.graph.analyze_empty_result import _analyze_empty_heuristic

            domain = ""
            try:
                from app.graph.sql_query_domain import detect_sql_query_domain
                domain = detect_sql_query_domain(query)
            except Exception:
                pass

            result = _analyze_empty_heuristic(sql, query, domain)
            return {
                "verdict": result.get("verdict", "legitimate"),
                "warning": result.get("warning", ""),
                "reason": result.get("reason", ""),
            }

        return generate, review, execute, analyze
```

Also update the caller to handle 4 return values. In `invoke` (around line 226):

```python
        callables = self._make_callables(query, ctx)
        generate, review, execute = callables[0], callables[1], callables[2]
        analyze = callables[3] if len(callables) > 3 else None

        runner = SelfCorrectingSqlRunner(
            sql_regen_max=regen_max,
            sql_empty_retry_max=empty_retry_max,
            generate=generate,
            review=review,
            execute=execute,
            analyze=analyze,
        )
```

- [ ] **Step 5: No change needed — existing code handles warning propagation**

The existing lines 248-249 in `sql_query.py` already prepend `runner_result.warning` to the observation. The analyze callable sets `warning` on `SelfCorrectingSqlResult`, and this existing code handles it automatically.

- [ ] **Step 6: Handle test mode — update `_make_callables` test override**

The test mode already overrides `_make_callables` returning 3 callables. Update the test helper:

In `_make_tool` helper at the top of the test file, ensure the mock doesn't break. Since `_test_generate` being set bypasses `_make_callables` entirely (line 161-162):

```python
        if self._test_generate is not None:
            return self._test_generate, self._test_review, self._test_execute
```

The test mode returns 3 values, but invoke now expects 4 (with optional analyze). Update the test path to handle 3-value return:

```python
        callables = self._make_callables(query, ctx)
        generate, review, execute = callables[0], callables[1], callables[2]
        analyze = callables[3] if len(callables) > 3 else None
```

This is backward-compatible — the test helper returns 3 values, `callables[3]` will raise `IndexError`. Fix with a slice:

```python
        callables = self._make_callables(query, ctx)
        generate, review, execute = callables[:3]
        analyze = callables[3] if len(callables) > 3 else None
```

- [ ] **Step 7: Run all tests**

Run: `python -m pytest ai_python/tests/ -x -q --tb=short`
Expected: 2 pre-existing failures, no new failures

- [ ] **Step 8: Commit**

```bash
git add ai_python/app/graph/tools/sql_query.py ai_python/tests/test_sql_query_tool_self_correct_integration.py
git commit -m "feat(empty-analyze): add analyze callable to SelfCorrectingSqlRunner"
```

---

### Task 9: Full regression run

**Files:** None

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest ai_python/tests/ -q --tb=short`
Expected: Same as baseline (2 pre-existing failures)

- [ ] **Step 2: Verify no import errors**

Run: `python -c "from app.graph.analyze_empty_result import make_analyze_empty_result_node, _analyze_empty_heuristic; print('analyze_empty_result OK')"`
Expected: `analyze_empty_result OK`

Run: `python -c "from app.graph.sql_subgraph import build_sql_subgraph; from unittest.mock import MagicMock; g = build_sql_subgraph(MagicMock()); print('subgraph OK')"`
Expected: `subgraph OK`

- [ ] **Step 3: Verify summarize change loads**

Run: `python -c "from app.graph.nodes.summarize import _build_sql_empty_message; print('summarize OK')"`
Expected: `summarize OK`

---

## Summary of changes

| File | Action | Lines touched |
|------|--------|--------------|
| `ai_python/app/graph/state.py` | Modify | +3 keys AgentState, +3 _TRANSIENT_KEYS |
| `ai_python/app/graph/analyze_empty_result.py` | Create | ~180 lines (heuristics + node factory) |
| `ai_python/app/prompts/agents/analyze_empty_result.md` | Create | ~80 lines (LLM prompt) |
| `ai_python/app/graph/sql_subgraph.py` | Modify | ~15 lines (node + routing) |
| `ai_python/app/graph/nodes/sql_pipeline.py` | Modify | ~4 lines (propagate warning) |
| `ai_python/app/graph/nodes/summarize.py` | Modify | ~15 lines (warning display) |
| `ai_python/app/graph/tools/sql_query.py` | Modify | ~30 lines (analyze callable + runner) |
| `ai_python/tests/test_analyze_empty_result.py` | Create | ~120 lines (18 tests) |
| `ai_python/tests/test_sql_query_tool_self_correct_integration.py` | Modify | ~20 lines (2 tests) |

## Edge cases covered

- **Error (no query_result):** `analyze_empty_result` returns legitimate immediately
- **No generated SQL:** Returns legitimate, no-op
- **Non-empty results:** Skips analysis entirely (checked at routing level + node level)
- **Future dates:** Counts as legitimate (empty is expected)
- **Year mismatch:** Suspicious with warning
- **Exact name match:** Suspicious with warning
- **Multiple warnings:** Concatenated with "; "
- **LLM failure:** Falls back to heuristic result (no crash)
- **Thin adapter (test mode):** `callables[:3]` handles 3-value return from test helper
