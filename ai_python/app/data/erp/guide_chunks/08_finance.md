## 8. Cash Flow Management

> Requires permission: `can_view_finance`

### 8.1. Cash Transactions

**UI (`TransactionsPage.tsx`):**
- Transaction table with filters: type (Income/Expense), status, date, fund
- Create form: direction, amount, category, date, payment method, fund
- Page-level stats: total income, total expense, balance

#### Create Transaction

```
POST /api/v1/cash-transactions { direction, amount, category, description?, paymentMethod, transactionDate, fundId }
  ↓
Backend CashTransactionService.create():
  1. Validate: direction (Income/Expense), amount > 0, fund exists and Active
  2. Block if status is anything other than "Pending"
  3. Generate code: PT-{year}-{seq} (Income), PC-{year}-{seq} (Expense)
  4. INSERT with status = "Pending", finance_ledger_id = NULL
  ↓
Response: 201 Created
```

#### Complete Transaction — **Ledger Posting Point**

```
PATCH /api/v1/cash-transactions/{id} { status: "Completed" }
  ↓
Backend completeCashTx():
  1. Check not already linked to ledger (idempotent)
  2. Compute signed amount: Income → positive, Expense → negative
  3. Map direction → ledger type: Income → "SalesRevenue", Expense → "OperatingExpense"
  4. INSERT finance ledger with reference_type="CashTransaction"
  5. UPDATE cash transaction with finance_ledger_id and status="Completed"
```

#### Status-Based Rules

| Current Status | Editable Fields | Behavior |
|---|---|---|
| **Pending** | amount, category, description, paymentMethod, transactionDate, status | Full edit. If status→Completed: creates ledger entry |
| **Completed** | status (only "Completed") | Idempotent — no changes |
| **Cancelled** | description only | Can only edit description |

#### Delete Transaction

- Only deletable when status = "Pending" or "Cancelled" **AND** finance_ledger_id IS NULL
- Blocks deletion of Completed or ledger-linked transactions

#### Permissions

- Only creator or Admin can mutate (patch/delete)

### 8.2. Cash Funds

```
GET /api/v1/cash-funds  → returns only Active funds, sorted: default first
POST /api/v1/cash-funds { code, name, isDefault }  (Admin only)
PATCH /api/v1/cash-funds/{id} { isActive?, isDefault? }  (Admin only)
```

**Invariant:** Only ONE default fund at a time. When setting `isDefault=true` → clear all other defaults.

### 8.3. Finance Ledger — Double-Entry Bookkeeping

**UI (`LedgerPage.tsx`):** **Admin only.**

```
GET /api/v1/finance-ledger?dateFrom=&dateTo=&transactionType=&referenceType=&search=&page=&limit=
  ↓
Backend FinanceLedgerService:
  - Defaults to 90-day window if no dates provided
  - Complex CTE query:
    - JOIN salesorders to resolve order_code
    - Compute debit (amount < 0 → -amount) and credit (amount > 0 → amount)
    - Running balance: SUM(amount) OVER (ORDER BY transaction_date ASC, id ASC)
    - Generate transaction_code: SalesOrder → so_code, else → FL-{id}
```

#### Signed Amount Convention

| Type | Amount | Display |
|---|---|---|
| Income / Revenue | Positive (+) | `+X` |
| Expense / COGS | Negative (-) | `-X` |
| Refund | Negative (-) | `-X` |

#### Automatic Ledger Posting Sources (Idempotent)

| Source | Condition | transaction_type | reference_type |
|---|---|---|---|
| Cash Transaction (Income) | Completed | SalesRevenue | CashTransaction |
| Cash Transaction (Expense) | Completed | OperatingExpense | CashTransaction |
| Sales Order (Wholesale) | Delivered + Paid | SalesRevenue | SalesOrder |
| Sales Order (Retail) | Paid | SalesRevenue | SalesOrder |
| Sales Order (Return) | Paid | Refund | SalesOrder |
| Sales Order (Retail Cancel) | Had revenue posted | Refund | SalesOrder |
| Stock Receipt | Approved | PurchaseCost | StockReceipt |
| Stock Dispatch | Delivered | OperatingExpense | StockDispatch |

### 8.4. Partner Debts

> **Note:** Frontend `DebtPage.tsx` currently uses **mock data**, not connected to real API. Backend is fully implemented.

#### Create Debt

```
POST /api/v1/debts { partnerType, customerId?, supplierId?, totalAmount, paidAmount?, dueDate?, notes? }
  ↓
Backend PartnerDebtService.create():
  1. Validate partnerType (Customer/Supplier)
  2. Validate partner exists (customer: non-deleted, supplier: exists)
  3. Validate paidAmount ≤ totalAmount
  4. Auto-determine status: paid ≥ total → "Cleared", else → "InDebt"
  5. Generate code: NO-{year}-{seq}
  6. SET customerId OR supplierId based on partnerType (other is NULL)
```

#### Pay Debt

```
PATCH /api/v1/debts/{id} { totalAmount?, paidAmount?, paymentAmount?, dueDate?, notes? }
  ↓
Backend (only when status = "InDebt"):
  - paymentAmount: incremental add to paidAmount (capped at total)
  - paidAmount: absolute set
  - CANNOT send both paidAmount and paymentAmount in same request
  - Auto-update status: newPaid >= newTotal → "Cleared"
  → When status = "Cleared": lock money fields, only dueDate and notes editable
```

**Permissions:** Only creator can patch debts (no Admin override).

---