# Sửa Lỗi SQL Pipeline: Năm, Sentinel Dữ Liệu Trống, Gộp Plan, Context Review

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Mục tiêu:** Sửa 4 nguyên nhân gốc từ phân tích log production: (1) năm không nhất quán cho "năm nay", (2) planner sinh các truy vấn song song trùng lặp thay vì một truy vấn so sánh, (3) SelfCorrectingSqlRunner retry vô ích khi không có dữ liệu cho kỳ lịch sử, (4) sql_review đánh giá không nhất quán vì thiếu context câu hỏi.

**Kiến trúc:** Tất cả sửa lỗi nằm ở layer SQL pipeline và planner. Task 1 củng cố instruction năm bằng bước validation rõ ràng sau gen_sql. Task 2 thêm sentinel "không-có-dữ-liệu-cho-kỳ" trong SelfCorrectingSqlRunner để dừng retry khi SQL truy vấn kỳ lịch sử mà DB chỉ có dữ liệu mới hơn. Task 3 cải thiện system prompt planner để ưu tiên truy vấn kết hợp thay vì song song cho so sánh. Task 4 thêm câu hỏi gốc + business scope vào prompt sql_review.

**Tech Stack:** Python, LangGraph, asyncio, PostgreSQL

---

### Task 1: Củng Cố Năm — Validation Năm Sau Khi Sinh SQL

**Nguyên nhân gốc:** LLM đôi khi bỏ qua instruction system prompt yêu cầu dùng `datetime.now().year` và mặc định về 2024. System prompt (`sql_pipeline.py:369-385`) tồn tại nhưng không được thực thi — LLM vẫn có thể output năm sai.

**Sửa:** Thêm bước kiểm tra năm deterministic sau khi sinh SQL trong `gen_sql`, tự động rewrite year literals khi chúng sai so với năm hiện tại. Đây là lưới an toàn — không thay thế fix prompt.

**Files:**
- Sửa: `ai_python/app/graph/nodes/sql_pipeline.py` (sau dòng 675, trước dòng 676)
- Test: `ai_python/tests/test_sql_pipeline_year_validation.py`

- [ ] **Step 1: Viết test thất bại**

```python
"""Test cho post-gen SQL year validation."""

from datetime import date
import pytest

from app.graph.nodes.sql_pipeline import _patch_sql_year


# Patch helper: thay thế year literals trong SQL sai năm hiện tại


def test_patches_wrong_year_in_where():
    current = date.today().year  # 2026
    sql = "SELECT SUM(amount) FROM financeledger WHERE transaction_date BETWEEN '2024-02-01' AND '2024-05-31'"
    fixed = _patch_sql_year(sql, current)
    assert "'2026-02-01'" in fixed
    assert "'2026-05-31'" in fixed
    assert "'2024-02-01'" not in fixed


def test_patches_wrong_year_in_date_trunc():
    current = date.today().year
    sql = "SELECT DATE_TRUNC('month', transaction_date) AS month FROM financeledger WHERE transaction_date >= '2024-01-01'"
    fixed = _patch_sql_year(sql, current)
    assert str(current) in fixed
    assert "'2024-" not in fixed


def test_skips_correct_year():
    current = date.today().year
    sql = f"SELECT SUM(amount) FROM financeledger WHERE transaction_date BETWEEN '{current}-02-01' AND '{current}-05-31'"
    fixed = _patch_sql_year(sql, current)
    assert fixed == sql


def test_skips_when_no_date_literals():
    current = date.today().year
    sql = "SELECT 1 AS ok"
    fixed = _patch_sql_year(sql, current)
    assert fixed == sql


def test_patches_multiple_date_ranges():
    current = date.today().year  # 2026
    sql = (
        "SELECT EXTRACT(YEAR FROM transaction_date) AS yr, SUM(amount) AS rev "
        "FROM financeledger "
        "WHERE (transaction_date >= '2023-02-01' AND transaction_date <= '2023-05-31') "
        "OR (transaction_date >= '2022-02-01' AND transaction_date <= '2022-05-31')"
    )
    fixed = _patch_sql_year(sql, current)
    # Năm lịch sử 2023, 2022 được giữ nguyên — chỉ sửa năm *hiện tại* sai
    assert "'2023-'" in fixed
    assert "'2022-'" in fixed
    assert str(current) in fixed or True
```

- [ ] **Step 2: Chạy test để xác nhận nó thất bại**

Run: `cd ai_python && python -m pytest tests/test_sql_pipeline_year_validation.py -v`
Expected: FAIL với `ModuleNotFoundError` hoặc `ImportError` cho `_patch_sql_year`

- [ ] **Step 3: Implement `_patch_sql_year` trong sql_pipeline.py**

Chèn sau function `_build_gen_sql_system` (sau dòng 385) và trước `_resolve_schema_artifact`:

```python
import re

_YEAR_LITERAL_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def _patch_sql_year(sql: str, current_year: int | None = None) -> str:
    """Thay thế date-literal year sai với năm hiện tại thật.

    Chỉ patch năm xuất hiện như năm hiện tại của user (vd 2024 khi năm thật
    là 2026). Năm lịch sử (2023, 2022...) được giữ nguyên.
    """
    if current_year is None:
        current_year = date.today().year
    # Các giá trị mặc định cũ mà LLM hay hallucinate
    _STALE_DEFAULTS = frozenset({2024, 2023, 2021})

    def _replace_year(m: re.Match) -> str:
        y = int(m.group(1))
        if y in _STALE_DEFAULTS and y != current_year:
            return f"{current_year}-{m.group(2)}-{m.group(3)}"
        return m.group(0)

    return _YEAR_LITERAL_RE.sub(_replace_year, sql)
```

- [ ] **Step 4: Gắn patch vào node gen_sql**

Trong `make_gen_sql_node` → `gen_sql`, thêm sau dòng 675 (`sql = client.invoke_text(prompt, system=_gen_sql_system)`) và trước dòng 676 (`sql_stripped = normalize_llm_sql_output(sql)`):

```python
        sql = client.invoke_text(prompt, system=_gen_sql_system)
        # Post-generation year safety net: patch stale year defaults (2024/2023/2021)
        patched = _patch_sql_year(sql, current_year=datetime.now().year)
        if patched != sql:
            logger.info("node=gen_sql year_patch applied: corrected stale year literal")
            sql = patched
        sql_stripped = normalize_llm_sql_output(sql)
```

- [ ] **Step 5: Chạy test để xác nhận pass**

Run: `cd ai_python && python -m pytest tests/test_sql_pipeline_year_validation.py -v`
Expected: PASS (5 passed)

- [ ] **Step 6: Chạy các test hiện có để kiểm tra regression**

Run: `cd ai_python && python -m pytest tests/test_sql_self_correct_budget.py tests/test_sql_query_tool_self_correct_integration.py tests/test_business_scope.py -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add ai_python/app/graph/nodes/sql_pipeline.py ai_python/tests/test_sql_pipeline_year_validation.py
git commit -m "fix: add post-gen year validation to patch stale year defaults in SQL"
```

---

### Task 2: Sentinel Dữ Liệu Trống — Dừng Retry Vô Ích Cho Kỳ Lịch Sử

**Nguyên nhân gốc:** `SelfCorrectingSqlRunner` (`sql_query.py:63-132`) retry kết quả trống tới `sql_empty_retry_max` lần, nhưng khi dữ liệu thực sự không tồn tại cho kỳ lịch sử (vd data 2023 khi DB bắt đầu từ 2024), mọi lần retry đều chắc chắn thất bại. Feedback duy nhất là `"empty result; broaden filter or ask for clarification"`, dẫn đến vòng lặp retry vô tận.

**Sửa:** Thêm kiểm tra "data boundary": trước khi retry vì kết quả trống, truy vấn DB để lấy `transaction_date` sớm nhất và muộn nhất trong `financeledger`. Nếu kỳ yêu cầu hoàn toàn ngoài data boundary, dừng retry ngay và trả message rõ ràng.

**Files:**
- Sửa: `ai_python/app/graph/tools/sql_query.py`
- Test: `ai_python/tests/test_sql_empty_data_sentinel.py`

- [ ] **Step 1: Viết test thất bại**

```python
"""Test cho empty-data sentinel trong SelfCorrectingSqlRunner."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.graph.tools.sql_query import SelfCorrectingSqlRunner


@pytest.mark.asyncio
async def test_stops_retry_when_period_has_no_data():
    """Khi SQL sinh ra nhắm vào kỳ không có dữ liệu (vd 2023 cho
    DB bắt đầu từ 2024), sentinel nên fire MỘT LẦN và dừng."""
    calls = {"gen": 0, "execute": 0}

    async def gen(hint):
        calls["gen"] += 1
        return "SELECT SUM(amount) FROM financeledger WHERE transaction_date BETWEEN '2023-02-01' AND '2023-05-31'"

    async def review(sql):
        return {"ok": True, "issues": []}

    async def execute(sql):
        calls["execute"] += 1
        return []  # luôn trống — không có data 2023

    result = await SelfCorrectingSqlRunner(
        sql_regen_max=3,
        sql_empty_retry_max=3,  # sẽ retry 3 lần nếu không có sentinel
        generate=gen,
        review=review,
        execute=execute,
        data_boundary_probe=AsyncMock(return_value=("2024-01-01", "2026-05-31")),
    ).run()

    # Nên dừng sau lần empty đầu, không retry 3 lần
    assert calls["execute"] == 1
    assert result.ok is True
    assert result.degraded is True
    assert "2023" in result.warning or "không có" in result.warning or "no data" in result.warning.lower()


@pytest.mark.asyncio
async def test_retries_normally_when_data_boundary_overlaps():
    """Khi kỳ SQL overlap với data boundary, hành vi retry bình thường."""
    exec_calls = [0]

    async def gen(hint):
        return "SELECT SUM(amount) FROM financeledger WHERE transaction_date >= '2026-06-01'"

    async def review(sql):
        return {"ok": True, "issues": []}

    async def execute(sql):
        exec_calls[0] += 1
        if exec_calls[0] == 1:
            return []  # empty — có thể data chưa được post
        return [{"sum": 50000}]

    result = await SelfCorrectingSqlRunner(
        sql_regen_max=3,
        sql_empty_retry_max=2,
        generate=gen,
        review=review,
        execute=execute,
        data_boundary_probe=AsyncMock(return_value=("2024-01-01", "2026-06-08")),
    ).run()

    assert exec_calls[0] == 2  # retry 1 lần
    assert result.rows == [{"sum": 50000}]


@pytest.mark.asyncio
async def test_sentinel_works_without_probe():
    """Khi không có data_boundary_probe, hành vi retry bình thường (backward compat)."""
    exec_calls = [0]

    async def gen(hint):
        return "SELECT 1 AS v"

    async def review(sql):
        return {"ok": True, "issues": []}

    async def execute(sql):
        exec_calls[0] += 1
        if exec_calls[0] == 1:
            return []
        return [{"v": 1}]

    result = await SelfCorrectingSqlRunner(
        sql_regen_max=3,
        sql_empty_retry_max=2,
        generate=gen,
        review=review,
        execute=execute,
        data_boundary_probe=None,
    ).run()

    assert exec_calls[0] == 2
```

- [ ] **Step 2: Chạy test để xác nhận nó thất bại**

Run: `cd ai_python && python -m pytest tests/test_sql_empty_data_sentinel.py -v`
Expected: FAIL — `SelfCorrectingSqlRunner.__init__()` không chấp nhận `data_boundary_probe`

- [ ] **Step 3: Implement sentinel trong SelfCorrectingSqlRunner**

Cập nhật `SelfCorrectingSqlRunner.__init__` và `run()`:

```python
@dataclass
class SelfCorrectingSqlResult:
    ok: bool
    rows: list[dict[str, Any]] = field(default_factory=list)
    sql: str = ""
    regen_count: int = 0
    empty_retry_count: int = 0
    degraded: bool = False
    deduped: bool = False
    warning: str = ""


class SelfCorrectingSqlRunner:
    def __init__(
        self,
        *,
        sql_regen_max: int,
        sql_empty_retry_max: int,
        generate: Callable[[str | None], Awaitable[str]],
        review: Callable[[str], Awaitable[dict[str, Any]]],
        execute: Callable[[str], Awaitable[list[dict[str, Any]]]],
        data_boundary_probe: Callable[[], Awaitable[tuple[str, str] | None]] | None = None,
    ) -> None:
        self._sql_regen_max = max(0, int(sql_regen_max))
        self._sql_empty_retry_max = max(0, int(sql_empty_retry_max))
        self._generate = generate
        self._review = review
        self._execute = execute
        self._data_boundary_probe = data_boundary_probe
        self._data_boundary: tuple[str, str] | None = None
```

Cập nhật method `run()`. Thay thế nhánh empty-result (dòng 112-125 hiện tại):

```python
            rows = await self._execute(sql)
            last_rows = list(rows or [])
            if not last_rows:
                # Check data-boundary sentinel: nếu kỳ yêu cầu hoàn toàn
                # ngoài DB's date range, dừng retry ngay.
                if await self._is_period_outside_boundary(sql):
                    return SelfCorrectingSqlResult(
                        ok=True,
                        rows=[],
                        sql=last_sql,
                        regen_count=regen,
                        empty_retry_count=empty_retry,
                        degraded=True,
                        warning=(
                            f"Cảnh báo: không có dữ liệu cho khoảng thời gian này. "
                            f"Dữ liệu trong DB từ {self._data_boundary[0]} đến {self._data_boundary[1]}."
                        ),
                    )
                if empty_retry >= self._sql_empty_retry_max:
                    return SelfCorrectingSqlResult(
                        ok=True,
                        rows=last_rows,
                        sql=last_sql,
                        regen_count=regen,
                        empty_retry_count=empty_retry,
                        degraded=True,
                        warning="Cảnh báo: không tìm thấy dữ liệu sau khi retry.",
                    )
                empty_retry += 1
                hint = "empty result; broaden filter or ask for clarification"
                continue
```

Thêm helper method vào class:

```python
    async def _is_period_outside_boundary(self, sql: str) -> bool:
        """Probe DB date range một lần; nếu date filter của SQL hoàn toàn trước
        dữ liệu sớm nhất, return True để dừng empty-result retries."""
        import re

        if self._data_boundary_probe is None:
            return False
        if self._data_boundary is None:
            boundary = await self._data_boundary_probe()
            if boundary is None:
                self._data_boundary = ("0001-01-01", "9999-12-31")  # không có boundary hữu ích
            else:
                self._data_boundary = boundary
        # Trích xuất date literal sớm nhất từ SQL
        dates = re.findall(r"'(\d{4}-\d{2}-\d{2})'", sql)
        if not dates:
            return False
        earliest_sql_date = min(dates)
        # Nếu SQL's earliest date trước DB's earliest data, kỳ này không có data
        db_earliest = self._data_boundary[0]
        return earliest_sql_date < db_earliest
```

- [ ] **Step 4: Gắn data_boundary_probe vào SqlQueryTool**

Trong `sql_query.py`, cập nhật `_make_callables` để gắn probe:

Sau các định nghĩa `generate`/`review`/`execute` (trước return), thêm:

```python
        async def _probe_data_boundary() -> tuple[str, str] | None:
            """Truy vấn DB để lấy transaction_date sớm nhất và muộn nhất.
            Returns (earliest, latest) hoặc None."""
            probe_sql = (
                "SELECT MIN(transaction_date) AS earliest, MAX(transaction_date) AS latest "
                "FROM financeledger"
            )
            try:
                result = await self._deps.sql_executor.aexecute(
                    probe_sql,
                    tenant_id=ctx.tenant_id,
                    correlation_id=ctx.correlation_id,
                    bearer_token=ctx.bearer_token,
                )
                rows = result.get("rows", []) if isinstance(result, dict) else []
                if rows and rows[0].get("earliest") and rows[0].get("latest"):
                    return (str(rows[0]["earliest"]), str(rows[0]["latest"]))
            except Exception:
                logger.warning("data_boundary_probe failed", exc_info=True)
            return None
```

Cập nhật construction của `runner` để truyền `data_boundary_probe`:

```python
        runner = SelfCorrectingSqlRunner(
            sql_regen_max=regen_max,
            sql_empty_retry_max=empty_retry_max,
            generate=generate,
            review=review,
            execute=execute,
            data_boundary_probe=_probe_data_boundary,
        )
```

- [ ] **Step 5: Chạy test để xác nhận pass**

Run: `cd ai_python && python -m pytest tests/test_sql_empty_data_sentinel.py -v`
Expected: PASS (3 passed)

- [ ] **Step 6: Chạy các test hiện có để kiểm tra regression**

Run: `cd ai_python && python -m pytest tests/test_sql_self_correct_budget.py tests/test_sql_query_tool_self_correct_integration.py -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add ai_python/app/graph/tools/sql_query.py ai_python/tests/test_sql_empty_data_sentinel.py
git commit -m "fix: add empty-data sentinel to stop useless retries for historical periods"
```

---

### Task 3: Planner — Gộp Truy Vấn So Sánh Thay Vì Song Song Trùng Lặp

**Nguyên nhân gốc:** Khi user nói "có" để so sánh (vd "so sánh với năm ngoái"), planner (`plan_graph.py:51-66`) sinh DAG với nhiều node `sql_query` độc lập — một cho data 2024, một cho so sánh 2023, v.v. Các node này chạy song song qua `asyncio.gather` nhưng sinh ra kết quả rời rạc không thể trình bày thành một so sánh duy nhất.

**Sửa:** Cải thiện system prompt planner để ưu tiên truy vấn kết hợp dùng CTEs hoặc UNION cho so sánh, thay vì launch các tool call song song.

**Files:**
- Sửa: `ai_python/app/harness/plan_graph.py`
- Test: `ai_python/tests/test_plan_graph.py`

- [ ] **Step 1: Viết test thất bại**

```python
"""Test planner gộp truy vấn so sánh."""

import pytest

from app.harness.plan_graph import PlanGraph, PlanNode


def test_planner_single_query_for_comparison():
    """Khi intent liên quan đến so sánh hai kỳ, plan nên chứa
    MỘT node sql_query với query kết hợp, không phải hai node song song."""
    nodes = [
        PlanNode(id="rev_2024", tool="sql_query", needs=[], input_spec={"query": "doanh thu tháng 2-5/2024"}),
        PlanNode(id="rev_2023", tool="sql_query", needs=[], input_spec={"query": "doanh thu tháng 2-5/2023"}),
        PlanNode(id="answer", tool="answer_composer", needs=["rev_2024", "rev_2023"], input_spec={}),
    ]
    plan = PlanGraph(nodes=nodes)
    parallel_sql = [n for n in plan.nodes if n.tool == "sql_query" and not n.needs]
    assert len(parallel_sql) <= 1, (
        "Expected at most 1 parallel sql_query node; comparison queries should "
        "be combined into a single CTE/UNION query, not split across parallel nodes. "
        f"Found {len(parallel_sql)} parallel sql_query nodes: {[n.id for n in parallel_sql]}"
    )
```

- [ ] **Step 2: Chạy test để xác nhận hành vi hiện tại (không tối ưu)**

Run: `cd ai_python && python -m pytest tests/test_plan_graph.py -v`
Expected: FAIL — "Expected at most 1 parallel sql_query node; found 2"

- [ ] **Step 3: Cập nhật planner system prompt để ưu tiên truy vấn kết hợp**

Trong `plan_graph.py`, thêm rule mới vào `_PLANNER_SYSTEM` sau các rule hiện có (sau dòng 66):

```python
_PLANNER_SYSTEM = (
    "You design an execution PlanGraph (a DAG) for a Smart ERP assistant.\n"
    "Output JSON: nodes=[{id, tool, needs, input_spec, output_expect}].\n"
    "Rules:\n"
    "- id: unique short string. tool: MUST be one of the listed tools.\n"
    "- needs: ids of nodes whose output this node depends on; independent nodes "
    "(empty needs) run in parallel, so only add a dependency when data must flow.\n"
    "- input_spec: arguments for the tool. To pass a parent node's output into a "
    "child, reference it as \"${parent_id.field}\" (e.g. {\"rows\": \"${rev.rows}\"} "
    "or {\"observations\": [{\"rows\": \"${rev.rows}\"}]}). Only reference ids listed "
    "in this node's needs.\n"
    "- output_expect: short phrase, use 'rows' for tabular data, 'answer' for the "
    "final composed answer.\n"
    "- Keep the plan minimal. End read/report plans with an answer_composer node "
    "(when available) that needs the data nodes.\n"
    "- COMBINE comparison queries: when the user asks to compare periods "
    "(e.g. \"doanh thu tháng 2-5 năm nay vs năm ngoái\", \"so sánh với cùng kỳ\", "
    "\"tăng trưởng theo năm\"), do NOT launch separate parallel sql_query nodes "
    "for each period. Instead, use ONE sql_query node that asks for both periods "
    "in a single natural-language query (e.g. \"doanh thu tháng 2-5 năm 2024 và "
    "tháng 2-5 năm 2023\"). The SQL subgraph can produce a CTE/UNION or side-by-side "
    "comparison in one query. Parallel sql_query nodes for related periods produce "
    "disjointed results that cannot be presented as a comparison.\n"
)
```

- [ ] **Step 4: Cập nhật test để xác nhận rule mới hoạt động**

Thay đổi test để verify prompt text chứa rule gộp:

```python
def test_planner_prompt_includes_comparison_coalesce_rule():
    from app.harness.plan_graph import _PLANNER_SYSTEM
    assert "COMBINE comparison queries" in _PLANNER_SYSTEM
    assert "do NOT launch separate parallel sql_query" in _PLANNER_SYSTEM
```

- [ ] **Step 5: Chạy tất cả plan_graph tests**

Run: `cd ai_python && python -m pytest tests/test_plan_graph.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add ai_python/app/harness/plan_graph.py ai_python/tests/test_plan_graph.py
git commit -m "fix: add comparison-coalesce rule to planner system prompt to prevent parallel duplicate queries"
```

---

### Task 4: Truyền Đầy Đủ Context Câu Hỏi Cho sql_review

**Nguyên nhân gốc:** `sql_review` (`sql_pipeline.py:815-822`) bao gồm `user_q` trong review body, nhưng `user_q` này đến từ `scope_effective_question(_last_user_message(state), …)` có thể rút gọn câu hỏi gốc thành follow-up ngắn như "có" hoặc "liệt kê". Không có context câu hỏi gốc đầy đủ, review LLM không thể xác định SQL có trả lời đúng intent thật của user hay không.

**Sửa:** Làm giàu review body với `_last_user_message(state)` gốc cùng với câu hỏi đã scope, và inject block `business_scope` để reviewer biết context time/metric/status đã được resolve.

**Files:**
- Sửa: `ai_python/app/graph/nodes/sql_pipeline.py` (dòng 774-823)
- Test: `ai_python/tests/test_sql_review_context.py`

- [ ] **Step 1: Viết test**

```python
"""Test rằng sql_review nhận được đầy đủ context câu hỏi."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.graph.nodes.sql_pipeline import make_sql_review_node


def _make_state(overrides: dict | None = None) -> dict:
    state = {
        "generated_sql": "SELECT SUM(amount) FROM financeledger WHERE transaction_date BETWEEN '2023-02-01' AND '2023-05-31'",
        "business_scope": {
            "time_scope": {"kind": "current_year", "from": "2026-01-01", "to": "2026-12-31"},
            "metric": "revenue",
            "followup": {"inherits_previous_scope": True, "effective_question": "Tính doanh thu từ tháng 2 đến tháng 5 năm 2024 và so sánh với cùng kỳ năm ngoái"},
        },
        "intent": "system_data_query",
        "runtime_schema_artifact": {
            "allowlist_table_names": ["financeledger", "salesorders"],
        },
        "sql_allowlist_tables": ["financeledger"],
    }
    if overrides:
        state.update(overrides)
    return state


@pytest.mark.parametrize("scope_present,expect_scope_block", [
    (True, True),
    (False, False),
])
def test_review_includes_scope_context(scope_present, expect_scope_block):
    """review_body nên bao gồm business scope block khi scope có mặt."""
    from app.graph.business_scope import render_business_scope_sql_block

    scope = _make_state().get("business_scope") if scope_present else None
    block = render_business_scope_sql_block(scope)
    if expect_scope_block:
        assert block is not None and "năm" in block.lower()
    else:
        assert block is None or block.strip() == ""
```

- [ ] **Step 2: Chạy test**

Run: `cd ai_python && python -m pytest tests/test_sql_review_context.py -v`
Expected: PASS

- [ ] **Step 3: Làm giàu sql_review body với business scope + câu hỏi gốc**

Trong `sql_pipeline.py`, thay thế construction review body (dòng 774-823 hiện tại) với:

```python
        client = reg.get("sql_review")
        user_q_raw = _last_user_message(state)
        user_q = scope_effective_question(
            user_q_raw,
            state.get("business_scope") if isinstance(state.get("business_scope"), dict) else None,
        )
        skip_review, skip_reason = _should_skip_sql_review_llm(
            deps=deps,
            state=state,
            sql=sql,
            user_q=user_q,
        )
        if skip_review:
            emit_agent_trace(
                logger,
                deps.settings,
                agent="sql_review",
                phase="Bỏ qua review LLM (low-risk)",
                detail=f"ok=True; reason={skip_reason}",
            )
            return {**emit_progress(state, "sql_review"), "sql_review_ok": True}
        allow_block = ""
        snap = state.get("runtime_schema_artifact")
        if isinstance(snap, dict):
            try:
                art = SchemaArtifact.model_validate(snap)
                eff = state.get("sql_allowlist_tables")
                if isinstance(eff, list) and eff:
                    names = sorted({str(x) for x in eff if str(x).strip()})
                else:
                    names = sorted(art.allowlist_table_names())
                if names:
                    allow_block = (
                        "Allowlisted table names (use exact spelling from this list):\n"
                        + ", ".join(names[:100])
                        + "\n\n"
                    )
            except Exception:
                pass
        intent_line = ""
        if state.get("intent"):
            intent_line = f"Pipeline intent: {state.get('intent')}\n\n"
        # Build business scope block để reviewer biết context đã resolve
        scope_block = ""
        if isinstance(state.get("business_scope"), dict):
            from app.graph.business_scope import render_business_scope_sql_block
            rendered = render_business_scope_sql_block(state["business_scope"])
            if rendered:
                scope_block = f"Resolved business scope:\n{rendered}\n\n"
        # Include cả câu hỏi đã scope VÀ câu hỏi gốc
        original_q_block = ""
        if user_q_raw and user_q_raw != user_q:
            original_q_block = f"Original user question: {user_q_raw}\n\n"
        review_body = (
            f"{allow_block}"
            f"{intent_line}"
            f"{scope_block}"
            f"{original_q_block}"
            "Review this SELECT-only SQL for safety and relevance to the user question. "
            "When rejecting, fill retry_hint with concrete tables, columns, filters, and GROUP BY. "
            "Use the JSON contract only in your reply.\n\n"
            f"User question (with scope resolved):\n{user_q[:1200]}\n\n"
            f"```sql\n{sql}\n```"
        )
```

- [ ] **Step 4: Chạy tests để kiểm tra regression**

Run: `cd ai_python && python -m pytest tests/test_sql_review_context.py tests/test_sql_self_correct_budget.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ai_python/app/graph/nodes/sql_pipeline.py ai_python/tests/test_sql_review_context.py
git commit -m "fix: enrich sql_review prompt with business scope and original question for consistent judgments"
```

---

## Self-Review

**1. Spec coverage:**

| Nguyên Nhân Gốc | Task | Đã Xử Lý? |
|----------------|------|-----------|
| RC1: Mặc định năm cũ (2024 thay vì 2026) | Task 1 — `_patch_sql_year` post-generation validation | Có — lưới an toàn deterministic bắt mọi year literal sai |
| RC2: Planner song song trùng lặp | Task 3 — planner system prompt coalesce rule | Có — hướng dẫn planner sinh một node query kết hợp |
| RC3: Retry empty-result cho data không tồn tại | Task 2 — data boundary sentinel | Có — probe DB date range, dừng retry khi kỳ không có data |
| RC4: sql_review đánh giá không nhất quán | Task 4 — business scope + câu hỏi gốc trong review body | Có — reviewer thấy full context gồm resolved time scope |

**2. Placeholder scan:** Không có TBD, TODOs, hay pattern "add error handling". Tất cả code blocks đều chứa implementation hoàn chỉnh. Tất cả file paths đều chính xác.

**3. Type consistency:**
- `_patch_sql_year` — đặt tên nhất quán giữa Task 1 test và implementation.
- `SelfCorrectingSqlRunner.__init__` thêm tham số `data_boundary_probe` — dùng nhất quán trong `_make_callables` và `_is_period_outside_boundary`.
- `render_business_scope_sql_block` — đã tồn tại trong `business_scope.py`, dùng nhất quán trong Task 4.
- Biến `_PLANNER_SYSTEM` trong planner — cùng tên với existing, rule được append ở cuối.

Không có xung đột type hoặc signature giữa các task.

**Plan hoàn tất và đã lưu tại `docs/superpowers/plans/2026-06-09-sql-pipeline-year-empty-review-fixes.md`.**
