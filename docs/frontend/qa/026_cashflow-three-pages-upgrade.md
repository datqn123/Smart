# QA Spec — Cashflow Three Pages Upgrade

## Scope

Validate SRS `docs/frontend/srs/021_cashflow-three-pages-upgrade.md` across:
- Giao dịch thu chi
- Sổ nợ đối tác
- Sổ cái tài chính

## Expected Failing Tests Before Coding

### Debt API Helper

- `getDebtsList` builds `/api/v1/debts` with `search`, `partnerType`, `status`, `dueDateFrom`, `dueDateTo`, `page`, `limit`.
- `postDebt` sends JSON to `POST /api/v1/debts`.
- `patchDebt` sends JSON to `PATCH /api/v1/debts/{id}`.
- `getDebtById` calls `GET /api/v1/debts/{id}`.

### Debt Form Mapping

- Create mode validates `paidAmount <= totalAmount`.
- Create mode requires `customerId` when `partnerType = Customer`.
- Create mode requires `supplierId` when `partnerType = Supplier`.
- Edit mode PATCH excludes unsupported `partnerName` and `debtCode`.

### Debt Table

- Table renders `Hạn tất toán`.
- Overdue debt with `status !== Cleared` uses rose emphasized date text.
- Empty state uses the new column count.
- Delete button is absent.

### Ledger Table

- Footer is rendered only when rows exist.
- Footer totals amount, debit, credit, and final balance are correct.
- Empty state does not render footer.

### Transactions UI

- Toolbar renders pill tabs for type/status and date range inputs.
- `dateFrom`/`dateTo` reset page and flow into API filters.
- Delete uses toast action confirmation, not `window.confirm`.
- Create form does not include client-generated transaction code.

## Manual QA

- Open `/cashflow/transactions`: check pills, date range, neutral stat cards, pagination buttons, and create dialog.
- Open `/cashflow/debt`: verify data loads from API, filters call API, no delete action, due date column appears, footer pagination is aligned.
- Open `/cashflow/ledger`: verify page fills height without double spacing and totals footer stays inside the table.

## Commands

```bash
npm run test -- src/features/cashflow
npm run build
npm run lint
```
