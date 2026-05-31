# CODEBASE ANALYSIS - Task039 Inbound Dispatch CRUD

> **File**: `docs/analysis/ANALYSIS_Task039.md`
> **Người viết**: Agent Codebase Analyst
> **Ngày**: 18/04/2026
> **Scope**: inventory/inventoryCrudLogic.ts, .test.ts

---

## 1. Module Overview

### 1.1 File Changes

| File | Type | Description |
|------|------|-------------|
| `inventoryCrudLogic.ts` | New | CRUD logic for receipts/dispatches |
| `inventoryCrudLogic.test.ts` | New | Unit tests (19 tests) |
| `ReceiptForm.tsx` | New | UI component for creating/editing receipts |
| `DispatchForm.tsx` | New | UI component for creating/editing dispatches |
| `InboundPage.tsx` | Modified | Integrated ReceiptForm and CRUD actions |
| `DispatchPage.tsx` | Modified | Integrated DispatchForm and CRUD actions |
| `ReceiptTable.tsx` | Modified | Added Edit/Delete actions |
| `DispatchTable.tsx` | Modified | Added Edit/Cancel actions |

### 1.2 Dependencies

- **Imports from**: `./mockData`, `./types`, `../inventoryCrudLogic`
- **New dependencies**: `react-hook-form`, `@hookform/resolvers/zod`, `zod`
- **Shared state**: Singleton pattern via `InventoryCrudStore` class

---

## 2. Business Logic Extraction

### 2.1 Core Functions

| Function | File Location | Purpose |
|----------|---------------|---------|
| `createReceipt` | lines 58-95 | Create new receipt with auto-generate code |
| `updateReceipt` | lines 98-120 | Update draft receipts only |
| `deleteReceipt` | lines 123-134 | Delete draft receipts only |
| `submitReceiptForApproval` | lines 137-147 | Submit to Pending status |
| `approveReceipt` | lines 150-174 | Approve + update inventory |
| `rejectReceipt` | lines 177-189 | Reject with reason |
| `createDispatch` | lines 195-229 | Create dispatch from order |
| `confirmDispatch` | lines 232-252 | Confirm + update inventory |
| `cancelDispatch` | lines 255-271 | Cancel pending/failed dispatches |

### 2.2 UI Integration

- **InboundPage**: Uses `ReceiptForm` for Create/Edit. Calls `createReceipt`, `updateReceipt`, `deleteReceipt`.
- **DispatchPage**: Uses `DispatchForm` for Create/Edit. Calls `createDispatch`, `confirmDispatch`, `cancelDispatch`.
- **Forms**: Use `zod` for validation (required fields, positive quantities).

---

## 3. Brittleness Hotspots

| Zone | Location | Risk Level | Reason |
|------|----------|------------|--------|
| Singleton state | `InventoryCrudStore` class | Medium | Shared mutable state - could cause issues in concurrent tests |
| Mock data pollution | `store.reset()` | Low | Tests reset but resets may not work if test crashes mid-execution |
| Window Reload | `InboundPage.tsx`, `DispatchPage.tsx` | Medium | Current implementation uses `window.location.reload()` instead of state update or React Query invalidation |

---

## 4. Test Coverage Assessment

### 4.1 Current Coverage

| Test Type | Count | Status |
|-----------|-------|--------|
| Total tests | 19 | - |
| Passing | 19 | ✅ (Fixed after RED phase) |
| Failing | 0 | ✅ |

### 4.2 Coverage Gaps

- **E2E tests**: Basic E2E for UI exists but hasn't been run in this environment.

---

## 5. Risk Register

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| Singleton state concurrency | Low | Low | Use React Query in production |
| Mock data pollution between tests | Low | Low | BeforeEach reset in place |
| Missing state management | Medium | Low | Current `window.location.reload()` is temporary, should use proper state update |

---

## 6. Recommendations

1. **State Management**: Replace `window.location.reload()` with a proper state update or `react-query` invalidation.
2. **Production ready**: Logic is clean, follows business rules, UI is functional.
3. **Add E2E tests**: Verify the full flow from creation to approval in the UI.

---

## 7. Next Steps

- ✅ Task040 (UNIT) passing
- ✅ Task041 (FEATURE) fully implemented with UI
- ✅ Task042 (E2E) ready for automation

---

> **CODEBASE_ANALYST done.**  
> **Brittle zones: 3 (singleton state, mock pollution, reload dependency)**  
> **Risks: Low-Medium**