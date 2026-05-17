# Mini-ERP — Index giao diện (`src/features/`)

> **Mục đích:** Agent / Dev tra **route → file page → feature** trong **một file**, tránh quét cả `features/`.  
> **Route nguồn:** [`../App.tsx`](../App.tsx) · **Nhãn menu:** [`../components/shared/layout/Sidebar.tsx`](../components/shared/layout/Sidebar.tsx)

---

## 1. Bảng route → màn hình (ưu tiên đọc khi sửa UI)

| Path | Page (export) | File |
| :--- | :--- | :--- |
| `/login` | `LoginPage` | `auth/pages/LoginPage.tsx` |
| `/dashboard` | `DashboardPage` | `dashboard/pages/DashboardPage.tsx` |
| `/dashboard/ai-insights` | *Placeholder* (không trong `features/`) | `App.tsx` |
| `/inventory/stock` | `StockPage` | `inventory/pages/StockPage.tsx` |
| `/inventory/locations` | `WarehouseLocationsPage` | `inventory/pages/WarehouseLocationsPage.tsx` |
| `/inventory/inbound` | `InboundPage` | `inventory/pages/InboundPage.tsx` |
| `/inventory/dispatch` | `DispatchPage` | `inventory/pages/DispatchPage.tsx` |
| `/inventory/audit` | *Redirect* → `/inventory/stock` | `App.tsx` (không còn màn Kiểm kê trong menu) |
| `/products/categories` | `CategoriesPage` | `product-management/pages/CategoriesPage.tsx` |
| `/products/list` | `ProductsPage` | `product-management/pages/ProductsPage.tsx` |
| `/products/suppliers` | `SuppliersPage` | `product-management/pages/SuppliersPage.tsx` |
| `/products/customers` | `CustomersPage` | `product-management/pages/CustomersPage.tsx` |
| `/orders/retail` | `RetailPage` | `orders/pages/RetailPage.tsx` |
| `/orders/wholesale` | `WholesalePage` | `orders/pages/WholesalePage.tsx` — **Lịch sử hóa đơn bán lẻ** (Task102; API `GET …/retail/history`; URL giữ `/orders/wholesale`) |
| `/orders/returns` | `ReturnsPage` | `orders/pages/ReturnsPage.tsx` |
| `/approvals/pending` | `PendingApprovalsPage` (default export) | `approvals/pages/PendingApprovalsPage.tsx` |
| `/approvals/history` | `ApprovalHistoryPage` | `approvals/pages/ApprovalHistoryPage.tsx` |
| `/cashflow/transactions` | `TransactionsPage` | `cashflow/pages/TransactionsPage.tsx` |
| `/cashflow/debt` | `DebtPage` | `cashflow/pages/DebtPage.tsx` |
| `/cashflow/ledger` | `LedgerPage` | `cashflow/pages/LedgerPage.tsx` |
| `/analytics/revenue` | `RevenuePage` | `analytics/pages/RevenuePage.tsx` |
| `/analytics/top-products` | `TopProductsPage` | `analytics/pages/TopProductsPage.tsx` |
| `/ai/chat` | `ChatBotPage` | `ai/pages/ChatBotPage.tsx` |
| `/settings/store-info` | `StoreInfoPage` | `settings/pages/StoreInfoPage.tsx` |
| `/settings/employees` | `EmployeesPage` | `settings/pages/EmployeesPage.tsx` |
| `/settings/alerts` | `AlertSettingsPage` | `settings/pages/AlertSettingsPage.tsx` |
| `/settings/system-logs` | `LogsPage` | `settings/pages/LogsPage.tsx` |

**Ghi chú:** `inventory/pages/CategoriesPage.tsx` **tồn tại** nhưng **không** có `<Route>` trong `App.tsx` (trùng tên với PM categories — chỉ PM route `/products/categories`).

**Thông báo (global, không route riêng):** chuông trên `Header` — [`components/shared/layout/Header.tsx`](../components/shared/layout/Header.tsx); API [`features/notifications/api/notificationsApi.ts`](notifications/api/notificationsApi.ts); click mở `ReceiptDetailDialog` / `DispatchDetailDialog` theo SRS PRD admin-notifications.

---

## 2. Feature → component UI chính (không liệt kê `*.test.tsx`)

### `notifications/`

| Loại | File |
| :--- | :--- |
| API (nối BE) | `api/notificationsApi.ts` — `GET /api/v1/notifications`, `PATCH …/{id}`, `POST …/mark-all-read` |
| Định dạng thời gian | `lib/formatRelativePastVi.ts` |

### `auth/`

| Loại | File |
| :--- | :--- |
| Form đăng nhập | `components/LoginForm.tsx` |
| API (nối BE) | `api/authApi.ts` |

### `dashboard/`

| Loại | File |
| :--- | :--- |
| Trang chủ | `pages/DashboardPage.tsx` |

### `inventory/`

| Loại | File |
| :--- | :--- |
| API (nối BE) | `api/inventoryApi.ts` — Task005–009 tồn kho; `api/stockReceiptsApi.ts` — Task013–017 + submit + approve (Task019) + **reject** `POST …/{id}/reject` (Task020); `api/auditSessionsApi.ts` — Task021–024 + Task025–027 + **GAP SRS** `DELETE …/{id}` (Owner xóa mềm) + `POST …/{id}/approve` + `POST …/{id}/reject` |
| Bảng / toolbar tồn | `components/StockTable.tsx`, `StockToolbar.tsx`, …; `pages/StockPage` — KPI qua Task009 (`getInventorySummary`); 20 bản ghi lần đầu, tải thêm khi **cuộn tới gần cuối** (`useInfiniteQuery`) |
| Nhập kho | `pages/InboundPage.tsx` — list phiếu Task013 (`useInfiniteQuery` + `getStockReceiptList`); `components/ReceiptForm.tsx`, `ReceiptTable.tsx`, `ReceiptDetailPanel.tsx`, `ReceiptDetailDialog.tsx` |
| Xuất / điều phối | `components/DispatchForm.tsx`, `DispatchTable.tsx`, `DispatchDetailDialog.tsx`, `DispatchDetailPanel.tsx` |
| Kho vị trí | `components/LocationTable.tsx`, `LocationToolbar.tsx` |
| Badge trạng thái | `components/StatusBadge.tsx` |

### `product-management/`

| Loại | File |
| :--- | :--- |
| Danh mục | `api/categoriesApi.ts` (Task029–033 — list/detail/create/patch/delete); `pages/CategoriesPage.tsx` (`useQuery` + `useMutation`); `components/CategoryTable.tsx`, `CategoryToolbar.tsx`, `CategoryForm.tsx`, `CategoryDetailDialog.tsx` |
| Sản phẩm | `api/productsApi.ts` (Task034–037, 039 — list/get/patch/post ảnh); `pages/ProductsPage.tsx` (`useQuery` list + detail form); `ProductForm.tsx` (PATCH + create); `ProductDetailDialog.tsx` (**Task036** `useQuery` `getProductById` khi mở dialog); `ProductTable.tsx`, `ProductToolbar.tsx` |
| NCC | `components/SupplierTable.tsx`, `SupplierToolbar.tsx`, `SupplierForm.tsx`, `SupplierDetailDialog.tsx` |
| Khách | `api/customersApi.ts` (Task048 list, Task049 `postCustomer`, Task050 `getCustomerById`, Task051 `patchCustomer` + `buildCustomerPatchBody`, Task052 `deleteCustomer`, Task053 `postCustomersBulkDelete`); `pages/CustomersPage.tsx` (list + form GET detail khi sửa + PATCH/POST + invalidate); `CustomerForm.tsx` (**Task051** ẩn `loyaltyPoints` khi `role=Staff`); `CustomerTable.tsx`, `CustomerToolbar.tsx`, `CustomerDetailDialog.tsx` |

### `orders/`

| Loại | File |
| :--- | :--- |
| API | `api/salesOrdersApi.ts` — Task054 list; **Task102** `GET /api/v1/sales-orders/retail/history`; **Task056** `POST /api/v1/sales-orders`; Task060 `postRetailCheckout`; **Task092** `postRetailVoucherPreview`; Task058 cancel; `api/posProductsApi.ts` — Task059; **`api/vouchersApi.ts`** — Task092 `getVouchersList`, `getVoucherById`; `hooks/useSalesOrdersListQuery.ts` — OQ-8a |
| POS / đơn | `pages/RetailPage.tsx`; `POSCartPanel.tsx` (Task060 checkout; **Task092** danh sách voucher + “Xem thêm”, preview, **409** checkout); `POSProductSelector.tsx` (Task059 `searchPosProducts`); `OrderTable.tsx`, `OrderToolbar.tsx`, `OrderDetailPanel.tsx`, `OrderDetailDialog.tsx`, `OrderFormDialog.tsx` |
| Trang danh sách | `pages/WholesalePage.tsx` — **Task102** `GET /sales-orders/retail/history`; `pages/ReturnsPage.tsx` — Task054 list + phân trang/sort/lọc |
| Trả hàng | `components/ReturnFormDialog.tsx` |

### `approvals/`

| Loại | File |
| :--- | :--- |
| API (nối BE) | `api/approvalsApi.ts` (Task061 `GET …/pending`, Task062 `GET …/history`) |
| Bảng lịch sử | `components/ApprovalHistoryTable.tsx` |
| *(chủ yếu trong `pages/`)* | `PendingApprovalsPage`, `ApprovalHistoryPage` |

### `cashflow/`

| Loại | File |
| :--- | :--- |
| Thu chi | `components/TransactionTable.tsx`, `TransactionToolbar.tsx`, `TransactionFormDialog.tsx`, `TransactionDetailDialog.tsx`, `TransactionDetailModal.tsx` |
| Nợ | `components/DebtTable.tsx`, `DebtToolbar.tsx` |
| Sổ cái | `components/LedgerTable.tsx`, `LedgerToolbar.tsx` |

### `analytics/`

| Loại | File |
| :--- | :--- |
| *(trang trong `pages/`)* | `RevenuePage`, `TopProductsPage` |

### `ai/`

| Loại | File |
| :--- | :--- |
| Chat | `pages/ChatBotPage.tsx`, `api/aiChatSse.ts`, `api/aiCatalogDraftApi.ts` |
| Bảng nháp AI (HITL catalog) | `components/AiChatDraftTableCard.tsx` — SSE `draft` + `PATCH`/`POST commit` nháp |
| Biểu đồ chat | `components/AiChatChartCard.tsx` |

### `settings/`

| Loại | File |
| :--- | :--- |
| Nhân viên | `components/EmployeeTable.tsx`, `EmployeeToolbar.tsx`, `EmployeeForm.tsx`, `EmployeeDetailDialog.tsx` |
| API (nối BE) | `api/usersApi.ts` (`POST /api/v1/users` — Task078) |
| Nhật ký | `components/LogTable.tsx`, `LogToolbar.tsx` |

---

## 3. Cách tra nhanh (Agent)

1. Có **URL path** → dùng **bảng 1**.  
2. Có **tên màn** (tiếng Việt) → `Sidebar.tsx` `label` → `path` → **bảng 1**.  
3. Sửa **bảng / dialog** trong feature → **bảng 2** feature tương ứng → `Read` **đúng** file (không `Glob` cả thư mục nếu đã biết tên).

**Cập nhật index:** khi thêm `<Route>` trong `App.tsx` hoặc page mới dưới `features/**/pages/`, chỉnh **bảng 1** (và bảng 2 nếu có component chính mới).
