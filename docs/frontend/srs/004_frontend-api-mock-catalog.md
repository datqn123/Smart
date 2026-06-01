# SRS - Frontend API Mock Catalog

> Agent: SRS_WRITER  
> Ngay cap nhat: 31/05/2026  
> Trang thai: Draft for frontend mocking  
> Scope chinh: `frontend/mini-erp`  
> Evidence: frontend API clients + backend Spring controllers  
> Muc dich: Liet ke API de frontend co the mock data va hien thi giao dien doc lap voi backend.

## 1. Tom Tat

Frontend Mini-ERP dang goi API qua `apiJson`/`apiFormData` trong `frontend/mini-erp/src/lib/api/http.ts`. Tat ca JSON response thanh cong can mock theo envelope:

```json
{
  "success": true,
  "data": {}
}
```

Loi can mock theo envelope:

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Du lieu khong hop le. Vui long kiem tra lai.",
  "details": {
    "field": "Thong tin loi theo field"
  }
}
```

## 2. Input Va Traceability

- Frontend route index: `docs/frontend/mini-erp/features/FEATURES_UI_INDEX.md` hoac fallback `docs/dev/frontend/mini-erp/features/FEATURES_UI_INDEX.md`.
- Frontend API gateway: `frontend/mini-erp/src/lib/api/http.ts`.
- API client files:
  - `features/auth/api/authApi.ts`
  - `features/inventory/api/*.ts`
  - `features/product-management/api/*.ts`
  - `features/orders/api/*.ts`
  - `features/cashflow/api/*.ts`
  - `features/settings/api/*.ts`
  - `features/approvals/api/approvalsApi.ts`
  - `features/notifications/api/notificationsApi.ts`
  - `features/ai/api/*.ts`
- Backend controllers under `backend/smart-erp/src/main/java/com/example/smart_erp/**/controller`.

## 3. Scope

### 3.1 In Scope

- Liet ke endpoint FE dang can mock de render man hinh.
- Neu endpoint la mutation, van liet ke de mock optimistic/invalidate flow.
- Ghi shape data toi thieu de table/card/dialog co du field hien thi.
- Ghi RBAC/permission de mock role-based UI.

### 3.2 Out Of Scope

- Khong tao MSW handlers trong task nay.
- Khong doi code frontend/backend.
- Khong dinh nghia day du business validation cho moi mutation.
- Khong thay the API docs chi tiet da co.

## 4. Mocking Rules

- Moi mock JSON thanh cong phai tra `{ success: true, data }`.
- Moi mock loi phai tra `{ success: false, error, message, details? }`.
- API co `auth: true` nen chap nhan header `Authorization: Bearer <token>` trong mock.
- List response nen co pagination fields thong dung: `items`, `page`, `limit`, `total`, `totalPages`.
- Date/time dung ISO string. Money/quantity dung number.
- Status string giu dung casing FE dang dung, vi table badge/filter phu thuoc vao status.

## 5. API Mock Catalog Theo Man Hinh

### 5.1 Authentication

| Method | Path | Mock data can co | Ghi chu |
| :--- | :--- | :--- | :--- |
| POST | `/api/v1/auth/login` | `accessToken`, `refreshToken`, `user`, `permissions` | Login page, luu sessionStorage |
| POST | `/api/v1/auth/refresh` | `accessToken`, optional `refreshToken` | Auto refresh khi 401 |
| POST | `/api/v1/auth/logout` | object rong | Logout |
| POST | `/api/v1/auth/password-reset-requests` | object rong/message | Form quen mat khau |

Mock user toi thieu:

```json
{
  "id": 1,
  "username": "owner",
  "fullName": "Chu cua hang",
  "role": "Owner",
  "permissions": ["can_manage_inventory", "can_manage_products", "can_manage_orders", "can_manage_staff"]
}
```

### 5.2 Dashboard Va Notifications

| Method | Path | Mock data can co | Ghi chu |
| :--- | :--- | :--- | :--- |
| GET | `/api/v1/notifications?page=&limit=&unreadOnly=` | `items`, `unreadCount`, pagination | Header notification bell |
| PATCH | `/api/v1/notifications/{id}` | updated notification | Mark one read |
| POST | `/api/v1/notifications/mark-all-read` | object rong | Mark all read |

Notification item toi thieu: `id`, `type`, `title`, `message`, `read`, `createdAt`, `entityType`, `entityId`.

### 5.3 Inventory - Ton Kho

| Method | Path | Permission | Mock data can co |
| :--- | :--- | :--- | :--- |
| GET | `/api/v1/inventory/summary` | `can_manage_inventory` | `totalSku`, `lowStockCount`, `outOfStockCount`, `expiringSoonCount` |
| GET | `/api/v1/inventory` | `can_manage_inventory` | `items`, pagination |
| GET | `/api/v1/inventory/{id}` | `can_manage_inventory` | inventory detail + related lines |
| PATCH | `/api/v1/inventory/{id}` | `can_manage_inventory` | updated inventory item |
| PATCH | `/api/v1/inventory/bulk` | `can_manage_inventory` | `updatedCount`, `items` |

Inventory item toi thieu: `id`, `productId`, `skuCode`, `productName`, `location`, `quantity`, `unit`, `expiryDate`, `status`, `updatedAt`.

### 5.4 Inventory - Nhap Kho

| Method | Path | Permission | Mock data can co |
| :--- | :--- | :--- | :--- |
| GET | `/api/v1/stock-receipts` | `can_manage_inventory` | list receipt |
| POST | `/api/v1/stock-receipts` | `can_manage_inventory` | created receipt detail |
| GET | `/api/v1/stock-receipts/{id}` | `can_manage_inventory` | receipt detail + lines |
| PATCH | `/api/v1/stock-receipts/{id}` | `can_manage_inventory` | updated receipt detail |
| DELETE | `/api/v1/stock-receipts/{id}` | `can_manage_inventory` | `null` |
| POST | `/api/v1/stock-receipts/{id}/submit` | `can_manage_inventory` | status `Pending` |
| POST | `/api/v1/stock-receipts/{id}/approve` | `can_approve` | status `Approved` |
| POST | `/api/v1/stock-receipts/{id}/reject` | `can_approve` | status `Rejected` |

Receipt fields toi thieu: `id`, `receiptCode`, `supplierName`, `receiptDate`, `staffName`, `lineCount`, `totalAmount`, `status`, `details`.

### 5.5 Inventory - Xuat Kho Va Dieu Phoi

| Method | Path | Permission | Mock data can co |
| :--- | :--- | :--- | :--- |
| GET | `/api/v1/stock-dispatches` | `can_manage_inventory` | list dispatch |
| POST | `/api/v1/stock-dispatches` | `can_manage_inventory` | created dispatch |
| POST | `/api/v1/stock-dispatches/from-order` | `can_manage_inventory` | created dispatch from order |
| GET | `/api/v1/stock-dispatches/{id}` | `can_manage_inventory` | dispatch detail + lines |
| PATCH | `/api/v1/stock-dispatches/{id}` | `can_manage_inventory` | updated dispatch |
| POST | `/api/v1/stock-dispatches/{id}/approve` | `can_manage_inventory` | approved dispatch |
| POST | `/api/v1/stock-dispatches/{id}/soft-delete` | `can_manage_inventory` | object rong |

Dispatch fields toi thieu: `id`, `dispatchCode`, `orderCode`, `customerName`, `dispatchDate`, `userName`, `itemCount`, `status`, `lines`.

### 5.6 Inventory - Kiem Ke

| Method | Path | Permission | Mock data can co |
| :--- | :--- | :--- | :--- |
| GET | `/api/v1/inventory/audit-sessions` | `can_manage_inventory` | list audit sessions |
| POST | `/api/v1/inventory/audit-sessions` | `can_manage_inventory` | created session |
| GET | `/api/v1/inventory/audit-sessions/{id}` | `can_manage_inventory` | detail + lines |
| PATCH | `/api/v1/inventory/audit-sessions/{id}` | `can_manage_inventory` | updated session |
| PATCH | `/api/v1/inventory/audit-sessions/{id}/lines` | `can_manage_inventory` | updated lines |
| POST | `/api/v1/inventory/audit-sessions/{id}/complete` | `can_manage_inventory` | completed session |
| POST | `/api/v1/inventory/audit-sessions/{id}/approve` | `can_manage_inventory` | approved session |
| POST | `/api/v1/inventory/audit-sessions/{id}/reject` | `can_manage_inventory` | rejected session |
| POST | `/api/v1/inventory/audit-sessions/{id}/cancel` | `can_manage_inventory` | canceled session |
| DELETE | `/api/v1/inventory/audit-sessions/{id}` | `can_manage_inventory` | `null` |

### 5.7 Product Management

| Method | Path | Permission | Mock data can co |
| :--- | :--- | :--- | :--- |
| GET | `/api/v1/categories` | `can_manage_products` | category tree/list |
| GET | `/api/v1/categories/{id}` | `can_manage_products` | category detail |
| POST | `/api/v1/categories` | `can_manage_products` | created category |
| PATCH | `/api/v1/categories/{id}` | `can_manage_products` | updated category |
| DELETE | `/api/v1/categories/{id}` | `can_manage_products` | delete result |
| GET | `/api/v1/products` | `can_manage_products` | product list |
| POST | `/api/v1/products` | `can_manage_products` | created product, JSON hoac multipart |
| GET | `/api/v1/products/{id}` | `can_manage_products` | product detail + units + images |
| PATCH | `/api/v1/products/{id}` | `can_manage_products` | updated product |
| DELETE | `/api/v1/products/{id}` | `can_manage_products` | delete result |
| POST | `/api/v1/products/bulk-delete` | `can_manage_products` | bulk delete result |
| POST | `/api/v1/products/{id}/images` | `can_manage_products` | image dto |
| GET | `/api/v1/suppliers` | `can_manage_products` | supplier list |
| POST | `/api/v1/suppliers` | `can_manage_products` | supplier detail |
| GET | `/api/v1/suppliers/{id}` | `can_manage_products` | supplier detail |
| PATCH | `/api/v1/suppliers/{id}` | `can_manage_products` | updated supplier |
| DELETE | `/api/v1/suppliers/{id}` | `can_manage_products` | delete result |
| POST | `/api/v1/suppliers/bulk-delete` | `can_manage_products` | bulk delete result |
| GET | `/api/v1/customers` | `can_manage_customers` | customer list |
| POST | `/api/v1/customers` | `can_manage_customers` | customer detail |
| GET | `/api/v1/customers/{id}` | `can_manage_customers` | customer detail |
| PATCH | `/api/v1/customers/{id}` | `can_manage_customers` | updated customer |
| DELETE | `/api/v1/customers/{id}` | `can_manage_customers` | delete result |
| POST | `/api/v1/customers/bulk-delete` | `can_manage_customers` | bulk delete result |

Product item toi thieu: `id`, `skuCode`, `name`, `categoryName`, `unitName`, `sellingPrice`, `status`, `imageUrl`.  
Supplier/customer item toi thieu: `id`, `code`, `name`, `phone`, `email`, `status`, `createdAt`.

### 5.8 Orders And POS

| Method | Path | Permission | Mock data can co |
| :--- | :--- | :--- | :--- |
| GET | `/api/v1/sales-orders` | `can_manage_orders` | order list |
| GET | `/api/v1/sales-orders/retail/history` | `can_manage_orders` | retail history list |
| GET | `/api/v1/sales-orders/{id}` | `can_manage_orders` | order detail + lines |
| POST | `/api/v1/sales-orders` | `can_manage_orders` | created order |
| PATCH | `/api/v1/sales-orders/{id}` | `can_manage_orders` | updated order |
| POST | `/api/v1/sales-orders/{id}/cancel` | `can_manage_orders` | canceled order |
| POST | `/api/v1/sales-orders/retail/checkout` | `can_manage_orders` | checkout order detail |
| POST | `/api/v1/sales-orders/retail/voucher-preview` | `can_manage_orders` | discount preview |
| GET | `/api/v1/pos/products` | `can_manage_orders` | searchable POS products |
| GET | `/api/v1/vouchers` | `can_manage_orders` | voucher list |
| GET | `/api/v1/vouchers/{id}` | `can_manage_orders` | voucher detail |

Order item toi thieu: `id`, `orderCode`, `customerName`, `orderDate`, `channel`, `status`, `totalAmount`, `paymentStatus`.  
POS product toi thieu: `productId`, `skuCode`, `name`, `price`, `stockQuantity`, `unitName`, `imageUrl`.

### 5.9 Approvals

| Method | Path | Mock data can co |
| :--- | :--- | :--- |
| GET | `/api/v1/approvals/pending` | pending approval list |
| GET | `/api/v1/approvals/history` | approval history list |

Approval item toi thieu: `id`, `entityType`, `entityId`, `code`, `requestedBy`, `requestedAt`, `status`, `amount`.

### 5.10 Cashflow

| Method | Path | Mock data can co |
| :--- | :--- | :--- |
| GET | `/api/v1/cash-funds` | fund list |
| GET | `/api/v1/cash-transactions` | transaction list |
| POST | `/api/v1/cash-transactions` | created transaction |
| GET | `/api/v1/cash-transactions/{id}` | transaction detail |
| PATCH | `/api/v1/cash-transactions/{id}` | updated transaction |
| DELETE | `/api/v1/cash-transactions/{id}` | `null` |
| GET | `/api/v1/finance-ledger` | ledger list |

Cash transaction fields toi thieu: `id`, `transactionCode`, `type`, `fundName`, `amount`, `description`, `transactionDate`, `createdByName`.

### 5.11 Settings

| Method | Path | Permission | Mock data can co |
| :--- | :--- | :--- | :--- |
| GET | `/api/v1/store-profile` | `can_view_store_profile` | store profile |
| PATCH | `/api/v1/store-profile` | `can_view_store_profile` | updated store profile |
| POST | `/api/v1/store-profile/logo` | `can_view_store_profile` | logo url |
| GET | `/api/v1/roles` | `can_manage_staff` | role list |
| GET | `/api/v1/users` | `can_manage_staff` | employee list |
| GET | `/api/v1/users/{id}` | staff detail permission | employee detail |
| GET | `/api/v1/users/next-staff-code` | `can_manage_staff` | `staffCode` |
| POST | `/api/v1/users` | `can_manage_staff` | created user |
| PATCH | `/api/v1/users/{id}` | `can_manage_staff` | updated user |
| DELETE | `/api/v1/users/{id}` | `can_manage_staff` | `null` |
| GET | `/api/v1/alert-settings` | authenticated/settings | alert settings list |
| POST | `/api/v1/alert-settings` | authenticated/settings | created setting |
| PATCH | `/api/v1/alert-settings/{id}` | authenticated/settings | updated setting |
| DELETE | `/api/v1/alert-settings/{id}` | authenticated/settings | `null` |
| GET | `/api/v1/system-logs` | admin/settings | system log list |
| GET | `/api/v1/system-logs/{id}` | admin/settings | system log detail |
| DELETE | `/api/v1/system-logs/{id}` | admin/settings | `null` |
| POST | `/api/v1/system-logs/bulk-delete` | admin/settings | bulk delete result |
| GET | `/api/v1/interface-settings/table-columns?scope=inventory` | `can_manage_inventory` | table column settings |
| PUT | `/api/v1/interface-settings/table-columns` | `can_manage_inventory` | normalized table column settings |

Table column settings mock toi thieu:

```json
{
  "items": [
    {
      "tableKey": "inventory_stock",
      "tableLabel": "Ton kho",
      "columns": [
        { "key": "skuCode", "label": "Ma SP", "required": true, "visible": true, "order": 0 }
      ],
      "updatedAt": "2026-05-31T10:20:30Z",
      "updatedByName": "Chu cua hang"
    }
  ]
}
```

### 5.12 AI Assistant

| Method | Path | Permission | Mock data can co |
| :--- | :--- | :--- | :--- |
| POST | `/api/v1/ai/chat/stream` | AI access | SSE events: `message`, `table`, `chart`, `draft`, `done`, `error` |
| POST | `/api/v1/ai/chat/transcribe` | AI access | `{ text }` |
| POST | `/api/v1/ai/chat/synthesize` | AI access | audio payload/url |
| POST | `/api/v1/ai/catalog-drafts/validate` | `can_use_ai` | validation result |
| GET | `/api/v1/ai/catalog-drafts/{id}` | `can_use_ai` | draft detail |
| PATCH | `/api/v1/ai/catalog-drafts/{id}` | `can_use_ai` | updated draft |
| POST | `/api/v1/ai/catalog-drafts/{id}/commit` | `can_use_ai` | commit result |
| DELETE | `/api/v1/ai/catalog-drafts/{id}` | `can_use_ai` | `null` |
| POST | `/api/v1/ai/inventory-drafts/validate` | `can_use_ai`, `can_manage_inventory` | validation result |
| GET | `/api/v1/ai/inventory-drafts/{id}` | `can_use_ai`, `can_manage_inventory` | draft detail |
| PATCH | `/api/v1/ai/inventory-drafts/{id}` | `can_use_ai`, `can_manage_inventory` | updated draft |
| POST | `/api/v1/ai/inventory-drafts/{id}/commit` | `can_use_ai`, `can_manage_inventory` | commit result |
| DELETE | `/api/v1/ai/inventory-drafts/{id}` | `can_use_ai`, `can_manage_inventory` | `null` |

AI mock can tach ro:

- LangGraph/SSE = orchestrator event stream.
- Harness = ket qua validate/commit co tinh deterministic.
- Tools = data query/table/chart/draft payload, khong mock thanh side effect that khi chua commit.

## 6. Query Parameters Chuan Can Mock

Ap dung cho list endpoint neu frontend co filter:

- Pagination: `page`, `limit`.
- Search: `search`, `q`, `keyword`.
- Sort: `sort`.
- Status filter: `status`.
- Date filter: `fromDate`, `toDate`, `startDate`, `endDate`.
- Domain filter:
  - Inventory: `stockLevel`, `categoryId`, `productId`, `locationId`, `supplierId`.
  - Orders: `channel`, `paymentStatus`, `customerId`.
  - Cashflow: `type`, `fundId`.

Mock handler nen chap nhan tham so khong dung va tra data mac dinh, tru khi test validation cu the.

## 7. Horizontal Analysis

- API clients co cung convention envelope, nen mock global nen dat o layer chung thay vi tung page.
- Cac list page deu can pagination metadata; neu mock thieu `total`/`totalPages`, table va load-more co the hien sai.
- Cac mutation nen tra object cap nhat thay vi message-only de React Query invalidate/refetch khong bi loi type.
- Auth refresh la luong ngang: moi endpoint `auth: true` co the bi 401 va goi `/api/v1/auth/refresh`.
- AI stream khac JSON API: mock SSE rieng, khong dung envelope JSON cho event stream.

## 8. Acceptance Criteria

```gherkin
Given frontend chay voi mock server
When user dang nhap thanh cong
Then mock POST /api/v1/auth/login tra accessToken, refreshToken, user va permissions
And giao dien vao dashboard duoc
```

```gherkin
Given user mo man Ton kho
When frontend goi /api/v1/inventory/summary va /api/v1/inventory
Then mock tra KPI va danh sach item du field de table render
```

```gherkin
Given user mo Quan ly san pham
When frontend goi categories, products, suppliers, customers
Then mock tra list/detail du field cho table, dialog va form sua
```

```gherkin
Given user mo tro ly AI
When frontend goi /api/v1/ai/chat/stream
Then mock tra SSE events du de hien message, table/chart hoac draft
```

## 9. Open Questions

- OQ-1: Co can tao MSW implementation theo catalog nay ngay trong frontend khong? Khong blocker cho tai lieu.
- OQ-2: Role mock mac dinh nen la Owner full permission hay tach nhieu persona Owner/Admin/Staff? De xuat tao 3 persona de test menu/RBAC.
- OQ-3: Cac endpoint analytics `/analytics/revenue` va `/analytics/top-products` hien chua thay API client ro trong evidence; neu can render data dong, can bo sung API contract rieng.

## 10. PO Sign-off

- Trang thai: cho review.
- SRS path: `docs/frontend/srs/004_frontend-api-mock-catalog.md`.

