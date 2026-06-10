# Reference Docs Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate `docs/reference/` as the single source of truth for agents by generating tables docs, writing per-module API contracts, deleting outdated API design docs, and updating agent instructions.

**Architecture:** Backend is Spring Boot 3.5.14 at `backend/smart-erp/` with 32 production controllers across 11 modules. All data access uses JdbcTemplate (no JPA except 3 entities in auth). API response envelope: `{ success: boolean, data: T, message: string }`.

**Tech Stack:** Spring Boot 3.5.14, Java 21, SpringDoc OpenAPI (Swagger at `/swagger-ui.html`)

---

### Task 1: Delete outdated API design docs

**Files:**
- Delete: `docs/dev/frontend/api/` (entire directory tree)

- [ ] **Step 1: Remove API_Task*.md and BRIDGE files**

Run:
```powershell
Remove-Item -LiteralPath "docs/dev/frontend/api" -Recurse -Force
```

- [ ] **Step 2: Verify deletion**

Run:
```powershell
Test-Path -LiteralPath "docs/dev/frontend/api"
```
Expected: `False`

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "docs: remove outdated API_Task and BRIDGE design docs from dev/"
```

---

### Task 2: Generate tables docs from DB schema

**Files:**
- Run: `python scripts/db-docs.py`
- Creates: `docs/reference/tables/`

- [ ] **Step 1: Run the db-docs script**

Run:
```powershell
python scripts/db-docs.py
```
Expected: Script connects to PostgreSQL and generates `docs/reference/tables/README.md`, `core_tables.md`, `indexes.md`, `foreign_keys.md`.

- [ ] **Step 2: Verify output**

Run:
```powershell
Get-ChildItem -LiteralPath "docs/reference/tables"
```
Expected: At least 4 files present.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "docs: generate reference/tables/ from DB schema via db-docs.py"
```

---

### Task 3: Write `auth.md` API contract

**Files:**
- Read: `backend/smart-erp/src/main/java/com/example/smart_erp/auth/controller/AuthController.java`
- Read: `backend/smart-erp/src/main/java/com/example/smart_erp/auth/controller/RolesController.java`
- Read: All files in `backend/smart-erp/src/main/java/com/example/smart_erp/auth/dto/`
- Read: All files in `backend/smart-erp/src/main/java/com/example/smart_erp/auth/response/`
- Create: `docs/reference/api-contracts/auth.md`

- [ ] **Step 1: Read AuthController.java to list endpoints**

Endpoints found:
| Method | Path | Auth |
|--------|------|------|
| POST | `/api/v1/auth/login` | Public |
| POST | `/api/v1/auth/refresh` | Public |
| POST | `/api/v1/auth/logout` | JWT (Bearer) |
| POST | `/api/v1/auth/password-reset-requests` | Public |

DTOs: `LoginRequest(email, password)`, `RefreshRequest(refreshToken)`, `LogoutRequest(refreshToken)`, `PasswordResetRequestDto(username, message?)`.

Responses: `LoginResponseData(accessToken, refreshToken, user: LoginUserDto{id, username, fullName, email, role})`, `RefreshResponseData(accessToken, refreshToken)`.

Read `RolesController.java` for `GET /api/v1/roles` — response is `ApiSuccessResponse<List<RolesListData>>`.

- [ ] **Step 2: Write `docs/reference/api-contracts/auth.md`**

```markdown
# Auth API Contracts

Base path: `/api/v1/auth`

> Response envelope: `{ success: boolean, data: T, message: string }`

## POST /api/v1/auth/login

**Mô tả:** Đăng nhập bằng email và mật khẩu.

**Auth:** Public

**Request body:**
```json
{
  "email": "string (email, required) — Email người dùng",
  "password": "string (min 6, required) — Mật khẩu"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "accessToken": "string — JWT access token",
    "refreshToken": "string — Refresh token",
    "user": {
      "id": "int",
      "username": "string",
      "fullName": "string",
      "email": "string",
      "role": "string — Tên role"
    }
  },
  "message": "Đăng nhập thành công"
}
```

**Errors:** 400 (validation), 401 (sai email/mật khẩu)

---

## POST /api/v1/auth/refresh

**Mô tả:** Làm mới access token bằng refresh token.

**Auth:** Public

**Request body:**
```json
{
  "refreshToken": "string (required) — Refresh token"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "accessToken": "string — JWT access token mới",
    "refreshToken": "string — Refresh token mới"
  },
  "message": "Token đã được làm mới"
}
```

**Errors:** 400 (validation), 401 (token hết hạn/không hợp lệ)

---

## POST /api/v1/auth/logout

**Mô tả:** Đăng xuất, hủy session và refresh token.

**Auth:** JWT (Bearer token trong `Authorization` header)

**Headers:**
- `Authorization: Bearer <accessToken>`
- `X-Client-Session-Id` (optional)

**Request body:**
```json
{
  "refreshToken": "string (required) — Refresh token cần hủy"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {},
  "message": "Đăng xuất thành công và đã hủy các phiên làm việc"
}
```

**Errors:** 401 (token không hợp lệ)

---

## POST /api/v1/auth/password-reset-requests

**Mô tả:** Gửi yêu cầu đặt lại mật khẩu (public).

**Auth:** Public

**Request body:**
```json
{
  "username": "string (max 100, required) — Tên đăng nhập",
  "message": "string (max 500, optional) — Ghi chú"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {},
  "message": "Yêu cầu đã được gửi đến quản trị viên"
}
```

**Errors:** 400 (validation)

---

## GET /api/v1/roles

**Mô tả:** Danh sách roles.

**Auth:** JWT + `can_manage_staff`

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "id": "int",
      "name": "string — Tên role",
      "permissions": "object — JSONB permissions map"
    }
  ],
  "message": "Thao tác thành công"
}
```

**Errors:** 403 (thiếu quyền)
```

- [ ] **Step 3: Verify file content**

Run:
```powershell
Get-Item -LiteralPath "docs/reference/api-contracts/auth.md"
```
Expected: File exists and is non-empty.

- [ ] **Step 4: Commit**

```bash
git add docs/reference/api-contracts/auth.md
git commit -m "docs: add auth API contract reference"
```

---

### Task 4: Write `users.md` API contract

**Files:**
- Read: `UsersController.java` (`/api/v1/users/next-staff-code`, `POST /api/v1/users`)
- Read: `UsersManagementController.java` (`GET/PATCH/DELETE /api/v1/users[/{userId}]`)
- Read: `users/dto/UserCreateRequest.java`, `UserPatchRequest.java`
- Create: `docs/reference/api-contracts/users.md`

- [ ] **Step 1: Read controllers + DTOs**

Endpoints:
| Method | Path | Auth |
|--------|------|------|
| GET | `/api/v1/users/next-staff-code` | JWT + can_manage_staff |
| POST | `/api/v1/users` | JWT + can_manage_staff |
| GET | `/api/v1/users` | JWT + can_manage_staff |
| GET | `/api/v1/users/{userId}` | JWT + can_manage_staff |
| PATCH | `/api/v1/users/{userId}` | JWT + can_manage_staff |
| DELETE | `/api/v1/users/{userId}` | JWT + can_manage_staff |

DTOs: `UserCreateRequest`, `UserPatchRequest`

- [ ] **Step 2: Write `docs/reference/api-contracts/users.md`**

Same format as `auth.md` (Task 3). Document all 6 endpoints with request body fields from DTOs and response fields from response classes.

- [ ] **Step 3: Commit**

```bash
git add docs/reference/api-contracts/users.md
git commit -m "docs: add users API contract reference"
```

---

### Task 5: Write `catalog.md` API contract

**Files:**
- Read: All 4 catalog controllers + their DTOs and responses
- Controllers: `ProductsController`, `CategoriesController`, `CustomersController`, `SuppliersController`
- DTOs: All files under `catalog/dto/`, `catalog/response/`
- Create: `docs/reference/api-contracts/catalog.md`

- [ ] **Step 1: Read controllers + DTOs**

Endpoints to document:
- Products: GET `/api/v1/products`, POST (JSON + multipart), GET `/{id}`, PATCH `/{id}`, DELETE `/{id}`, POST `/bulk-delete`, POST `/{id}/images` (JSON + multipart)
- Categories: GET `/api/v1/categories`, GET `/{id}`, POST, PATCH `/{id}`, DELETE `/{id}`
- Customers: GET `/api/v1/customers`, POST, GET `/{id}`, PATCH `/{id}`, DELETE `/{id}`, POST `/bulk-delete`
- Suppliers: GET `/api/v1/suppliers`, POST, GET `/{id}`, PATCH `/{id}`, DELETE `/{id}`, POST `/bulk-delete`

- [ ] **Step 2: Write `docs/reference/api-contracts/catalog.md`**

Same format as `auth.md`. Document all endpoints with request/response schemas from DTOs.

- [ ] **Step 3: Commit**

```bash
git add docs/reference/api-contracts/catalog.md
git commit -m "docs: add catalog API contract reference"
```

---

### Task 6: Write `inventory.md` API contract

**Files:**
- Read: All 5 inventory controllers + their DTOs and responses
- Controllers: `InventoryController`, `StockReceiptsController`, `StockDispatchesController`, `AuditSessionsController`, `ApprovalsController`
- DTOs: Under each sub-module (`inventory/dispatch/dto/`, `inventory/receipts/dto/`, `inventory/audit/dto/`, etc.)
- Create: `docs/reference/api-contracts/inventory.md`

- [ ] **Step 1: Read controllers**

Endpoints to document:
- Inventory: GET `/api/v1/inventory/summary`, GET `/api/v1/inventory`, GET `/{id}`, PATCH `/{id}`, PATCH `/bulk`
- StockReceipts: GET `/api/v1/stock-receipts`, POST, GET `/{id}`, PATCH `/{id}`, DELETE `/{id}`, POST `/{id}/submit`, POST `/{id}/approve`, POST `/{id}/reject`
- StockDispatches: GET `/api/v1/stock-dispatches`, GET `/{id}`, POST, POST `/from-order`, POST `/{id}/approve`, PATCH `/{id}`, POST `/{id}/soft-delete`
- AuditSessions: GET/POST `/api/v1/inventory/audit-sessions`, GET/PATCH `/{id}`, PATCH `/{id}/lines`, POST `/{id}/complete`, POST `/{id}/approve`, POST `/{id}/reject`, DELETE `/{id}`, POST `/{id}/cancel`, POST `/{id}/apply-variance`
- Approvals: GET `/api/v1/approvals/pending`, GET `/api/v1/approvals/history`

- [ ] **Step 2: Write `docs/reference/api-contracts/inventory.md`**

Same format as `auth.md` (Task 3). Document all ~30 endpoints across 5 controllers.

- [ ] **Step 3: Commit**

```bash
git add docs/reference/api-contracts/inventory.md
git commit -m "docs: add inventory API contract reference"
```

---

### Task 7: Write `sales.md` API contract

**Files:**
- Read: `SalesOrdersController`, `PosProductsController`, `VouchersController` + their DTOs
- DTOs: `sales/dto/`
- Create: `docs/reference/api-contracts/sales.md`

- [ ] **Step 1: Read controllers**

Endpoints:
- SalesOrders: GET `/api/v1/sales-orders/retail/history`, GET `/api/v1/sales-orders`, GET `/{id}`, POST, POST `/retail/checkout`, POST `/retail/voucher-preview`, PATCH `/{id}`, POST `/{id}/cancel`
- PosProducts: GET `/api/v1/pos/products` (search)
- Vouchers: GET `/api/v1/vouchers`, GET `/{id}`

- [ ] **Step 2: Write `docs/reference/api-contracts/sales.md`**

Same format as `auth.md` (Task 3). Include request DTO fields for retail checkout, voucher preview, etc.

- [ ] **Step 3: Commit**

```bash
git add docs/reference/api-contracts/sales.md
git commit -m "docs: add sales API contract reference"
```

---

### Task 8: Write `finance.md` API contract

**Files:**
- Read: 5 finance controllers + their DTOs/responses
- Controllers: `FinanceLedgerController`, `CashTransactionsController`, `CashflowMovementsController`, `CashFundsController`, `DebtsController`
- DTOs: Under each sub-module (`finance/cashfunds/request/`, `finance/cashtx/request/`, `finance/debts/request/`)
- Create: `docs/reference/api-contracts/finance.md`

- [ ] **Step 1: Read controllers**

Endpoints:
- FinanceLedger: GET `/api/v1/finance-ledger`
- CashTransactions: GET/POST `/api/v1/cash-transactions`, GET/PATCH/DELETE `/{id}`
- CashflowMovements: GET `/api/v1/cashflow/movements`
- CashFunds: GET/POST `/api/v1/cash-funds`, PATCH `/{id}`
- Debts: GET/POST `/api/v1/debts`, GET/PATCH `/{id}`

- [ ] **Step 2: Write `docs/reference/api-contracts/finance.md`**

Same format as `auth.md` (Task 3). Document request DTO fields for transactions, funds, debts.

- [ ] **Step 3: Commit**

```bash
git add docs/reference/api-contracts/finance.md
git commit -m "docs: add finance API contract reference"
```

---

### Task 9: Write `ai.md` API contract

**Files:**
- Read: 4 AI controllers + their DTOs
- Controllers: `AiChatRelayController`, `AiCatalogDraftController`, `AiInventoryDraftController`, `AiDbReadonlyController`
- DTOs: Under each sub-module (`ai/catalogdraft/dto/`, `ai/inventorydraft/dto/`, `ai/dbreadonly/dto/`)
- Create: `docs/reference/api-contracts/ai.md`

- [ ] **Step 1: Read controllers**

Endpoints:
- AiChatRelay: POST `/api/v1/ai/chat/stream` (SSE), POST `/api/v1/ai/chat/transcribe` (multipart), POST `/api/v1/ai/chat/synthesize`
- AiCatalogDraft: POST `/api/v1/ai/catalog-drafts/validate`, POST, GET `/{id}`, PATCH `/{id}`, POST `/{id}/commit`
- AiInventoryDraft: POST `/api/v1/ai/inventory-drafts/validate`, POST, GET `/{id}`, PATCH `/{id}`, POST `/{id}/commit`
- AiDbReadonly: POST `/api/v1/ai/db/sql/describe`, POST `/api/v1/ai/db/sql/query-readonly`, POST `/api/v1/ai/db/sql/query-readonly-raw`

- [ ] **Step 2: Write `docs/reference/api-contracts/ai.md`**

Same format as `auth.md` (Task 3). Note SSE response for chat stream, multipart for transcribe.

- [ ] **Step 3: Commit**

```bash
git add docs/reference/api-contracts/ai.md
git commit -m "docs: add AI API contract reference"
```

---

### Task 10: Write `dashboard.md` + `notifications.md` API contracts

**Files:**
- Read: `DashboardController.java`
- Read: `NotificationsController.java` + response DTOs
- Create: `docs/reference/api-contracts/dashboard.md`
- Create: `docs/reference/api-contracts/notifications.md`

- [ ] **Step 1: Read controllers**

Dashboard: GET `/api/v1/dashboard` (JWT + can_view_dashboard)

Notifications: GET `/api/v1/notifications`, PATCH `/{id}`, POST `/mark-all-read`

- [ ] **Step 2: Write `docs/reference/api-contracts/dashboard.md`**

Same format as `auth.md` (Task 3). Dashboard response includes KPIs/summary data.

- [ ] **Step 3: Write `docs/reference/api-contracts/notifications.md`**

Same format as `auth.md` (Task 3).

- [ ] **Step 4: Commit**

```bash
git add docs/reference/api-contracts/dashboard.md docs/reference/api-contracts/notifications.md
git commit -m "docs: add dashboard and notifications API contract references"
```

---

### Task 11: Write `settings.md` API contract

**Files:**
- Read: `StoreProfileController`, `SystemLogsController`, `AlertSettingsController`, `InterfaceSettingsTableColumnsController`
- DTOs: Under `settings/alerts/dto/`, `settings/tablecolumns/dto/`
- Create: `docs/reference/api-contracts/settings.md`

- [ ] **Step 1: Read controllers**

Endpoints:
- StoreProfile: GET/PATCH `/api/v1/store-profile`, POST `/logo`
- SystemLogs: GET `/api/v1/system-logs`, GET/DELETE `/{id}`, POST `/bulk-delete`
- AlertSettings: GET/POST `/api/v1/alert-settings`, PATCH/DELETE `/{id}`
- InterfaceSettingsTableColumns: GET/PUT `/api/v1/interface-settings/table-columns`

- [ ] **Step 2: Write `docs/reference/api-contracts/settings.md`**

Same format as `auth.md` (Task 3).

- [ ] **Step 3: Commit**

```bash
git add docs/reference/api-contracts/settings.md
git commit -m "docs: add settings API contract reference"
```

---

### Task 12: Write `custom-interface.md` API contract

**Files:**
- Read: `CustomInterfaceController.java` + its DTOs
- Create: `docs/reference/api-contracts/custom-interface.md`

- [ ] **Step 1: Read CustomInterfaceController**

Endpoints:
- GET `/api/v1/custom/menu-tree`
- POST `/api/v1/custom/menu-folders`, PATCH `/{folderKey}`, PATCH `/{folderKey}/archive`
- POST `/api/v1/custom/menu-pages`, PATCH `/{pageKey}`, PATCH `/{pageKey}/archive`
- POST `/api/v1/custom/menu/reorder`
- POST `/api/v1/custom/menu/validate`
- POST `/api/v1/custom/menu/publish`
- GET `/api/v1/custom/runtime-menu`
- GET `/api/v1/custom/pages/{pageKey}/runtime`

- [ ] **Step 2: Write `docs/reference/api-contracts/custom-interface.md`**

Same format as `auth.md` (Task 3). Include DTO fields for folder/page create requests.

- [ ] **Step 3: Commit**

```bash
git add docs/reference/api-contracts/custom-interface.md
git commit -m "docs: add custom interface API contract reference"
```

---

### Task 13: Update agent instructions

**Files:**
- Modify: `.opencode/instructions.md`
- Modify: `docs/README.md`

- [ ] **Step 1: Read current instruction files**

Read both `.opencode/instructions.md` and `docs/README.md`.

- [ ] **Step 2: Rewrite `.opencode/instructions.md`**

Replace current content:

```markdown
# Agent Instructions — Docs Management

## Cấu trúc docs

- `docs/reference/` — Tài liệu active, agent PHẢI đọc trước khi làm việc
  - `ai-knowledge/` (K1-K15 knowledge base)
  - `guides/` (GUID_ERP, Custom Builder guide)
  - `api-contracts/` (API contracts từng module)
  - `tables/` (DB schema — auto-generated)
- `docs/dev/` — Tài liệu kiến trúc cũ, **KHÔNG đọc** (chỉ tham khảo khi cần thiết)
- `docs/archive/` — Docs cũ, task đã hoàn thành, **KHÔNG đọc**
- `docs/tests/` — Test cases, **KHÔNG đọc**

## Khi bạn thay đổi codebase

1. **DB schema** (thêm/sửa migration Flyway):
   - Chạy `python scripts/db-docs.py` để cập nhật `docs/reference/tables/`
2. **Business logic** lớn:
   - Cập nhật `docs/reference/guides/` tương ứng
3. **API endpoints**:
   - Cập nhật file tương ứng trong `docs/reference/api-contracts/`

## Cách chạy

```bash
# Windows
python scripts\db-docs.py

# Linux/Mac
python scripts/db-docs.py
```
```

- [ ] **Step 3: Update `docs/README.md`**

Ensure it reflects the same changes — reference/ is the primary source, dev/ is not for agents.

- [ ] **Step 4: Commit**

```bash
git add .opencode/instructions.md docs/README.md
git commit -m "docs: update agent instructions to point only to reference/"
```
