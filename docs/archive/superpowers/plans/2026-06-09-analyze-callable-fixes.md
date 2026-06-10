# Analyze Callable — Fix Dead State, Contract, and Test Coverage

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 4 code review issues found in the `analyze` callable integration: dead state `_last_analyze_result`, stale docstring, missing test coverage for 3 paths, and misleading `analyze(sql, hint)` contract.

**Architecture:** All changes are in `SelfCorrectingSqlRunner` and its integration tests. The misleading contract fix threads user `query` through the runner instead of passing review retry hint, making the callable interface honest. `_last_analyze_result` is actually wired to store the last result. Tests cover suspicious-warning, exception, and no-analyze paths.

**Tech Stack:** Python 3.12+, asyncio, pytest

---

## File Structure

| File | Change |
|------|--------|
| `ai_python/app/graph/tools/sql_query.py` | Fix `_last_analyze_result` assignment, fix docstring, thread `query` through runner |
| `ai_python/tests/test_sql_query_tool_self_correct_integration.py` | Add 3 new tests for coverage gaps |

---

### Task 1: Fix `_last_analyze_result` dead state + docstring

**Files:**
- Modify: `ai_python/app/graph/tools/sql_query.py:59,127,184`

- [ ] **Step 1: Wire `_last_analyze_result` assignment**

In `run()` method, after line 127 (`analyze_warning = (analyze_result or {}).get("warning", "")`), add:

```python
                    self._last_analyze_result = analyze_result or {}
```

Full context (lines 121-138):
```python
            if not last_rows:
                # SQL passed review — analyze empty result for suspicious patterns
                analyze_warning = ""
                if self._analyze is not None:
                    try:
                        analyze_result = await self._analyze(sql, hint or "")
                        analyze_warning = (analyze_result or {}).get("warning", "")
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
                    warning=analyze_warning,
                )
```

- [ ] **Step 2: Fix stale docstring**

Replace line 184:
```python
        """Return (generate, review, execute) async callables for the runner."""
```
with:
```python
        """Return (generate, review, execute, analyze) async callables for the runner."""
```

- [ ] **Step 3: Run tests to verify no regression**

```bash
cd ai_python && pytest tests/test_sql_query_tool_self_correct_integration.py tests/test_sql_self_correct_budget.py -v
```

Expected: All existing tests pass.

---

### Task 2: Fix misleading `analyze(sql, hint)` contract

**Files:**
- Modify: `ai_python/app/graph/tools/sql_query.py:51,126,243,273`

**Root cause:** `SelfCorrectingSqlRunner.__init__` stores `generate`, `review`, `execute`, `analyze` callables but has no knowledge of the user question. When `run()` calls `self._analyze(sql, hint or "")` (line 126), it passes the review retry hint — but the `analyze` closure in `SqlQueryTool` ignores this parameter and captures `query` from outer scope instead. The `(sql, hint)` contract is misleading.

**Fix:** Thread the user query through `SelfCorrectingSqlRunner` instead of passing review hint.

- [ ] **Step 1: Add `query` parameter to `SelfCorrectingSqlRunner.__init__`**

Replace:
```python
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

with:
```python
    def __init__(
        self,
        *,
        sql_regen_max: int,
        sql_empty_retry_max: int,
        generate: Callable[[str | None], Awaitable[str]],
        review: Callable[[str], Awaitable[dict[str, Any]]],
        execute: Callable[[str], Awaitable[list[dict[str, Any]]]],
        analyze: Callable[[str, str], Awaitable[dict[str, Any]]] | None = None,
        query: str = "",
    ) -> None:
        self._sql_regen_max = max(0, int(sql_regen_max))
        self._sql_empty_retry_max = max(0, int(sql_empty_retry_max))
        self._generate = generate
        self._review = review
        self._execute = execute
        self._analyze = analyze
        self._query = query
        self._last_analyze_result: dict[str, Any] = {}
```

- [ ] **Step 2: Change `run()` to pass `self._query` instead of `hint`**

Replace line 126:
```python
                        analyze_result = await self._analyze(sql, hint or "")
```
with:
```python
                        analyze_result = await self._analyze(sql, self._query)
```

- [ ] **Step 3: Update `SqlQueryTool.invoke()` to pass `query` to runner**

Replace the runner construction (lines 267-274):
```python
        runner = SelfCorrectingSqlRunner(
            sql_regen_max=regen_max,
            sql_empty_retry_max=empty_retry_max,
            generate=generate,
            review=review,
            execute=execute,
            analyze=analyze,
        )
```
with:
```python
        runner = SelfCorrectingSqlRunner(
            sql_regen_max=regen_max,
            sql_empty_retry_max=empty_retry_max,
            generate=generate,
            review=review,
            execute=execute,
            analyze=analyze,
            query=query,
        )
```

- [ ] **Step 4: Update `analyze` closure to use passed query**

Replace the analyze closure (lines 243-254):
```python
        async def analyze(sql: str, hint: str) -> dict[str, Any]:
            """Run empty-result analysis when rows == 0."""
            from app.graph.analyze_empty_result import _analyze_empty_heuristic
            from app.graph.sql_query_domain import detect_sql_query_domain

            domain = detect_sql_query_domain(query)
            result = _analyze_empty_heuristic(sql, query, domain)
            return {
                "verdict": result.get("verdict", "legitimate"),
                "warning": result.get("warning", ""),
                "reason": result.get("reason", ""),
            }
```

Note: The closure still captures `query` from `_make_callables` scope — this is fine because `query` is the user question in both the runner and the closure. The key improvement is that the runner now passes the correct value. The parameter is still named `query` in the closure (renamed from `hint`).

Wait — actually the closure parameter is the second `str` in the callable signature. Let me fix this: the closure accepts the query from the runner now, so use it instead of capturing:

```python
        async def analyze(sql: str, user_query: str) -> dict[str, Any]:
            """Run empty-result analysis when rows == 0."""
            from app.graph.analyze_empty_result import _analyze_empty_heuristic
            from app.graph.sql_query_domain import detect_sql_query_domain

            domain = detect_sql_query_domain(user_query)
            result = _analyze_empty_heuristic(sql, user_query, domain)
            return {
                "verdict": result.get("verdict", "legitimate"),
                "warning": result.get("warning", ""),
                "reason": result.get("reason", ""),
            }
```

- [ ] **Step 5: Run tests to verify**

```bash
cd ai_python && pytest tests/test_sql_query_tool_self_correct_integration.py tests/test_sql_self_correct_budget.py -v
```

Expected: All existing tests pass (analyze is None in tests, so no behavior change).

---

### Task 3: Add tests for missing coverage paths

**Files:**
- Modify: `ai_python/tests/test_sql_query_tool_self_correct_integration.py`

Three tests to append at end of file (before final blank line):

- [ ] **Step 1: Add test for suspicious-empty warning**

```python
@pytest.mark.asyncio
async def test_invoke_empty_suspicious_warning():
    """Empty result with suspicious pattern produces a warning in observation_text."""
    async def _gen(hint):
        return "SELECT id FROM nonexistent_table WHERE id = 999"

    async def _review(sql):
        return {"ok": True, "issues": []}

    async def _execute(sql):
        return []

    deps = _make_deps()
    tool = SqlQueryTool(deps, _test_generate=_gen, _test_review=_review, _test_execute=_execute)
    result = await tool.invoke({"query": "find something in missing table"}, _ctx())
    assert result.ok is True
    assert result.output["query_result"]["rows"] == []
```

Note: Since `_test_execute` is set, `SqlQueryTool._make_callables` returns early (line 185-186) and the production `analyze` closure is never created. The analyze callable is `None`, so this test verifies the no-analyze path. The suspicious-warning path requires the production analyze closure, which needs a full integration test without `_test_execute` injection — that's non-trivial.

Actually, let me reconsider. The test injection bypasses the production `_make_callables` entirely. To test the analyze path, we need to either:
1. Provide a custom `_test_generate` that also includes analyze (but there's no `_test_analyze` param)
2. Test `SelfCorrectingSqlRunner` directly with a mock analyze callable

Option 2 is better. Let me look at how `test_sql_self_correct_budget.py` tests work — they test `SelfCorrectingSqlRunner` directly.

So the tests should be in `test_sql_self_correct_budget.py` or a new file.

Actually, let me reconsider the approach. The cleanest way:

- For suspicious warning: test `SelfCorrectingSqlRunner` directly with a mock analyze callable
- For analyze exception: same — `SelfCorrectingSqlRunner` directly
- For no-analyze: already covered by existing tests

Let me revise the test code:

```python
@pytest.mark.asyncio
async def test_analyze_warning_propagates_to_result():
    """When analyze callable returns a warning, SelfCorrectingSqlResult.warning contains it."""
    from app.graph.tools.sql_query import SelfCorrectingSqlRunner

    async def _gen(hint):
        return "SELECT 1"

    async def _review(sql):
        return {"ok": True, "issues": []}

    async def _execute(sql):
        return []

    async def _analyze(sql, query):
        return {"verdict": "suspicious", "warning": "Table 'nonexistent' not found in schema", "reason": "missing table"}

    runner = SelfCorrectingSqlRunner(
        sql_regen_max=2,
        sql_empty_retry_max=1,
        generate=_gen,
        review=_review,
        execute=_execute,
        analyze=_analyze,
        query="test query",
    )
    result = await runner.run()
    assert result.ok is True
    assert result.warning == "Table 'nonexistent' not found in schema"


@pytest.mark.asyncio
async def test_analyze_exception_caught_gracefully():
    """When analyze callable raises, runner catches exception, logs warning, returns empty warning."""
    from app.graph.tools.sql_query import SelfCorrectingSqlRunner

    async def _gen(hint):
        return "SELECT 1"

    async def _review(sql):
        return {"ok": True, "issues": []}

    async def _execute(sql):
        return []

    async def _analyze(sql, query):
        raise RuntimeError("analyze exploded")

    runner = SelfCorrectingSqlRunner(
        sql_regen_max=2,
        sql_empty_retry_max=1,
        generate=_gen,
        review=_review,
        execute=_execute,
        analyze=_analyze,
        query="test query",
    )
    result = await runner.run()
    assert result.ok is True
    assert result.warning == ""


@pytest.mark.asyncio
async def test_analyze_none_returns_empty_warning():
    """When analyze is None, empty result returns warning == ''."""
    from app.graph.tools.sql_query import SelfCorrectingSqlRunner

    async def _gen(hint):
        return "SELECT 1"

    async def _review(sql):
        return {"ok": True, "issues": []}

    async def _execute(sql):
        return []

    runner = SelfCorrectingSqlRunner(
        sql_regen_max=2,
        sql_empty_retry_max=1,
        generate=_gen,
        review=_review,
        execute=_execute,
        analyze=None,
        query="test query",
    )
    result = await runner.run()
    assert result.ok is True
    assert result.warning == ""
```

These 3 tests should go in `test_sql_self_correct_budget.py` since they test `SelfCorrectingSqlRunner` directly (matching that file's pattern).

Actually wait — `test_sql_self_correct_budget.py` tests `SelfCorrectingSqlRunner` without `SqlQueryTool`. So this is the right place.

But the plan file lists tests for `test_sql_query_tool_self_correct_integration.py`. Let me reconsider...

The `test_sql_self_correct_budget.py` file is more appropriate because:
1. It already tests `SelfCorrectingSqlRunner` directly
2. The tests don't need SqlQueryTool
3. They use the same assertion patterns

Let me update the plan.<｜end▁of▁thinking｜>

<｜｜DSML｜｜tool_calls>
<｜｜DSML｜｜invoke name="write">
<｜｜DSML｜｜parameter name="content" string="true"># Analyze Callable — Fix Dead State, Contract, and Test Coverage

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 4 code review issues found in the `analyze` callable integration: dead state `_last_analyze_result`, stale docstring, missing test coverage for 3 paths, and misleading `analyze(sql, hint)` contract.

**Architecture:** All changes are in `SelfCorrectingSqlRunner` and its tests. The misleading contract fix threads user `query` through the runner instead of passing review retry hint, making the callable interface honest. `_last_analyze_result` is wired to actually store the last result. New tests in `test_sql_self_correct_budget.py` directly exercise `SelfCorrectingSqlRunner` with mock analyze callables to cover suspicious-warning, exception, and no-analyze paths.

**Tech Stack:** Python 3.12+, asyncio, pytest

---

## File Structure

| File | Change |
|------|--------|
| `ai_python/app/graph/tools/sql_query.py` | Fix `_last_analyze_result` assignment, fix docstring, thread `query` through runner |
| `ai_python/tests/test_sql_self_correct_budget.py` | Add 3 tests for coverage gaps (analyze warning, exception, None) |

---

### Task 1: Fix `_last_analyze_result` dead state + docstring

**Files:**
- Modify: `ai_python/app/graph/tools/sql_query.py:59,127,184`

- [ ] **Step 1: Wire `_last_analyze_result` assignment**

In `run()` at line 127, after `analyze_warning = (analyze_result or {}).get("warning", "")`, add:
```python
                        self._last_analyze_result = analyze_result or {}
```

Full context (lines 121-138 will look like):
```python
            if not last_rows:
                # SQL passed review — analyze empty result for suspicious patterns
                analyze_warning = ""
                if self._analyze is not None:
                    try:
                        analyze_result = await self._analyze(sql, hint or "")
                        analyze_warning = (analyze_result or {}).get("warning", "")
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
                    warning=analyze_warning,
                )
```

- [ ] **Step 2: Fix stale docstring**

Replace docstring at line 184:
```python
        """Return (generate, review, execute) async callables for the runner."""
```
with:
```python
        """Return (generate, review, execute, analyze) async callables for the runner."""
```

- [ ] **Step 3: Run tests to verify no regression**

```bash
cd ai_python && pytest tests/test_sql_query_tool_self_correct_integration.py tests/test_sql_self_correct_budget.py -v
```

Expected: All existing tests pass.

---

### Task 2: Fix misleading `analyze(sql, hint)` contract

**Files:**
- Modify: `ai_python/app/graph/tools/sql_query.py`

**Root cause:** `SelfCorrectingSqlRunner.run()` calls `self._analyze(sql, hint or "")`, passing the review retry hint — but the `analyze` closure in `SqlQueryTool._make_callables` ignores this parameter and captures `query` from outer scope instead. The `(sql, hint)` contract is not honest.

**Fix:** Add optional `query` parameter to `SelfCorrectingSqlRunner`, thread it from `SqlQueryTool.invoke()`, and pass it to `analyze` instead of the review hint. The `analyze` closure uses the passed `query` parameter instead of capturing from scope.

- [ ] **Step 1: Add `query` parameter to `SelfCorrectingSqlRunner.__init__`**

Replace lines 42-59:
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

with:
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
        query: str = "",
    ) -> None:
        self._sql_regen_max = max(0, int(sql_regen_max))
        self._sql_empty_retry_max = max(0, int(sql_empty_retry_max))
        self._generate = generate
        self._review = review
        self._execute = execute
        self._analyze = analyze
        self._query = query
        self._last_analyze_result: dict[str, Any] = {}
```

- [ ] **Step 2: Change `run()` to pass `self._query` instead of `hint`**

Replace line 126:
```python
                        analyze_result = await self._analyze(sql, hint or "")
```
with:
```python
                        analyze_result = await self._analyze(sql, self._query)
```

- [ ] **Step 3: Update `SqlQueryTool.invoke()` to pass `query` to runner**

Replace lines 267-274:
```python
        runner = SelfCorrectingSqlRunner(
            sql_regen_max=regen_max,
            sql_empty_retry_max=empty_retry_max,
            generate=generate,
            review=review,
            execute=execute,
            analyze=analyze,
        )
```
with:
```python
        runner = SelfCorrectingSqlRunner(
            sql_regen_max=regen_max,
            sql_empty_retry_max=empty_retry_max,
            generate=generate,
            review=review,
            execute=execute,
            analyze=analyze,
            query=query,
        )
```

- [ ] **Step 4: Update analyze closure to use passed `user_query` instead of captured `query`**

Replace lines 243-254:
```python
        async def analyze(sql: str, hint: str) -> dict[str, Any]:
            """Run empty-result analysis when rows == 0."""
            from app.graph.analyze_empty_result import _analyze_empty_heuristic
            from app.graph.sql_query_domain import detect_sql_query_domain

            domain = detect_sql_query_domain(query)
            result = _analyze_empty_heuristic(sql, query, domain)
            return {
                "verdict": result.get("verdict", "legitimate"),
                "warning": result.get("warning", ""),
                "reason": result.get("reason", ""),
            }
```
with:
```python
        async def analyze(sql: str, user_query: str) -> dict[str, Any]:
            """Run empty-result analysis when rows == 0."""
            from app.graph.analyze_empty_result import _analyze_empty_heuristic
            from app.graph.sql_query_domain import detect_sql_query_domain

            domain = detect_sql_query_domain(user_query)
            result = _analyze_empty_heuristic(sql, user_query, domain)
            return {
                "verdict": result.get("verdict", "legitimate"),
                "warning": result.get("warning", ""),
                "reason": result.get("reason", ""),
            }
```

- [ ] **Step 5: Run tests to verify no regression**

```bash
cd ai_python && pytest tests/test_sql_query_tool_self_correct_integration.py tests/test_sql_self_correct_budget.py -v
```

Expected: All existing tests pass (analyze is `None` in all existing tests, so `query` parameter is unused by current tests).

---

### Task 3: Add tests for missing coverage paths

**Files:**
- Modify: `ai_python/tests/test_sql_self_correct_budget.py`

Three tests to append at end of file. They test `SelfCorrectingSqlRunner` directly with mock analyze callables, following the same pattern as existing tests in this file.

- [ ] **Step 1: Add test for warning propagation**

```python
@pytest.mark.asyncio
async def test_analyze_warning_propagates_to_result():
    """When analyze callable returns a warning, SelfCorrectingSqlResult.warning contains it."""

    from app.graph.tools.sql_query import SelfCorrectingSqlResult, SelfCorrectingSqlRunner

    async def _gen(hint):
        return "SELECT 1"

    async def _review(sql):
        return {"ok": True, "issues": []}

    async def _execute(sql):
        return []

    async def _analyze(sql, query):
        return {
            "verdict": "suspicious",
            "warning": "Table 'nonexistent' not found in schema",
            "reason": "missing table",
        }

    runner = SelfCorrectingSqlRunner(
        sql_regen_max=2,
        sql_empty_retry_max=1,
        generate=_gen,
        review=_review,
        execute=_execute,
        analyze=_analyze,
        query="test query",
    )
    result: SelfCorrectingSqlResult = await runner.run()
    assert result.ok is True
    assert result.warning == "Table 'nonexistent' not found in schema"
```

- [ ] **Step 2: Add test for analyze exception safety**

```python
@pytest.mark.asyncio
async def test_analyze_exception_caught_gracefully():
    """When analyze callable raises, runner catches exception and returns empty warning."""

    from app.graph.tools.sql_query import SelfCorrectingSqlResult, SelfCorrectingSqlRunner

    async def _gen(hint):
        return "SELECT 1"

    async def _review(sql):
        return {"ok": True, "issues": []}

    async def _execute(sql):
        return []

    async def _analyze(sql, query):
        raise RuntimeError("analyze exploded")

    runner = SelfCorrectingSqlRunner(
        sql_regen_max=2,
        sql_empty_retry_max=1,
        generate=_gen,
        review=_review,
        execute=_execute,
        analyze=_analyze,
        query="test query",
    )
    result: SelfCorrectingSqlResult = await runner.run()
    assert result.ok is True
    assert result.warning == ""
```

- [ ] **Step 3: Add test for analyze=None behavior**

```python
@pytest.mark.asyncio
async def test_analyze_none_returns_empty_warning():
    """When analyze is None, empty result returns warning == ''."""

    from app.graph.tools.sql_query import SelfCorrectingSqlResult, SelfCorrectingSqlRunner

    async def _gen(hint):
        return "SELECT 1"

    async def _review(sql):
        return {"ok": True, "issues": []}

    async def _execute(sql):
        return []

    runner = SelfCorrectingSqlRunner(
        sql_regen_max=2,
        sql_empty_retry_max=1,
        generate=_gen,
        review=_review,
        execute=_execute,
        analyze=None,
        query="test query",
    )
    result: SelfCorrectingSqlResult = await runner.run()
    assert result.ok is True
    assert result.warning == ""
```

- [ ] **Step 4: Run tests to verify**

```bash
cd ai_python && pytest tests/test_sql_self_correct_budget.py -v
```

Expected output (9 tests total — 6 existing + 3 new):
```
test_sql_regen_within_budget PASSED
test_sql_empty_result_returns_immediately PASSED
test_sql_dedup_short_circuits PASSED
test_sql_empty_result_not_retried PASSED
test_sql_write_blocked_by_readonly PASSED
test_legit_empty_result_not_degraded PASSED
test_analyze_warning_propagates_to_result PASSED
test_analyze_exception_caught_gracefully PASSED
test_analyze_none_returns_empty_warning PASSED
```

---

### Task 4: Commit

- [ ] **Step 1: Run full test suite**

```bash
cd ai_python && pytest tests/test_sql_self_correct_budget.py tests/test_sql_query_tool_self_correct_integration.py tests/test_verify_sql_intent.py -v
```

Expected: All tests pass.

- [ ] **Step 2: Commit**

```bash
git add ai_python/app/graph/tools/sql_query.py ai_python/tests/test_sql_self_correct_budget.py
git commit -m "fix: wire _last_analyze_result, fix docstring, thread query through runner, add analyze tests"
```
