# Tech Spec — Cashflow Three Pages Upgrade

## Context

- Source SRS: `docs/frontend/srs/021_cashflow-three-pages-upgrade.md`.
- Scope: only `TransactionsPage`, `DebtPage`, `LedgerPage` and their local cashflow components/API helpers.
- CodeGraph preflight: `status --json`, `context` for `cashflow`, and direct source verification.

## Implementation Slices

### 1. Transactions Filters and Visual Cleanup

Files:
- Modify `frontend/mini-erp/src/features/cashflow/pages/TransactionsPage.tsx`
- Modify `frontend/mini-erp/src/features/cashflow/components/TransactionToolbar.tsx`
- Modify `frontend/mini-erp/src/features/cashflow/components/TransactionTable.tsx`
- Modify `frontend/mini-erp/src/features/cashflow/components/TransactionFormDialog.tsx`

Changes:
- Add `dateFrom` / `dateTo` state and include both in `getCashTransactionsList` filters.
- Replace status/type selects in `TransactionToolbar` with neutral pill tabs.
- Keep date inputs in toolbar with `Calendar` icon and compact height.
- Replace delete `window.confirm` with Sonner toast action confirmation.
- Replace raw pagination buttons with shadcn `Button variant="outline" size="sm"`.
- Change title typography to `font-semibold tracking-tight`, remove uppercase/font-black.
- Change stat cards to `min-w-50`; replace paragraph footnote with compact `(i)` indicator.
- Update status badges to green/amber/red neutral fills.
- Remove client-generated `transactionCode` default in create mode and do not render code input.

### 2. Debts Real API Wiring

Files:
- Create `frontend/mini-erp/src/features/cashflow/api/debtsApi.ts`
- Create `frontend/mini-erp/src/features/cashflow/hooks/useDebtsListQuery.ts`
- Modify `frontend/mini-erp/src/features/cashflow/pages/DebtPage.tsx`
- Modify `frontend/mini-erp/src/features/cashflow/components/DebtToolbar.tsx`
- Modify `frontend/mini-erp/src/features/cashflow/components/DebtTable.tsx`
- Modify `frontend/mini-erp/src/features/cashflow/components/DebtFormDialog.tsx`
- Modify `frontend/mini-erp/src/lib/data-table-layout.ts`

Changes:
- Implement `/api/v1/debts` list/detail/create/patch helpers.
- Add debounced TanStack Query hook with `PAGE_SIZE = 20`, search, status, partner type, due date range, page.
- Replace mock local-state CRUD in `DebtPage` with real query + mutations + query invalidation.
- Remove delete action from toolbar/table because no DELETE endpoint exists.
- Add loading and error overlays.
- Add footer pagination matching other record tables.
- Add `Hạn tất toán` column and overdue visual state.
- Normalize colors to slate/green/rose and remove strong blue/purple accents.
- Keep create/update form API-safe: POST requires the matching `customerId` or `supplierId`; PATCH sends supported fields only.

### 3. Ledger Layout and Totals

Files:
- Modify `frontend/mini-erp/src/features/cashflow/pages/LedgerPage.tsx`
- Modify `frontend/mini-erp/src/features/cashflow/components/LedgerToolbar.tsx`
- Modify `frontend/mini-erp/src/features/cashflow/components/LedgerTable.tsx`

Changes:
- Use full-height `min-h-0 overflow-hidden` wrapper.
- Remove toolbar `mb-4`.
- Replace raw pagination buttons with shadcn buttons.
- Add `TableFooter` totals row for amount, debit, credit, and final balance when data exists.

## Data Contracts

Debt list query:

```ts
type GetDebtsListParams = {
  partnerType?: "Customer" | "Supplier"
  status?: "InDebt" | "Cleared"
  search?: string
  dueDateFrom?: string
  dueDateTo?: string
  page?: number
  limit?: number
}
```

Debt create body:

```ts
type DebtCreateBody = {
  partnerType: "Customer" | "Supplier"
  customerId?: number | null
  supplierId?: number | null
  totalAmount: number
  paidAmount?: number
  dueDate?: string | null
  notes?: string | null
}
```

## Verification

- Run focused tests for new cashflow logic.
- Run `npm run build`.
- Run `npm run lint`.
- Inspect `/cashflow/transactions`, `/cashflow/debt`, `/cashflow/ledger` if local dev server is available.
