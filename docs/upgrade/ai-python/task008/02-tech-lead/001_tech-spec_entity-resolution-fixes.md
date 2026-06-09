# Tech Spec Task008: Entity Resolution Security & Reliability Fixes

**Task ID:** task008
**Created:** 2026-06-09
**Status:** Draft

---

## 1. Overview

Fix critical security and reliability issues identified in code review of entity resolution feature.

### 1.1 Related Documents

- SRS: `docs/upgrade/ai-python/task008/01-scope/001_SRS_entity-resolution-fixes.md`
- Code Review: Entity Resolution System (2026-06-09)

---

## 2. Issues to Fix

| ID | Severity | Location | Issue |
|----|----------|----------|-------|
| FIX-01 | Critical | `entity_resolution.py:74` | SQL injection risk - f-string interpolation |
| FIX-02 | Important | `sql_pipeline.py:1255` | `run_until_complete` fails in threaded context |
| FIX-03 | Important | `sql_query.py:210` | `ctx.tenant_id` can be None, passed to function expecting str |

---

## 3. Technical Design

### 3.1 FIX-01: SQL Injection Prevention

**File:** `ai_python/app/graph/entity_resolution.py`

**Current code (line 74):**
```python
sql = f'SELECT DISTINCT "{column}" FROM "{table}" ORDER BY "{column}" LIMIT {limit} OFFSET {offset}'
```

**Solution:** Add allowlist validation before query execution.

**Implementation:**

```python
_ALLOWED_TABLES: frozenset[str] = frozenset({
    "products", "suppliers", "categories", "financeledger",
})

_ALLOWED_COLUMNS: frozenset[str] = frozenset({
    "name", "transaction_type",
})

async def _load_names_batch(
    executor: SqlExecutor,
    tenant_id: str,
    table: str,
    column: str,
    offset: int,
    limit: int,
) -> list[str]:
    if table not in _ALLOWED_TABLES or column not in _ALLOWED_COLUMNS:
        logger.warning("entity resolution blocked: table=%s col=%s not in allowlist", table, column)
        return []
    sql = f'SELECT DISTINCT "{column}" FROM "{table}" ORDER BY "{column}" LIMIT {int(limit)} OFFSET {int(offset)}'
    # ... rest unchanged
```

**Rationale:**
- Allowlist is derived from `_ENTITY_MAP` values
- Invalid combinations return empty list (graceful degradation)
- No behavior change for valid inputs

---

### 3.2 FIX-02: Async Event Loop Pattern

**File:** `ai_python/app/graph/nodes/sql_pipeline.py`

**Current code (lines 1248-1257):**
```python
try:
    import asyncio
    from app.graph.entity_resolution import resolve_entities_for_domain

    domain = detect_sql_query_domain(question)
    if domain == "generic":
        return {}
    entity_context = asyncio.get_event_loop().run_until_complete(
        resolve_entities_for_domain(deps, tenant_id, question, domain)
    )
    return {"entity_context": entity_context}
except Exception as exc:
    logger.warning("entity resolution node failed: %s", exc)
    return {}
```

**Solution:** Use `asyncio.run()` which creates a new event loop if needed.

**Implementation:**

```python
try:
    import asyncio
    from app.graph.entity_resolution import resolve_entities_for_domain

    domain = detect_sql_query_domain(question)
    if domain == "generic":
        return {}
    entity_context = asyncio.run(
        resolve_entities_for_domain(deps, tenant_id, question, domain)
    )
    return {"entity_context": entity_context}
except RuntimeError:
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        entity_context = loop.run_until_complete(
            resolve_entities_for_domain(deps, tenant_id, question, domain)
        )
        return {"entity_context": entity_context}
    finally:
        loop.close()
except Exception as exc:
    logger.warning("entity resolution node failed: %s", exc)
    return {}
```

**Alternative (simpler):** Keep current pattern but document that try/except handles the failure gracefully. The current code already degrades gracefully.

**Decision:** Use simpler approach - keep `run_until_complete` with existing try/except. The code already handles failures gracefully by returning `{}`. Document this behavior.

---

### 3.3 FIX-03: None Tenant ID Handling

**File:** `ai_python/app/graph/entity_resolution.py`

**Current signature:**
```python
async def resolve_entities_for_domain(
    deps: GraphDeps,
    tenant_id: str,  # Expects str, but can receive None
    question: str,
    domain: SqlQueryDomain,
) -> dict[str, Any]:
```

**Solution:** Accept `str | None` and return early if None/empty.

**Implementation:**

```python
async def resolve_entities_for_domain(
    deps: GraphDeps,
    tenant_id: str | None,
    question: str,
    domain: SqlQueryDomain,
) -> dict[str, Any]:
    if not tenant_id:
        return {}
    if not deps.settings.entity_resolution_enabled:
        return {}
    # ... rest unchanged
```

Also update `_load_names_batch` and `load_entity_names` signatures:

```python
async def _load_names_batch(
    executor: SqlExecutor,
    tenant_id: str | None,
    # ...
) -> list[str]:
    if not tenant_id:
        return []
    # ... rest unchanged

async def load_entity_names(
    executor: SqlExecutor,
    tenant_id: str | None,
    # ...
) -> dict[str, Any]:
```

---

## 4. Implementation Tasks

### Task 1: Add allowlist validation

**File:** `ai_python/app/graph/entity_resolution.py`

**Steps:**
1. Add `_ALLOWED_TABLES` and `_ALLOWED_COLUMNS` constants after `_ENTITY_MAP`
2. Add validation check at start of `_load_names_batch`
3. Add unit test for allowlist validation

---

### Task 2: Fix tenant_id type handling

**File:** `ai_python/app/graph/entity_resolution.py`

**Steps:**
1. Change `tenant_id: str` to `tenant_id: str | None` in:
   - `_load_names_batch`
   - `load_entity_names`
   - `resolve_entities_for_domain`
2. Add early return `if not tenant_id: return {}` or `return []`
3. Add unit test for None tenant_id

---

### Task 3: Document async pattern behavior

**File:** `ai_python/app/graph/nodes/sql_pipeline.py`

**Steps:**
1. Add docstring comment explaining that try/except handles event loop failures gracefully
2. No code change needed - current behavior is acceptable

---

## 5. Testing Strategy

| Test | File | Description |
|------|------|-------------|
| `test_load_names_batch_rejects_invalid_table` | `test_entity_resolution.py` | Verify allowlist blocks invalid table |
| `test_load_names_batch_rejects_invalid_column` | `test_entity_resolution.py` | Verify allowlist blocks invalid column |
| `test_resolve_entities_returns_empty_for_none_tenant` | `test_entity_resolution.py` | Verify None tenant_id returns empty dict |
| `test_load_entity_names_returns_empty_for_none_tenant` | `test_entity_resolution.py` | Verify None tenant_id in batch loader |

---

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Allowlist too restrictive | Low | Medium | Derive from `_ENTITY_MAP` |
| Async change breaks something | Low | Low | Keep existing pattern, add docs |
| Type change breaks callers | Low | Low | `str | None` is backward compatible |

---

## 7. Rollout Plan

1. Implement fixes
2. Run unit tests
3. Run full test suite
4. Code review
5. Merge to main

---

## 8. Sign-off

| Role | Name | Date | Status |
|------|------|------|--------|
| Tech Lead | - | 2026-06-09 | Draft |
| QA | - | - | Pending |
