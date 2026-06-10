# Test Plan Task008: Entity Resolution Security & Reliability Fixes

**Task ID:** task008
**Created:** 2026-06-09
**Status:** Draft

---

## 1. Overview

Test plan for verifying security and reliability fixes to entity resolution module.

### 1.1 Related Documents

- SRS: `docs/upgrade/ai-python/task008/01-scope/001_SRS_entity-resolution-fixes.md`
- Tech Spec: `docs/upgrade/ai-python/task008/02-tech-lead/001_tech-spec_entity-resolution-fixes.md`

---

## 2. Test Scope

| Fix ID | Description | Test Type |
|--------|-------------|-----------|
| FIX-01 | SQL injection prevention via allowlist | Unit |
| FIX-02 | Async pattern documentation | N/A (no code change) |
| FIX-03 | None tenant_id handling | Unit |

---

## 3. Test Cases

### 3.1 FIX-01: Allowlist Validation

#### TC-01: Reject invalid table name

**File:** `ai_python/tests/test_entity_resolution.py`
**Class:** `TestLoadNamesBatch`
**Method:** `test_rejects_invalid_table`

```python
@pytest.mark.asyncio
async def test_rejects_invalid_table(self) -> None:
    executor = AsyncMock()
    result = await _load_names_batch(
        executor, "t1", "users", "name", 0, 500
    )
    assert result == []
    executor.aexecute.assert_not_awaited()
```

**Expected:** Returns empty list without executing query.

---

#### TC-02: Reject invalid column name

**File:** `ai_python/tests/test_entity_resolution.py`
**Class:** `TestLoadNamesBatch`
**Method:** `test_rejects_invalid_column`

```python
@pytest.mark.asyncio
async def test_rejects_invalid_column(self) -> None:
    executor = AsyncMock()
    result = await _load_names_batch(
        executor, "t1", "products", "password", 0, 500
    )
    assert result == []
    executor.aexecute.assert_not_awaited()
```

**Expected:** Returns empty list without executing query.

---

#### TC-03: Accept valid table and column

**File:** `ai_python/tests/test_entity_resolution.py`
**Class:** `TestLoadNamesBatch`
**Method:** `test_accepts_valid_table_and_column` (existing test covers this)

**Expected:** Query executes and returns results.

---

### 3.2 FIX-03: None Tenant ID Handling

#### TC-04: resolve_entities_for_domain returns empty for None tenant_id

**File:** `ai_python/tests/test_entity_resolution.py`
**Class:** `TestResolveEntitiesForDomain`
**Method:** `test_returns_empty_for_none_tenant_id`

```python
@pytest.mark.asyncio
async def test_returns_empty_for_none_tenant_id(self) -> None:
    deps = AsyncMock()
    deps.settings.entity_resolution_enabled = True
    result = await resolve_entities_for_domain(
        deps, None, "some question", "inventory",
    )
    assert result == {}
```

**Expected:** Returns empty dict without calling executor.

---

#### TC-05: resolve_entities_for_domain returns empty for empty string tenant_id

**File:** `ai_python/tests/test_entity_resolution.py`
**Class:** `TestResolveEntitiesForDomain`
**Method:** `test_returns_empty_for_empty_tenant_id`

```python
@pytest.mark.asyncio
async def test_returns_empty_for_empty_tenant_id(self) -> None:
    deps = AsyncMock()
    deps.settings.entity_resolution_enabled = True
    result = await resolve_entities_for_domain(
        deps, "", "some question", "inventory",
    )
    assert result == {}
```

**Expected:** Returns empty dict without calling executor.

---

#### TC-06: load_entity_names returns empty for None tenant_id

**File:** `ai_python/tests/test_entity_resolution.py`
**Class:** `TestLoadEntityNames`
**Method:** `test_returns_empty_for_none_tenant_id`

```python
@pytest.mark.asyncio
async def test_returns_empty_for_none_tenant_id(self) -> None:
    executor = AsyncMock()
    result = await load_entity_names(
        executor, None, "products", "name",
        keywords=["test"], batch_size=5, max_batches=3,
    )
    assert result["exact_matches"] == []
    assert result["loaded_names"] == []
    executor.aexecute.assert_not_awaited()
```

**Expected:** Returns empty result without executing query.

---

#### TC-07: _load_names_batch returns empty for None tenant_id

**File:** `ai_python/tests/test_entity_resolution.py`
**Class:** `TestLoadNamesBatch`
**Method:** `test_returns_empty_for_none_tenant_id`

```python
@pytest.mark.asyncio
async def test_returns_empty_for_none_tenant_id(self) -> None:
    executor = AsyncMock()
    result = await _load_names_batch(
        executor, None, "products", "name", 0, 500
    )
    assert result == []
    executor.aexecute.assert_not_awaited()
```

**Expected:** Returns empty list without executing query.

---

## 4. Regression Tests

### 4.1 Existing Tests Must Pass

```bash
cd ai_python && pytest tests/test_entity_resolution.py -v
```

**Expected:** All existing tests pass.

---

### 4.2 Full Test Suite

```bash
cd ai_python && pytest -x
```

**Expected:** No regressions.

---

## 5. Test Execution Checklist

| # | Test | Status |
|---|------|--------|
| TC-01 | Reject invalid table | Pending |
| TC-02 | Reject invalid column | Pending |
| TC-03 | Accept valid table/column | Pending (existing) |
| TC-04 | None tenant_id in resolve_entities | Pending |
| TC-05 | Empty tenant_id in resolve_entities | Pending |
| TC-06 | None tenant_id in load_entity_names | Pending |
| TC-07 | None tenant_id in _load_names_batch | Pending |
| Regression | Existing entity resolution tests | Pending |
| Regression | Full test suite | Pending |

---

## 6. Acceptance Criteria

- [ ] All new test cases pass
- [ ] All existing tests continue to pass
- [ ] No regressions in full test suite

---

## 7. Sign-off

| Role | Name | Date | Status |
|------|------|------|--------|
| QA | - | 2026-06-09 | Draft |
