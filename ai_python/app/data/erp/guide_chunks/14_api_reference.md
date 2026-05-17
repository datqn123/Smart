## 14. API Reference

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/refresh` | Refresh token |
| POST | `/api/v1/auth/logout` | Logout |
| POST | `/api/v1/auth/password-reset-requests` | Request password reset |

### Users / Employees

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/users` | List employees |
| GET | `/api/v1/users/{userId}` | Employee detail |
| POST | `/api/v1/users` | Create employee |
| PATCH | `/api/v1/users/{userId}` | Edit employee |
| DELETE | `/api/v1/users/{userId}` | Lock employee (soft delete) |
| GET | `/api/v1/users/next-staff-code` | Generate next staff code |

### Products

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/products` | List products |
| GET | `/api/v1/products/{id}` | Product detail |
| POST | `/api/v1/products` | Create product |
| PATCH | `/api/v1/products/{id}` | Edit product |
| DELETE | `/api/v1/products/{id}` | Delete product |
| POST | `/api/v1/products/{id}/images` | Add product image |

### Categories

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/categories` | List as tree |
| GET | `/api/v1/categories/{id}` | Detail + breadcrumb |
| POST | `/api/v1/categories` | Create category |
| PATCH | `/api/v1/categories/{id}` | Edit category |
| DELETE | `/api/v1/categories/{id}` | Soft delete category |

### Suppliers

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/suppliers` | List suppliers |
| POST | `/api/v1/suppliers` | Create supplier |
| PATCH | `/api/v1/suppliers/{id}` | Edit supplier |
| DELETE | `/api/v1/suppliers/{id}` | Delete supplier |
| POST | `/api/v1/suppliers/bulk-delete` | Bulk delete suppliers |

### Customers

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/customers` | List customers |
| POST | `/api/v1/customers` | Create customer |
| PATCH | `/api/v1/customers/{id}` | Edit customer |
| DELETE | `/api/v1/customers/{id}` | Soft delete customer |
| POST | `/api/v1/customers/bulk-delete` | Bulk delete customers |

### Inventory

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/inventory` | List stock |
| GET | `/api/v1/inventory/summary` | Stock KPIs |
| GET | `/api/v1/inventory/{id}` | Stock lot detail |
| PATCH | `/api/v1/inventory/{id}` | Edit stock info |
| PATCH | `/api/v1/inventory/bulk` | Bulk edit stock |

### Stock Receipts

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/stock-receipts` | List receipts |
| GET | `/api/v1/stock-receipts/{id}` | Receipt detail |
| POST | `/api/v1/stock-receipts` | Create receipt |
| PATCH | `/api/v1/stock-receipts/{id}` | Edit draft receipt |
| DELETE | `/api/v1/stock-receipts/{id}` | Delete receipt |
| POST | `/api/v1/stock-receipts/{id}/submit` | Submit for approval |
| POST | `/api/v1/stock-receipts/{id}/approve` | Approve receipt |
| POST | `/api/v1/stock-receipts/{id}/reject` | Reject receipt |

### Stock Dispatchs

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/stock-dispatches` | List dispatches |
| GET | `/api/v1/stock-dispatches/{id}` | Dispatch detail |
| POST | `/api/v1/stock-dispatches` | Create manual dispatch |
| POST | `/api/v1/stock-dispatches/from-order` | Create dispatch from order |
| PATCH | `/api/v1/stock-dispatches/{id}` | Edit dispatch |
| POST | `/api/v1/stock-dispatches/{id}/approve` | Approve dispatch |
| POST | `/api/v1/stock-dispatches/{id}/soft-delete` | Soft delete dispatch |

### Audit Sessions

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/inventory/audit-sessions` | List audit sessions |
| GET | `/api/v1/inventory/audit-sessions/{id}` | Audit session detail |
| POST | `/api/v1/inventory/audit-sessions` | Create audit session |
| PATCH | `/api/v1/inventory/audit-sessions/{id}` | Edit audit session |
| PATCH | `/api/v1/inventory/audit-sessions/{id}/lines` | Enter actual quantities |
| POST | `/api/v1/inventory/audit-sessions/{id}/complete` | Complete audit |
| POST | `/api/v1/inventory/audit-sessions/{id}/approve` | Owner approve |
| POST | `/api/v1/inventory/audit-sessions/{id}/reject` | Owner reject |
| POST | `/api/v1/inventory/audit-sessions/{id}/cancel` | Cancel audit |
| POST | `/api/v1/inventory/audit-sessions/{id}/apply-variance` | Apply variance |
| DELETE | `/api/v1/inventory/audit-sessions/{id}` | Soft delete |

### Sales Orders

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/sales-orders` | List orders |
| GET | `/api/v1/sales-orders/{id}` | Order detail |
| GET | `/api/v1/sales-orders/retail/history` | Retail history |
| POST | `/api/v1/sales-orders` | Create wholesale/return order |
| POST | `/api/v1/sales-orders/retail/checkout` | POS checkout |
| POST | `/api/v1/sales-orders/retail/voucher-preview` | Preview voucher |
| PATCH | `/api/v1/sales-orders/{id}` | Edit order |
| POST | `/api/v1/sales-orders/{id}/cancel` | Cancel order |

### POS & Vouchers

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/pos/products` | Search POS products |
| GET | `/api/v1/vouchers` | List vouchers |
| GET | `/api/v1/vouchers/{id}` | Voucher detail |

### Cashflow

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/cash-transactions` | List transactions |
| GET | `/api/v1/cash-transactions/{id}` | Transaction detail |
| POST | `/api/v1/cash-transactions` | Create transaction |
| PATCH | `/api/v1/cash-transactions/{id}` | Edit transaction |
| DELETE | `/api/v1/cash-transactions/{id}` | Delete transaction |
| GET | `/api/v1/cash-funds` | List funds |
| POST | `/api/v1/cash-funds` | Create fund |
| PATCH | `/api/v1/cash-funds/{id}` | Edit fund |
| GET | `/api/v1/finance-ledger` | Finance ledger |
| GET | `/api/v1/debts` | List debts |
| POST | `/api/v1/debts` | Create debt |
| PATCH | `/api/v1/debts/{id}` | Pay debt |
| GET | `/api/v1/cashflow/movements` | Cash flow summary |

### AI Chat

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/ai/chat/stream` | Chat streaming (SSE) |
| POST | `/api/v1/ai/catalog-drafts` | Create catalog draft |
| GET | `/api/v1/ai/catalog-drafts/{id}` | Get draft |
| PATCH | `/api/v1/ai/catalog-drafts/{id}` | Edit draft |
| POST | `/api/v1/ai/catalog-drafts/{id}/commit` | Commit draft to DB |
| DELETE | `/api/v1/ai/catalog-drafts/{id}` | Cancel draft |
| POST | `/api/v1/ai/db/sql/describe` | Describe table (for AI) |
| POST | `/api/v1/ai/db/sql/query-readonly-raw` | Execute read-only SQL |

### Settings

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/store-profile` | View store profile |
| PATCH | `/api/v1/store-profile` | Edit store profile |
| POST | `/api/v1/store-profile/logo` | Upload logo |
| GET | `/api/v1/alert-settings` | List alerts |
| POST | `/api/v1/alert-settings` | Create alert |
| PATCH | `/api/v1/alert-settings/{id}` | Edit alert |
| DELETE | `/api/v1/alert-settings/{id}` | Disable alert |
| GET | `/api/v1/system-logs` | List system logs |
| GET | `/api/v1/system-logs/{id}` | Log detail |

### Notifications

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/notifications` | List notifications |
| PATCH | `/api/v1/notifications/{id}` | Mark as read |
| POST | `/api/v1/notifications/mark-all-read` | Mark all as read |

### Approvals (Read-only)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/approvals/pending` | Pending approvals |
| GET | `/api/v1/approvals/history` | Approval history |

---