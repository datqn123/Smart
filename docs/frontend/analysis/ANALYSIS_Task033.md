# 📊 CODEBASE ANALYSIS - Task033

> **Task:** Standardize Inventory Tables (Dispatch & Stock)
> **Scope:** `DispatchPage`, `DispatchTable`, `StockPage`, `StockTable`

## 1. Inventory & Entry Points
- `src/features/inventory/pages/DispatchPage.tsx`
- `src/features/inventory/pages/StockPage.tsx`
- `src/features/inventory/components/DispatchTable.tsx`
- `src/features/inventory/components/StockTable.tsx`

## 2. Module Mapping
The standard table pattern consists of:
- `Page Container` (flex-col, h-full, p-4..8, gap-4..5)
- `Filter Bar` (bg-white, rounded-lg, border-slate-200)
- `Table Wrapper` (flex-col, rounded-xl, border-slate-200/60, shadow-md, overflow-hidden)
- `Standalone Header` (bg-slate-50, border-b, separate from the body scroll container)
- `Scrollable Body` (overflow-y-auto, relative)

## 3. Business Logic Extraction
- **Selection State:** `StockPage` manages the selection of multiple SKU items via `selectedIds` state. This state is passed down to `StockTable` and `StockTableHeader`.
- **Infinite Scrolling:** Both pages use `IntersectionObserver` to trigger `loadMore` functionality. This logic is preserved in the new layout structure.

## 4. Brittleness Hotspots
- **Cell Width Alignment:** The standalone header requires precise matching of column widths (`w-[px]`) with the body table cells.
- **Scroll Synchronization:** Incorrect parent height (`min-h-0`, `flex-1`) can cause the header to scroll away or the body to not scroll at all.

## 5. Coverage Gaps
- Created `DispatchPage.test.tsx` and `StockPage.test.tsx` to verify the layout structure.
- Created `e2e/dispatch-standard.spec.ts` and `e2e/stock-standard.spec.ts` for visual validation.

## 6. Risks
- **Mobile View:** The card layout for mobile must be checked to ensure that the new `flex-col` page container doesn't disrupt its vertical scroll.
- **Z-Index:** The action column (`sticky right-0`) must be at the correct z-index to stay above other row content but below the header.

---
*Analysis completed by Agent CODEBASE_ANALYST.*
