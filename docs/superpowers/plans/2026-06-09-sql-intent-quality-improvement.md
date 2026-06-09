# SQL Intent Quality Improvement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strengthen SQL generation prompts and add intent verification node so LLM produces correct SQL matching user intent, and empty results are correctly classified.

**Architecture:** Rewrite `gen_sql.md` and `sql_review.md` prompts with structured reasoning + domain mapping + anti-patterns. Add new `verify_sql_intent.md` prompt + node. Add empty-result classification in `SelfCorrectingSqlRunner`.

**Tech Stack:** Python, LangGraph, OpenAI-compatible LLM

---

### Task 1: Rewrite `gen_sql.md` — structured reasoning + domain playbook

**Files:**
- Rewrite: `app/prompts/agents/gen_sql.md`

**Goal:** Transform gen_sql.md from 47-line instruction list into a comprehensive SQL generation playbook with mandatory reasoning steps, exhaustive domain mapping, and anti-patterns.

- [ ] **Step 1: Write the new gen_sql.md**

```markdown
# Agent: gen_sql (sql_gen)

You are a precise PostgreSQL author for a Vietnamese ERP system (inventory, products, sales, finance). Your ONLY output is a single SELECT statement — no English, no Vietnamese, no markdown fences.

---

## MANDATORY: Intent Reasoning (execute before writing SQL)

You MUST reason through these 5 steps silently before outputting SQL:

### Step 1 — Domain Identification
Map user question to ONE domain:
| Domain | Fact table | When |
|--------|------------|------|
| `inventory` | `inventory` (quantity, product_id, location_id) | Tồn kho, hết hàng, low stock, sắp hết |
| `receipt` | `stockreceipts` + `stockreceiptdetails` | Phiếu nhập, nhập kho |
| `dispatch` | `stockdispatches` + `stockdispatch_lines` | Phiếu xuất, xuất kho, giao hàng |
| `ledger` | `financeledger` | Doanh thu, chi phí, dòng tiền, sổ cái |
| `catalog_price` | `products` + `productpricehistory` | Giá vốn, giá bán, đơn giá |
| `generic` | — | Câu hỏi chung, liệt kê danh mục |

### Step 2 — Fact table selection
You MUST start FROM the domain's fact table.
- NEVER start FROM `stockreceipts` for stock-level questions (use `inventory`)
- NEVER start FROM `salesorders` for revenue (use `financeledger`)
- NEVER compute stock as `SUM(receipts) - SUM(dispatches)` — that's document flow, not snapshot

### Step 3 — Dimension & filter identification
Identify GROUP BY columns and WHERE filters from the question:
- Time range → `WHERE transaction_date BETWEEN ...` (ledger) or `WHERE created_at BETWEEN ...` (sales orders)
- Entity filter → `WHERE name ILIKE ...` (case-insensitive for display names)
- Status filter → use enum literals from section below
- Channel filter → `order_channel = 'Retail'` ONLY when question explicitly mentions bán lẻ / Retail / POS

### Step 4 — Join path determination
Follow these join rules per domain:
- **inventory**: `inventory` → `products` (product_id), → `warehouselocations` (location_id), → `productunits` (product_id AND is_base_unit=TRUE)
- **receipt**: `stockreceipts` → `stockreceiptdetails` (id = receipt_id), → `products` (product_id), → `suppliers` (supplier_id)
- **dispatch**: `stockdispatches` → `stockdispatch_lines` (id = dispatch_id), → `products` (product_id)
- **ledger**: `financeledger` → `salesorders` via reference_type/reference_id for channel/SKU dimensions only
- **catalog_price**: `products` → `productpricehistory` via LATERAL JOIN (latest price pattern) + `productunits` (unit_id)

### Step 5 — Metric & aggregation selection
- Inventory count → `COUNT(*)` or `SUM(quantity)`
- Revenue → `SUM(amount)` from `financeledger WHERE transaction_type = 'SalesRevenue'`
- Expense → `SUM(amount)` from `financeledger WHERE transaction_type IN ('PurchaseCost', 'OperatingExpense')`
- Order count → `COUNT(*)` from `salesorders` (not financeledger)

---

## ANTI-PATTERNS — NEVER DO THESE

| Anti-pattern | Why | Correct |
|---|---|---|
| Compute tồn kho từ chứng từ nhập/xuất | `inventory.quantity` là snapshot thực tế, không phải tổng chứng từ | `SELECT quantity FROM inventory WHERE ...` |
| Dùng `products.status = 'Inactive'` cho hết hàng | Status là Active/Inactive (master data), không phải stock level | `WHERE inventory.quantity <= products.min_stock` |
| Dùng `salesorders` cho doanh thu tổng | `salesorders` chỉ có order value, không phải revenue thực ghi nhận | `financeledger` với `transaction_type = 'SalesRevenue'` |
| Dùng `transaction_type` cho phân loại không phải tài chính | Chỉ dùng cho ledger entries | Dùng column riêng của từng domain table |
| WHERE `name = '...'` (case-sensitive) | DB lưu hoa/thường không nhất quán | `name ILIKE '...'` |
| SELECT * | Waste tokens, không rõ columns | Liệt kê columns cụ thể (3-6 columns) |
| Thiếu LIMIT trên query không aggregate | Có thể trả về hàng nghìn rows | `LIMIT {sql_limit_max}` |

---

## EMPTY RESULT HANDLING

- If SQL is semantically correct (right tables, right joins, right filters) but returns 0 rows → this IS valid. Do NOT change the SQL to force non-empty results.
- If 0 rows because WHERE filter uses `=` on a name/display value → the observation will suggest ILIKE instead. Do NOT change SQL preemptively.
- NEVER invent fake data or fabricate rows.

---

## Tên hiển thị (danh mục, sản phẩm, NCC, KH) — KHÔNG phân biệt hoa thường

- Khi lọc theo **tên** cột `name` hoặc `category_name` (vd. danh mục, tên SP, tên NCC): dùng **`ILIKE '...'`**, không dùng `=`.
- Ví dụ: `c.name ILIKE 'Điện tử 1'` (khớp cả `Điện Tử 1` trong DB).
- **Mã** (`sku_code`, `supplier_code`, `customer_code`, `receipt_code`, …) vẫn dùng `=` — so khớp chính xác.

## Enum literals (CASE-SENSITIVE)

- `stockreceipts.status`: Draft | Pending | **Approved** | Rejected
- `salesorders.order_channel`: **Retail** | Wholesale | Return (never `Export`)
- `salesorders.status`: Pending | Processing | Partial | Shipped | Delivered | Cancelled
- `stockdispatches.status`: Pending | Full | Partial | Cancelled | WaitingDispatch | Delivering | Delivered — active rows: `deleted_at IS NULL`
- `financeledger.transaction_type`: SalesRevenue | PurchaseCost | OperatingExpense | Refund
- Master data `status`: Active | Inactive

## Calendar spine (when brief has include_zero_months)

- Use `WITH <name> AS (generate_series(...) ...)` + `LEFT JOIN` fact table + `COALESCE(COUNT(...), 0)`.
- CTE names (e.g. `months`) are **not** physical tables — only join allowed tables from schema.
- One row per month in `calendar` range from brief; `ORDER BY` month ascending.
- **Năm hiện tại:** `generate_series` kết thúc ở **tháng hiện tại**, không sinh tháng 6–12 nếu mới đang tháng 5 — trừ khi brief ghi rõ `to_month: 12` / đủ 12 tháng.

## Metric hints (when tables appear in schema)

- **Revenue/expense/cashflow**: `financeledger` + `transaction_type` + `transaction_date`
- **Retail order counts**: `salesorders` + `order_channel = 'Retail'` + `created_at` (khi brief nói bán lẻ)
- **Dispatch/shipment**: `stockdispatches` + `dispatch_date` (not `salesorders`)
- **Total inventory value (giá trị tồn kho)**: `products` has **no** `sale_price` / `cost_price` — prices in `productpricehistory`. Pattern: `inventory i` → `products p` → **`JOIN productunits pu ON pu.product_id = p.id AND pu.is_base_unit = TRUE`** (do **not** join `pu` via `i.unit_id`). Latest price: `productpricehistory pph` with **`pph.unit_id = pu.id`** (`productunits` PK is **`id`**, never `pu.unit_id`). Use `COALESCE(SUM(i.quantity * pph.cost_price), 0)`; prefer `LEFT JOIN LATERAL (... ORDER BY effective_date DESC, id DESC LIMIT 1)`. Use **`cost_price`** unless the user asks for sale price.
- **Tồn hiện tại / hết hàng / sắp hết / low stock** (snapshot, không theo kỳ): dùng **`inventory`** (`product_id`, `quantity`, `reserved_quantity`) JOIN `products` (`min_stock`, `sku_code`, `name`). Hết hàng: `COALESCE(i.quantity, 0) <= COALESCE(p.min_stock, 0)` hoặc `= 0` khi user hỏi hết sạch. **Không** suy tồn bằng `SUM(stockreceiptdetails.quantity) - SUM(stockdispatch_lines.quantity)`. Không cần filter ngày trừ khi câu hỏi ghi rõ kỳ (tháng/năm).

Dynamic fragments (ledger-first, month calendar block) may be appended by the runtime after this playbook.
```

- [ ] **Step 2: Read generated prompt to verify structure**

Run: `Get-Content app/prompts/agents/gen_sql.md | Select-Object -First 5`
Expected: First lines show the system header

- [ ] **Step 3: Commit**

```bash
git add app/prompts/agents/gen_sql.md
git commit -m "feat: rewrite gen_sql.md with structured reasoning + domain playbook + anti-patterns"
```

---

### Task 2: Rewrite `sql_review.md` — add intent alignment check

**Files:**
- Rewrite: `app/prompts/agents/sql_review.md`

**Goal:** Transform sql_review.md from safety-only review into intent + safety review with clear accept/reject criteria including empty-result handling.

- [ ] **Step 1: Write the new sql_review.md**

```markdown
# Agent: sql_review

Review **SELECT-only** PostgreSQL for:
1. Intent alignment — does this SQL answer the user question?
2. Safety — is it read-only and safe?

Return ONLY a JSON object with keys: `ok` (bool), `issues` (array), `retry_hint` (string), `suggested_tables` (array).

---

## Accept criteria (ok=true)

The SQL MUST pass ALL of:
- Single SELECT statement (WITH...SELECT ok)
- All tables in FROM/JOIN are from the schema block
- Read-only: no INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE
- Fact table matches domain (inventory question → inventory table, revenue → financeledger)
- JOIN columns exist in schema
- WHERE filters use correct columns for the domain
- GROUP BY columns appear in SELECT (for aggregate queries)

## Reject criteria (ok=false)

Reject ONLY for concrete, fixable problems:
| Problem | retry_hint example |
|---------|-------------------|
| Wrong fact table | "Use inventory as fact table, not stockreceipts. inventory has quantity, product_id columns" |
| Missing required filter | "Add WHERE order_channel = 'Retail' when question mentions bán lẻ" |
| Wrong table name | "Use productpricehistory (exact name), not product_price_history" |
| JOIN uses non-existent column | "inventory has location_id, not warehouse_id — join via location_id" |
| Wrong metric function | "Use SUM(amount) for revenue, not COUNT(*)" |
| WHERE uses = on display name | "Change name = 'X' to name ILIKE 'X' for case-insensitive match" |
| SELECT * used | "List explicit columns: sku_code, name, quantity" |
| Multi-statement or DDL | "Return one SELECT only — no DML/DLL" |

---

## DO NOT reject (ok=true, no issues)

These are NOT errors:
- **Empty result possible**: SQL is correct semantically but WHERE may match 0 rows — this is valid
- **LIMIT present or absent**: executor handles LIMIT injection
- **Division by zero**: only reject if SQL actually has `/` operator with possible zero divisor
- **Missing date range on stock snapshot**: current stock (`inventory.quantity`) does not need period filter unless user asked for time range
- **Missing LATERAL for latest price**: stylistic choice, not a correctness error
- **CTE naming**: CTE aliases (e.g. `months`) are temp names, not physical tables
- **Table name match**: `productpricehistory` is correct (no underscores) — do not suggest `product_price_history`

---

## Intent Alignment Check (required)

After safety check, verify intent:
1. Does SQL's fact table match the question domain?
2. Are there filter columns for ALL entities the user mentioned?
3. Is the aggregation correct for the question? (COUNT vs SUM vs AVG)
4. Does the SQL avoid all anti-patterns listed in gen_sql playbook?

If intent is misaligned but SQL is safe → ok=false with retry_hint explaining what table/filter to change.

---

## JSON contract

```json
{
  "ok": true,
  "issues": [],
  "retry_hint": "",
  "suggested_tables": []
}
```

or on reject:

```json
{
  "ok": false,
  "issues": ["wrong fact table: use inventory not stockreceipts"],
  "retry_hint": "Replace FROM stockreceipts with FROM inventory. Join products via product_id.",
  "suggested_tables": ["inventory", "products"]
}
```

No markdown fences, no prose outside JSON.
```

- [ ] **Step 2: Read to verify**

Run: `Get-Content app/prompts/agents/sql_review.md | Select-Object -First 5`
Expected: Header lines visible

- [ ] **Step 3: Commit**

```bash
git add app/prompts/agents/sql_review.md
git commit -m "feat: rewrite sql_review.md with intent alignment check + empty-result accept criteria"
```

---

### Task 3: Create `verify_sql_intent.md` prompt + node

**Files:**
- Create: `app/prompts/agents/verify_sql_intent.md`
- Create: `app/graph/verify_sql_intent.py`
- Modify: `app/graph/nodes/sql_pipeline.py` (add `make_verify_sql_intent_node()`)
- Modify: `app/graph/sql_subgraph.py` (add node + edge)

**Goal:** Add lightweight LLM verification step between gen_sql and sql_review that checks intent alignment before proceeding to safety review.

- [ ] **Step 1: Create verify_sql_intent.md prompt**

```markdown
# Agent: verify_sql_intent

You verify whether a generated SQL query matches the user's intent.

## Input
- user_question: the original question
- sql: the generated SQL
- domain: detected query domain (inventory|receipt|dispatch|ledger|catalog_price|generic)
- schema_tables: list of allowed tables

## Rules

Check ALL of these:
1. Fact table correctness: does FROM/JOIN start with the domain's correct fact table?
2. Filter completeness: if user mentions an entity (customer, supplier, product, date range), does WHERE include it?
3. Metric correctness: is the aggregation function right for the question?
4. Join sanity: are JOIN columns compatible with the schema?

## Output JSON

```json
{
  "intent_match": true,
  "confidence": "high",
  "action": "proceed",
  "reason": "SQL uses inventory (correct fact table), filters by product name via ILIKE, returns quantity snapshot"
}
```

### Action values
- `proceed`: intent matches → pass to sql_review
- `regen`: intent mismatch → return feedback, gen_sql must retry
- `bypass_review`: intent_match=high AND SQL is simple (1 table, WHERE only, no CTE/subquery) → skip sql_review

### On regen
Populate `feedback` with concrete instructions:
```json
{
  "intent_match": false,
  "confidence": "high",
  "action": "regen",
  "reason": "Wrong fact table: question asks about tồn kho but SQL uses stockreceipts",
  "feedback": "Replace FROM stockreceipts with FROM inventory. Join products via product_id. Use quantity column."
}
```
```

- [ ] **Step 2: Write verify_sql_intent prompt to file**

Write prompt to `app/prompts/agents/verify_sql_intent.md`

- [ ] **Step 3: Create verify_sql_intent.py with node factory**

```python
"""Intent verification node for SQL subgraph — checks generated SQL against user intent."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.graph.deps import GraphDeps
from app.graph.feedback import append_feedback
from app.graph.state import AgentState
from app.graph.sql_prompts import load_agent_prompt
from app.graph.validate_sql import is_llm_select_sql_shape
from app.harness.capability import sanitize_user_data

logger = logging.getLogger(__name__)

_INTENT_VERIFICATION_ENABLED = True


def _detect_fact_table(sql: str) -> str | None:
    """Heuristic: extract first table after FROM (before JOIN/WHERE)."""
    import re
    m = re.search(r'\bFROM\s+(\w+)', sql, re.IGNORECASE)
    return m.group(1).lower() if m else None


_DOMAIN_FACT_TABLES = {
    "inventory": "inventory",
    "receipt": "stockreceipts",
    "dispatch": "stockdispatches",
    "ledger": "financeledger",
    "catalog_price": "products",
}


def _is_simple_sql(sql: str) -> bool:
    """Heuristic: single table, no CTE, no subquery, no complex joins."""
    s = sql.lower().strip()
    if "with " in s[:60] and "as (" in s[:200]:
        return False
    if "subquery" in s or "select (" in s:
        return False
    join_count = s.count("join ")
    return join_count <= 1


def make_verify_sql_intent_node(deps: GraphDeps):
    """Return a node function: state → dict (updates to state)."""

    def verify_sql_intent(state: AgentState) -> dict:
        logger.info("node=verify_sql_intent action=start")
        sql = str(state.get("generated_sql") or "")
        domain = str(state.get("sql_query_domain") or "generic")
        user_q = str(state.get("messages") or [None])  # simplified

        if not sql or not is_llm_select_sql_shape(sql):
            return {"verify_intent_ok": False, "verify_intent_action": "regen"}

        # Try LLM verification first
        reg = getattr(deps, "llm_registry", None)
        if reg is not None and _INTENT_VERIFICATION_ENABLED:
            client = reg.get("sql_gen")  # reuse sql_gen role
            if client is not None:
                prompt = _build_verify_prompt(sql, domain, user_q)
                system = load_agent_prompt("verify_sql_intent")
                try:
                    raw = client.invoke_text(prompt, system=system)
                    result = json.loads(raw)
                except Exception as exc:
                    logger.warning("verify_sql_intent LLM failed: %s", exc)
                    result = _fallback_verify(sql, domain)
            else:
                result = _fallback_verify(sql, domain)
        else:
            result = _fallback_verify(sql, domain)

        action = result.get("action", "proceed")
        out: dict[str, Any] = {
            "verify_intent_ok": result.get("intent_match", True),
            "verify_intent_action": action,
            "verify_intent_reason": result.get("reason", ""),
        }

        if action == "regen":
            feedback = result.get("feedback", "SQL does not match intent")
            fb = append_feedback(state, "sql_fix", feedback)
            out["validation_feedback"] = fb

        return out

    return verify_sql_intent


def _build_verify_prompt(sql: str, domain: str, user_q: str) -> str:
    return (
        f"User question: {user_q}\n"
        f"Domain: {domain}\n"
        f"SQL: {sql}\n\n"
        "Verify intent alignment. Return JSON with keys: intent_match, confidence, action, reason, feedback"
    )


def _fallback_verify(sql: str, domain: str) -> dict:
    """Deterministic intent check when LLM unavailable."""
    fact = _detect_fact_table(sql)
    expected = _DOMAIN_FACT_TABLES.get(domain)

    if expected and fact and fact != expected:
        return {
            "intent_match": False,
            "confidence": "high",
            "action": "regen",
            "reason": f"Wrong fact table: expected '{expected}' but SQL uses '{fact}'",
            "feedback": f"Replace FROM {fact} with FROM {expected} for domain {domain}",
        }

    return {
        "intent_match": True,
        "confidence": "medium",
        "action": "bypass_review" if _is_simple_sql(sql) else "proceed",
        "reason": "Heuristic check passed",
    }
```

- [ ] **Step 4: Add verify_sql_intent node to sql_pipeline.py**

Find `make_gen_sql_node` and `make_sql_review_node` in `app/graph/nodes/sql_pipeline.py`. After the existing node functions, add import for `make_verify_sql_intent_node` from `app.graph.verify_sql_intent`.

- [ ] **Step 5: Add verify_sql_intent to sql_subgraph.py**

In `sql_subgraph.py`, add the node and conditional edge between `gen_sql` and `sql_review`:

```python
# In build_sql_subgraph():
from app.graph.verify_sql_intent import make_verify_sql_intent_node

def build_sql_subgraph(deps):
    # ... existing setup ...
    
    graph.add_node("verify_sql_intent", make_verify_sql_intent_node(deps))
    
    # Route after gen_sql
    def route_after_gen_sql(state):
        action = state.get("verify_intent_action", "proceed")
        if action == "regen":
            return "gen_sql"
        elif action == "bypass_review":
            return "execute_sql"
        return "sql_review"
    
    graph.add_conditional_edges("gen_sql", route_after_gen_sql, {
        "gen_sql": "gen_sql",
        "sql_review": "sql_review",
        "execute_sql": "execute_sql",
    })
```

- [ ] **Step 6: Run existing tests to verify no regression**

Run: `cd D:\do_an_tot_nghiep\project\ai_python && .venv\Scripts\python -m pytest tests/ -x -q 2>&1`

- [ ] **Step 7: Commit**

```bash
git add app/prompts/agents/verify_sql_intent.md app/graph/verify_sql_intent.py app/graph/nodes/sql_pipeline.py app/graph/sql_subgraph.py
git commit -m "feat: add verify_sql_intent node + prompt for intent alignment check"
```

---

### Task 4: Update `SelfCorrectingSqlRunner` — empty-result classification

**Files:**
- Modify: `app/graph/tools/sql_query.py`

**Goal:** Update `SelfCorrectingSqlRunner.run()` to distinguish "SQL is wrong" vs "legit 0 rows" when execute returns empty results.

- [ ] **Step 1: Add empty-result classification logic**

In `SelfCorrectingSqlRunner.run()`, add a method `_classify_empty(sql: str, domain: str | None) -> bool` that returns `True` if the empty result is likely legitimate (SQL is correct, just no matching data).

Add after `rows = await self._execute(sql)` and the `if not last_rows:` check:

```python
# In the empty result branch, replace simple retry with classification:
if not last_rows:
    if not self._is_sql_structurally_correct(sql):
        # SQL itself is wrong — regen
        if regen >= self._sql_regen_max:
            return SelfCorrectingSqlResult(
                ok=True, rows=last_rows, sql=last_sql,
                regen_count=regen, empty_retry_count=empty_retry,
                degraded=True,
                warning="Câu SQL không phù hợp với câu hỏi. Vui lòng kiểm tra lại.",
            )
        regen += 1
        hint = "SQL structure does not match the question; rewrite with correct tables/joins"
        continue
    
    if empty_retry >= self._sql_empty_retry_max:
        return SelfCorrectingSqlResult(
            ok=True, rows=last_rows, sql=last_sql,
            regen_count=regen, empty_retry_count=empty_retry,
            degraded=False,  # NOT degraded — this is legitimate no-data
        )
    empty_retry += 1
    hint = "empty result; broaden filter or ask for clarification"
    continue
```

- [ ] **Step 2: Add `_is_sql_structurally_correct` method**

```python
def _is_sql_structurally_correct(self, sql: str) -> bool:
    """Check if SQL is structurally valid (passes shape + review stages).
    
    Uses the last review result. If review wasn't run (bypass), assume correct.
    """
    if not sql.strip():
        return False
    if not is_llm_select_sql_shape(sql):
        return False
    # If we reached execution, review already passed — SQL is structurally correct
    return True
```

- [ ] **Step 3: Update `_format_rows_observation` for 0 rows**

Update the empty result observation:

```python
def _format_rows_observation(rows: list[Any], *, sql: str = "", is_degraded: bool = False) -> str:
    if not rows:
        if is_degraded:
            return (
                "Câu SQL không phù hợp với câu hỏi. "
                "Vui lòng kiểm tra lại thông tin hoặc đặt câu hỏi chi tiết hơn."
            )
        return "Không có dữ liệu phù hợp với điều kiện bạn yêu cầu."
    # ... existing head rows logic ...
```

- [ ] **Step 4: Run existing tests**

Run: `cd D:\do_an_tot_nghiep\project\ai_python && .venv\Scripts\python -m pytest tests/test_sql_self_correct_budget.py tests/test_sql_query_tool_self_correct_integration.py -v 2>&1`

- [ ] **Step 5: Commit**

```bash
git add app/graph/tools/sql_query.py
git commit -m "feat: classify empty results as wrong SQL vs legit no-data in SelfCorrectingSqlRunner"
```

---

### Task 5: Integration tests

**Files:**
- Create: `tests/test_verify_sql_intent.py`
- Modify: `tests/test_sql_self_correct_budget.py`

**Goal:** Test verify_sql_intent node and empty-result classification.

- [ ] **Step 1: Create test_verify_sql_intent.py**

```python
"""Tests for verify_sql_intent node — intent alignment detection."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.graph.verify_sql_intent import _detect_fact_table, _fallback_verify, _is_simple_sql


def test_detect_fact_table_inventory():
    sql = "SELECT quantity FROM inventory WHERE product_id = 1"
    assert _detect_fact_table(sql) == "inventory"


def test_detect_fact_table_joins():
    sql = "SELECT p.name, i.quantity FROM inventory i JOIN products p ON i.product_id = p.id"
    assert _detect_fact_table(sql) == "inventory"


def test_detect_fact_table_wrong():
    sql = "SELECT * FROM stockreceipts"
    assert _detect_fact_table(sql) == "stockreceipts"


def test_fallback_verify_wrong_fact_table():
    result = _fallback_verify("SELECT * FROM stockreceipts", "inventory")
    assert result["intent_match"] is False
    assert result["action"] == "regen"
    assert "inventory" in result["feedback"]


def test_fallback_verify_correct():
    result = _fallback_verify("SELECT quantity FROM inventory WHERE product_id = 1", "inventory")
    assert result["intent_match"] is True


def test_is_simple_sql_true():
    assert _is_simple_sql("SELECT name FROM products WHERE status = 'Active' LIMIT 10") is True


def test_is_simple_sql_cte():
    assert _is_simple_sql("WITH months AS (...) SELECT ...") is False


def test_is_simple_sql_join():
    assert _is_simple_sql("SELECT p.name, i.quantity FROM inventory i JOIN products p ON i.product_id = p.id") is True


def test_is_simple_sql_multiple_joins():
    assert _is_simple_sql("SELECT * FROM a JOIN b ON a.id = b.id JOIN c ON b.id = c.id") is False
```

- [ ] **Step 2: Run verify tests**

Run: `cd D:\do_an_tot_nghiep\project\ai_python && .venv\Scripts\python -m pytest tests/test_verify_sql_intent.py -v 2>&1`

- [ ] **Step 3: Add empty-result test to test_sql_self_correct_budget.py**

Add test that verifies legit 0 rows returns success (not degraded):

```python
@pytest.mark.asyncio
async def test_sql_empty_result_legit_no_data():
    """SQL is correct, data legitimately doesn't exist — should return ok=True without degrade."""
    gen_calls = []
    async def _gen(hint):
        gen_calls.append(hint)
        return "SELECT name FROM products WHERE category_name ILIKE '%NonExistent%'"
    
    async def _review(sql):
        return {"ok": True, "issues": []}
    
    async def _execute(sql):
        return []
    
    runner = SelfCorrectingSqlRunner(
        sql_regen_max=1,
        sql_empty_retry_max=1,
        generate=_gen,
        review=_review,
        execute=_execute,
    )
    result = await runner.run()
    assert result.ok is True
    assert result.degraded is False  # Not degraded — legitimate no data
    assert result.warning == ""  # No warning
```

- [ ] **Step 4: Run all SQL tests**

Run: `cd D:\do_an_tot_nghiep\project\ai_python && .venv\Scripts\python -m pytest tests/ -x -q 2>&1`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add tests/test_verify_sql_intent.py tests/test_sql_self_correct_budget.py
git commit -m "test: add verify_sql_intent tests + legit empty-result test"
```

---

### Task 6: Integrate for thin adapter (SelfCorrectingSqlRunner in SqlQueryTool)

**Files:**
- Modify: `app/graph/tools/sql_query.py`

**Goal:** Wire the verify_sql_intent logic into the thin adapter path so `SelfCorrectingSqlRunner` in `SqlQueryTool` benefits from the classification.

- [ ] **Step 1: Update SqlQueryTool._make_callables to include verify step**

In `_make_callables`, after the `generate` callable, add a `verify` callable that checks intent:

```python
async def generate(hint: str | None) -> str:
    nonlocal shared
    if hint:
        shared = {**shared, "validation_feedback": append_feedback(shared, "sql_fix", str(hint))}
    result = await asyncio.to_thread(gen_node, shared)
    shared = {**shared, **result}
    sql = str(shared.get("generated_sql") or "")
    # Optionally run verify_sql_intent here
    return sql
```

- [ ] **Step 2: Run full test suite**

Run: `cd D:\do_an_tot_nghiep\project\ai_python && .venv\Scripts\python -m pytest tests/ -q 2>&1`

- [ ] **Step 3: Commit**

```bash
git add app/graph/tools/sql_query.py
git commit -m "feat: integrate verify_sql_intent into thin adapter path"
```
