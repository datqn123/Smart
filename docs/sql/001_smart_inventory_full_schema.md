# Smart Inventory Management — Toàn bộ Database Schema

> **Tổng hợp từ tất cả Flyway migration files** (V1–V56) + `docs/dev/frontend/UC/schema.sql`
> **Database:** PostgreSQL 15+
> **Dự án:** Đồ án Tốt nghiệp - Quản lý Kho thông minh

---

## Mục lục

1. [Bảng cốt lõi (Core)](#1-bảng-cốt-lõi-core)
2. [Bảng định tuyến (Reference)](#2-bảng-định-tuyến-reference)
3. [Bảng vệ tinh & hệ thống](#3-bảng-vệ-tinh--hệ-thống)
4. [Bảng chứng từ cha & tồn kho (Header)](#4-bảng-chứng-từ-cha--tồn-kho-header)
5. [Bảng chi tiết chứng từ (Detail)](#5-bảng-chi-tiết-chứng-từ-detail)
6. [Bảng log](#6-bảng-log)
7. [Bảng optional & bổ sung](#7-bảng-optional--bổ-sung)
8. [Bảng AI & Meta](#8-bảng-ai--meta)
9. [Custom Interface Builder](#9-custom-interface-builder)
10. [Function & Trigger](#10-function--trigger)

---

## 1. Bảng cốt lõi (Core)

### 1.1. `roles` — Vai trò người dùng

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID vai trò |
| `name` | `VARCHAR(50)` | `NOT NULL, UNIQUE` | Tên vai trò: Owner, Staff, Admin |
| `permissions` | `JSONB` | `NOT NULL DEFAULT '{}'` | Quyền hạn JSON (VD: can_approve, can_manage_customers, can_view_finance, can_view_system_logs...) |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |

### 1.2. `categories` — Danh mục sản phẩm

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID danh mục |
| `category_code` | `VARCHAR(50)` | `NOT NULL, UNIQUE (partial WHERE deleted_at IS NULL)` | Mã danh mục |
| `name` | `VARCHAR(255)` | `NOT NULL` | Tên danh mục |
| `description` | `TEXT` | | Mô tả |
| `parent_id` | `INT` | `FK → categories(id) ON DELETE SET NULL` | Danh mục cha (cây phân cấp) |
| `sort_order` | `INT` | `NOT NULL DEFAULT 0` | Thứ tự hiển thị |
| `status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'Active', CHECK(Active, Inactive)` | Trạng thái |
| `deleted_at` | `TIMESTAMPTZ` | *(added V14)* | Xóa mềm |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật cuối |

### 1.3. `suppliers` — Nhà cung cấp

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID nhà cung cấp |
| `supplier_code` | `VARCHAR(50)` | `NOT NULL, UNIQUE` | Mã NCC |
| `name` | `VARCHAR(255)` | `NOT NULL` | Tên NCC |
| `contact_person` | `VARCHAR(255)` | | Người liên hệ |
| `phone` | `VARCHAR(20)` | | SĐT |
| `email` | `VARCHAR(255)` | | Email |
| `address` | `TEXT` | | Địa chỉ |
| `tax_code` | `VARCHAR(50)` | | Mã số thuế |
| `status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'Active', CHECK(Active, Inactive)` | Trạng thái |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật cuối |

**Indexes:** `idx_suppliers_name`, `idx_suppliers_phone`

### 1.4. `customers` — Khách hàng

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID khách hàng |
| `customer_code` | `VARCHAR(50)` | `NOT NULL, UNIQUE (partial WHERE deleted_at IS NULL)` | Mã KH |
| `name` | `VARCHAR(255)` | `NOT NULL` | Tên khách hàng |
| `phone` | `VARCHAR(20)` | `NOT NULL` | SĐT |
| `email` | `VARCHAR(255)` | | Email |
| `address` | `TEXT` | | Địa chỉ |
| `loyalty_points` | `INT` | `NOT NULL DEFAULT 0` | Điểm tích lũy |
| `status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'Active', CHECK(Active, Inactive)` | Trạng thái |
| `deleted_at` | `TIMESTAMPTZ` | *(added V38)* | Xóa mềm |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật cuối |

**Indexes:** `idx_customers_phone`, `idx_customers_deleted_at`, `uq_customers_customer_code_active`

### 1.5. `warehouselocations` — Vị trí kho / Kệ

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID vị trí |
| `warehouse_code` | `VARCHAR(20)` | `NOT NULL` | Mã kho |
| `shelf_code` | `VARCHAR(20)` | `NOT NULL` | Mã kệ |
| `description` | `VARCHAR(255)` | | Mô tả vị trí |
| `capacity` | `DECIMAL(8,2)` | | Sức chứa |
| `status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'Active', CHECK(Active, Maintenance, Inactive)` | Trạng thái |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |

**Unique:** `uq_warehouse_shelf(warehouse_code, shelf_code)`

---

## 2. Bảng định tuyến (Reference)

### 2.1. `users` — Người dùng

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID người dùng |
| `username` | `VARCHAR(100)` | `NOT NULL, UNIQUE` | Tên đăng nhập |
| `password_hash` | `VARCHAR(255)` | `NOT NULL` | Mật khẩu hash (bcrypt) |
| `full_name` | `VARCHAR(255)` | `NOT NULL` | Họ tên |
| `email` | `VARCHAR(255)` | `NOT NULL, UNIQUE` | Email |
| `phone` | `VARCHAR(20)` | | SĐT |
| `role_id` | `INT` | `NOT NULL, FK → roles(id) ON DELETE RESTRICT` | Vai trò |
| `staff_code` | `VARCHAR(50)` | *(added V5), UNIQUE partial* | Mã nhân viên |
| `status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'Active', CHECK(Active, Locked)` | Trạng thái |
| `last_login` | `TIMESTAMP` | | Lần đăng nhập cuối |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật cuối |

**Indexes:** `idx_users_phone`, `uq_users_staff_code`

### 2.2. `refresh_tokens` — Refresh Token (OAuth)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID token |
| `user_id` | `INT` | `NOT NULL, FK → users(id) ON DELETE CASCADE` | Người dùng |
| `token` | `VARCHAR(64)` | `NOT NULL, UNIQUE` | Refresh token hash |
| `expires_at` | `TIMESTAMP` | `NOT NULL` | Hết hạn |
| `delete_ymd` | `TIMESTAMPTZ` | *(added V4)* | Thời điểm thu hồi (soft delete) |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |

**Indexes:** `idx_refresh_tokens_user_id`

### 2.3. `products` — Sản phẩm

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID sản phẩm |
| `category_id` | `INT` | `FK → categories(id) ON DELETE SET NULL` | Danh mục |
| `sku_code` | `VARCHAR(50)` | `NOT NULL, UNIQUE` | Mã SKU |
| `barcode` | `VARCHAR(100)` | | Mã vạch |
| `name` | `VARCHAR(255)` | `NOT NULL` | Tên sản phẩm |
| `image_url` | `VARCHAR(500)` | | URL ảnh đại diện |
| `description` | `TEXT` | | Mô tả |
| `weight` | `DECIMAL(8,2)` | | Trọng lượng (gram) |
| `status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'Active', CHECK(Active, Inactive)` | Trạng thái |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật cuối |

**Indexes:** `idx_products_sku`, `idx_products_barcode`, `idx_products_name`, `idx_products_status`

### 2.4. `productimages` — Hình ảnh sản phẩm

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID ảnh |
| `product_id` | `INT` | `NOT NULL, FK → products(id) ON DELETE CASCADE` | Sản phẩm |
| `image_url` | `VARCHAR(500)` | `NOT NULL` | URL ảnh |
| `alt_text` | `VARCHAR(255)` | | Alt SEO |
| `is_primary` | `BOOLEAN` | `NOT NULL DEFAULT FALSE` | Ảnh chính (1 ảnh/SKU) |
| `sort_order` | `INT` | `NOT NULL DEFAULT 0` | Thứ tự hiển thị |
| `file_size_bytes` | `INT` | | Kích thước file |
| `mime_type` | `VARCHAR(100)` | | MIME type |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |

**Indexes:** `idx_pi_product`, `idx_pi_primary`, `uq_productimages_one_primary`

---

## 3. Bảng vệ tinh & hệ thống

### 3.1. `alertsettings` — Cấu hình cảnh báo

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID cấu hình |
| `owner_id` | `INT` | `NOT NULL, FK → users(id) ON DELETE CASCADE` | Chủ cấu hình |
| `alert_type` | `VARCHAR(30)` | `NOT NULL, CHECK(LowStock, ExpiryDate, HighValueTransaction, PendingApproval, OverStock, SalesOrderCreated, PartnerDebtDueSoon, SystemHealth)` | Loại cảnh báo |
| `threshold_value` | `DECIMAL(10,2)` | | Ngưỡng |
| `channel` | `VARCHAR(20)` | `NOT NULL, CHECK(App, Email, SMS, Zalo)` | Kênh gửi |
| `frequency` | `VARCHAR(20)` | `NOT NULL DEFAULT 'Realtime', CHECK(Realtime, Daily, Weekly)` | Tần suất |
| `is_enabled` | `BOOLEAN` | `NOT NULL DEFAULT TRUE` | Bật/tắt |
| `recipients` | `JSONB` | | Danh sách người nhận bổ sung |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật cuối |

**Indexes:** `idx_alert_owner`, `uq_alert_settings_owner_alert_type`

### 3.2. `systemlogs` — Nhật ký hệ thống

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID log |
| `log_level` | `VARCHAR(20)` | `NOT NULL, CHECK(INFO, WARNING, ERROR, CRITICAL)` | Cấp độ |
| `module` | `VARCHAR(100)` | `NOT NULL` | Module |
| `action` | `VARCHAR(255)` | `NOT NULL` | Hành động |
| `user_id` | `INT` | `FK → users(id) ON DELETE SET NULL` | Người thao tác |
| `message` | `TEXT` | `NOT NULL` | Nội dung |
| `stack_trace` | `TEXT` | | Stack trace |
| `context_data` | `JSONB` | | Dữ liệu bổ sung |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm ghi |

**Indexes:** `idx_syslog_level`, `idx_syslog_created_at`

### 3.3. `financeledger` — Sổ cái tài chính

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID bút toán |
| `transaction_date` | `DATE` | `NOT NULL` | Ngày chứng từ |
| `transaction_type` | `VARCHAR(30)` | `NOT NULL, CHECK(SalesRevenue, PurchaseCost, OperatingExpense, Refund)` | Loại |
| `reference_type` | `VARCHAR(50)` | | Loại chứng từ nguồn (polymorphic) |
| `reference_id` | `INT` | `NOT NULL` | ID chứng từ nguồn |
| `amount` | `DECIMAL(10,2)` | `NOT NULL` | Số tiền (dương=thu, âm=chi) |
| `description` | `TEXT` | | Diễn giải |
| `created_by` | `INT` | `NOT NULL, FK → users(id) ON DELETE RESTRICT` | Người lập |
| `fund_id` | `INT` | `NOT NULL, FK → cash_funds(id) (added V41)` | Quỹ |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật cuối |

**Indexes:** `idx_finance_date`, `idx_finance_type`, `idx_financeledger_ref_dispatch`

### 3.4. `aiinsights` — Phân tích kinh doanh AI

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID insight |
| `owner_id` | `INT` | `NOT NULL, FK → users(id) ON DELETE CASCADE` | Chủ sở hữu |
| `dashboard_snapshot` | `JSONB` | `NOT NULL` | Snapshot dashboard |
| `prompt` | `TEXT` | `NOT NULL` | Prompt gửi LLM |
| `ai_advice` | `TEXT` | `NOT NULL` | Kết quả LLM (Markdown) |
| `model_used` | `VARCHAR(100)` | | Tên model |
| `tokens_used` | `INT` | | Số token |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |

**Indexes:** `idx_ai_insight_owner`

### 3.5. `aichathistory` — Lịch sử Chat Bot

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID tin nhắn |
| `user_id` | `INT` | `NOT NULL, FK → users(id) ON DELETE CASCADE` | Người dùng |
| `session_id` | `VARCHAR(100)` | | Phiên chat |
| `message` | `TEXT` | `NOT NULL` | Nội dung |
| `sender` | `VARCHAR(10)` | `NOT NULL, CHECK(User, Bot)` | Người gửi |
| `intent` | `JSONB` | | Intent nhận dạng |
| `response_time_ms` | `INT` | | Độ trễ |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |

**Indexes:** `idx_chat_user`, `idx_chat_session`, `idx_chat_created_at`

### 3.6. `mediaaudits` — Lưu vết Media Cloud

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID audit |
| `file_type` | `VARCHAR(20)` | `NOT NULL, CHECK(OCR_Image, Voice_Audio)` | Loại file |
| `cloud_url` | `VARCHAR(1000)` | `NOT NULL` | URL Cloud |
| `entity_type` | `VARCHAR(50)` | `NOT NULL` | Loại thực thể (polymorphic) |
| `entity_id` | `INT` | `NOT NULL` | ID thực thể |
| `file_size_bytes` | `INT` | | Kích thước |
| `mime_type` | `VARCHAR(100)` | | MIME |
| `uploaded_by` | `INT` | `FK → users(id) ON DELETE SET NULL` | Người upload |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |

### 3.7. `productunits` — Đơn vị tính quy đổi

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID đơn vị |
| `product_id` | `INT` | `NOT NULL, FK → products(id) ON DELETE CASCADE` | Sản phẩm |
| `unit_name` | `VARCHAR(50)` | `NOT NULL` | Tên đơn vị |
| `conversion_rate` | `DECIMAL(8,2)` | `NOT NULL, CHECK(>0)` | Hệ số quy đổi về base unit |
| `is_base_unit` | `BOOLEAN` | `NOT NULL DEFAULT FALSE` | Đơn vị cơ sở |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật cuối |

**Unique:** `uq_product_unit_name(product_id, unit_name)`, **Index:** `idx_pu_product`

### 3.8. `productpricehistory` — Lịch sử giá

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID lịch sử giá |
| `product_id` | `INT` | `NOT NULL, FK → products(id) ON DELETE CASCADE` | Sản phẩm |
| `unit_id` | `INT` | `NOT NULL, FK → productunits(id) ON DELETE CASCADE` | Đơn vị |
| `cost_price` | `DECIMAL(10,2)` | `NOT NULL, CHECK(>=0)` | Giá vốn |
| `sale_price` | `DECIMAL(10,2)` | `NOT NULL, CHECK(>=0)` | Giá bán |
| `effective_date` | `DATE` | `NOT NULL` | Ngày hiệu lực |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |

**Index:** `idx_price_lookup(product_id, unit_id, effective_date DESC)`

---

## 4. Bảng chứng từ cha & tồn kho (Header)

### 4.1. `inventory` — Tồn kho vật lý

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID tồn kho |
| `product_id` | `INT` | `NOT NULL, FK → products(id) ON DELETE CASCADE` | Sản phẩm |
| `location_id` | `INT` | `NOT NULL, FK → warehouselocations(id) ON DELETE RESTRICT` | Vị trí kho |
| `unit_id` | `INT` | `FK → productunits(id) ON DELETE SET NULL (added V7)` | Đơn vị hiển thị meta |
| `batch_number` | `VARCHAR(100)` | | Số lô |
| `expiry_date` | `DATE` | | Hạn dùng |
| `quantity` | `INT` | `NOT NULL DEFAULT 0, CHECK(>=0)` | Số lượng (base unit) |
| `min_quantity` | `INT` | `NOT NULL DEFAULT 0` | Ngưỡng tối thiểu |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật cuối |

**Unique:** `uq_inventory_product_location_batch(product_id, location_id, batch_number)`
**Indexes:** `idx_inv_product`, `idx_inv_expiry_date`, `idx_inv_unit`

### 4.2. `stockreceipts` — Phiếu Nhập kho

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID phiếu nhập |
| `receipt_code` | `VARCHAR(50)` | `NOT NULL, UNIQUE` | Mã phiếu |
| `supplier_id` | `INT` | `NOT NULL, FK → suppliers(id) ON DELETE RESTRICT` | Nhà cung cấp |
| `staff_id` | `INT` | `NOT NULL, FK → users(id) ON DELETE RESTRICT` | Nhân viên lập |
| `receipt_date` | `DATE` | `NOT NULL` | Ngày nhập |
| `status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'Draft', CHECK(Draft, Pending, Approved, Rejected)` | Trạng thái |
| `invoice_number` | `VARCHAR(100)` | | Số hóa đơn |
| `total_amount` | `DECIMAL(10,2)` | `NOT NULL DEFAULT 0, CHECK(>=0)` | Tổng tiền |
| `notes` | `TEXT` | | Ghi chú |
| `approved_by` | `INT` | `FK → users(id) ON DELETE SET NULL` | Người duyệt |
| `approved_at` | `TIMESTAMP` | | Thời điểm duyệt |
| `rejection_reason` | `TEXT` | *(added V9)* | Lý do từ chối |
| `reviewed_by` | `INT` | `FK → users(id) ON DELETE SET NULL (added V9)` | Người review |
| `reviewed_at` | `TIMESTAMP` | *(added V9)* | Thời điểm review |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật cuối |

**Indexes:** `idx_sr_supplier`, `idx_sr_status`, `idx_sr_reviewed_at`, `idx_sr_receipt_date`

### 4.3. `salesorders` — Đơn hàng bán

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID đơn hàng |
| `order_code` | `VARCHAR(50)` | `NOT NULL, UNIQUE` | Mã đơn |
| `customer_id` | `INT` | `NOT NULL, FK → customers(id) ON DELETE RESTRICT` | Khách hàng |
| `user_id` | `INT` | `NOT NULL, FK → users(id) ON DELETE RESTRICT` | Nhân viên tạo |
| `total_amount` | `DECIMAL(10,2)` | `NOT NULL DEFAULT 0, CHECK(>=0)` | Tổng trước CK |
| `discount_amount` | `DECIMAL(10,2)` | `NOT NULL DEFAULT 0, CHECK(>=0)` | Chiết khấu |
| `final_amount` | `DECIMAL(10,2)` | `GENERATED ALWAYS AS (total_amount - discount_amount) STORED` | Thành tiền |
| `voucher_id` | `INT` | `FK → vouchers(id) ON DELETE SET NULL (added V19)` | Voucher áp dụng |
| `pos_shift_ref` | `VARCHAR(100)` | *(added V19)* | Tham chiếu ca POS |
| `status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'Pending', CHECK(Pending, Processing, Partial, Shipped, Delivered, Cancelled)` | Trạng thái |
| `parent_order_id` | `INT` | `FK → salesorders(id) ON DELETE SET NULL` | Đơn cha (backorder) |
| `shipping_address` | `TEXT` | | Địa chỉ giao |
| `notes` | `TEXT` | | Ghi chú |
| `order_channel` | `VARCHAR(20)` | `NOT NULL DEFAULT 'Wholesale', CHECK(Retail, Wholesale, Return)` | Kênh bán |
| `payment_status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'Unpaid', CHECK(Paid, Unpaid, Partial)` | Thanh toán |
| `ref_sales_order_id` | `INT` | `FK → salesorders(id) ON DELETE SET NULL` | Đơn tham chiếu (đổi/trả) |
| `cancelled_at` | `TIMESTAMP` | | Hủy lúc |
| `cancelled_by` | `INT` | `FK → users(id) ON DELETE SET NULL` | Người hủy |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật cuối |

**Indexes:** `idx_so_customer`, `idx_so_user`, `idx_so_status`, `idx_so_parent`, `idx_so_created_at`, `idx_so_order_channel`, `idx_so_payment_status`, `idx_salesorders_voucher`

### 4.4. `stockdispatches` — Phiếu Xuất kho

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID phiếu xuất |
| `dispatch_code` | `VARCHAR(50)` | `NOT NULL, UNIQUE` | Mã phiếu |
| `order_id` | `INT` | `FK → salesorders(id) ON DELETE RESTRICT (nullable từ V32)` | Đơn hàng (NULL = xuất tay) |
| `reference_label` | `VARCHAR(255)` | *(added V32)* | Mô tả khi xuất tay |
| `user_id` | `INT` | `NOT NULL, FK → users(id) ON DELETE RESTRICT` | Người lập |
| `dispatch_date` | `DATE` | `NOT NULL` | Ngày xuất |
| `status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'Pending', CHECK(Pending, Full, Partial, Cancelled, WaitingDispatch, Delivering, Delivered)` | Trạng thái |
| `notes` | `TEXT` | | Ghi chú |
| `deleted_at` | `TIMESTAMPTZ` | *(added V35)* | Xóa mềm |
| `deleted_by_user_id` | `INT` | `FK → users(id) (added V35)` | Người xóa |
| `delete_reason` | `TEXT` | *(added V35)* | Lý do xóa |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật cuối |

**Indexes:** `idx_sd_order`, `idx_sd_status`, `ix_stockdispatches_deleted_active`

---

## 5. Bảng chi tiết chứng từ (Detail)

### 5.1. `stockreceiptdetails` — Chi tiết Phiếu Nhập

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID dòng nhập |
| `receipt_id` | `INT` | `NOT NULL, FK → stockreceipts(id) ON DELETE CASCADE` | Phiếu nhập |
| `product_id` | `INT` | `NOT NULL, FK → products(id) ON DELETE RESTRICT` | Sản phẩm |
| `unit_id` | `INT` | `NOT NULL, FK → productunits(id) ON DELETE RESTRICT` | Đơn vị |
| `quantity` | `INT` | `NOT NULL, CHECK(>0)` | Số lượng |
| `cost_price` | `DECIMAL(10,2)` | `NOT NULL, CHECK(>=0)` | Đơn giá vốn |
| `batch_number` | `VARCHAR(100)` | | Số lô |
| `expiry_date` | `DATE` | | Hạn dùng |
| `line_total` | `DECIMAL(10,2)` | `GENERATED ALWAYS AS (quantity * cost_price) STORED` | Thành tiền |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |

**Unique:** `uq_srd_receipt_product_batch(receipt_id, product_id, batch_number)`
**Index:** `idx_srd_receipt`

### 5.2. `orderdetails` — Chi tiết Đơn hàng

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID dòng đơn |
| `order_id` | `INT` | `NOT NULL, FK → salesorders(id) ON DELETE CASCADE` | Đơn hàng |
| `product_id` | `INT` | `NOT NULL, FK → products(id) ON DELETE RESTRICT` | Sản phẩm |
| `unit_id` | `INT` | `NOT NULL, FK → productunits(id) ON DELETE RESTRICT` | Đơn vị |
| `quantity` | `INT` | `NOT NULL, CHECK(>0)` | Số lượng đặt |
| `price_at_time` | `DECIMAL(10,2)` | `NOT NULL, CHECK(>=0)` | Đơn giá snapshot |
| `line_total` | `DECIMAL(10,2)` | `GENERATED ALWAYS AS (quantity * price_at_time) STORED` | Thành tiền |
| `dispatched_qty` | `INT` | `NOT NULL DEFAULT 0, CHECK(>=0), CHECK(<=quantity)` | Đã xuất |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |

**Unique:** `uq_od_order_product_unit(order_id, product_id, unit_id)`
**Index:** `idx_od_order`

### 5.3. `stockdispatch_lines` — Chi tiết Phiếu Xuất

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | `PK` | ID dòng xuất |
| `dispatch_id` | `INTEGER` | `NOT NULL, FK → stockdispatches(id) ON DELETE CASCADE` | Phiếu xuất |
| `inventory_id` | `INTEGER` | `NOT NULL, FK → inventory(id)` | Lô tồn |
| `quantity` | `INTEGER` | `NOT NULL, CHECK(>0)` | Số lượng xuất |
| `unit_price_snapshot` | `NUMERIC(14,4)` | *(added V36)* | Đơn giá snapshot |

**Unique:** `uq_stockdispatch_line(dispatch_id, inventory_id)`
**Index:** `ix_stockdispatch_lines_dispatch`

---

## 6. Bảng log

### 6.1. `inventorylogs` — Nhật ký biến động Kho

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID log |
| `product_id` | `INT` | `NOT NULL, FK → products(id) ON DELETE RESTRICT` | Sản phẩm |
| `action_type` | `VARCHAR(20)` | `NOT NULL, CHECK(INBOUND, OUTBOUND, TRANSFER, ADJUSTMENT)` | Loại biến động |
| `quantity_change` | `INT` | `NOT NULL` | Số lượng (+/-) |
| `unit_id` | `INT` | `NOT NULL, FK → productunits(id) ON DELETE RESTRICT` | Đơn vị |
| `user_id` | `INT` | `FK → users(id) ON DELETE SET NULL` | Người thao tác |
| `dispatch_id` | `INT` | `FK → stockdispatches(id) ON DELETE SET NULL` | Phiếu xuất |
| `receipt_id` | `INT` | `FK → stockreceipts(id) ON DELETE SET NULL` | Phiếu nhập |
| `from_location_id` | `INT` | `FK → warehouselocations(id) ON DELETE SET NULL` | Vị trí nguồn |
| `to_location_id` | `INT` | `FK → warehouselocations(id) ON DELETE SET NULL` | Vị trí đích |
| `reference_note` | `VARCHAR(255)` | | Ghi chú |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm |

**Indexes:** `idx_il_product`, `idx_il_created_at`, `idx_il_dispatch`, `idx_il_receipt`

### 6.2. `inventory_audit_session_events` — Sự kiện timeline kiểm kê

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID sự kiện |
| `session_id` | `INT` | `NOT NULL, FK → inventoryauditsessions(id) ON DELETE CASCADE` | Phiên kiểm kê |
| `event_type` | `VARCHAR(80)` | `NOT NULL` | Loại sự kiện |
| `payload` | `JSONB` | | Chi tiết |
| `created_by` | `INT` | `NOT NULL, FK → users(id) ON DELETE RESTRICT` | Người tạo |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Thời điểm |

**Index:** `idx_audit_session_events_session`

---

## 7. Bảng optional & bổ sung

### 7.1. `notifications` — Thông báo in-app

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID thông báo |
| `user_id` | `INT` | `NOT NULL, FK → users(id) ON DELETE CASCADE` | Người nhận |
| `notification_type` | `VARCHAR(30)` | `NOT NULL, CHECK(ApprovalResult, LowStock, ExpiryWarning, SystemAlert, PasswordResetRequest, StockReceiptPendingApproval, StockDispatchPendingApproval, StockDispatchShortage)` | Loại |
| `title` | `VARCHAR(255)` | `NOT NULL` | Tiêu đề |
| `message` | `TEXT` | `NOT NULL` | Nội dung |
| `is_read` | `BOOLEAN` | `NOT NULL DEFAULT FALSE` | Đã đọc |
| `reference_type` | `VARCHAR(50)` | | Loại thực thể liên kết |
| `reference_id` | `INT` | | ID thực thể |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `read_at` | `TIMESTAMP` | | Thời điểm đọc |

**Index:** `idx_notif_user_unread(user_id, is_read)`

### 7.2. `storeprofiles` — Hồ sơ cửa hàng

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID hồ sơ |
| `owner_id` | `INT` | `NOT NULL, UNIQUE, FK → users(id) ON DELETE CASCADE` | Chủ sở hữu |
| `name` | `VARCHAR(255)` | `NOT NULL` | Tên cửa hàng |
| `default_retail_location_id` | `INT` | `FK → warehouselocations(id) ON DELETE SET NULL (added V20)` | Kho mặc định POS |
| `business_category` | `VARCHAR(255)` | | Ngành hàng |
| `address` | `TEXT` | | Địa chỉ |
| `phone` | `VARCHAR(30)` | | SĐT |
| `email` | `VARCHAR(255)` | | Email |
| `website` | `VARCHAR(500)` | | Website |
| `tax_code` | `VARCHAR(50)` | | MST |
| `footer_note` | `TEXT` | | Chân in bill |
| `logo_url` | `VARCHAR(500)` | | Logo |
| `facebook_url` | `VARCHAR(500)` | | Facebook |
| `instagram_handle` | `VARCHAR(255)` | | Instagram |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật cuối |

**Indexes:** `idx_store_profiles_owner`, `idx_storeprofiles_default_retail_location`

### 7.3. `cashtransactions` — Phiếu thu chi

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID phiếu |
| `transaction_code` | `VARCHAR(50)` | `NOT NULL, UNIQUE` | Mã giao dịch |
| `direction` | `VARCHAR(10)` | `NOT NULL, CHECK(Income, Expense)` | Thu/Chi |
| `amount` | `DECIMAL(15,2)` | `NOT NULL, CHECK(>0)` | Số tiền |
| `category` | `VARCHAR(500)` | `NOT NULL` | Danh mục |
| `description` | `TEXT` | | Diễn giải |
| `payment_method` | `VARCHAR(30)` | `NOT NULL DEFAULT 'Cash'` | Phương thức |
| `status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'Pending', CHECK(Pending, Completed, Cancelled)` | Trạng thái |
| `transaction_date` | `DATE` | `NOT NULL` | Ngày chứng từ |
| `finance_ledger_id` | `INT` | `FK → financeledger(id) ON DELETE SET NULL` | Bút toán sổ cái |
| `created_by` | `INT` | `NOT NULL, FK → users(id) ON DELETE RESTRICT` | Người tạo |
| `performed_by` | `INT` | `NOT NULL, FK → users(id) (added V25)` | Người thực hiện |
| `fund_id` | `INT` | `NOT NULL, FK → cash_funds(id) (added V41)` | Quỹ |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật cuối |

**Indexes:** `idx_cash_tx_date`, `idx_cash_tx_status`, `idx_cash_tx_created_at`

### 7.4. `partnerdebts` — Công nợ đối tác

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID công nợ |
| `debt_code` | `VARCHAR(50)` | `NOT NULL, UNIQUE` | Mã công nợ |
| `partner_type` | `VARCHAR(20)` | `NOT NULL, CHECK(Customer, Supplier)` | Loại đối tác |
| `customer_id` | `INT` | `FK → customers(id) ON DELETE RESTRICT` | Khách hàng (nếu là Customer) |
| `supplier_id` | `INT` | `FK → suppliers(id) ON DELETE RESTRICT` | NCC (nếu là Supplier) |
| `total_amount` | `DECIMAL(15,2)` | `NOT NULL, CHECK(>=0)` | Tổng nợ |
| `paid_amount` | `DECIMAL(15,2)` | `NOT NULL DEFAULT 0, CHECK(>=0)` | Đã trả |
| `due_date` | `DATE` | | Hạn thanh toán |
| `status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'InDebt', CHECK(InDebt, Cleared)` | Trạng thái |
| `notes` | `TEXT` | | Ghi chú |
| `created_by` | `INT` | `NOT NULL, FK → users(id) ON DELETE RESTRICT (added V26)` | Người lập |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật cuối |

**Checks:** `chk_partner_debts_partner` (chỉ 1 trong 2 FK), `chk_paid_le_total`
**Indexes:** `idx_partner_debts_status`, `idx_partner_debts_customer`, `idx_partner_debts_supplier`, `idx_partnerdebts_updated_id`

### 7.5. `staffpasswordresetrequests` — Yêu cầu reset mật khẩu

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID yêu cầu |
| `user_id` | `INT` | `NOT NULL, FK → users(id) ON DELETE CASCADE` | Nhân viên |
| `message` | `TEXT` | | Nội dung |
| `status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'Pending', CHECK(Pending, Processed, Cancelled)` | Trạng thái |
| `processed_by` | `INT` | `FK → users(id) ON DELETE SET NULL` | Người xử lý |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `processed_at` | `TIMESTAMP` | | Thời điểm xử lý |

**Index:** `idx_sp_reset_user_status(user_id, status)`

### 7.6. `inventoryauditsessions` — Phiên kiểm kê

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID phiên |
| `audit_code` | `VARCHAR(50)` | `NOT NULL, UNIQUE` | Mã phiên |
| `title` | `VARCHAR(255)` | `NOT NULL` | Tiêu đề |
| `audit_date` | `DATE` | `NOT NULL` | Ngày kiểm |
| `status` | `VARCHAR(50)` | `NOT NULL, CHECK(Pending, In Progress, Pending Owner Approval, Completed, Cancelled, Re-check)` | Trạng thái |
| `location_filter` | `VARCHAR(100)` | | Lọc vị trí |
| `category_filter` | `VARCHAR(50)` | | Lọc danh mục |
| `notes` | `TEXT` | | Ghi chú |
| `cancel_reason` | `VARCHAR(1000)` | *(added V11)* | Lý do hủy |
| `created_by` | `INT` | `NOT NULL, FK → users(id) ON DELETE RESTRICT` | Người tạo |
| `completed_at` | `TIMESTAMP` | | Hoàn tất lúc |
| `completed_by` | `INT` | `FK → users(id) ON DELETE SET NULL` | Người hoàn tất |
| `deleted_at` | `TIMESTAMPTZ` | *(added V12)* | Xóa mềm |
| `owner_notes` | `TEXT` | *(added V12)* | Ghi chú Owner |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật cuối |

**Indexes:** `idx_audit_sessions_status`

### 7.7. `inventoryauditlines` — Dòng kiểm kê

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID dòng kiểm |
| `session_id` | `INT` | `NOT NULL, FK → inventoryauditsessions(id) ON DELETE CASCADE` | Phiên kiểm kê |
| `inventory_id` | `INT` | `NOT NULL, FK → inventory(id) ON DELETE RESTRICT` | Lô tồn |
| `system_quantity` | `DECIMAL(12,4)` | `NOT NULL` | SL hệ thống |
| `actual_quantity` | `DECIMAL(12,4)` | | SL thực tế |
| `is_counted` | `BOOLEAN` | `NOT NULL DEFAULT FALSE` | Đã đếm |
| `notes` | `VARCHAR(500)` | | Ghi chú |
| `variance_applied_at` | `TIMESTAMP` | | Áp dụng điều chỉnh |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật cuối |

**Index:** `idx_audit_lines_session`

### 7.8. `vouchers` — Mã khuyến mãi

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID voucher |
| `code` | `VARCHAR(50)` | `NOT NULL, UNIQUE` | Mã quét |
| `name` | `VARCHAR(255)` | | Tên hiển thị |
| `discount_type` | `VARCHAR(20)` | `NOT NULL, CHECK(Percent, FixedAmount)` | Loại giảm giá |
| `discount_value` | `NUMERIC(12,2)` | `NOT NULL` | Giá trị giảm |
| `is_active` | `BOOLEAN` | `NOT NULL DEFAULT TRUE` | Đang dùng |
| `valid_from` | `DATE` | | Hiệu lực từ |
| `valid_to` | `DATE` | | Hiệu lực đến |
| `used_count` | `INTEGER` | `NOT NULL DEFAULT 0 (added V24)` | Số lần đã dùng |
| `max_uses` | `INTEGER` | *(added V24)* | Giới hạn lượt |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật cuối |

### 7.9. `voucher_redemptions` — Lượt sử dụng voucher

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID redemption |
| `voucher_id` | `INT` | `NOT NULL, FK → vouchers(id) ON DELETE CASCADE` | Voucher |
| `sales_order_id` | `INT` | `NOT NULL, FK → salesorders(id) ON DELETE CASCADE, UNIQUE` | Đơn hàng |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm áp dụng |

**Index:** `idx_voucher_redemptions_voucher`

### 7.10. `cash_funds` — Quỹ tiền

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PK` | ID quỹ |
| `code` | `VARCHAR(30)` | `NOT NULL, UNIQUE` | Mã quỹ |
| `name` | `VARCHAR(255)` | `NOT NULL` | Tên quỹ |
| `is_default` | `BOOLEAN` | `NOT NULL DEFAULT FALSE` | Quỹ mặc định |
| `is_active` | `BOOLEAN` | `NOT NULL DEFAULT TRUE` | Đang dùng |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Thời điểm tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật cuối |

**Unique:** `uq_cash_funds_code`, **Index:** `idx_cash_funds_active_default`

---

## 8. Bảng AI & Meta

### 8.1. `ai_table_description` — Registry mô tả bảng cho AI

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | `PK` | ID |
| `table_name` | `VARCHAR(128)` | `NOT NULL, UNIQUE, CHECK(lowercase)` | Tên bảng PostgreSQL |
| `description` | `TEXT` | `NOT NULL DEFAULT ''` | Mô tả nghiệp vụ |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật |

### 8.2. `ai_column_description` — Registry mô tả cột cho AI

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | `PK` | ID |
| `table_name` | `VARCHAR(128)` | `NOT NULL, FK → ai_table_description(table_name) ON DELETE CASCADE` | Tên bảng |
| `column_name` | `VARCHAR(128)` | `NOT NULL` | Tên cột |
| `description` | `TEXT` | `NOT NULL DEFAULT ''` | Mô tả nghiệp vụ |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Tạo |
| `updated_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Cập nhật |

**Unique:** `uq_ai_column_description_table_column(table_name, column_name)`
**Index:** `idx_ai_column_description_table_name`

### 8.3. `ai_catalog_draft` — Nháp catalog do AI sinh

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | ID |
| `user_id` | `VARCHAR(64)` | `NOT NULL` | Người dùng |
| `tenant_id` | `VARCHAR(32)` | `NOT NULL DEFAULT '1'` | Tenant |
| `conversation_id` | `VARCHAR(128)` | | Hội thoại |
| `entity_type` | `VARCHAR(32)` | `NOT NULL, CHECK(product, category, supplier, customer)` | Loại thực thể |
| `status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'draft', CHECK(draft, committed, expired)` | Trạng thái |
| `payload` | `JSONB` | `NOT NULL` | Dữ liệu nháp |
| `commit_result` | `JSONB` | | Kết quả commit |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Tạo |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Cập nhật |
| `expires_at` | `TIMESTAMPTZ` | `NOT NULL` | Hết hạn |

**Indexes:** `ix_ai_catalog_draft_user_created`, `ix_ai_catalog_draft_expires`

### 8.4. `ai_inventory_draft` — Nháp chứng từ kho do AI sinh

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | ID |
| `user_id` | `VARCHAR(64)` | `NOT NULL` | Người dùng |
| `tenant_id` | `VARCHAR(32)` | `NOT NULL DEFAULT '1'` | Tenant |
| `conversation_id` | `VARCHAR(128)` | | Hội thoại |
| `entity_type` | `VARCHAR(32)` | `NOT NULL, CHECK(stock_receipt)` | Loại chứng từ |
| `status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'draft', CHECK(draft, committed, expired)` | Trạng thái |
| `payload` | `JSONB` | `NOT NULL` | Dữ liệu nháp |
| `commit_result` | `JSONB` | | Kết quả commit |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Tạo |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Cập nhật |
| `expires_at` | `TIMESTAMPTZ` | `NOT NULL` | Hết hạn |

**Indexes:** `ix_ai_inventory_draft_user_created`, `ix_ai_inventory_draft_expires`

---

## 9. Custom Interface Builder

### 9.1. `custom_menu_folders` — Thư mục menu tùy chỉnh

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | `PK` | ID |
| `folder_key` | `VARCHAR(80)` | `NOT NULL` | Key thư mục |
| `label` | `VARCHAR(160)` | `NOT NULL` | Nhãn hiển thị |
| `icon` | `VARCHAR(80)` | | Icon |
| `description` | `TEXT` | | Mô tả |
| `status` | `VARCHAR(30)` | `NOT NULL DEFAULT 'Draft'` | Trạng thái |
| `sort_order` | `INT` | `NOT NULL DEFAULT 0` | Thứ tự |
| `visibility_roles` | `JSONB` | `NOT NULL DEFAULT '[]'` | Vai trò được xem |
| `visibility_permissions` | `JSONB` | `NOT NULL DEFAULT '[]'` | Quyền được xem |
| `draft_version` | `INT` | `NOT NULL DEFAULT 1` | Phiên bản nháp |
| `published_version` | `INT` | | Phiên bản published |
| `etag` | `VARCHAR(160)` | `NOT NULL` | ETag |
| `created_by` | `INT` | `NOT NULL` | Người tạo |
| `updated_by` | `INT` | | Người cập nhật |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Tạo |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Cập nhật |
| `published_at` | `TIMESTAMPTZ` | | Published lúc |
| `archived_at` | `TIMESTAMPTZ` | | Archived lúc |

**Unique Index:** `ux_custom_menu_folders_key_active(folder_key) WHERE archived_at IS NULL`

### 9.2. `custom_menu_pages` — Trang menu tùy chỉnh

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | `PK` | ID |
| `page_key` | `VARCHAR(80)` | `NOT NULL` | Key trang |
| `parent_folder_key` | `VARCHAR(80)` | `NOT NULL` | Thư mục cha |
| `label` | `VARCHAR(160)` | `NOT NULL` | Nhãn |
| `icon` | `VARCHAR(80)` | | Icon |
| `description` | `TEXT` | | Mô tả |
| `route_path` | `VARCHAR(200)` | `NOT NULL` | Đường dẫn |
| `entity_key` | `VARCHAR(80)` | `NOT NULL` | Entity |
| `page_type` | `VARCHAR(40)` | `NOT NULL` | Loại trang |
| `status` | `VARCHAR(30)` | `NOT NULL DEFAULT 'NeedsConfig'` | Trạng thái |
| `sort_order` | `INT` | `NOT NULL DEFAULT 0` | Thứ tự |
| `visibility_roles` | `JSONB` | `NOT NULL DEFAULT '[]'` | Vai trò được xem |
| `entity_permission` | `VARCHAR(80)` | | Quyền entity |
| `data_permission` | `VARCHAR(80)` | | Quyền dữ liệu |
| `draft_version` | `INT` | `NOT NULL DEFAULT 1` | Phiên bản nháp |
| `published_version` | `INT` | | Phiên bản published |
| `etag` | `VARCHAR(160)` | `NOT NULL` | ETag |
| `created_by` | `INT` | `NOT NULL` | Người tạo |
| `updated_by` | `INT` | | Người cập nhật |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Tạo |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Cập nhật |
| `published_at` | `TIMESTAMPTZ` | | Published lúc |
| `archived_at` | `TIMESTAMPTZ` | | Archived lúc |

**Unique Indexes:** `ux_custom_menu_pages_key_active`, `ux_custom_menu_pages_route_active`
**Index:** `idx_custom_menu_pages_parent_order`

### 9.3. `custom_menu_folder_versions` — Phiên bản thư mục

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | `PK` | ID |
| `folder_key` | `VARCHAR(80)` | `NOT NULL` | Key thư mục |
| `version` | `INT` | `NOT NULL` | Phiên bản |
| `label` | `VARCHAR(160)` | `NOT NULL` | Nhãn |
| `icon` | `VARCHAR(80)` | | Icon |
| `description` | `TEXT` | | Mô tả |
| `sort_order` | `INT` | `NOT NULL` | Thứ tự |
| `visibility_roles` | `JSONB` | `NOT NULL DEFAULT '[]'` | Vai trò |
| `published_by` | `INT` | `NOT NULL` | Người publish |
| `published_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Thời điểm publish |

**Unique:** `UNIQUE(folder_key, version)`

### 9.4. `custom_menu_page_versions` — Phiên bản trang

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | `PK` | ID |
| `page_key` | `VARCHAR(80)` | `NOT NULL` | Key trang |
| `version` | `INT` | `NOT NULL` | Phiên bản |
| `parent_folder_key` | `VARCHAR(80)` | `NOT NULL` | Thư mục cha |
| `label` | `VARCHAR(160)` | `NOT NULL` | Nhãn |
| `icon` | `VARCHAR(80)` | | Icon |
| `description` | `TEXT` | | Mô tả |
| `route_path` | `VARCHAR(200)` | `NOT NULL` | Đường dẫn |
| `entity_key` | `VARCHAR(80)` | `NOT NULL` | Entity |
| `page_type` | `VARCHAR(40)` | `NOT NULL` | Loại trang |
| `sort_order` | `INT` | `NOT NULL` | Thứ tự |
| `visibility_roles` | `JSONB` | `NOT NULL DEFAULT '[]'` | Vai trò |
| `entity_permission` | `VARCHAR(80)` | | Quyền entity |
| `data_permission` | `VARCHAR(80)` | | Quyền dữ liệu |
| `published_by` | `INT` | `NOT NULL` | Người publish |
| `published_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Thời điểm publish |

**Unique:** `UNIQUE(page_key, version)`, **Index:** `idx_custom_menu_page_versions_lookup`

### 9.5. `custom_menu_events` — Sự kiện menu

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | `PK` | ID |
| `target_type` | `VARCHAR(30)` | `NOT NULL` | Loại đối tượng |
| `target_key` | `VARCHAR(80)` | `NOT NULL` | Key đối tượng |
| `event_type` | `VARCHAR(40)` | `NOT NULL` | Loại sự kiện |
| `payload` | `JSONB` | `NOT NULL DEFAULT '{}'` | Chi tiết |
| `created_by` | `INT` | `NOT NULL` | Người tạo |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Thời điểm |

### 9.6. `user_table_column_settings` — Cài đặt cột bảng theo user

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | `PK` | ID |
| `user_id` | `BIGINT` | `NOT NULL, FK → users(id) ON DELETE CASCADE` | Người dùng |
| `table_key` | `VARCHAR(80)` | `NOT NULL, CHECK(inventory_stock, inventory_receipts, inventory_dispatch, product_categories, product_list, product_suppliers, product_customers)` | Khóa bảng |
| `hidden_columns` | `JSONB` | `NOT NULL DEFAULT '[]'` | Cột ẩn |
| `column_order` | `JSONB` | `NOT NULL DEFAULT '[]'` | Thứ tự cột |
| `updated_by` | `BIGINT` | `FK → users(id) ON DELETE SET NULL` | Người cập nhật |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Tạo |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Cập nhật |

**Unique:** `uq_user_table_column_settings_user_table(user_id, table_key)`
**Index:** `idx_user_table_column_settings_user_id`

### 9.7. `global_table_column_settings` — Cài đặt cột bảng toàn cục

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | `PK` | ID |
| `table_key` | `VARCHAR(80)` | `NOT NULL, UNIQUE, CHECK(inventory_stock, inventory_receipts, inventory_dispatch, product_categories, product_list, product_suppliers, product_customers)` | Khóa bảng |
| `hidden_columns` | `JSONB` | `NOT NULL DEFAULT '[]'` | Cột ẩn |
| `column_order` | `JSONB` | `NOT NULL DEFAULT '[]'` | Thứ tự cột |
| `updated_by` | `BIGINT` | `FK → users(id) ON DELETE SET NULL` | Người cập nhật |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Tạo |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Cập nhật |

---

## 10. Function & Trigger

### Function `fn_update_timestamp()`

```sql
CREATE OR REPLACE FUNCTION fn_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### Triggers (auto-update `updated_at`)

| Trigger | Bảng |
|---------|------|
| `trg_categories_updated` | categories |
| `trg_suppliers_updated` | suppliers |
| `trg_customers_updated` | customers |
| `trg_users_updated` | users |
| `trg_products_updated` | products |
| `trg_alertsettings_updated` | alertsettings |
| `trg_finance_updated` | financeledger |
| `trg_productunits_updated` | productunits |
| `trg_inventory_updated` | inventory |
| `trg_stockreceipts_updated` | stockreceipts |
| `trg_salesorders_updated` | salesorders |
| `trg_dispatches_updated` | stockdispatches |
| `trg_storeprofiles_updated` | storeprofiles |
| `trg_cashtx_updated` | cashtransactions |
| `trg_partnerdebts_updated` | partnerdebts |
| `trg_audit_sessions_updated` | inventoryauditsessions |
| `trg_audit_lines_updated` | inventoryauditlines |
| `trg_vouchers_updated` | vouchers |

---

## Tổng kết

| Thống kê | Số lượng |
|----------|---------|
| **Tổng số bảng** | **~44** (core + bổ sung + meta) |
| **Foreign Keys** | 50+ |
| **UNIQUE Constraints** | 20+ |
| **CHECK Constraints** | 25+ |
| **Indexes** | 45+ |
| **Generated Columns** | 3 (`line_total × 2`, `final_amount`) |
| **Triggers** | 18 (auto-update `updated_at`) |

> **Nguồn:** Toàn bộ Flyway migration files (`V1__baseline_smart_inventory.sql` → `V56__task001_custom_interface_builder.sql`)
