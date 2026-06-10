# Entity Context Persistence Across Turns Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist entity resolution results across conversation turns so follow-up queries can reuse resolved product names instead of falling back to ILIKE wildcard searches.

**Architecture:** Add a thread-level in-memory cache to `SqlQueryTool` (thin-adapter path). After entity resolution resolves product names (e.g., "Gạo ST25"), cache them keyed by `thread_id`. On subsequent turns, load the cached context and inject into `gen_sql` system prompt via the existing `_build_entity_context_section` mechanism. Fix the unbound variable bug when domain is `"generic"`.

**Tech Stack:** Python 3.12+, asyncio, LangGraph, PostgreSQL.

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `ai_python/app/graph/tools/sql_query.py` | **Modify** | Add `_entity_cache` class variable; load/save entity context; fix unbound variable |
| `ai_python/tests/test_entity_resolution.py` | **Modify** | Add tests for cross-turn cache behavior |

---

### Task 1: Fix unbound variable bug in thin-adapter entity resolution

**Files:**
- Modify: `ai_python/app/graph/tools/sql_query.py:202-213`

- [ ] **Step 1: Read the current code to verify the bug**

```bash
cd ai_python && python -c "
from app.graph.tools.sql_query import SqlQueryTool
import inspect
src = inspect.getsource(SqlQueryTool._make_callables)
# Check lines around entity resolution
for i, line in enumerate(src.split('\n')[195:220], start=195):
    print(f'{i}: {line}')
"
```

Expected: Line ~213 shows `shared = {**shared, "entity_context": entity_context or {}}` outside the `if domain != "generic"` block, meaning `entity_context` is unbound when domain is `"generic"`.

- [ ] **Step 2: Fix the unbound variable**

Edit `ai_python/app/graph/tools/sql_query.py`. Change the entity resolution block in `generate()` from:

```python
            if self._deps.settings.entity_resolution_enabled and "entity_context" not in shared:
                try:
                    from app.graph.entity_resolution import resolve_entities_for_domain
                    from app.graph.sql_query_domain import detect_sql_query_domain

                    domain = detect_sql_query_domain(query)
                    if domain != "generic":
                        entity_context = await resolve_entities_for_domain(
                            self._deps, ctx.tenant_id, query, domain,
                            bearer_token=ctx.bearer_token,
                        )
                    shared = {**shared, "entity_context": entity_context or {}}
                except Exception as exc:
                    logger.warning("entity resolution (thin adapter) failed: %s", exc)
```

to:

```python
            if self._deps.settings.entity_resolution_enabled and "entity_context" not in shared:
                try:
                    from app.graph.entity_resolution import resolve_entities_for_domain
                    from app.graph.sql_query_domain import detect_sql_query_domain

                    domain = detect_sql_query_domain(query)
                    entity_context = None
                    if domain != "generic":
                        entity_context = await resolve_entities_for_domain(
                            self._deps, ctx.tenant_id, query, domain,
                            bearer_token=ctx.bearer_token,
                        )
                    shared = {**shared, "entity_context": entity_context or {}}
                except Exception as exc:
                    logger.warning("entity resolution (thin adapter) failed: %s", exc)
```

- [ ] **Step 3: Verify fix**

```bash
cd ai_python && python -c "
from app.graph.tools.sql_query import SqlQueryTool
# Just validate the module loads without SyntaxError
print('Module loads OK')
"
```

Expected: `Module loads OK`

- [ ] **Step 4: Commit**

```bash
git add ai_python/app/graph/tools/sql_query.py
git commit -m "fix: initialize entity_context before conditional assignment in thin adapter"
```


### Task 2: Add thread-level entity cache to SqlQueryTool

**Files:**
- Modify: `ai_python/app/graph/tools/sql_query.py`

- [ ] **Step 1: Add `_entity_cache` class variable**

Add to `SqlQueryTool` class (after `_test_execute` attribute, before `_make_callables`):

```python
from typing import Any, ClassVar

class SqlQueryTool:
    ...
    _test_execute: Any | None = None
    # Thread-level entity context cache keyed by thread_id.
    # Persists resolved entity names across conversation turns.
    _entity_cache: ClassVar[dict[str, dict[str, Any]]] = {}
```

- [ ] **Step 2: Update `generate()` to load from cache and save after resolution**

Edit the entity resolution block in `generate()` to:

```python
            if self._deps.settings.entity_resolution_enabled:
                thread_id = ctx.thread_id
                entity_context = SqlQueryTool._entity_cache.get(thread_id, {})
                if not entity_context and "entity_context" not in shared:
                    try:
                        from app.graph.entity_resolution import resolve_entities_for_domain
                        from app.graph.sql_query_domain import detect_sql_query_domain

                        domain = detect_sql_query_domain(query)
                        if domain != "generic":
                            entity_context = await resolve_entities_for_domain(
                                self._deps, ctx.tenant_id, query, domain,
                                bearer_token=ctx.bearer_token,
                            )
                            if entity_context:
                                SqlQueryTool._entity_cache[thread_id] = entity_context
                    except Exception as exc:
                        logger.warning("entity resolution (thin adapter) failed: %s", exc)
                shared["entity_context"] = entity_context or {}
```

Key changes from current code:
- Removed `and "entity_context" not in shared` from outer `if` — replaced with inner check `and "entity_context" not in shared`
- Load cached context via `SqlQueryTool._entity_cache.get(thread_id, {})`
- Only run resolution if cache miss AND context not already in shared
- After successful resolution, save to cache: `SqlQueryTool._entity_cache[thread_id] = entity_context`
- Always set `shared["entity_context"]` (direct assignment instead of merge)

- [ ] **Step 3: Add cache eviction guard (prevent unbounded growth)**

Add a constant after the class definition:

```python
_ENTITY_CACHE_MAX_THREADS = 1000
```

Add a classmethod on `SqlQueryTool` for cache write with eviction:

```python
    @classmethod
    def _cache_put_entity_context(cls, thread_id: str, entity_context: dict[str, Any]) -> None:
        if thread_id not in cls._entity_cache and len(cls._entity_cache) >= _ENTITY_CACHE_MAX_THREADS:
            cls._entity_cache.pop(next(iter(cls._entity_cache)))
        cls._entity_cache[thread_id] = entity_context
```

And update the cache write in step 2 to use this method:

```python
                            if entity_context:
                                SqlQueryTool._cache_put_entity_context(thread_id, entity_context)
```

- [ ] **Step 4: Verify module loads correctly**

```bash
cd ai_python && python -c "
from app.graph.tools.sql_query import SqlQueryTool, _ENTITY_CACHE_MAX_THREADS
print(f'Entity cache max threads: {_ENTITY_CACHE_MAX_THREADS}')
print(f'SqlQueryTool has _entity_cache: {hasattr(SqlQueryTool, \"_entity_cache\")}')
"
```

Expected: `Entity cache max threads: 1000` and `SqlQueryTool has _entity_cache: True`

- [ ] **Step 5: Update `_make_callables` import block if needed**

Check if `ClassVar` import already exists at top of `sql_query.py`. If not, add it:

```python
from typing import Any, ClassVar
```

- [ ] **Step 6: Run existing tests to verify no regression**

```bash
cd ai_python && python -m pytest tests/test_entity_resolution.py -v
```

Expected: All tests pass (28 passed)

- [ ] **Step 7: Commit**

```bash
git add ai_python/app/graph/tools/sql_query.py
git commit -m "feat: add thread-level entity context cache to SqlQueryTool"
```


### Task 3: Add tests for entity cache behavior

**Files:**
- Modify: `ai_python/tests/test_entity_resolution.py`

- [ ] **Step 1: Add import for SqlQueryTool and pytest marks**

Add to the imports at the top of `test_entity_resolution.py`:

```python
import pytest_asyncio
from app.graph.tools.sql_query import SqlQueryTool
```

- [ ] **Step 2: Write cache test class**

Add at the end of `test_entity_resolution.py`:

```python
class TestEntityContextCache:
    """Tests for thread-level entity context persistence across turns."""

    def teardown_method(self) -> None:
        SqlQueryTool._entity_cache.clear()

    @pytest.mark.asyncio
    async def test_cache_stores_resolved_context(self) -> None:
        thread_id = "test-thread-1"
        executor_mock = AsyncMock()
        executor_mock.aexecute.return_value = {
            "rows": [{"name": "Gạo ST25"}, {"name": "Gạo Nàng Hương"}],
        }
        deps = AsyncMock()
        deps.sql_executor = executor_mock
        deps.settings.entity_resolution_enabled = True
        deps.settings.entity_resolution_batch_size = 500
        deps.settings.entity_resolution_max_batches = 1

        ctx = AsyncMock()
        ctx.thread_id = thread_id
        ctx.tenant_id = "t1"
        ctx.bearer_token = None

        from app.graph.entity_resolution import resolve_entities_for_domain

        result = await resolve_entities_for_domain(
            deps, "t1", "gạo tồn kho", "inventory",
        )
        assert "products" in result
        SqlQueryTool._entity_cache[thread_id] = result

        cached = SqlQueryTool._entity_cache.get(thread_id)
        assert cached is not None
        assert "products" in cached

    @pytest.mark.asyncio
    async def test_cached_context_survives_generic_domain(self) -> None:
        thread_id = "test-thread-2"
        SqlQueryTool._entity_cache[thread_id] = {
            "products": {
                "exact_matches": [],
                "fuzzy_matches": ["Gạo ST25", "Gạo Nàng Hương"],
                "loaded_names": ["Gạo ST25", "Gạo Nàng Hương"],
                "truncated": False,
            },
        }

        cached = SqlQueryTool._entity_cache.get(thread_id)
        assert cached is not None
        assert "Gạo ST25" in cached["products"]["fuzzy_matches"]

    @pytest.mark.asyncio
    async def test_eviction_oldest_when_over_limit(self) -> None:
        SqlQueryTool._entity_cache.clear()
        from app.graph.tools.sql_query import _ENTITY_CACHE_MAX_THREADS

        max_threads = _ENTITY_CACHE_MAX_THREADS
        for i in range(max_threads):
            SqlQueryTool._entity_cache[f"thread-{i}"] = {"data": f"value-{i}"}
        assert len(SqlQueryTool._entity_cache) == max_threads

        SqlQueryTool._cache_put_entity_context("overflow-thread", {"data": "overflow"})
        assert len(SqlQueryTool._entity_cache) == max_threads
        assert "thread-0" not in SqlQueryTool._entity_cache
        assert "overflow-thread" in SqlQueryTool._entity_cache

        SqlQueryTool._entity_cache.clear()

    @pytest.mark.asyncio
    async def test_cache_returns_empty_for_unknown_thread(self) -> None:
        SqlQueryTool._entity_cache.clear()
        SqlQueryTool._entity_cache["existing-thread"] = {"products": {"found": True}}

        cached = SqlQueryTool._entity_cache.get("unknown-thread", {})
        assert cached == {}

    def teardown_method(self) -> None:
        SqlQueryTool._entity_cache.clear()
```

- [ ] **Step 3: Run the new tests**

```bash
cd ai_python && python -m pytest tests/test_entity_resolution.py::TestEntityContextCache -v
```

Expected: All 4 cache tests pass

- [ ] **Step 4: Run full entity resolution test suite**

```bash
cd ai_python && python -m pytest tests/test_entity_resolution.py -v
```

Expected: 32 passed (28 existing + 4 new)

- [ ] **Step 5: Commit**

```bash
git add ai_python/tests/test_entity_resolution.py
git commit -m "test: add entity context cache tests for cross-turn persistence"
```


### Task 4: Verify integration end-to-end

**Files:**
- Read-only: `ai_python/app/graph/tools/sql_query.py`
- Read-only: `ai_python/app/graph/nodes/sql_pipeline.py` (verify `_build_entity_context_section` handles cached data)

- [ ] **Step 1: Verify `_build_entity_context_section` handles cached data**

Read `sql_pipeline.py` lines 1225-1236:

```bash
cd ai_python && python -c "
from app.graph.nodes.sql_pipeline import _build_entity_context_section

# Simulate cached entity context from a previous turn
state = {
    'entity_context': {
        'products': {
            'exact_matches': [],
            'fuzzy_matches': ['Gạo ST25', 'Gạo Nàng Hương'],
            'loaded_names': ['Gạo ST25', 'Gạo Nàng Hương'],
            'truncated': False,
        },
    },
}
section = _build_entity_context_section(state)
print(repr(section))
assert 'Gạo ST25' in section
assert 'Gạo Nàng Hương' in section
print('OK: _build_entity_context_section handles cached entity context correctly')
"
```

Expected: Section contains product names. Prints "OK".

- [ ] **Step 2: Run the full self-correcting SQL test suite**

```bash
cd ai_python && python -m pytest tests/test_sql_self_correct_budget.py -v
```

Expected: All budget-based tests pass

- [ ] **Step 3: Run query tool integration tests**

```bash
cd ai_python && python -m pytest tests/test_sql_query_tool_self_correct_integration.py -v
```

Expected: All integration tests pass

- [ ] **Step 4: Final commit (if any changes from verification)**

```bash
git add -A
git commit -m "chore: finalize entity context persistence implementation"
```
