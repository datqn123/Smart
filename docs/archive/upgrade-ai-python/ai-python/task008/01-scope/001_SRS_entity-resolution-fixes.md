# SRS Task008: Entity Resolution Security & Reliability Fixes

**Task ID:** task008
**Created:** 2026-06-09
**Priority:** Critical
**Status:** Draft

---

## 1. Background

Code review of entity resolution feature (commits `39fa4fcc..124a5857`) identified security and reliability issues that must be fixed before production deployment.

### 1.1 Related Documents

- Code Review: Entity Resolution System (2026-06-09)
- Original Spec: `docs/superpowers/specs/002_entity-resolution-step.md`
- Implementation Plan: `docs/superpowers/plans/2026-06-09-entity-resolution-step.md`

---

## 2. Problem Statement

### 2.1 Critical: SQL Injection Risk

**Location:** `ai_python/app/graph/entity_resolution.py:329`

```python
sql = f'SELECT DISTINCT "{column}" FROM "{table}" ORDER BY "{column}" LIMIT {int(limit)} OFFSET {int(offset)}'
```

While `table` and `column` currently come from hardcoded `_ENTITY_MAP`, the f-string interpolation pattern is dangerous. If these values ever come from user input or config, this becomes SQL injection.

### 2.2 Important: Async Event Loop Issues

**Location:** `ai_python/app/graph/nodes/sql_pipeline.py:1255`

```python
entity_context = asyncio.get_event_loop().run_until_complete(
    resolve_entities_for_domain(deps, tenant_id, question, domain)
)
```

This pattern can fail if the event loop is already running in another thread (e.g., when LangGraph runs nodes in a thread pool). The try/except handles failure gracefully, but behavior is non-deterministic.

### 2.3 Important: None Tenant ID Handling

**Location:** `ai_python/app/graph/tools/sql_query.py:209-211`

`ctx.tenant_id` may be `None`, producing `"None"` string when passed to `resolve_entities_for_domain`.

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | SQL queries must use parameterized values or validated allowlist for table/column names | Critical |
| FR-02 | Entity resolution must work correctly in threaded/async environments | Important |
| FR-03 | System must handle `None` tenant_id gracefully without string conversion | Important |
| FR-04 | All fixes must maintain backward compatibility with existing tests | Required |

### 3.2 Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-01 | No regression in entity resolution functionality |
| NFR-02 | All existing tests must continue to pass |
| NFR-03 | Code must follow existing patterns in the codebase |

---

## 4. Acceptance Criteria

### 4.1 FR-01: SQL Injection Prevention

- [ ] `_load_names_batch` validates `table` and `column` against an allowlist before query execution
- [ ] Allowlist is defined as a module-level constant
- [ ] Invalid table/column combinations return empty list without executing query
- [ ] Unit test verifies allowlist validation

### 4.2 FR-02: Async Environment Compatibility

- [ ] Entity resolution node uses `asyncio.run()` instead of `run_until_complete()`
- [ ] OR node is converted to async and uses `await`
- [ ] Integration test verifies node works in threaded context

### 4.3 FR-03: None Tenant ID Handling

- [ ] `resolve_entities_for_domain` returns empty dict when `tenant_id` is `None` or empty
- [ ] Type hint for `tenant_id` parameter is `str | None` or validated before use
- [ ] Unit test covers `None` tenant_id case

### 4.4 FR-04: Backward Compatibility

- [ ] `pytest tests/test_entity_resolution.py` passes
- [ ] `pytest tests/test_sql_subgraph_entity_resolution.py` passes (if exists)
- [ ] Full test suite passes without regressions

---

## 5. Scope

### 5.1 In Scope

- `ai_python/app/graph/entity_resolution.py` - Add allowlist validation
- `ai_python/app/graph/nodes/sql_pipeline.py` - Fix async pattern
- `ai_python/app/graph/tools/sql_query.py` - Handle None tenant_id

### 5.2 Out of Scope

- Changes to entity resolution logic/algorithm
- New features or enhancements
- Documentation updates beyond code comments

---

## 6. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Allowlist too restrictive | Entity resolution fails for valid tables | Review `_ENTITY_MAP` to ensure all entries are in allowlist |
| Async change breaks LangGraph integration | Node fails silently | Test in actual LangGraph execution context |

---

## 7. Dependencies

- Existing entity resolution implementation
- `GraphSettings` configuration
- `sql_executor` interface

---

## 8. Sign-off

| Role | Name | Date | Status |
|------|------|------|--------|
| BA | - | 2026-06-09 | Draft |
| Tech Lead | - | - | Pending |
| QA | - | - | Pending |
