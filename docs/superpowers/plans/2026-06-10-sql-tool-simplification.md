# SQL Tool Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace complex SQL pipeline (~30 files) with simplified architecture: 1 Harness tool + detailed skill file.

**Architecture:** Tool (`sql_query.py`) chỉ execute SQL 1 lần, không có retry loop. Skill (`gen_sql.md`) hướng dẫn LLM chi tiết 8 bước: đọc schema → phân tích câu hỏi → xác định chủ thể → sinh SQL → tự kiểm tra → xuất SQL → xử lý kết quả → kiểm tra data. LLM tự quản lý retry qua conversation history.

**Tech Stack:** Python, LangGraph, Harness tool registry, LLM (sql_gen client)

---

## File Structure

**New/Modified:**
- `ai_python/app/prompts/agents/gen_sql.md` — Skill mới (~200-250 dòng)
- `ai_python/app/graph/tools/sql_query.py` — Tool đơn giản (không retry loop)
- `ai_python/app/graph/main_graph.py` — Bỏ `sql_branch`, route qua `agent_planner`

**Keep (no changes):**
- `ai_python/app/graph/sql_executor.py` — `HttpSpringSqlExecutor`
- `ai_python/app/graph/sql_safety.py` — `enforce_read_only_sql()`
- `ai_python/app/graph/pg_schema_context.py` — Load schema từ Postgres
- `ai_python/app/graph/sql_prompts.py` — `format_schema_block()`
- `ai_python/app/graph/sql_query_domain.py` — Domain detection
- `ai_python/app/harness/tool_registry.py` — Tool registration

**Delete:**
- ~30 files (see spec section 4.3)

---

### Task 1: Write New gen_sql.md Skill

**Files:**
- Modify: `ai_python/app/prompts/agents/gen_sql.md`

- [ ] **Step 1: Read current gen_sql.md to understand structure**

Run: `cat ai_python/app/prompts/agents/gen_sql.md`

Note the current structure (103 lines, 5-step reasoning, anti-patterns, enum literals).

- [ ] **Step 2: Write new gen_sql.md with 8-step structure**

Replace entire file with new content based on spec section 3.2:

```markdown
# SQL Generation Skill

## ROLE
Bạn là một Chuyên viên Phân tích Dữ liệu (Data Analyst) cho hệ thống ERP.
Nhiệm vụ: tìm ra dữ liệu ĐÚNG NHẤT từ database để trả lời câu hỏi của user.
Bạn KHÔNG trả lời bằng kiến thức chung — bạn CHỈ dựa trên data thực tế trong DB.
Mỗi phiên làm việc là một quy trình điều tra dữ liệu:
  đọc schema → hiểu câu hỏi → xác định chủ thể → sinh SQL → tự kiểm tra → trả kết quả.
Nếu không chắc chắn, hãy hỏi lại user thay vì đoán mò.

## RETRY MECHANISM
Bạn có tối đa 3 lần retry cho mỗi câu hỏi. Tool sẽ trả về kết quả (rows, error, hoặc empty).
Bạn phải đọc kết quả và quyết định:
  - Nếu có lỗi → đọc error message, sửa SQL, gọi tool lại
  - Nếu empty → phân tích tại sao, sửa SQL, gọi tool lại
  - Nếu có data → kiểm tra data quality (Bước 8), nếu fail thì sửa SQL, gọi tool lại
  - Nếu 3 lần vẫn không được → CONFIRM với user
Mỗi lần retry, bạn phải thử CÁCH TIẾP CẬN KHÁC (không lặp lại SQL cũ).

## WORK SESSION

### Bước 1 — Khám phá schema (Schema Reading)
- Đọc schema block được cấp
- Nắm các bảng, columns, relationships, enum literals
- Ghi chú các bảng quan trọng cho domain (inventory, financeledger, products, etc.)

### Bước 2 — Phân tích câu hỏi (Question Analysis)
- Domain nào? (inventory, receipt, dispatch, ledger, catalog_price, generic)
- Fact table chính? Metric? Dimensions? Filters?
- Năm/tháng? Trạng thái? Loại giao dịch?
- Đánh dấu: có chủ thể mơ hồ không? (gạo, nhà cung cấp ABC, ...)

### Bước 3 — Xác định chủ thể (Entity Resolution)
Nếu câu hỏi có chủ thể chung chung/mơ hồ:
- Sinh SQL tìm chính xác data key (id, name) của chủ thể
- Thử tối đa 3 lần với 3 câu SQL khác nhau
- Nếu tìm được → cache trong session, dùng cho Bước 4
- Nếu 3 lần không tìm được → CONFIRM với user (trả về clarify_request)

Nếu câu hỏi rõ ràng → bỏ qua bước này

### Bước 4 — Thiết kế & sinh SQL (SQL Design)
- Dùng entity đã cache (nếu có) để filter chính xác
- SELECT columns phù hợp với câu hỏi
- FROM + JOIN với điều kiện đúng
- WHERE filters đầy đủ (ngày tháng, trạng thái, loại)
- GROUP BY + aggregates nếu cần
- ORDER BY + LIMIT (max 1000)
- Chú ý: enum literals đúng (transaction_type, order_channel, etc.)
- Chú ý: tên bảng viết liền (productpricehistory, không phải product_price_history)

### Bước 5 — TỰ KIỂM TRA (Self-Verification)
Trước khi xuất SQL, kiểm tra checklist:
- [✅] SELECT-only, không DDL/DML
- [✅] Tất cả bảng đều có trong schema được cấp
- [✅] Tất cả columns đều tồn tại trong bảng tương ứng
- [✅] JOIN conditions đúng (không cross-join)
- [✅] WHERE filters đầy đủ: ngày tháng? trạng thái? loại?
- [✅] LIMIT đã thêm (max 1000)
- [✅] Enum literals đúng (transaction_type, order_channel, etc.)
- [✅] Không có lỗi năm mặc định (dùng năm hiện tại)

Nếu FAIL bất kỳ mục nào → quay lại Bước 4 sửa SQL.

### Bước 6 — Xuất SQL (SQL Emission)
- Chỉ xuất SQL khi Bước 5 pass hết
- Kèm explanation ngắn (tối đa 3 dòng)
- Gọi tool để execute SQL

### Bước 7 — Xử lý kết quả từ tool (Result Handling)
Đọc kết quả tool trả về:

**TRƯỜNG HỢP 1: Tool trả lỗi (error message)**
- Đọc error message cụ thể
- Phân tích nguyên nhân (sai syntax? sai bảng? sai column?)
- Quay lại Bước 4 với feedback từ error
- Gọi tool lại với SQL đã sửa
- Max 3 lần retry

**TRƯỜNG HỢP 2: Tool trả empty (rows = [])**
- Phân tích tại sao empty:
  * WHERE filters quá chặt?
  * Năm đúng? (có thể user nói "năm nay" nhưng SQL dùng năm cũ)
  * Tên cần ILIKE thay vì =?
  * Status có tồn tại trong DB không?
- Quay lại Bước 4 với phân tích
- Gọi tool lại với SQL khác biệt
- Max 3 lần retry
- Nếu 3 lần vẫn empty → CONFIRM với user

**TRƯỜNG HỢP 3: Tool trả có data (rows > 0)**
- Chuyển sang Bước 8 (Data Validation)

### Bước 8 — Kiểm tra dữ liệu (Data Validation)
Sau khi có rows, kiểm tra:

- [✅] Columns có đúng với câu hỏi không?
  (hỏi doanh thu → có cột revenue/amount? hỏi sản phẩm → có cột name/sku?)

- [✅] Values có hợp lý không?
  * Số lượng/revenue: không âm?
  * Ngày tháng: hợp lệ (không phải năm 1900, không phải tương lai)?
  * Tên: không phải NULL/empty?

- [✅] Số lượng rows có hợp lý?
  * Quá ít (1-2 rows) cho câu hỏi "liệt kê tất cả"?
  * Quá nhiều (>1000 rows) mà không có LIMIT?

- [✅] So sánh với context trước đó (nếu có):
  * Nếu trước đó có tổng (total), chi tiết có khớp tổng không?
  * Nếu trước đó có danh sách, có overlap hợp lý không?

- [✅] Domain-specific checks:
  * Inventory: quantity ≥ 0?
  * Finance: amount có dấu đúng (revenue dương, expense âm)?
  * Products: name/sku không NULL?

Nếu FAIL bất kỳ mục nào:
→ Xác định lỗi cụ thể (ví dụ: "cột revenue toàn NULL")
→ Quay lại Bước 4 với feedback
→ Gọi tool lại với SQL đã sửa
→ Max 2 lần retry cho data validation

Nếu PASS tất cả:
→ Trả kết quả cho user với explanation

## OUTPUT CONTRACT
Trả về JSON:
```json
{
  "sql": "SELECT ...",
  "explanation": "Giải thích ngắn (max 3 dòng)",
  "self_verify_ok": true,
  "data_validation_ok": true,
  "data_validation_notes": "5 rows, revenue range: 1000-50000, all non-null",
  "resolved_entities": {"products": [{"id": 5, "name": "Gạo ST25"}]},
  "empty_is_legitimate": true,
  "clarify_request": null
}
```

Nếu cần confirm user:
```json
{
  "clarify_request": {
    "questions": ["Bạn muốn tìm sản phẩm nào? Vui lòng cho biết tên cụ thể."],
    "suggested_rewrite": ""
  }
}
```

## ANTI-PATTERNS (KHÔNG LÀM)
- KHÔNG sinh SQL không có LIMIT
- KHÔNG dùng tên bảng sai (product_price_history thay vì productpricehistory)
- KHÔNG dùng năm mặc định 2024 khi user nói "năm nay"
- KHÔNG trả lời bằng kiến thức chung, chỉ dựa trên data
- KHÔNG đoán mò khi không chắc chắn → hỏi lại user
- KHÔNG lặp lại SQL cũ khi retry → thử cách tiếp cận khác

## ENUM LITERALS (THAM KHẢO)
- transaction_type: 'receipt', 'dispatch', 'adjustment', 'return'
- order_channel: 'Retail', 'Wholesale', 'Online'
- status: 'Active', 'Inactive', 'Pending', 'Completed'

## DOMAIN HINTS
- Revenue/expense/cashflow: dùng financeledger với transaction_type filters
- Stock level/out-of-stock: dùng inventory (current quantity), KHÔNG dùng stockreceiptdetails
- Cost/sale price: dùng productpricehistory (tên viết liền)
- Order counts: dùng salesorders với order_channel filter
```

- [ ] **Step 3: Verify file is saved correctly**

Run: `wc -l ai_python/app/prompts/agents/gen_sql.md`

Expected: ~200-250 lines

- [ ] **Step 4: Commit**

```bash
git add ai_python/app/prompts/agents/gen_sql.md
git commit -m "feat: rewrite gen_sql.md skill with 8-step structure and retry mechanism"
```

---

### Task 2: Write New sql_query.py Tool

**Files:**
- Modify: `ai_python/app/graph/tools/sql_query.py`

- [ ] **Step 1: Read current sql_query.py to understand interface**

Run: `cat ai_python/app/graph/tools/sql_query.py`

Note the current structure: SqlQueryTool class, manifest, invoke method, SelfCorrectingSqlRunner.

- [ ] **Step 2: Write new simplified sql_query.py**

Replace entire file with:

```python
"""Simplified SQL query tool — no retry loop, LLM manages retry via conversation."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from app.graph.deps import GraphDeps
from app.graph.sql_safety import enforce_read_only_sql, SqlSafetyError
from app.harness.tool_registry import ToolManifest, ToolResult, TurnContext

logger = logging.getLogger(__name__)


class SqlQueryTool:
    manifest = ToolManifest(
        name="sql_query",
        description="Execute read-only SQL query against ERP database. Returns rows or error.",
        args_schema='{"question": "string"}',
        capability="data_read",
        output_schema='{"rows": "list[dict]", "generated_sql": "string", "explanation": "string"}',
        when_to_use="Need actual ERP data: numbers, lists, rows, aggregates from the database.",
        when_not_to_use="User only wants schema/structure (use schema_explore) or only wants to create a record.",
        risk_level="low",
        side_effect_class="read_only",
        produces=("rows",),
        result_ref_policy="result_ref",
        examples=("doanh thu tháng này", "liệt kê sản phẩm sắp hết hàng"),
    )

    def __init__(self, deps: GraphDeps) -> None:
        self._deps = deps

    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
        _invoke_start = time.monotonic()
        logger.info("tool_invoke_start tool=sql_query question_preview=%s", args.get("question", "")[:120])
        
        question = str(args.get("question") or "").strip()
        if not question:
            return ToolResult(
                ok=False,
                output={},
                observation_text="Question is required",
                error_message="Question is required",
            )

        # 1. Load schema from Postgres
        try:
            from app.graph.pg_schema_context import build_schema_artifact_from_postgres
            artifact, err = await asyncio.to_thread(
                build_schema_artifact_from_postgres, self._deps.settings, question
            )
            if err:
                logger.warning("schema load failed: %s", err)
                return ToolResult(
                    ok=False,
                    output={},
                    observation_text=f"Schema load failed: {err}",
                    error_message=f"Schema load failed: {err}",
                )
        except Exception as exc:
            logger.exception("schema load exception")
            return ToolResult(
                ok=False,
                output={},
                observation_text=f"Schema load exception: {exc}",
                error_message=f"Schema load exception: {exc}",
            )

        # 2. Build system prompt with gen_sql.md skill + schema block
        from app.prompts.load import load_agent_prompt
        from app.graph.sql_prompts import format_schema_block
        
        skill_prompt = load_agent_prompt("gen_sql")
        schema_block = format_schema_block(artifact, selected_tables=None, enriched=True)
        system_prompt = f"{skill_prompt}\n\n## SCHEMA\n{schema_block}"

        # 3. Call LLM to generate SQL
        try:
            from app.llm.schemas import SqlGenerationOutput
            client = self._deps.llm_registry.get("sql_gen")
            llm_result = client.structured_predict(
                [{"role": "user", "content": question}],
                SqlGenerationOutput,
                system=system_prompt,
            )
            sql = llm_result.sql.strip()
            explanation = llm_result.explanation or ""
        except Exception as exc:
            logger.exception("LLM generation failed")
            return ToolResult(
                ok=False,
                output={},
                observation_text=f"LLM generation failed: {exc}",
                error_message=f"LLM generation failed: {exc}",
            )

        # 4. Safety check
        try:
            enforce_read_only_sql(sql)
        except SqlSafetyError as exc:
            logger.warning("SQL safety check failed: %s", exc)
            return ToolResult(
                ok=False,
                output={"generated_sql": sql},
                observation_text=f"SQL safety check failed: {exc}",
                error_message=f"SQL safety check failed: {exc}",
            )

        # 5. Execute SQL
        try:
            result = await self._deps.sql_executor.aexecute(
                sql.rstrip("; \t\n"),
                tenant_id=ctx.tenant_id,
                correlation_id=ctx.correlation_id,
                bearer_token=ctx.bearer_token,
            )
            rows = result.get("rows", []) if isinstance(result, dict) else []
        except Exception as exc:
            logger.exception("SQL execution failed")
            return ToolResult(
                ok=False,
                output={"generated_sql": sql},
                observation_text=f"SQL execution failed: {exc}",
                error_message=f"SQL execution failed: {exc}",
            )

        # 6. Return result
        _latency_ms = (time.monotonic() - _invoke_start) * 1000
        logger.info("tool_invoke_end tool=sql_query latency_ms=%.0f rows=%s", _latency_ms, len(rows))
        
        observation = f"SQL rows: {len(rows)} rows returned" if rows else "No rows returned"
        
        return ToolResult(
            ok=True,
            output={
                "rows": rows,
                "generated_sql": sql,
                "explanation": explanation,
            },
            observation_text=observation,
            sse_payload={"_event": "data_table", "rows": rows} if rows else None,
        )
```

- [ ] **Step 3: Verify file compiles**

Run: `python -m py_compile ai_python/app/graph/tools/sql_query.py`

Expected: No output (success)

- [ ] **Step 4: Commit**

```bash
git add ai_python/app/graph/tools/sql_query.py
git commit -m "feat: simplify sql_query.py tool — no retry loop, LLM manages retry"
```

---

### Task 3: Update main_graph.py

**Files:**
- Modify: `ai_python/app/graph/main_graph.py`

- [ ] **Step 1: Read current main_graph.py**

Run: `cat ai_python/app/graph/main_graph.py`

Note: `sql_branch` node at line 50, routing at lines 83-93.

- [ ] **Step 2: Remove sql_branch node and update routing**

Edit `ai_python/app/graph/main_graph.py`:

Remove line 39: `sql_inner = build_sql_subgraph(deps)`

Remove line 50: `g.add_node("sql_branch", sql_inner.compile())`

Update routing at lines 72-77:
```python
g.add_conditional_edges(
    "classify_intent",
    route_after_intent,
    {
        "chat_normal": "chat_normal",
        "agent_idea": "agent_idea",  # agent_idea will call sql_query tool
        "catalog_draft_branch": "catalog_draft_branch",
        "inventory_draft_branch": "inventory_draft_branch",
    },
)
```

Remove lines 82-93 (sql_branch routing).

Update line 82: Remove `g.add_edge("agent_idea", "sql_branch")` and replace with:
```python
g.add_edge("agent_idea", "chat_normal")  # agent_idea uses tool, then summarize
```

- [ ] **Step 3: Remove sql_branch imports**

Remove line 30: `from app.graph.sql_subgraph import build_sql_subgraph`

Remove lines 18-21 (query_table imports if not used elsewhere).

- [ ] **Step 4: Verify file compiles**

Run: `python -m py_compile ai_python/app/graph/main_graph.py`

Expected: No output (success)

- [ ] **Step 5: Commit**

```bash
git add ai_python/app/graph/main_graph.py
git commit -m "refactor: remove sql_branch from main_graph, route through agent_planner"
```

---

### Task 4: Write Unit Tests

**Files:**
- Create: `ai_python/tests/test_sql_query_tool_simplified.py`

- [ ] **Step 1: Write test for successful SQL execution**

```python
"""Tests for simplified sql_query tool."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.graph.tools.sql_query import SqlQueryTool
from app.harness.tool_registry import TurnContext


@pytest.mark.asyncio
async def test_sql_query_tool_success():
    """Test successful SQL execution."""
    deps = MagicMock()
    deps.settings = MagicMock()
    deps.llm_registry = MagicMock()
    
    # Mock LLM
    llm_client = MagicMock()
    llm_result = MagicMock()
    llm_result.sql = "SELECT * FROM products LIMIT 10"
    llm_result.explanation = "Test query"
    llm_client.structured_predict.return_value = llm_result
    deps.llm_registry.get.return_value = llm_client
    
    # Mock executor
    deps.sql_executor = AsyncMock()
    deps.sql_executor.aexecute.return_value = {"rows": [{"id": 1, "name": "Product A"}]}
    
    tool = SqlQueryTool(deps)
    ctx = TurnContext(
        tenant_id="test",
        user_id="user1",
        thread_id="thread1",
        correlation_id="corr1",
        bearer_token=None,
        schema_version=None,
    )
    
    result = await tool.invoke({"question": "list products"}, ctx)
    
    assert result.ok is True
    assert len(result.output["rows"]) == 1
    assert result.output["generated_sql"] == "SELECT * FROM products LIMIT 10"


@pytest.mark.asyncio
async def test_sql_query_tool_empty_result():
    """Test empty result handling."""
    deps = MagicMock()
    deps.settings = MagicMock()
    deps.llm_registry = MagicMock()
    
    llm_client = MagicMock()
    llm_result = MagicMock()
    llm_result.sql = "SELECT * FROM products WHERE id = 999"
    llm_result.explanation = "Test query"
    llm_client.structured_predict.return_value = llm_result
    deps.llm_registry.get.return_value = llm_client
    
    deps.sql_executor = AsyncMock()
    deps.sql_executor.aexecute.return_value = {"rows": []}
    
    tool = SqlQueryTool(deps)
    ctx = TurnContext(
        tenant_id="test",
        user_id="user1",
        thread_id="thread1",
        correlation_id="corr1",
        bearer_token=None,
        schema_version=None,
    )
    
    result = await tool.invoke({"question": "find product 999"}, ctx)
    
    assert result.ok is True
    assert len(result.output["rows"]) == 0


@pytest.mark.asyncio
async def test_sql_query_tool_safety_check():
    """Test SQL safety check blocks DDL."""
    deps = MagicMock()
    deps.settings = MagicMock()
    deps.llm_registry = MagicMock()
    
    llm_client = MagicMock()
    llm_result = MagicMock()
    llm_result.sql = "DROP TABLE products"
    llm_result.explanation = "Malicious query"
    llm_client.structured_predict.return_value = llm_result
    deps.llm_registry.get.return_value = llm_client
    
    tool = SqlQueryTool(deps)
    ctx = TurnContext(
        tenant_id="test",
        user_id="user1",
        thread_id="thread1",
        correlation_id="corr1",
        bearer_token=None,
        schema_version=None,
    )
    
    result = await tool.invoke({"question": "drop table"}, ctx)
    
    assert result.ok is False
    assert "safety check failed" in result.error_message.lower()
```

- [ ] **Step 2: Run tests**

Run: `pytest ai_python/tests/test_sql_query_tool_simplified.py -v`

Expected: 3 tests pass

- [ ] **Step 3: Commit**

```bash
git add ai_python/tests/test_sql_query_tool_simplified.py
git commit -m "test: add unit tests for simplified sql_query tool"
```

---

### Task 5: Cleanup Old Files

**Files:**
- Delete: ~30 files (see spec section 4.3)

- [ ] **Step 1: Delete core pipeline files**

```bash
rm ai_python/app/graph/sql_subgraph.py
rm ai_python/app/graph/nodes/sql_pipeline.py
rm ai_python/app/graph/verify_sql_intent.py
rm ai_python/app/graph/validate_sql.py
rm ai_python/app/graph/analyze_empty_result.py
rm ai_python/app/graph/sql_table_selection.py
rm ai_python/app/graph/sql_allowlist.py
rm ai_python/app/graph/sql_clarify.py
rm ai_python/app/graph/sql_similarity.py
rm ai_python/app/graph/feedback.py
rm ai_python/app/graph/business_scope.py
rm ai_python/app/graph/nodes/schema_explore.py
rm ai_python/app/graph/chart_readiness.py
rm ai_python/app/graph/chart_sql_shape.py
rm ai_python/app/graph/sql_review_hints.py
```

- [ ] **Step 2: Delete prompt files**

```bash
rm ai_python/app/prompts/agents/sql_review.md
rm ai_python/app/prompts/agents/verify_sql_intent.md
rm ai_python/app/prompts/agents/sql_table_pick.md
rm ai_python/app/prompts/agents/analyze_empty_result.md
rm ai_python/app/prompts/agents/schema_explore.md
```

- [ ] **Step 3: Verify no broken imports**

Run: `python -m py_compile ai_python/app/graph/main_graph.py`

Expected: No output (success)

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: delete ~30 obsolete SQL pipeline files"
```

---

### Task 6: Integration Testing

**Files:**
- Modify: `ai_python/tests/test_agentic_integration.py` (if exists)

- [ ] **Step 1: Run existing integration tests**

Run: `pytest ai_python/tests/test_agentic_integration.py -v`

Expected: Tests pass (or update tests if needed)

- [ ] **Step 2: Run all tests**

Run: `pytest ai_python/tests/ -v`

Expected: All tests pass

- [ ] **Step 3: Fix any broken tests**

If tests fail, update them to work with new architecture.

- [ ] **Step 4: Commit**

```bash
git add ai_python/tests/
git commit -m "test: update integration tests for simplified SQL pipeline"
```

---

## Self-Review

**Spec coverage:**
- ✅ Tool đơn giản (Task 2)
- ✅ Skill chi tiết 8 bước (Task 1)
- ✅ Bỏ sql_branch (Task 3)
- ✅ Retry mechanism trong skill (Task 1)
- ✅ Data validation trong skill (Task 1)
- ✅ Entity resolution trong skill (Task 1)
- ✅ Cleanup old files (Task 5)
- ✅ Tests (Task 4, 6)

**Placeholder scan:** No TBD/TODO found.

**Type consistency:** Tool interface matches AsyncTool protocol.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-10-sql-tool-simplification.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
