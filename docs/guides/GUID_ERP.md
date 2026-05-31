# Smart ERP — Detailed Business Workflow Guide

> This document describes the detailed business workflow of each feature in the Smart ERP system, from user interface → Backend API → Database → Response. Purpose: provide AI with reference documentation to guide users and understand the system.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Permissions & Roles](#2-permissions--roles)
3. [Login / Logout / Session](#3-login--logout--session)
4. [Dashboard](#4-dashboard)
5. [Inventory Management](#5-inventory-management)
6. [Product Management](#6-product-management)
7. [Order Management](#7-order-management)
8. [Cash Flow Management](#8-cash-flow-management)
9. [AI Chat — Smart Assistant](#9-ai-chat--smart-assistant)
10. [System Settings](#10-system-settings)
11. [Notifications](#11-notifications)
12. [Approvals](#12-approvals)
13. [Reports & Analytics](#13-reports--analytics)
14. [API Reference](#14-api-reference)
15. [Database Reference](#15-database-reference)
16. [Appendix: Key Business Rules](#16-appendix-key-business-rules)

---

## 1. Architecture Overview

### Technology Stack

| Tier | Technology |
|------|-----------|
| **Frontend** | React 19 + TypeScript + Vite + TanStack Query + Zustand + Radix UI + TailwindCSS |
| **Backend** | Spring Boot 3.5.14 + Java 21 + PostgreSQL + Flyway + JWT Auth + Redis |
| **AI Service** | Python FastAPI + LangGraph + LangChain + OpenAI-compatible LLM |

### General Data Flow

```
User → React Frontend (Vite dev server)
        ↓ HTTP/REST (JSON envelope: {success, data})
     Spring Boot Backend (port 8080)
        ↓ JDBC / JPA
     PostgreSQL Database
        ↓
     JSON Response → Frontend render
```

### AI Chat Flow

```
User → React Frontend
        ↓ SSE POST /api/v1/ai/chat/stream
     Spring Boot (relay)
        ↓ HTTP forward (same Bearer token)
     Python FastAPI (port 9000)
        ↓ LangGraph → LLM + SQL execution (calls back Spring JDBC)
     SSE events (delta/chart/draft/done/error)
        ↓
     Frontend renders text / charts / tables
```

### Response Envelope (Spring Boot)

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional"
}
```

**Error:**
```json
{
  "success": false,
  "error": "BAD_REQUEST | UNAUTHORIZED | FORBIDDEN | NOT_FOUND | CONFLICT | UNPROCESSABLE_ENTITY | TOO_MANY_REQUESTS | INTERNAL_SERVER_ERROR",
  "message": "Vietnamese error description",
  "details": { "fieldName": "Error detail" }
}
```

---

## 2. Permissions & Roles

### Roles

| Role | Description |
|------|-------------|
| **Owner** | Store owner — highest privileges, cannot be deleted or assigned to new users |
| **Admin** | Administrator — manages staff, inventory, orders, finance |
| **Manager** | Manager — operational privileges |
| **Staff** | Staff — limited privileges, can request password reset |
| **Warehouse** | Warehouse keeper — inventory management |

### Permission System (12 flags)

Each role has a set of permission flags stored as JSONB in the `roles.permissions` table. On login, these flags are embedded into the JWT claim `"mp"` (menu permissions).

| Permission Key | Description |
|---|---|
| `can_view_dashboard` | View Dashboard page |
| `can_use_ai` | Use AI Chat |
| `can_manage_inventory` | Manage inventory (inbound/outbound/audit) |
| `can_manage_products` | Manage products |
| `can_manage_customers` | Manage customers |
| `can_manage_orders` | Manage orders |
| `can_approve` | Approve inbound/outbound receipts |
| `can_view_finance` | View finance |
| `can_manage_staff` | Manage staff |
| `can_configure_alerts` | Configure alerts |
| `can_view_store_profile` | View store profile |
| `can_view_system_logs` | View system logs |

### Permission Enforcement

- **Backend:** `@PreAuthorize("hasAuthority('can_manage_staff')")` on each controller
- **Frontend:** Sidebar auto-hides items without permission based on `menuPermissions` from Zustand store
- **Client does NOT verify JWT signature** — only parses payload for UI rendering. Backend always enforces 403.

---

## 3. Login / Logout / Session

### 3.1. Login

**UI:**
1. User opens app → If valid session in sessionStorage → redirects to `/dashboard`
2. Otherwise → shows `LoginForm` with 2 fields: email + password (min 6 chars)
3. User submits → "Login"

**Flow:**
```
Frontend POST /api/v1/auth/login { email, password }
  ↓
Backend AuthService.login():
  1. Check user exists and status != "Locked"
  2. Not found → 401 UNAUTHORIZED
  3. Locked → 403 FORBIDDEN
  4. Verify password (BCrypt)
     - 5 consecutive failures → lock account (status = 'Locked')
     - Success → clear failure counter
  5. Create JWT access token (HS256, TTL 5 min)
     - Claims: sub, user_id, tenant_id, name, role, mp (permissions)
  6. Create refresh token (32-char hex, 30-day expiry)
  7. Save refresh token to refresh_tokens table
  8. Update last_login
  9. Write login log to systemlogs
  10. Register session in Redis: auth:session:{userId}
  ↓
Frontend receives response:
  { accessToken, refreshToken, user }
  1. Save accessToken, refreshToken, user to sessionStorage
  2. Parse "mp" claim from JWT → update Zustand store (persist localStorage)
  3. Navigate to /dashboard
```

**Tables involved:** `users`, `roles`, `refresh_tokens`, `systemlogs`, Redis `auth:session:{userId}`

### 3.2. Token Refresh

**Trigger:** When a request with `auth: true` receives 401, frontend auto-calls refresh.

```
Frontend POST /api/v1/auth/refresh { refreshToken }
  ↓
Backend AuthService.refresh():
  1. Validate refresh token (exists, not revoked, not expired)
  2. Verify user is still Active
  3. Throttle: max 1 new access token / 5 min / user
  4. Create new access token (same process as login)
  5. Return same refresh token (no rotation)
  6. Update Redis session
  ↓
Frontend:
  1. Save new accessToken + refreshToken to sessionStorage
  2. Re-parse "mp" claim → update Zustand store
  3. Retry original request with new token
```

### 3.3. Logout

```
Frontend calls logoutAndGoToLogin():
  1. POST /api/v1/auth/logout { refreshToken } + Bearer token (best-effort)
  2. Remove accessToken, refreshToken, user from sessionStorage
  3. Reset Zustand store (clear localStorage auth-storage)
  4. Navigate to /login
  ↓
Backend AuthService.logout():
  1. Soft revoke refresh token: UPDATE refresh_tokens SET deleteYmd = now
     - Not found → 403
  2. Clear refresh throttle
  3. Write logout log to systemlogs
  4. Delete Redis session: auth:session:{userId}
```

### 3.4. Session Persistence

| Layer | Storage | Data |
|---|---|---|
| **sessionStorage** (per tab) | accessToken, refreshToken, user | Tokens + user info |
| **localStorage** (Zustand persist) | user, isAuthenticated, menuPermissions | No tokens stored (security) |
| **Redis** (server-side) | `auth:session:{userId}` → accessToken | Multi-instance sync |

### 3.5. Password Reset Request

**Only for Staff role.** Owner/Admin/Manager must contact Owner directly.

```
Frontend: "Request Password" Dialog → username + message (optional)
POST /api/v1/auth/password-reset-requests { username, message }
  ↓
Backend:
  1. Find user by username
  2. Check: role = "Staff" AND status IN ("Active", "Locked")
  3. If not met → silently return (prevents username enumeration)
  4. INSERT INTO staffpasswordresetrequests (user_id, message, status='Pending')
  5. Write log to systemlogs
  6. Notify all Owner/Admin users
  7. Return success message (always shows success)
```

---

## 4. Dashboard

**UI:** Welcome page with greeting, 4 navigation cards to main modules:
- **Inventory** → `/inventory/stock`
- **Orders** → `/orders/retail`
- **Cash Flow** → `/cashflow/transactions`
- **Reports** → `/analytics/revenue`

**Note:** Dashboard is currently a static page, does NOT call APIs for real-time data.

---

## 5. Inventory Management

> Requires permission: `can_manage_inventory`

### 5.1. View & Search Stock

**UI (`StockPage.tsx`):**
- 4 KPI cards: Total SKUs, Total Inventory Value, Low Stock Count, Expiring Soon Count
- Stock table with infinite scroll
- Toolbar: search, filter by stock level, location, category

**Data Flow:**
```
GET /api/v1/inventory?search=&stockLevel=all&locationId=&categoryId=&page=1&limit=20&sort=id:asc
GET /api/v1/inventory/summary?search=&stockLevel=all  (KPI cards)
  ↓
Backend InventoryListService:
  1. loadSummary() — COUNT, SUM(quantity×costPrice), low/expiring counts
  2. countRows() — total rows for pagination
  3. loadPage() — JOIN products, locations, units
     - isLowStock = quantity > 0 AND quantity <= minQuantity
     - isExpiringSoon = expiryDate <= today+30days AND quantity > 0
     - totalValue = costPrice × quantity
  ↓
Frontend:
  - IntersectionObserver loads more on near-end scroll
  - Search debounce 400ms
```

**Display Status:**

| Status | Condition | Color |
|---|---|---|
| Draft | Draft | Gray |
| Out of Stock | quantity = 0 | Red |
| Low Stock | isLowStock | Red |
| Expiring Soon | isExpiringSoon | Amber |
| Normal | Default | Green |

**Batch Detail View:** Click eye icon → `StockBatchDetailsDialog` shows batch info + list of same-product lots still in stock.

### 5.2. Edit Stock Info

**UI:** Select rows → click "Edit" → `StockEditDialog`

**Editable fields:** `locationId`, `minQuantity`, `batchNumber`, `expiryDate`, `unitId`

**Read-only fields:** `costPrice`, `unitName`, `productName`, `skuCode`, `quantity`

**Data Flow:**
```
Single: PATCH /api/v1/inventory/{id} { changedFields }
Bulk:   PATCH /api/v1/inventory/bulk { items: [{id, ...fields}] }  (max 100 rows)
  ↓
Backend InventoryPatchService:
  1. SELECT ... FOR UPDATE (row lock)
  2. Check: product status != "Inactive", location status != "Maintenance"
  3. Check: new locationId exists and is Active
  4. Check: unitId belongs to product
  5. Check: no duplicate (productId + locationId + batchNumber)
  6. UPDATE only changed fields
  7. Write log to systemlogs (before/after JSON)
  8. Notify Owner (if actor is not Owner)
```

### 5.3. Stock Receipt (Inbound)

**UI (`InboundPage.tsx`):**
- Receipt list with filters: status, date, supplier, "mine"
- "Create Receipt" button → `ReceiptForm`

#### Create Receipt

```
Frontend: ReceiptForm (Zod validation)
  - supplierId (required), receiptDate (required)
  - details[]: productId, unitId, quantity, costPrice (required)
  - expiryDate >= receiptDate
  - Mode: "Save Draft" or "Submit for Approval"
POST /api/v1/stock-receipts { supplierId, receiptDate, invoiceNumber?, notes?, saveMode, details[] }
  ↓
Backend StockReceiptLifecycleService.create():
  1. Validate supplier exists and is Active
  2. Validate each line: product Active, unitId belongs to product, must be base unit
  3. Check no duplicate (productId + batchNumber) within same receipt
  4. Generate code: PN-{year}-{seq} (retry max 5 on duplicate)
  5. INSERT header + detail rows
  6. If saveMode=pending → notify approvers
  ↓
Response: 201 Created with full receipt data
```

#### Approve Receipt — **Inventory Increase Point**

```
POST /api/v1/stock-receipts/{id}/approve { inboundLocationId }
  ↓
Backend (requires can_approve + Admin/Owner):
  1. Check status = "Pending"
  2. Check location is Active
  3. For each detail line:
     - Find existing inventory (same productId + locationId + batchNumber) or create new
     - Add quantity (converted to base unit)
     - INSERT inventory_logs (INBOUND)
  4. UPDATE receipt status → "Approved", record approverId + approvedAt
  5. Post to finance ledger (purchase cost)
  6. Write system log
```

#### Reject Receipt

```
POST /api/v1/stock-receipts/{id}/reject { reason }  (min 15 chars)
  ↓
Backend: UPDATE status → "Rejected", record reviewerId + reviewedAt + rejectionReason
```

#### Edit / Delete

| Status | Edit | Delete |
|---|---|---|
| Draft | Creator can edit | Owner only |
| Pending | Cannot edit | Staff/Admin/Owner can delete |
| Approved/Rejected | Cannot edit | Cannot delete |

#### Receipt Status Diagram

```
Draft → (submit) → Pending → (approve) → Approved [INCREASES INVENTORY]
Draft → (submit) → Pending → (reject)  → Rejected
Draft → (delete) → [deleted]
Pending → (delete) → [deleted]
```

### 5.4. Stock Dispatch (Outbound)

**UI (`DispatchPage.tsx`):**
- Dispatch list with filters
- Create manually from Stock page or Dispatch page
- Create from order (order-linked)

#### Create Manual Dispatch

```
POST /api/v1/stock-dispatches { dispatchDate, referenceLabel?, notes?, lines: [{ inventoryId, quantity, unitPriceSnapshot? }] }
  ↓
Backend ManualStockDispatchService.createManual():
  1. Validate quantity > 0 for each line
  2. INSERT header with temp code, status = "Pending"
  3. For each line: lock inventory, check sufficient or shortage
  4. INSERT dispatch lines
  5. Generate code: PX-{year}-{id} (6-digit padded)
  6. If shortage → status = "Partial", notify shortage
  7. If sufficient → notify creation success
```

#### Approve Dispatch (Admin)

```
POST /api/v1/stock-dispatches/{id}/approve
  ↓
Backend (Admin only):
  1. Check status = Pending/Partial, no shortage
  2. UPDATE status → "WaitingDispatch"
```

#### Delivery Complete — **Inventory Decrease Point**

```
PATCH /api/v1/stock-dispatches/{id} { status: "Delivered" }
  ↓
Backend finalizeDelivered():
  1. For each line: deduct inventory quantity
  2. INSERT inventory_logs (OUTBOUND)
  3. Post COGS to finance ledger
  4. UPDATE status → "Delivered"
```

#### Dispatch Status Diagram

```
Pending → (admin approve, no shortage) → WaitingDispatch → Delivering → Delivered [DECREASES INVENTORY]
Pending → (has shortage) → Partial → (fix lines) → Pending
Any (not Delivered) → (soft-delete) → [soft deleted]
```

### 5.5. Audit Session

**UI (`AuditPage.tsx`):**
- Audit session list with filters
- "Create Audit Session" → select scope

#### Create Audit Session

```
POST /api/v1/inventory/audit-sessions { title, auditDate, notes?, scope: { mode, ... } }
  ↓
Backend AuditSessionService.create():
  1. Validate scope:
     - by_location_ids: find all inventory at these locations
     - by_category_id: find inventory for products in this category
     - by_inventory_ids: direct selection by ID
  2. Generate code: KK-{year}-{seq}
  3. INSERT session header, status = "Pending"
  4. For each inventory in scope:
     - INSERT audit line with systemQuantity (snapshot), actualQuantity = NULL
```

#### Enter Actual Quantities

```
PATCH /api/v1/inventory/audit-sessions/{id}/lines { lines: [{ lineId, actualQuantity, notes? }] }
  ↓
Backend (only when status = "In Progress" or "Re-check"):
  1. UPDATE actualQuantity, isCounted = true
  2. Recalculate variance = actual - system
```

#### Complete Audit

```
POST /api/v1/inventory/audit-sessions/{id}/complete { requireAllCounted? }  (default true)
  ↓
Backend:
  1. Check status = "In Progress"
  2. If requireAllCounted → all lines must be counted
  3. UPDATE status → "Pending Owner Approval"
  → Does NOT apply variance to inventory yet
```

#### Owner Approve / Reject

```
POST /api/v1/inventory/audit-sessions/{id}/approve   → Completed
POST /api/v1/inventory/audit-sessions/{id}/reject    → In Progress
  ↓ (Owner only)
```

#### Apply Variance — **Inventory Adjustment Point**

```
POST /api/v1/inventory/audit-sessions/{id}/apply-variance { mode?, reason? }
  ↓
Backend (only when status = "Completed"):
  1. For each line with variance: lock inventory
  2. Mode "set_actual": quantity = actualQuantity (rounded)
  3. Mode "add_delta" (default): quantity += (actual - system) (rounded)
  4. Check quantity >= 0
  5. UPDATE inventory
  6. INSERT inventory_log
  7. Mark varianceAppliedAt
```

#### Audit Status Diagram

```
Pending → In Progress → (complete) → Pending Owner Approval
Pending Owner Approval → (owner approve) → Completed → (apply-variance) → [inventory adjusted]
Pending Owner Approval → (owner reject) → In Progress
Pending/In Progress/Pending Owner Approval → (cancel) → Cancelled
Completed → (owner Re-check) → Re-check → (complete) → Pending Owner Approval
```

### 5.6. Warehouse Locations

**UI (`WarehouseLocationsPage.tsx`):**
- Currently uses mock data (4 hardcoded locations)
- Table: location code, area, shelf, capacity, current stock, status
- Statuses: "Active", "Full", "Inactive" (Maintenance)

**Backend:** Locations are referenced by `locationId` in inventory rows, validated during inventory patch and receipt approval.

---

## 6. Product Management

> Requires permission: `can_manage_products` (products), `can_manage_customers` (customers)

### 6.1. Products

#### Create Product

```
Frontend: ProductForm → if images exist → multipart/form-data
POST /api/v1/products  (JSON or multipart)
  ↓
Backend ProductService:
  1. Check SKU uniqueness
  2. Validate category (if provided) — must exist and be Active
  3. INSERT into products
  4. INSERT base unit into productunits (conversion_rate=1, is_base_unit=TRUE)
  5. INSERT initial price into productpricehistory
  6. If images: parallel upload to Cloudinary (max 10 images, JPEG/PNG/WebP, ≤5MB each)
  7. If upload fails → rollback (delete product)
  ↓
Response: 201 Created { id, skuCode, barcode, name, categoryId, imageUrl, status, currentStock, currentPrice }
```

#### Product List

```
GET /api/v1/products?search=&categoryId=&status=&page=&limit=&sort=
  ↓
Backend: JOIN products → productunits (base) → categories → inventory (COALESCE qty)
         + LATERAL subquery on productpricehistory for latest price
Frontend: Infinite scroll (IntersectionObserver), search debounce 400ms
```

#### Edit Product (Differential PATCH)

```
PATCH /api/v1/products/{id} { changedFields }
  ↓
Backend:
  1. SELECT ... FOR UPDATE (pessimistic lock)
  2. Validate each field (skuCode ≤50, name ≤255, barcode ≤100, weight ≥0)
  3. Price pair rule: if changing price → MUST send both salePrice AND costPrice
  4. Compare with latest productpricehistory → only INSERT history row if actually changed
  5. priceEffectiveDate defaults to today
```

#### Delete Product — **Owner Only**

**Delete Guards:**

| Check | Related Table |
|---|---|
| Has stock receipts | `stockreceiptdetails` |
| Has order lines | `orderdetails` |
| Has stock | `inventory.quantity > 0` |

#### Product Image Management

- **JSON mode:** `POST /api/v1/products/{id}/images` with `{url, sortOrder, isPrimary}` — add from external URL
- **Multipart mode:** `POST /api/v1/products/{id}/images` with `file` part — upload to Cloudinary
- **Primary image:** When setting `isPrimary=true` → clear all existing primaries → update `products.image_url`

### 6.2. Categories — Hierarchical Tree

#### Tree List

```
GET /api/v1/categories?format=tree&search=&status=
  ↓
Backend CategoryService:
  1. Load all active categories (deleted_at IS NULL) with product counts
  2. Apply search filter — INCLUDES ancestors of matching nodes (preserves tree context)
  3. Build tree in memory: buildChildrenIndex() → recursive buildSubTree() with BFS cycle guard
  4. Sort by sortOrder, then name
```

#### Create Category

```
POST /api/v1/categories { categoryCode, name, description?, parentId?, sortOrder?, status? }
  ↓
Backend:
  1. Validate: code not blank, unique, name ≤255
  2. Parent must exist and be Active
  3. INSERT into categories
```

#### Edit — Cycle Prevention

```
PATCH /api/v1/categories/{id} { parentId?, ... }
  ↓
Backend:
  1. wouldPutParentInDescendantSubtree() — BFS from current node's descendants
     - If newParentId found among descendants → reject "hierarchy cycle"
  2. v1 limitation: Cannot move back to root (parentId=null) via PATCH
```

#### Delete Category — **Owner Only, Soft Delete**

**Delete Guards:**
- Has active child categories
- Has products assigned to this category

```
DELETE /api/v1/categories/{id}
→ UPDATE categories SET deleted_at = CURRENT_TIMESTAMP
```

### 6.3. Suppliers

#### Basic CRUD

```
POST /api/v1/suppliers { supplierCode, name, contactPerson, phone, email?, address?, taxCode?, status? }
PATCH /api/v1/suppliers/{id} { changedFields }  (differential)
GET /api/v1/suppliers?search=&status=&page=&limit=&sort=  (infinite scroll)
```

#### Delete — **Owner Only, Hard Delete**

**Delete Guards:**

| Check | Related Table |
|---|---|
| Has receipts | `stockreceipts` |
| Has partner debts | `partnerdebts` |

### 6.4. Customers

#### Basic CRUD

```
POST /api/v1/customers { customerCode, name, phone, email?, address?, status? }
  → loyaltyPoints initialized to 0
PATCH /api/v1/customers/{id} { changedFields }
  → Staff CANNOT edit loyaltyPoints (403)
  → Frontend hides loyaltyPoints field for Staff
GET /api/v1/customers?search=&status=&page=&limit=&sort=
  → Aggregates total_spent, order_cnt from salesorders (excluding Cancelled)
```

#### Delete — Split Authority

| Action | Permission | Type | Delete Guards |
|---|---|---|---|
| Single delete | **Admin** | Soft Delete | Open orders, Partner debts |
| Bulk delete (≤50) | **Owner** | Hard Delete | ANY orders, Partner debts |

---

## 7. Order Management

> Requires permission: `can_manage_orders`

### 7.1. Retail POS

**UI (`RetailPage.tsx`):** Split-screen layout
- **Left (8 cols):** POS product grid — search, cards with stock badges
- **Right (4 cols):** Cart + checkout

#### Cart (Zustand store, persist sessionStorage)

- `addItem`: merge by `(productId, unitId)` pair, accumulate quantity
- `updateQuantity`: minimum = 1
- `getTotal()`: sum of `lineTotal`
- `getFinalTotal()`: `total - discount`

#### Checkout

```
Frontend: POSCartPanel
  - Select customer (default "Walk-in Customer")
  - Enter voucher code (optional) → preview discount
  - "Cash" button → paymentStatus: "Paid"
  - "Card/Transfer" button → paymentStatus: "Unpaid"
POST /api/v1/sales-orders/retail/checkout { customerId?, walkIn?, lines[], discountAmount?, voucherCode?, paymentStatus? }
  ↓
Backend SalesOrderService.retailCheckout():
  1. Resolve customer: walkIn=true → lookup "WALKIN" customer
  2. Validate each line: product exists, unitId belongs to product, qty > 0, price ≥ 0, price within ±10% of catalog price
  3. Compute subtotal = Σ(unitPrice × quantity)
  4. Validate discount: 0 ≤ discount ≤ subtotal
  5. Process voucher (if provided):
     - SELECT ... FROM vouchers WHERE code = ? FOR UPDATE (row lock)
     - Validate: isActive, within validity period, has remaining uses
     - Compute discount: Percent → subtotal × value/100; FixedAmount → min(value, subtotal)
  6. INSERT order header: status = "Delivered", orderChannel = "Retail", temp code TMP-UUID
  7. INSERT order lines
  8. Deduct stock (FEFO — First Expired First Out):
     - SELECT inventory ... FOR UPDATE (ordered by expiry date)
     - Check sufficient stock → 409 if insufficient
     - Create stockdispatches (code PX-{year}-{id})
     - Deduct inventory buckets, INSERT inventory_log outbound
     - Update dispatched_qty for order lines
  9. Voucher redemption: increment used_count + insert redemption record
  10. Post revenue to finance ledger
  ↓
Response: 201 Created with full order data
```

### 7.2. Returns / Refunds

```
POST /api/v1/sales-orders { orderChannel: "Return", customerId, refSalesOrderId?, lines[] }
  ↓
Backend:
  1. Validate refSalesOrderId customer must match return's customer
   2. Create order normally (same as retail, with orderChannel="Return")
```

#### Cancel Order

```
POST /api/v1/sales-orders/{id}/cancel
  ↓
Backend SalesOrderService.cancel():
  1. SELECT ... FOR UPDATE
  2. Idempotent: already Cancelled → return immediately (200)
   3. Check stock dispatch:
      - Retail: Call RetailStockService.reverseDeductionForRetailCancel()
        → Restore inventory, INSERT inventory_log inbound, cancel dispatch records
  4. Voucher reversal (Retail): restore voucher used_count
  5. Finance ledger: post refund entry
  6. UPDATE status = 'Cancelled', cancelled_at = now, cancelled_by = userId
```

### 7.3. Vouchers

#### Voucher Types

| Type | Formula |
|---|---|
| Percent | discount = subtotal × value / 100 |
| FixedAmount | discount = min(value, subtotal) |

#### Preview Voucher

```
POST /api/v1/sales-orders/retail/voucher-preview { voucherCode?, subtotal, manualDiscount? }
  ↓ (read-only, no locks, no state changes)
Backend:
  1. Validate voucher: active, within validity, has remaining uses
  2. Compute discount breakdown
  ↓
Response: { applicable: true/false, voucherDiscountAmount, totalDiscountAmount, payableAmount }
```

#### Redemption (during checkout)

1. `SELECT ... FOR UPDATE` — row lock prevents race conditions
2. Validate applicability
3. Compute discount
4. After successful order creation:
   - `UPDATE vouchers SET used_count = used_count + 1`
   - `INSERT INTO voucher_redemptions (voucher_id, order_id)`
5. On order cancel: `reverseRedemptionForOrder` — decrement used_count, delete redemption record

**Concurrency protection:** 409 Conflict if voucher runs out of uses between preview and checkout

---

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

## 9. AI Chat — Smart Assistant

> Requires permission: `can_use_ai`

### Architecture

```
Browser (React) → Spring Boot (Java, port 8080) → Python FastAPI (port 9000) → PostgreSQL (via Spring JDBC)
     ↑                    ↑                      ↑
   SSE events          JWT Auth              LLM (Gemma/OpenAI-compatible)
   Chart cards         Relay
   Draft tables        SQL exec
```

### 9.1. General Chat

**Flow:** `START → domain_guard → classify_intent → chat_normal → END`

`domain_guard` loads the ERP capability index (from `docs/guides/GUID_ERP.md`) and may return `clarify` (SSE + questions) or `reject` before any SQL/draft/chart branch runs.

```
Frontend: User types message → POST /api/v1/ai/chat/stream { message, conversationId } + Bearer token
  ↓
Spring: Extract user_id/tenant_id from JWT → Build ChatRequest → Forward to Python (same Bearer)
  ↓
Python Auth: Validate JWT → Cross-check claims with metadata
  ↓
Intent Node: LLM classifies intent → "general_chat"
  ↓
Chat Normal Node: Takes last 20 messages (truncated to 4000 chars) → calls LLM with system prompt
  ↓
SSE Streaming: event: delta (partial text), event: done (end)
  ↓
Frontend: appendDeltaSmart() (Vietnamese-aware spacing) → render chat bubble
```

### 9.2. Data Query (SQL Generation Pipeline)

**Flow:** `START → classify_intent → sql_branch(subgraph) → summarize_answer → END`

#### SQL Subgraph Diagram

```
schema_explore (optional) → gen_sql → sql_review → validate_sql → execute_sql → validate_result
                                                                        ↓ (failure)
                                                                   decide_sql_retry → back to gen_sql
                                                                        ↓ (success)
                                                                 summarize_answer
```

#### Step Details

| Step | Description |
|---|---|
| **schema_explore** | LLM identifies metric, dimensions, tables → calls Spring `/describe` for column metadata → builds SchemaArtifact |
| **gen_sql** | Increment sql_attempt_count → load schema → build prompt with schema + dialog tail + feedback → LLM generates SQL |
| **sql_review** | LLM reviews SQL → SqlReviewOutput(ok, issues[]) → filters benign issues → appends feedback |
| **validate_sql** | Deterministic: sqlparse parse → checks: 1 statement, SELECT only, no DDL/DML, table allowlist, column allowlist → auto-inject LIMIT |
| **execute_sql** | Calls Spring `/query-readonly-raw` → JDBC PreparedStatement.executeQuery() → returns {rows, columns, meta} |
| **validate_result** | Checks: has data, ≤50,000 rows → flags result_empty if 0 rows |

#### Retry Logic

| Type | Max Budget |
|---|---|
| Policy validation | 3 attempts |
| Execution | 3 attempts |
| Result validation | 2 attempts |
| Total SQL attempts | MAX_SQL_ATTEMPTS (configurable) |

#### Summarization

```
summarize_answer node:
  - Localize timestamps to Asia/Ho_Chi_Minh
  - Build prompt with dialog tail + SQL rows (6000 chars)
  - LLM summarizes in Vietnamese Markdown
```

### 9.3. Chart Generation

**Flow:** `START → classify_intent → agent_idea → sql_branch → chart_readiness → agent_chart → agent_review → END`

| Step | Description |
|---|---|
| **agent_idea** | LLM generates IdeaPlannerOutput: data_request (metric, time range, filters) + chart_idea (chart_type, axis semantics) |
| **sql_branch** | Runs SQL pipeline to fetch data (same as 9.2) |
| **chart_readiness** | Heuristic checks + optional LLM critic → determines data is suitable for charting |
| **agent_chart** | LLM generates ChartSpecDraftOutput(chart_type, x_key, y_key, title) — Recharts-compatible |
| **agent_review** | Reviews draft, aligns keys to real columns → chart_spec_final with ≤200 rows data |

**SSE:** `event: chart` → Frontend `AiChatChartCard.tsx` renders Bar/Line/Pie via Recharts

**Chart degrade:** When SQL retries exhausted but query_result has data → draw chart from last available data.

### 9.4. Catalog Draft (HITL — Human-In-The-Loop)

**Flow:** `START → classify_intent → catalog_draft_branch(subgraph) → END`

| Step | Description |
|---|---|
| **classify_catalog_entity** | LLM classifies: product|category|supplier|customer + row count (1-50) |
| **generate_catalog_draft** | LLM generates columns and rows → enrich → validate → fallback stub rows on error |
| **persist_catalog_draft** | Calls Spring `POST /api/v1/ai/catalog-drafts` → saves draft to DB |

**SSE:** `event: draft` → Frontend `AiChatDraftTableCard.tsx` renders editable table

**Frontend actions:**
- "Add Row" → adds new row
- "Save Draft" → PATCH draft
- "Confirm Write to DB" → POST /commit → Spring creates real entities (products, categories, etc.)
- "Cancel" → DELETE draft

**Commit result:** Each row shows `committedAt` (green bg) or `lastError` (red bg with error messages).

### 9.5. Intent Classification

| Intent | Route | Description |
|---|---|---|
| `general_chat` | chat_normal | General conversation (fallback) |
| `system_data_query` | sql_branch | Data query via SQL |
| `system_data_chart` | agent_idea → sql_branch → chart | Chart generation |
| `catalog_data_entry` | catalog_draft_branch | Catalog data entry HITL |

### 9.6. SSE Events

| Event | Trigger | Payload | Frontend Handler |
|---|---|---|---|
| `delta` | Each final_answer increment | Text string | onDelta → appendDeltaSmart() |
| `chart` | chart_spec_final first appears | JSON spec | onChart → AiChatChartCard |
| `draft` | catalog_draft_sse first appears | JSON draft | onDraft → AiChatDraftTableCard |
| `done` | Graph completes | Empty | onDone → stop typing indicator |
| `error` | Graph or HTTP error | Vietnamese text | onError → display error |

### 9.7. SQL Safety — 4 Layers

| Layer | Mechanism |
|---|---|
| **Executor-level** | enforce_read_only_sql(): blocks DDL/DML, multi-statement, transaction control |
| **Deterministic validation** | sqlparse AST: 1 statement, SELECT only, table/column allowlist, auto-LIMIT |
| **LLM review** | Structured review with SqlReviewOutput(ok, issues[]) |
| **Retry policy** | Per-kind budgets, duplicate SQL detection, chart degrade fallback |

### 9.8. Conversation Memory

- **Checkpointer:** MemorySaver (in-memory) or SqliteSaver (persistent file)
- **Thread ID:** `sessionStorage ai_chat_conversation_id` — UUID per browser tab
- **Dialog tail:** Last 12 messages (max 2000 chars) injected into prompt for gen_sql and summarize; when a summary exists it is prepended as `[Tóm tắt các lượt trước]`.
- **Compaction:** After `domain_guard` (proceed path), node `context_compact` runs when user turn count exceeds `CONTEXT_COMPACT_MAX_TURNS` (default 10). LLM writes an 8-line Vietnamese summary; keeps the last 2 user turns verbatim; prunes older messages from checkpoint via `RemoveMessage`.
- **State keys:** `conversation_summary`, `context_compact_generation` (persist across turns; not reset in `_build_state`).
- **Each new turn:** Resets query_result, generated_sql, final_answer, error_payload, intent. Keeps thread_id, user_id, tenant_id, conversation summary.

---

## 10. System Settings

### 10.1. Employee Management

> Requires permission: `can_manage_staff`

#### Employee List

```
GET /api/v1/users?search=&status=all&roleId=&page=1&limit=20
  ↓
Backend UsersManagementService:
  1. requireActorCanManageStaff() — checks actor is Active + has permission
  2. JOIN users → roles
  3. ORDER BY created_at DESC
```

#### Create Employee

```
Frontend: EmployeeForm (Zod validation)
  - username (3-100), password (8-128), fullName (1-255), employeeCode (1-50)
  - email (valid), phone (≤20), role (Admin/Staff), status (Active/Inactive)
  - "Get code from server" → GET /api/v1/users/next-staff-code → NV-ADM-001, NV-STF-001, ...
POST /api/v1/users { username, password, fullName, email, phone, roleId, status }
  ↓
Backend UserCreationService:
  1. Check actor is Active + can_manage_staff
  2. Lookup role → BLOCK assigning "Owner" role (403)
  3. Check duplicates: username + email → 409 CONFLICT
  4. Map status: UI "Inactive" → DB "Locked"
  5. Encode password (BCrypt)
  6. INSERT INTO users
```

#### Edit Employee

```
PATCH /api/v1/users/{userId} { fullName?, staffCode?, email?, phone?, status?, roleId?, password? }
  ↓
Backend UsersManagementService:
  1. Block empty body (400)
  2. **Role change guard**: only Owner can change roleId; cannot assign "Owner" role
  3. Apply partial updates
  4. Catch DataIntegrityViolationException → 409 (duplicate email/staffCode)
```

#### Delete Employee (Soft Delete — locks account)

```
DELETE /api/v1/users/{userId}
  ↓
Backend:
  1. Cannot delete self → 409
  2. Cannot delete Owner → 409
  3. UPDATE users SET status = 'Locked' WHERE id = ? AND status = 'Active'
```

#### Generate Next Staff Code

```
GET /api/v1/users/next-staff-code?roleId=3&staffFamily=ADMIN
  ↓
Backend NextStaffCodeService:
  1. Validate roleId exists, staffFamily compatible with roleId
  2. Prefix: NV-OWN (Owner), NV-ADM (Admin), NV-MAN (Manager), NV-STF (Staff), NV-WH (Warehouse)
  3. Query: SELECT staff_code FROM users WHERE staff_code LIKE 'NV-ADM-%'
  4. Parse suffix, find max, +1 → format zero-padded 3 digits
  ↓
Response: { nextCode: "NV-ADM-001", prefix: "NV-ADM" }
```

### 10.2. Store Profile

#### View Profile

```
GET /api/v1/store-profile
  ↓
Backend StoreProfileService.getOrCreate():
  1. INSERT ... ON CONFLICT DO NOTHING (auto-create if missing)
  2. SELECT by owner_id
```

#### Edit Profile (Differential PATCH)

```
Frontend: buildPatchBody() — only sends changed fields. Empty string → null. No changes → toast
PATCH /api/v1/store-profile { name?, address?, phone?, email?, website?, taxCode?, ... }
  ↓
Backend:
  1. Validate body not empty, accepts only 12 whitelisted keys
  2. Per-field validation: name not blank, email has "@", website/logo/facebook is valid URI
  3. Validate defaultRetailLocationId exists in warehouselocations
  4. Dynamic SQL UPDATE
```

#### Upload Logo

```
POST /api/v1/store-profile/logo  (multipart/form-data, part "file")
  ↓
Backend:
  1. Upload to Cloudinary: smart-erp/store-profiles/{ownerId}/{UUID}
  2. UPDATE storeprofiles SET logo_url = ?
```

### 10.3. Alert Settings

> **Owner only** can configure alerts.

#### List

```
GET /api/v1/alert-settings?ownerId=&alertType=&isEnabled=
  ↓
Backend: Owner → force ownerId = JWT userId; Admin → uses provided ownerId; else → 403
```

#### Create Alert

```
POST /api/v1/alert-settings { alertType, channel:"App", frequency:"Realtime", thresholdValue?, isEnabled:true, recipients? }
  ↓
Backend:
  1. Owner-only
  2. Normalize threshold: only allowed for LowStock/ExpiryDate/HighValueTransaction/PartnerDebtDueSoon; block negative
  3. Validate recipients usernames exist
  4. INSERT with recipients as JSONB
  5. Unique constraint (owner_id, alert_type) → 409 if duplicate
```

#### Toggle Alert (Soft Disable)

```
DELETE /api/v1/alert-settings/{id}
→ UPDATE alertsettings SET is_enabled = FALSE  (not a hard delete)
```

### 10.4. System Logs

> **Admin only** + `can_view_system_logs` required.

#### List

```
GET /api/v1/system-logs?search=&module=&logLevel=&dateFrom=&dateTo=&page=&limit=
  ↓
Backend:
  1. Admin-only: checks role = "Admin" AND mp.can_view_system_logs = true
  2. Validate: page ≥ 1, limit 1-100, search ≤200, module ≤100, logLevel valid
  3. JOIN users to get full_name
  4. Search spans: message, action, module, full_name, context_data (ILIKE)
```

#### Delete Logs

```
DELETE /api/v1/system-logs/{id}  or  POST /api/v1/system-logs/bulk-delete
→ ALWAYS returns 403 FORBIDDEN: "Not allowed to delete system logs per system policy"
→ System logs are IMMUTABLE
```

---

## 11. Notifications

### UI (Header notification bell)

- **Polling:** `GET /api/v1/notifications?page=1&limit=50` every **12 seconds**
- **Red badge:** shows unread count (capped at "99+")
- **Dropdown:** max 50 notifications, newest first, unread has blue left bar

### Click Notification

| referenceType | Action |
|---|---|
| `StockReceipt` | Fetch receipt detail → open ReceiptDetailDialog → mark read |
| `StockDispatch` | Fetch dispatch detail → open DispatchDetailDialog → mark read |
| Other | Just mark read |

### API

```
GET /api/v1/notifications?page=1&limit=50&unreadOnly=true
PATCH /api/v1/notifications/:id  (mark single read)
POST /api/v1/notifications/mark-all-read
```

### Backend

- **Table:** `notifications` — user_id, notification_type, title, message, is_read, reference_type, reference_id
- **Source:** Other services INSERT notifications (password reset requests, receipts/dispatches, etc.)
- **Time format:** Vietnamese relative — "Just now", "X minutes ago", "X days ago", or full date (>14 days)

---

## 12. Approvals

> Requires: Owner or Admin

> **Note:** Routes `/approvals/pending` and `/approvals/history` in `App.tsx` currently redirect to `/dashboard` — approval pages exist in code but are not accessible via navigation.

### Pending Approvals

```
GET /api/v1/approvals/pending?search=&type=&fromDate=&toDate=&page=&limit=
  ↓
Backend ApprovalsService:
  1. Query stockreceipts WHERE status = 'Pending'
  2. Search: receipt_code ILIKE or full_name ILIKE
  3. Date filter on receipt_date
  4. Returns summary with totalPending and byType breakdown
  → Only Inbound has real data; Outbound/Return/Debt hardcoded = 0
```

### Approval History

```
GET /api/v1/approvals/history?resolution=&search=&type=&fromDate=&toDate=&page=&limit=
  ↓
Backend:
  1. Query stockreceipts WHERE status IN ('Approved', 'Rejected') AND reviewed_at IS NOT NULL
  2. Search includes reviewer name
  3. Date filter on reviewed_at::date
```

### Approve / Reject

> **Note:** Approve/reject mutations go through `stockReceiptsApi` (`approveStockReceipt`, `rejectStockReceipt`), NOT through dedicated approvals endpoints. Approvals endpoints are read-only.

- **Approve:** Click ✓ → dialog select inbound location → `POST /api/v1/stock-receipts/{id}/approve`
- **Reject:** Click ✗ → dialog enter reason → `POST /api/v1/stock-receipts/{id}/reject`

---

## 13. Reports & Analytics

> **Note:** All analytics data is currently **mock data** — no backend API exists.

### Revenue Page

- Mock data: 7 days of March 2024
- Stats: total revenue, total profit, profit margin %
- Area chart: revenue vs profit over time (Recharts)
- Bar chart: revenue vs profit comparison

### Top Products Page

- Mock data: 5 products
- Horizontal bar chart: top 5 by quantity sold
- Donut/pie chart: revenue composition by product
- Detail table: SKU, name, quantity, revenue, percentage bar

---

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
| POST | `/api/v1/sales-orders` | Create return order |
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

## 15. Database Reference

### Core Tables

| Table | Description |
|---|---|
| `users` | User accounts |
| `roles` | Roles + JSONB permissions |
| `refresh_tokens` | Login refresh tokens |
| `staffpasswordresetrequests` | Password reset requests |
| `storeprofiles` | Store profile information |
| `alertsettings` | Alert configurations |
| `systemlogs` | System audit logs |
| `notifications` | User notifications |

### Catalog & Partners

| Table | Description |
|---|---|
| `categories` | Product categories (hierarchical tree) |
| `products` | Products |
| `productimages` | Product image gallery |
| `productunits` | Product units of measure |
| `productpricehistory` | Product price history |
| `suppliers` | Suppliers |
| `customers` | Customers |

### Inventory

| Table | Description |
|---|---|
| `inventory` | Current stock levels |
| `inventorylogs` | Stock movement logs |
| `stockreceipts` | Inbound stock receipts |
| `stockreceiptdetails` | Receipt line items |
| `stockdispatches` | Outbound stock dispatches |
| `stockdispatch_lines` | Dispatch line items |
| `inventoryauditsessions` | Audit sessions |
| `inventoryauditlines` | Audit session lines |
| `inventory_audit_session_events` | Audit session events |
| `warehouselocations` | Warehouse locations |

### Orders

| Table | Description |
|---|---|
| `salesorders` | Sales orders |
| `orderdetails` | Order line items |
| `vouchers` | Discount vouchers |
| `voucher_redemptions` | Voucher redemption history |

### Finance

| Table | Description |
|---|---|
| `cashtransactions` | Cash transactions |
| `cash_funds` | Cash funds |
| `financeledger` | Finance ledger (double-entry) |
| `partnerdebts` | Partner debts (receivables/payables) |

### AI

| Table | Description |
|---|---|
| `ai_table_description` | Table descriptions for AI |
| `ai_column_description` | Column descriptions for AI |
| `aichathistory` | AI chat history |
| `aiinsights` | AI insights |

---

## 16. Appendix: Key Business Rules

### Inventory Rules

1. **Increase inventory:** Only occurs when **approving a stock receipt** (Stock Receipt Approve)
2. **Decrease inventory:** Only occurs when **dispatch reaches Delivered status** or **applying audit variance**
3. **Retail POS:** Auto-deducts stock on checkout (FEFO — First Expired First Out)
4. **Row locking (FOR UPDATE):** Prevents race conditions on inventory patches, receipt approvals, checkout
5. **No duplicates:** Cannot have 2 inventory rows with same (productId + locationId + batchNumber)

### Product Pricing Rules

1. **Price pair:** When changing price, MUST send both `salePrice` AND `costPrice`
2. **Price history:** Only INSERT new record into `productpricehistory` if price actually changed
3. **Effective date:** `priceEffectiveDate` defaults to current date

### Delete Permission Rules

| Entity | Single Delete | Bulk Delete |
|---|---|---|
| Product | Owner only (hard) | Owner only (hard) |
| Category | Owner only (soft) | Owner only (soft, sequential) |
| Supplier | Owner only (hard) | Owner only (hard) |
| Customer | Admin only (soft) | Owner only (hard) |
| User | can_manage_staff (soft → Locked) | N/A |

### Finance Rules

1. **Idempotent posting:** All automatic postings check `existsPosting()` before INSERT
2. **Signed amounts:** Income = positive, Expense = negative
3. **Running balance:** Computed via window function `SUM() OVER (ORDER BY ...)`
4. **Default fund:** Automatic postings use fund with `is_default = TRUE`

### AI Chat Rules

1. **SQL read-only:** Only SELECT allowed, completely blocks DDL/DML
2. **Table allowlist:** SQL can only query registered tables
3. **Ledger metric policy:** Revenue/expense queries MUST use `financeledger` table
4. **Auto-LIMIT:** Automatically adds LIMIT if missing (default 1000)
5. **Conversation memory:** Sqlite checkpointer or in-memory, per thread_id
