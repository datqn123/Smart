# Thiết kế API tổng thể — Smart Inventory Management (Mini-ERP)

> **Trạng thái**: Draft — bàn giao mức kiến trúc; chi tiết từng endpoint theo [`AGENTS/docs/templates/api/RESTFUL_API_TEMPLATE.md`](../../AGENTS/docs/templates/api/RESTFUL_API_TEMPLATE.md) và file `docs/api/API_TaskXXX_<slug>.md`.  
> **Tham chiếu Agent**: [`AGENTS/API_AGENT_INSTRUCTIONS.md`](../../AGENTS/API_AGENT_INSTRUCTIONS.md) (Agent API_SPEC, v1.1+ **bắt buộc** đọc tài liệu này trước UC/DB), [`AGENTS/API_UPGRADE_AGENT_INSTRUCTIONS.md`](../../AGENTS/API_UPGRADE_AGENT_INSTRUCTIONS.md).  
> **Nguồn nghiệp vụ & dữ liệu**: `docs/UC/Use Case Specification/UC*.txt`, `docs/UC/Database_Specification.md`, `docs/UC/Database_Specification_Part2.md`, `docs/UC/Entity_Relationships.md`, `docs/UC/schema.sql`.

---

## 1. Mục tiêu và phạm vi

Hệ thống cung cấp **REST API phiên bản hóa** cho ứng dụng quản lý kho thông minh, bao phủ **13 Use Case (UC1–UC13)** và **24 bảng** (theo đặc tả DB). Tài liệu này cố định **khung thiết kế** (URL, auth, envelope, nhóm tài nguyên, RBAC, ánh xạ UC); mỗi nhóm chức năng lớn được chi tiết hóa trong các file API theo Task.

**Tiết kiệm token**: trước khi đọc thêm UC/DB, xem [`AGENTS/docs/CONTEXT_INDEX.md`](../../AGENTS/docs/CONTEXT_INDEX.md).

---

## 2. Nguyên tắc bắt buộc (theo Agent API_SPEC)

| Hạng mục | Quy định |
| :--- | :--- |
| Kiến trúc | RESTful: `GET` (đọc), `POST` (tạo), `PUT`/`PATCH` (cập nhật), `DELETE` (xóa / ưu tiên soft delete nếu DB quy định). |
| Base path | `/api/v1/` — danh từ số nhiều cho tài nguyên (ví dụ `/api/v1/products`). |
| Định dạng | JSON; **camelCase** cho key request/response (khớp `Entity_Relationships.md` phía client). |
| Xác thực | **JWT Bearer**: `Authorization: Bearer <accessToken>`. Endpoint công khai chỉ nhóm auth và một số health/metadata nếu có. |
| Phân quyền | RBAC theo `Roles.name` và `permissions` (JSONB): Owner, Staff, Admin — kiểm tra quyền và **data ownership** (người dùng chỉ thao tác dữ liệu được phép). |
| Hiệu năng SQL (backend) | Không `SELECT *`; chỉ cột cần thiết; JOIN tối thiểu (theo `API_AGENT_INSTRUCTIONS` §3.4). |
| Lỗi | HTTP status chuẩn; nội dung lỗi **tiếng Việt**; envelope thống nhất với template (xem §4). |
| Tài liệu chi tiết | Mỗi API cụ thể: `docs/api/API_TaskXXX_<slug>.md` + tuân thủ [`AGENTS/docs/templates/api/RESTFUL_API_TEMPLATE.md`](../../AGENTS/docs/templates/api/RESTFUL_API_TEMPLATE.md). |

---

## 3. Envelope phản hồi và mã lỗi

**Chuẩn chi tiết** (field bắt buộc/tùy chọn, phân trang trong `data`, bảng mã `error`, checklist spec): [`API_RESPONSE_ENVELOPE.md`](API_RESPONSE_ENVELOPE.md).

### 3.1 Thành công (gợi ý)

```json
{
  "success": true,
  "data": {},
  "message": "Thao tác thành công"
}
```

### 3.2 Lỗi (tối thiểu phải mô tả trong spec từng API)

| HTTP | Ý nghĩa |
| :--- | :--- |
| 400 | Validation / nghiệp vụ từ chối (hiển thị `details` theo field nếu có). |
| 401 | Token thiếu, hết hạn, không hợp lệ. |
| 403 | Đã xác thực nhưng không đủ quyền RBAC hoặc không sở hữu dữ liệu. |
| 404 | Không tìm thấy tài nguyên. |
| 409 | Xung đột (ví dụ trạng thái phiếu/đơn không cho phép thao tác). |
| 500 | Lỗi máy chủ. |

Cấu trúc lỗi tham chiếu mục **3.2** trong [`RESTFUL_API_TEMPLATE.md`](../../AGENTS/docs/templates/api/RESTFUL_API_TEMPLATE.md).

---

## 4. Nhóm endpoint theo nghiệp vụ (catalog)

Prefix: **`/api/v1`**. Dưới đây là **danh mục thiết kế** (resource + verb chính); chi tiết request/response/schema Zod nằm trong từng `API_TaskXXX`.

### 4.1 Auth & phiên (UC đăng nhập / bảo mật phiên)

| Phương thức | Đường dẫn đề xuất | Mô tả ngắn |
| :--- | :--- | :--- |
| POST | `/auth/login` | Đăng nhập — **đã spec**: [`API_Task001_login.md`](API_Task001_login.md) |
| POST | `/auth/logout` | Hủy phiên / invalidate refresh — **đã spec**: [`API_Task002_logout.md`](API_Task002_logout.md) |
| POST | `/auth/refresh` | Làm mới access (và khuyến nghị rotation refresh) — **đã spec**: [`API_Task003_auth_refresh.md`](API_Task003_auth_refresh.md) |
| POST | `/auth/password-reset-requests` | **Luồng Staff → Owner**: nhân viên không đăng nhập được, gửi yêu cầu — [`API_Task004_staff_owner_password_reset.md`](API_Task004_staff_owner_password_reset.md) §1 |
| GET | `/users/password-reset-requests` | Owner xem hàng chờ — **Task004** §2 |
| POST | `/users/{userId}/password-reset/complete` | Owner cấp mật khẩu mới + gửi email staff — **Task004** §3 |

#### Quên / mất mật khẩu (Staff)

| Luồng | Ai dùng | API | Ghi chú |
| :------ | :------ | :---- | :------ |
| **Qua Owner** | **Staff** không vào được, bấm gửi yêu cầu | Task004: `password-reset-requests` + Owner `complete` | Owner nhận hàng chờ, hệ thống gửi **mật khẩu mới** tới `Users.email` của nhân viên; phù hợp UC3 *Reset Account*. Không có `forgot-password` / `reset-password` self-service trong phạm vi dự án. |

**Refresh token**: chỉ dùng [`POST /auth/refresh`](API_Task003_auth_refresh.md) (Task003), tách khỏi login để hợp đồng rõ và dễ bảo mật/rate-limit riêng.

### 4.2 Dashboard & thống kê (UC1 — View Overall Statistical Dashboard)

| Phương thức | Đường dẫn đề xuất | Bảng / nguồn dữ liệu chính |
| :--- | :--- | :--- |
| GET | `/dashboard/summary` | Tổng hợp từ `Inventory`, `SalesOrders`, `StockReceipts`, `FinanceLedger`, … |
| GET | `/dashboard/kpis` | Chỉ số theo khoảng thời gian (query params: `from`, `to`). |

### 4.3 AI — Insight & Chat (UC2, UC11)

| Phương thức | Đường dẫn đề xuất | Bảng chính |
| :--- | :--- | :--- |
| GET | `/ai/insights` | `AIInsights` (lọc theo `owner_id` / quyền). |
| POST | `/ai/insights/generate` | Tạo insight mới (async/sync tuỳ kiến trúc). |
| GET | `/ai/chat/history` | `AIChatHistory`. |
| POST | `/ai/chat/messages` | Gửi tin nhắn, nhận phản hồi bot; ghi `AIChatHistory`. |

### 4.4 Người dùng & vai trò (UC3 — Manage Staff Accounts)

| Phương thức | Đường dẫn đề xuất | Bảng chính | Tài liệu Task |
| :--- | :--- | :--- | :--- |
| GET | `/roles` | `Roles` (dropdown phân quyền) | [`API_Task076_roles_get_list.md`](API_Task076_roles_get_list.md) |
| GET | `/users` | `Users` + join `Roles` + `staff_code` — màn **Quản lý nhân viên** | [`API_Task077_users_get_list.md`](API_Task077_users_get_list.md) |
| POST | `/users` | Tạo nhân viên; hash `password_hash` | [`API_Task078_users_post.md`](API_Task078_users_post.md) |
| GET | `/users/{userId}` | Chi tiết (không trả `passwordHash`) | [`API_Task079_users_get_by_id.md`](API_Task079_users_get_by_id.md) |
| PATCH | `/users/{userId}` | Profile, `role_id`, `status`, `staff_code` | [`API_Task080_users_patch.md`](API_Task080_users_patch.md) |
| DELETE | `/users/{userId}` | Xóa / vô hiệu — FK RESTRICT | [`API_Task081_users_delete.md`](API_Task081_users_delete.md) |

_(Endpoint Owner xử lý yêu cầu reset mật khẩu nhân viên nằm trong **§4.1** cùng Task004 — tránh trùng lặp bảng catalog.)_

### 4.5 Phê duyệt giao dịch (UC4 — Approve Pending Transactions)

| Phương thức | Đường dẫn đề xuất | Bảng chính | Tài liệu Task |
| :--- | :--- | :--- | :--- |
| GET | `/approvals/pending` | Hàng chờ duyệt (đa loại; MVP: `StockReceipts` `Pending`) — màn **Chờ phê duyệt** | [`API_Task061_approvals_pending_get_list.md`](API_Task061_approvals_pending_get_list.md) |
| GET | `/approvals/history` | Lịch sử đã duyệt / từ chối (MVP: `StockReceipts` `Approved`/`Rejected`) — màn **Lịch sử phê duyệt** | [`API_Task062_approvals_history_get_list.md`](API_Task062_approvals_history_get_list.md) |
| POST | `/stock-receipts/{id}/approve` | Cập nhật phiếu nhập; `approved_by`; `SystemLogs` — [`API_Task019_stock_receipts_approve.md`](API_Task019_stock_receipts_approve.md). |
| POST | `/stock-receipts/{id}/reject` | Từ chối kèm lý do — [`API_Task020_stock_receipts_reject.md`](API_Task020_stock_receipts_reject.md). |

### 4.6 Cảnh báo (UC5 — Configure Alert Settings)

| Phương thức | Đường dẫn đề xuất | Bảng chính | Tài liệu Task |
| :--- | :--- | :--- | :--- |
| GET | `/alert-settings` | `AlertSettings` theo Owner — màn **Cấu hình cảnh báo** | [`API_Task082_alert_settings_get_list.md`](API_Task082_alert_settings_get_list.md) |
| POST | `/alert-settings` | Tạo rule | [`API_Task083_alert_settings_post.md`](API_Task083_alert_settings_post.md) |
| PATCH | `/alert-settings/{id}` | `threshold_value`, `channel`, `is_enabled`, `recipients` | [`API_Task084_alert_settings_patch.md`](API_Task084_alert_settings_patch.md) |
| DELETE | `/alert-settings/{id}` | Xóa rule | [`API_Task085_alert_settings_delete.md`](API_Task085_alert_settings_delete.md) |

### 4.7 Tồn kho & vị trí kho (UC6 — Manage inventory list)

| Phương thức | Đường dẫn đề xuất | Bảng chính |
| :--- | :--- | :--- |
| GET | `/inventory` | `Inventory` + `Products` + `WarehouseLocations` + `ProductUnits` — [`API_Task005_inventory_get_list.md`](API_Task005_inventory_get_list.md) |
| GET | `/inventory/{id}` | Chi tiết một dòng + `relatedLines` — [`API_Task006_inventory_get_by_id.md`](API_Task006_inventory_get_by_id.md) |
| PATCH | `/inventory/{id}` | Cập nhật meta tồn (không `quantity`) — [`API_Task007_inventory_patch.md`](API_Task007_inventory_patch.md) |
| PATCH | `/inventory/bulk` | Sửa nhiều dòng — [`API_Task008_inventory_bulk_patch.md`](API_Task008_inventory_bulk_patch.md) |
| POST | `/inventory/adjustments` | Điều chỉnh `quantity` + `InventoryLogs` — [`API_Task010_inventory_post_adjustments.md`](API_Task010_inventory_post_adjustments.md) |
| GET | `/inventory/summary` | _(Tuỳ chọn)_ chỉ KPI — [`API_Task009_inventory_get_summary.md`](API_Task009_inventory_get_summary.md) |
| GET | `/inventory/logs` | `InventoryLogs` — **chưa gán Task spec**; dùng khi có **màn tra cứu / báo cáo** biến động (không thuộc màn Tồn kho hiện tại). |
| _(Chính sách)_ | **Ghi log DB sau mutation tồn** | `SystemLogs` + `InventoryLogs` — [`API_Task011_inventory_mutation_audit_logs.md`](API_Task011_inventory_mutation_audit_logs.md) (đi kèm Task007, 008, 010…) |
| _(Chính sách)_ | **Thông báo Owner khi Staff đổi tồn** | `Notifications` — [`API_Task012_inventory_staff_change_notify_owner.md`](API_Task012_inventory_staff_change_notify_owner.md) |
| GET | `/warehouse-locations` | `WarehouseLocations`. |
| POST | `/warehouse-locations` | Tạo vị trí (Owner/Admin tuỳ UC). |
| PATCH | `/warehouse-locations/{id}` | Cập nhật `status`, `capacity`. |
| _(UC6 — Kiểm kê)_ | **`/inventory/audit-sessions`…** | Xem **§4.15** và Task021–028. |

### 4.8 Phiếu nhập kho (UC7 — Manage stock receipts)

| Phương thức | Đường dẫn đề xuất | Bảng chính |
| :--- | :--- | :--- |
| GET | `/stock-receipts` | Danh sách + lọc + phân trang — [`API_Task013_stock_receipts_get_list.md`](API_Task013_stock_receipts_get_list.md). |
| POST | `/stock-receipts` | Tạo header + `StockReceiptDetails`; `saveMode` `draft` \| `pending` — [`API_Task014_stock_receipts_post.md`](API_Task014_stock_receipts_post.md). |
| GET | `/stock-receipts/{id}` | Chi tiết + dòng — [`API_Task015_stock_receipts_get_by_id.md`](API_Task015_stock_receipts_get_by_id.md). |
| PATCH | `/stock-receipts/{id}` | Sửa khi `Draft` — [`API_Task016_stock_receipts_patch.md`](API_Task016_stock_receipts_patch.md). |
| DELETE | `/stock-receipts/{id}` | Xóa khi `Draft` (mặc định) — [`API_Task017_stock_receipts_delete.md`](API_Task017_stock_receipts_delete.md). |
| POST | `/stock-receipts/{id}/submit` | `Draft` → `Pending` (gửi duyệt) — [`API_Task018_stock_receipts_submit.md`](API_Task018_stock_receipts_submit.md). |

**Hỗ trợ form / bảng (catalog §4.14, §4.9–§4.10):** **NCC** — [`API_Task042_suppliers_get_list.md`](API_Task042_suppliers_get_list.md); **KH** — [`API_Task048_customers_get_list.md`](API_Task048_customers_get_list.md); **danh mục & sản phẩm** — [`API_Task029_categories_get_list.md`](API_Task029_categories_get_list.md), [`API_Task034_products_get_list.md`](API_Task034_products_get_list.md), chi tiết / đơn vị — [`API_Task036_products_get_by_id.md`](API_Task036_products_get_by_id.md). Màn **Phiếu nhập kho** bắt buộc có nguồn NCC + SP hợp lệ trước khi gọi POST/PATCH.

### 4.9 Sản phẩm & danh mục (UC8 — Manage Products)

| Phương thức | Đường dẫn đề xuất | Bảng chính | Tài liệu Task |
| :--- | :--- | :--- | :--- |
| GET | `/categories` | `Categories` (cây / phẳng, `parent_id`) | [`API_Task029_categories_get_list.md`](API_Task029_categories_get_list.md) |
| POST | `/categories` | `Categories` | [`API_Task030_categories_post.md`](API_Task030_categories_post.md) |
| GET | `/categories/{id}` | `Categories` + breadcrumb | [`API_Task031_categories_get_by_id.md`](API_Task031_categories_get_by_id.md) |
| PATCH | `/categories/{id}` | `Categories` | [`API_Task032_categories_patch.md`](API_Task032_categories_patch.md) |
| DELETE | `/categories/{id}` | `Categories` | [`API_Task033_categories_delete.md`](API_Task033_categories_delete.md) |
| GET | `/products` | `Products` (+ read-model tồn, giá) | [`API_Task034_products_get_list.md`](API_Task034_products_get_list.md) |
| POST | `/products` | `Products`, `ProductUnits`, `ProductPriceHistory` | [`API_Task035_products_post.md`](API_Task035_products_post.md) |
| GET | `/products/{id}` | Chi tiết + units (+ `ProductImages` khi có migration) | [`API_Task036_products_get_by_id.md`](API_Task036_products_get_by_id.md) |
| PATCH | `/products/{id}` | `Products`; ghi `ProductPriceHistory` khi đổi giá | [`API_Task037_products_patch.md`](API_Task037_products_patch.md) |
| DELETE | `/products/{id}` | `Products` (ràng buộc phiếu/đơn/tồn) | [`API_Task038_products_delete.md`](API_Task038_products_delete.md) |
| POST | `/products/{id}/images` | `ProductImages` (DDL đề xuất trong Task) | [`API_Task039_products_post_image.md`](API_Task039_products_post_image.md) |
| DELETE | `/products/{id}/images/{imageId}` | `ProductImages` | [`API_Task040_products_delete_image.md`](API_Task040_products_delete_image.md) |
| POST | `/products/bulk-delete` | `Products` (xóa nhiều; ràng buộc như xóa đơn) | [`API_Task041_products_bulk_delete.md`](API_Task041_products_bulk_delete.md) |

**Lưu ý schema:** `Database_Specification.md` có `Products.image_url`; bảng gallery **`ProductImages`** được định nghĩa DDL đề xuất trong [`API_Task039_products_post_image.md`](API_Task039_products_post_image.md) — migration trước khi bật Task039/040.

### 4.10 Đơn bán hàng (UC9 — Manage Sales Orders)

| Phương thức | Đường dẫn đề xuất | Bảng chính | Tài liệu Task |
| :--- | :--- | :--- | :--- |
| GET | `/customers` | `Customers` + read-model đơn / chi tiêu | [`API_Task048_customers_get_list.md`](API_Task048_customers_get_list.md) |
| POST | `/customers` | `Customers` | [`API_Task049_customers_post.md`](API_Task049_customers_post.md) |
| GET | `/customers/{id}` | Chi tiết + tổng đơn / chi tiêu | [`API_Task050_customers_get_by_id.md`](API_Task050_customers_get_by_id.md) |
| PATCH | `/customers/{id}` | Cập nhật hồ sơ / điểm (RBAC) | [`API_Task051_customers_patch.md`](API_Task051_customers_patch.md) |
| DELETE | `/customers/{id}` | Xóa nếu **không** còn `SalesOrders` (bổ sung cho UI; có thể dùng soft-delete) | [`API_Task052_customers_delete.md`](API_Task052_customers_delete.md) |
| POST | `/customers/bulk-delete` | Xóa nhiều KH | [`API_Task053_customers_bulk_delete.md`](API_Task053_customers_bulk_delete.md) |
| GET | `/sales-orders` | `SalesOrders` (lọc `orderChannel`, phân trang) — **Đơn bán sỉ / Trả hàng** | [`API_Task054_sales_orders_get_list.md`](API_Task054_sales_orders_get_list.md) |
| GET | `/sales-orders/{id}` | Chi tiết + `OrderDetails` | [`API_Task055_sales_orders_get_by_id.md`](API_Task055_sales_orders_get_by_id.md) |
| POST | `/sales-orders` | Tạo đơn **Wholesale** hoặc **Return** + dòng | [`API_Task056_sales_orders_post.md`](API_Task056_sales_orders_post.md) |
| PATCH | `/sales-orders/{id}` | Cập nhật meta / trạng thái / thanh toán | [`API_Task057_sales_orders_patch.md`](API_Task057_sales_orders_patch.md) |
| POST | `/sales-orders/{id}/cancel` | Hủy đơn (`cancelled_by`, …) | [`API_Task058_sales_orders_cancel.md`](API_Task058_sales_orders_cancel.md) |
| GET | `/pos/products` | Tìm hàng cho **POS / Bán lẻ** | [`API_Task059_pos_products_get_search.md`](API_Task059_pos_products_get_search.md) |
| GET | `/sales-orders/retail/history` | `SalesOrders` — **lịch sử hóa đơn bán lẻ** (Retail only, read-only list) | [`API_Task102_sales_orders_retail_history_get_list.md`](API_Task102_sales_orders_retail_history_get_list.md) |
| POST | `/sales-orders/retail/checkout` | Thanh toán **một lần** (bán lẻ) | [`API_Task060_sales_orders_retail_checkout.md`](API_Task060_sales_orders_retail_checkout.md) |
| GET | `/vouchers` | Danh sách voucher áp dụng được (POS) | [`API_Task092_vouchers_and_retail_preview.md`](API_Task092_vouchers_and_retail_preview.md) |
| GET | `/vouchers/{id}` | Chi tiết voucher | [`API_Task092_vouchers_and_retail_preview.md`](API_Task092_vouchers_and_retail_preview.md) |
| POST | `/sales-orders/retail/voucher-preview` | Preview giảm giá theo giỏ | [`API_Task092_vouchers_and_retail_preview.md`](API_Task092_vouchers_and_retail_preview.md) |

**Lưu ý schema UC9:** `SalesOrders` cần bổ sung `order_channel`, `payment_status`, (tuỳ chọn) `ref_sales_order_id` — DDL trong [`API_Task054_sales_orders_get_list.md`](API_Task054_sales_orders_get_list.md). **Task092:** `vouchers.used_count` / `max_uses`, bảng `voucher_redemptions` — Flyway `V24`.

### 4.11 Xuất kho (UC10 — Manage inventory dispatch)

| Phương thức | Đường dẫn đề xuất | Bảng chính |
| :--- | :--- | :--- |
| GET | `/stock-dispatches` | `StockDispatches` + `SalesOrders`. |
| POST | `/stock-dispatches` | Tạo xuất từ đơn; cập nhật `Inventory`; ghi `InventoryLogs`. |
| GET | `/stock-dispatches/{id}` | Chi tiết. |

### 4.12 Cập nhật qua hình ảnh / OCR (UC12 — Update via Image)

| Phương thức | Đường dẫn đề xuất | Bảng chính |
| :--- | :--- | :--- |
| POST | `/media/audits` hoặc `/integrations/ocr/invoices` | Upload; `MediaAudits` (polymorphic); pipeline AI cập nhật `Products` / phiếu tuỳ UC. |

### 4.13 Cập nhật qua giọng nói (UC13 — Update via Voice)

| Phương thức | Đường dẫn đề xuất | Ghi chú |
| :--- | :--- | :--- |
| POST | `/voice/intents` hoặc WebSocket `/ws/voice` | Nhận transcript/command; map sang use case (điều chỉnh tồn, tìm SKU) — chi tiết trong Task riêng. |

### 4.14 Hệ thống & tài chính (hỗ trợ đa UC)

| Phương thức | Đường dẫn đề xuất | Bảng chính | Tài liệu Task |
| :--- | :--- | :--- | :--- |
| GET | `/suppliers` | `Suppliers` (+ `receiptCount` read-model) | [`API_Task042_suppliers_get_list.md`](API_Task042_suppliers_get_list.md) |
| POST | `/suppliers` | `Suppliers` | [`API_Task043_suppliers_post.md`](API_Task043_suppliers_post.md) |
| GET | `/suppliers/{id}` | Chi tiết NCC | [`API_Task044_suppliers_get_by_id.md`](API_Task044_suppliers_get_by_id.md) |
| PATCH | `/suppliers/{id}` | Cập nhật NCC | [`API_Task045_suppliers_patch.md`](API_Task045_suppliers_patch.md) |
| DELETE | `/suppliers/{id}` | Xóa khi không còn phiếu nhập | [`API_Task046_suppliers_delete.md`](API_Task046_suppliers_delete.md) |
| POST | `/suppliers/bulk-delete` | Xóa nhiều NCC | [`API_Task047_suppliers_bulk_delete.md`](API_Task047_suppliers_bulk_delete.md) |
| GET | `/finance-ledger` | `FinanceLedger` + running balance (quyền `can_view_finance`) | [`API_Task063_finance_ledger_get_list.md`](API_Task063_finance_ledger_get_list.md) |
| GET | `/cash-transactions` | `CashTransactions` (§12.1 — Giao dịch thu chi) | [`API_Task064_cash_transactions_get_list.md`](API_Task064_cash_transactions_get_list.md) |
| POST | `/cash-transactions` | Tạo phiếu thu/chi | [`API_Task065_cash_transactions_post.md`](API_Task065_cash_transactions_post.md) |
| GET | `/cash-transactions/{id}` | Chi tiết | [`API_Task066_cash_transactions_get_by_id.md`](API_Task066_cash_transactions_get_by_id.md) |
| PATCH | `/cash-transactions/{id}` | Cập nhật / hoàn tất → ghi `FinanceLedger` | [`API_Task067_cash_transactions_patch.md`](API_Task067_cash_transactions_patch.md) |
| DELETE | `/cash-transactions/{id}` | Xóa khi `Pending` / `Cancelled` | [`API_Task068_cash_transactions_delete.md`](API_Task068_cash_transactions_delete.md) |
| GET | `/debts` | `PartnerDebts` (§12.2 — Sổ nợ) | [`API_Task069_debts_get_list.md`](API_Task069_debts_get_list.md) |
| POST | `/debts` | Tạo khoản nợ | [`API_Task070_debts_post.md`](API_Task070_debts_post.md) |
| GET | `/debts/{id}` | Chi tiết nợ | [`API_Task071_debts_get_by_id.md`](API_Task071_debts_get_by_id.md) |
| PATCH | `/debts/{id}` | Cập nhật / ghi nhận trả nợ | [`API_Task072_debts_patch.md`](API_Task072_debts_patch.md) |
| GET | `/system-logs` | `SystemLogs` — **Admin-only** (JWT `role` + `mp.can_view_system_logs`); màn **Nhật ký hệ thống** | [`API_Task086_system_logs_get_list.md`](API_Task086_system_logs_get_list.md) |
| DELETE | `/system-logs/{id}` | Policy **cấm xóa** (403); gọi chỉ khi có quyền Admin | [`API_Task087_system_logs_delete.md`](API_Task087_system_logs_delete.md) |
| POST | `/system-logs/bulk-delete` | Xóa nhiều id | [`API_Task088_system_logs_bulk_delete.md`](API_Task088_system_logs_bulk_delete.md) |
| GET | `/notifications` | `Notifications` (optional table) | _(Task sau)_ |

### 4.15 Kiểm kê kho (UC6 — Inventory audit sessions / `AuditPage`)

| Phương thức | Đường dẫn đề xuất | Bảng / ghi chú |
| :--- | :--- | :--- |
| GET | `/inventory/audit-sessions` | Danh sách đợt kiểm + tiến độ tổng hợp — [`API_Task021_inventory_audit_sessions_get_list.md`](API_Task021_inventory_audit_sessions_get_list.md). |
| POST | `/inventory/audit-sessions` | Tạo đợt + **snapshot** dòng từ `Inventory` — [`API_Task022_inventory_audit_sessions_post.md`](API_Task022_inventory_audit_sessions_post.md). |
| GET | `/inventory/audit-sessions/{id}` | Chi tiết đợt + từng dòng kiểm — [`API_Task023_inventory_audit_sessions_get_by_id.md`](API_Task023_inventory_audit_sessions_get_by_id.md). |
| PATCH | `/inventory/audit-sessions/{id}` | Cập nhật meta / chuyển trạng thái (`Pending` → `In Progress`, …) — [`API_Task024_inventory_audit_sessions_patch.md`](API_Task024_inventory_audit_sessions_patch.md). |
| PATCH | `/inventory/audit-sessions/{id}/lines` | Ghi **số kiểm thực tế** hàng loạt — [`API_Task025_inventory_audit_sessions_patch_lines.md`](API_Task025_inventory_audit_sessions_patch_lines.md). |
| POST | `/inventory/audit-sessions/{id}/complete` | Hoàn tất đợt (`Completed`) — [`API_Task026_inventory_audit_sessions_complete.md`](API_Task026_inventory_audit_sessions_complete.md). |
| POST | `/inventory/audit-sessions/{id}/cancel` | Hủy đợt — [`API_Task027_inventory_audit_sessions_cancel.md`](API_Task027_inventory_audit_sessions_cancel.md). |
| POST | `/inventory/audit-sessions/{id}/apply-variance` | Áp chênh lệch lên `Inventory` + `InventoryLogs` (cùng nghiệp vụ Task010/011) — [`API_Task028_inventory_audit_sessions_apply_variance.md`](API_Task028_inventory_audit_sessions_apply_variance.md). |

**Lưu ý schema:** `Database_Specification.md` hiện **chưa** có bảng đợt kiểm kê — Task022/028 đính kèm **DDL đề xuất** (`inventory_audit_sessions`, `inventory_audit_lines`); backend phải migration trước triển khai.

### 4.16 Thông tin cửa hàng (mini-ERP — `StoreInfoPage`)

| Phương thức | Đường dẫn đề xuất | Bảng chính | Tài liệu Task |
| :--- | :--- | :--- | :--- |
| GET | `/store-profile` | `StoreProfiles` (§6.1 DB) — một bản ghi theo Owner | [`API_Task073_store_profile_get.md`](API_Task073_store_profile_get.md) |
| PATCH | `/store-profile` | Cập nhật meta cửa hàng (camelCase đồng bộ FE) | [`API_Task074_store_profile_patch.md`](API_Task074_store_profile_patch.md) |
| POST | `/store-profile/logo` | Upload logo → URL lưu `logo_url` | [`API_Task075_store_profile_post_logo.md`](API_Task075_store_profile_post_logo.md) |

---

## 5. Ánh xạ Use Case → module API

| UC | Tên (tóm tắt) | Module API chính |
| :--- | :--- | :--- |
| UC1 | Dashboard thống kê | §4.2 |
| UC2 | AI Business Insight | §4.3 (`/ai/insights`) |
| UC3 | Quản lý nhân viên & thông tin cửa hàng | §4.4, **§4.16** |
| UC4 | Phê duyệt giao dịch | §4.5 |
| UC5 | Cấu hình cảnh báo | §4.6 |
| UC6 | Danh sách tồn kho & kiểm kê | §4.7, **§4.15** |
| UC7 | Phiếu nhập kho | §4.8 |
| UC8 | Quản lý sản phẩm | §4.9 |
| UC9 | Đơn bán hàng | §4.10 |
| UC10 | Xuất kho | §4.11 |
| UC11 | Chat bot AI | §4.3 (`/ai/chat`) |
| UC12 | Cập nhật qua ảnh | §4.12 |
| UC13 | Cập nhật qua giọng nói | §4.13 |

---

## 6. RBAC (khung)

- **Admin**: cấu hình hệ thống, xem log, quản trị user/role (theo `permissions` trong DB).  
- **Owner**: phê duyệt, tài chính, cảnh báo, toàn bộ dữ liệu doanh nghiệp.  
- **Staff**: thao tác nghiệp vụ hàng ngày (nhập/xuất/đơn/sản phẩm) trong phạm vi `permissions`.  

Mỗi file `API_TaskXXX` phải ghi rõ **`RBAC Roles`** và điều kiện **ownership** (ví dụ chỉ Owner được `PATCH /alert-settings` của `owner_id` khác).

---

## 7. Trạng thái tài liệu API theo Task

> **SRS backend không có `API_TaskXXX` tương ứng (Task ≥ 100):** [`SRS_Task100_auth-session-registry-stale-access.md`](../../../docs/backend/srs/SRS_Task100_auth-session-registry-stale-access.md) — xử lý `LoginSessionRegistry` khi access JWT hết hạn mà không refresh (Draft).

| File | Trạng thái |
| :--- | :--- |
| [`API_Task001_login.md`](API_Task001_login.md) | Approved |
| [`API_Task002_logout.md`](API_Task002_logout.md) | Approved |
| [`API_Task003_auth_refresh.md`](API_Task003_auth_refresh.md) | Approved — refresh token tách endpoint |
| [`API_Task004_staff_owner_password_reset.md`](API_Task004_staff_owner_password_reset.md) | Approved — Staff → Owner → email (UC3) |
| [`API_Task005_inventory_get_list.md`](API_Task005_inventory_get_list.md) | Draft — `GET /inventory` (danh sách + KPI trong response) |
| [`API_Task006_inventory_get_by_id.md`](API_Task006_inventory_get_by_id.md) | Draft — `GET /inventory/{id}` |
| [`API_Task007_inventory_patch.md`](API_Task007_inventory_patch.md) | Draft — `PATCH /inventory/{id}` |
| [`API_Task008_inventory_bulk_patch.md`](API_Task008_inventory_bulk_patch.md) | Draft — `PATCH /inventory/bulk` |
| [`API_Task009_inventory_get_summary.md`](API_Task009_inventory_get_summary.md) | Draft — `GET /inventory/summary` |
| [`API_Task010_inventory_post_adjustments.md`](API_Task010_inventory_post_adjustments.md) | Draft — `POST /inventory/adjustments` |
| [`API_Task011_inventory_mutation_audit_logs.md`](API_Task011_inventory_mutation_audit_logs.md) | Draft — Ghi `SystemLogs` / `InventoryLogs` khi mutation tồn (cross-cutting) |
| [`API_Task012_inventory_staff_change_notify_owner.md`](API_Task012_inventory_staff_change_notify_owner.md) | Draft — Thông báo Owner khi Staff đổi tồn (`Notifications`) |
| [`API_Task013_stock_receipts_get_list.md`](API_Task013_stock_receipts_get_list.md) | Draft — `GET /stock-receipts` (UC7 — `InboundPage`) |
| [`API_Task014_stock_receipts_post.md`](API_Task014_stock_receipts_post.md) | Draft — `POST /stock-receipts` |
| [`API_Task015_stock_receipts_get_by_id.md`](API_Task015_stock_receipts_get_by_id.md) | Draft — `GET /stock-receipts/{id}` |
| [`API_Task016_stock_receipts_patch.md`](API_Task016_stock_receipts_patch.md) | Draft — `PATCH /stock-receipts/{id}` |
| [`API_Task017_stock_receipts_delete.md`](API_Task017_stock_receipts_delete.md) | Draft — `DELETE /stock-receipts/{id}` |
| [`API_Task018_stock_receipts_submit.md`](API_Task018_stock_receipts_submit.md) | Draft — `POST /stock-receipts/{id}/submit` |
| [`API_Task019_stock_receipts_approve.md`](API_Task019_stock_receipts_approve.md) | Draft — `POST /stock-receipts/{id}/approve` (UC4) |
| [`API_Task020_stock_receipts_reject.md`](API_Task020_stock_receipts_reject.md) | Draft — `POST /stock-receipts/{id}/reject` (UC4) |
| [`API_Task021_inventory_audit_sessions_get_list.md`](API_Task021_inventory_audit_sessions_get_list.md) | Draft — `GET /inventory/audit-sessions` (Kiểm kê — `AuditPage`) |
| [`API_Task022_inventory_audit_sessions_post.md`](API_Task022_inventory_audit_sessions_post.md) | Draft — `POST /inventory/audit-sessions` |
| [`API_Task023_inventory_audit_sessions_get_by_id.md`](API_Task023_inventory_audit_sessions_get_by_id.md) | Draft — `GET /inventory/audit-sessions/{id}` |
| [`API_Task024_inventory_audit_sessions_patch.md`](API_Task024_inventory_audit_sessions_patch.md) | Draft — `PATCH /inventory/audit-sessions/{id}` |
| [`API_Task025_inventory_audit_sessions_patch_lines.md`](API_Task025_inventory_audit_sessions_patch_lines.md) | Draft — `PATCH /inventory/audit-sessions/{id}/lines` |
| [`API_Task026_inventory_audit_sessions_complete.md`](API_Task026_inventory_audit_sessions_complete.md) | Draft — `POST /inventory/audit-sessions/{id}/complete` |
| [`API_Task027_inventory_audit_sessions_cancel.md`](API_Task027_inventory_audit_sessions_cancel.md) | Draft — `POST /inventory/audit-sessions/{id}/cancel` |
| [`API_Task028_inventory_audit_sessions_apply_variance.md`](API_Task028_inventory_audit_sessions_apply_variance.md) | Draft — `POST /inventory/audit-sessions/{id}/apply-variance` |
| [`API_Task029_categories_get_list.md`](API_Task029_categories_get_list.md) | Draft — `GET /categories` (UC8 — `CategoriesPage`) |
| [`API_Task030_categories_post.md`](API_Task030_categories_post.md) | Draft — `POST /categories` |
| [`API_Task031_categories_get_by_id.md`](API_Task031_categories_get_by_id.md) | Draft — `GET /categories/{id}` |
| [`API_Task032_categories_patch.md`](API_Task032_categories_patch.md) | Draft — `PATCH /categories/{id}` |
| [`API_Task033_categories_delete.md`](API_Task033_categories_delete.md) | Draft — `DELETE /categories/{id}` |
| [`API_Task034_products_get_list.md`](API_Task034_products_get_list.md) | Draft — `GET /products` (UC8 — `ProductsPage`) |
| [`API_Task035_products_post.md`](API_Task035_products_post.md) | Draft — `POST /products` |
| [`API_Task036_products_get_by_id.md`](API_Task036_products_get_by_id.md) | Draft — `GET /products/{id}` |
| [`API_Task037_products_patch.md`](API_Task037_products_patch.md) | Draft — `PATCH /products/{id}` |
| [`API_Task038_products_delete.md`](API_Task038_products_delete.md) | Draft — `DELETE /products/{id}` |
| [`API_Task039_products_post_image.md`](API_Task039_products_post_image.md) | Draft — `POST /products/{id}/images` |
| [`API_Task040_products_delete_image.md`](API_Task040_products_delete_image.md) | Draft — `DELETE /products/{id}/images/{imageId}` |
| [`API_Task041_products_bulk_delete.md`](API_Task041_products_bulk_delete.md) | Draft — `POST /products/bulk-delete` (UC8 — `ProductsPage`) |
| [`API_Task042_suppliers_get_list.md`](API_Task042_suppliers_get_list.md) | Draft — `GET /suppliers` (`SuppliersPage`) |
| [`API_Task043_suppliers_post.md`](API_Task043_suppliers_post.md) | Draft — `POST /suppliers` |
| [`API_Task044_suppliers_get_by_id.md`](API_Task044_suppliers_get_by_id.md) | Draft — `GET /suppliers/{id}` |
| [`API_Task045_suppliers_patch.md`](API_Task045_suppliers_patch.md) | Draft — `PATCH /suppliers/{id}` |
| [`API_Task046_suppliers_delete.md`](API_Task046_suppliers_delete.md) | Draft — `DELETE /suppliers/{id}` |
| [`API_Task047_suppliers_bulk_delete.md`](API_Task047_suppliers_bulk_delete.md) | Draft — `POST /suppliers/bulk-delete` |
| [`API_Task048_customers_get_list.md`](API_Task048_customers_get_list.md) | Draft — `GET /customers` (`CustomersPage`) |
| [`API_Task049_customers_post.md`](API_Task049_customers_post.md) | Draft — `POST /customers` |
| [`API_Task050_customers_get_by_id.md`](API_Task050_customers_get_by_id.md) | Draft — `GET /customers/{id}` |
| [`API_Task051_customers_patch.md`](API_Task051_customers_patch.md) | Draft — `PATCH /customers/{id}` |
| [`API_Task052_customers_delete.md`](API_Task052_customers_delete.md) | Draft — `DELETE /customers/{id}` |
| [`API_Task053_customers_bulk_delete.md`](API_Task053_customers_bulk_delete.md) | Draft — `POST /customers/bulk-delete` |
| [`API_Task054_sales_orders_get_list.md`](API_Task054_sales_orders_get_list.md) | Draft — `GET /sales-orders` (UC9 — bán sỉ / trả hàng) |
| [`API_Task055_sales_orders_get_by_id.md`](API_Task055_sales_orders_get_by_id.md) | Draft — `GET /sales-orders/{id}` |
| [`API_Task056_sales_orders_post.md`](API_Task056_sales_orders_post.md) | Draft — `POST /sales-orders` (Wholesale / Return) |
| [`API_Task057_sales_orders_patch.md`](API_Task057_sales_orders_patch.md) | Draft — `PATCH /sales-orders/{id}` |
| [`API_Task058_sales_orders_cancel.md`](API_Task058_sales_orders_cancel.md) | Draft — `POST /sales-orders/{id}/cancel` |
| [`API_Task059_pos_products_get_search.md`](API_Task059_pos_products_get_search.md) | Draft — `GET /pos/products` (UC9 — POS bán lẻ) |
| [`API_Task060_sales_orders_retail_checkout.md`](API_Task060_sales_orders_retail_checkout.md) | Draft — `POST /sales-orders/retail/checkout` |
| [`API_Task102_sales_orders_retail_history_get_list.md`](API_Task102_sales_orders_retail_history_get_list.md) | Draft — `GET /sales-orders/retail/history` (UC9 — lịch sử hóa đơn bán lẻ; SRS Task102 Approved 02/05/2026) |
| [`API_Task092_vouchers_and_retail_preview.md`](API_Task092_vouchers_and_retail_preview.md) | Draft — `GET /vouchers`, `GET /vouchers/{id}`, `POST /sales-orders/retail/voucher-preview` (UC9 POS) |
| [`API_Task061_approvals_pending_get_list.md`](API_Task061_approvals_pending_get_list.md) | Draft — `GET /approvals/pending` (UC4 — Chờ phê duyệt) |
| [`API_Task062_approvals_history_get_list.md`](API_Task062_approvals_history_get_list.md) | Draft — `GET /approvals/history` (UC4 — Lịch sử phê duyệt) |
| [`API_Task063_finance_ledger_get_list.md`](API_Task063_finance_ledger_get_list.md) | Draft — `GET /finance-ledger` (Sổ cái tài chính / `LedgerPage`) |
| [`API_Task064_cash_transactions_get_list.md`](API_Task064_cash_transactions_get_list.md) | Approved — `GET /cash-transactions` (SRS Task064–068 30/04/2026) |
| [`API_Task065_cash_transactions_post.md`](API_Task065_cash_transactions_post.md) | Approved — `POST /cash-transactions` |
| [`API_Task066_cash_transactions_get_by_id.md`](API_Task066_cash_transactions_get_by_id.md) | Approved — `GET /cash-transactions/{id}` |
| [`API_Task067_cash_transactions_patch.md`](API_Task067_cash_transactions_patch.md) | Approved — `PATCH /cash-transactions/{id}` |
| [`API_Task068_cash_transactions_delete.md`](API_Task068_cash_transactions_delete.md) | Approved — `DELETE /cash-transactions/{id}` |
| [`API_Task069_debts_get_list.md`](API_Task069_debts_get_list.md) | Approved — `GET /debts` (Sổ nợ / `DebtPage`; SRS Task069–072 30/04/2026) |
| [`API_Task070_debts_post.md`](API_Task070_debts_post.md) | Approved — `POST /debts` |
| [`API_Task071_debts_get_by_id.md`](API_Task071_debts_get_by_id.md) | Approved — `GET /debts/{id}` |
| [`API_Task072_debts_patch.md`](API_Task072_debts_patch.md) | Approved — `PATCH /debts/{id}` |
| [`API_Task073_store_profile_get.md`](API_Task073_store_profile_get.md) | Draft — `GET /store-profile` (`StoreInfoPage`) |
| [`API_Task074_store_profile_patch.md`](API_Task074_store_profile_patch.md) | Draft — `PATCH /store-profile` |
| [`API_Task075_store_profile_post_logo.md`](API_Task075_store_profile_post_logo.md) | Draft — `POST /store-profile/logo` |
| [`API_Task076_roles_get_list.md`](API_Task076_roles_get_list.md) | Draft — `GET /roles` |
| [`API_Task077_users_get_list.md`](API_Task077_users_get_list.md) | Draft — `GET /users` (`EmployeesPage`) |
| [`API_Task078_users_post.md`](API_Task078_users_post.md) | Draft — `POST /users` |
| [`API_Task079_users_get_by_id.md`](API_Task079_users_get_by_id.md) | Draft — `GET /users/{userId}` |
| [`API_Task080_users_patch.md`](API_Task080_users_patch.md) | Draft — `PATCH /users/{userId}` |
| [`API_Task081_users_delete.md`](API_Task081_users_delete.md) | Draft — `DELETE /users/{userId}` |
| [`API_Task082_alert_settings_get_list.md`](API_Task082_alert_settings_get_list.md) | Draft — `GET /alert-settings` (`AlertSettingsPage`) |
| [`API_Task083_alert_settings_post.md`](API_Task083_alert_settings_post.md) | Draft — `POST /alert-settings` |
| [`API_Task084_alert_settings_patch.md`](API_Task084_alert_settings_patch.md) | Draft — `PATCH /alert-settings/{id}` |
| [`API_Task085_alert_settings_delete.md`](API_Task085_alert_settings_delete.md) | Draft — `DELETE /alert-settings/{id}` |
| [`API_Task086_system_logs_get_list.md`](API_Task086_system_logs_get_list.md) | Draft — `GET /system-logs` (`LogsPage`) |
| [`API_Task087_system_logs_delete.md`](API_Task087_system_logs_delete.md) | Draft — `DELETE /system-logs/{id}` |
| [`API_Task088_system_logs_bulk_delete.md`](API_Task088_system_logs_bulk_delete.md) | Draft — `POST /system-logs/bulk-delete` |
| UC1–UC13 (catalog §4) | Tiếp tục bổ sung Task (ví dụ `GET /inventory/logs`, …) theo backlog PM |

---

## 8. QA checklist (bàn giao mức dự án)

Áp dụng tinh thần mục **6** trong `API_AGENT_INSTRUCTIONS.md` cho từng spec con:

- [ ] Đã đối chiếu UC và bảng trong `schema.sql` cho từng endpoint.  
- [ ] REST đúng method; URL danh từ số nhiều; JSON camelCase.  
- [ ] Auth Bearer cho endpoint cần bảo mật; mô tả 401/403.  
- [ ] Mô tả thao tác DB (INSERT/UPDATE/transaction/trigger nếu có).  
- [ ] Thông báo lỗi tiếng Việt; có ví dụ 400/404/500.  
- [ ] Có mục Zod (hoặc schema tương đương) cho frontend trong từng file Task.

---

## 9. Bước tiếp theo

1. PM/Dev gán **Task ID** cho từng cụm API trong §4 và tạo `docs/api/API_TaskXXX_<slug>.md` theo template.  
2. Sau khi Owner phản hồi chuỗi thiết kế, triệu hồi **Agent API_UPGRADE** để cập nhật `API_AGENT_INSTRUCTIONS.md` (vòng nâng cấp quy trình).
