# Code Review Task008: Entity Resolution Security & Reliability Fixes

**Task ID:** task008
**Reviewer:** Code Review Agent
**Date:** 2026-06-09
**Status:** Approved

---

## 1. Summary

Review of security and reliability fixes for entity resolution module.

### 1.1 Related Documents

- SRS: `docs/upgrade/ai-python/task008/01-scope/001_SRS_entity-resolution-fixes.md`
- Tech Spec: `docs/upgrade/ai-python/task008/02-tech-lead/001_tech-spec_entity-resolution-fixes.md`
- Test Plan: `docs/upgrade/ai-python/task008/04-tester/001_test-plan_entity-resolution-fixes.md`

---

## 2. Changes Reviewed

| File | Change |
|------|--------|
| `ai_python/app/graph/entity_resolution.py` | Added allowlist validation, fixed tenant_id types |
| `ai_python/tests/test_entity_resolution.py` | Added 7 new test cases |

---

## 3. Review Findings

### 3.1 Strengths

- **Allowlist over blocklist** for SQL injection prevention -- the correct pattern
- **`int()` coercion** on `limit`/`offset` as defense-in-depth
- **Consistent `str | None`** type widening across all 3 functions
- **Tests assert `assert_not_awaited()`** -- verifying no DB call is made, not just empty return
- Both callers (`sql_pipeline.py`, `sql_query.py`) are compatible with the type changes

### 3.2 Critical Issues

None.

### 3.3 Important Issues (Fixed)

**I-1: Allowlist should be derived from `_ENTITY_MAP`, not maintained separately.**

**Original:** Hardcoded allowlist values.

**Fix Applied:** Allowlists now derived from `_ENTITY_MAP`:

```python
_ALLOWED_TABLES: frozenset[str] = frozenset(
    e["table"] for entries in _ENTITY_MAP.values() for e in entries
)

_ALLOWED_COLUMNS: frozenset[str] = frozenset(
    e["column"] for entries in _ENTITY_MAP.values() for e in entries
)
```

This makes the allowlist self-maintaining and eliminates "forgot to update" bugs.

### 3.4 Minor Issues (Noted)

**M-1:** No empty-string `tenant_id` test for `_load_names_batch` and `load_entity_names`. The `if not tenant_id` guard handles both, but symmetry in test coverage would be more robust.

**M-2:** Check ordering in `_load_names_batch` -- `tenant_id` guard runs before allowlist check, so an invalid table with `None` tenant silently returns `[]` without the warning log. Consider swapping order if you want the allowlist warning regardless.

---

## 4. Test Results

| Test Suite | Result |
|------------|--------|
| `test_entity_resolution.py` | 20 passed |
| Related SQL tests | 40 passed |

---

## 5. Assessment

**Status:** Approved

**Rationale:**
- All critical issues from original code review are addressed
- Security fix (allowlist) is sound and self-maintaining
- Type changes are compatible with all callers
- Tests are meaningful and comprehensive

**Recommendation:** Ready to merge.

---

## 6. Sign-off

| Role | Name | Date | Status |
|------|------|------|--------|
| Code Reviewer | Agent | 2026-06-09 | Approved |
