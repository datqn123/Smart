# Đặc tả Chi tiết Cơ sở dữ liệu - Smart Inventory Management

## 📋 Thông tin tài liệu

- **Dự án**: Quản lý Kho thông minh (Smart Inventory Management)
- **Database**: PostgreSQL 15+
- **Phiên bản**: 5.0 - PRODUCTION SPECIFICATION
- **Ngày tạo**: 11/04/2026
- **Tham chiếu**:
  - Database_Schema_Detail.md v4.0
  - schema.sql (747 lines)
  - UseCase_Database_Coverage.md
  - 13 Use Cases (UC1-UC13)

---

## 🎯 Tổng quan kiến trúc

### Số lượng bảng: **25** (24 chính + 1 optional)

| Nhóm | Số bảng | Bảng |
|------|---------|------|
| Quản trị & Người dùng | 5 | Roles, Users, StoreProfiles (§6.1), AlertSettings, SystemLogs |
| Đối tác & Tài chính | 5 | Customers, Suppliers, FinanceLedger, CashTransactions (§12.1), PartnerDebts (§12.2) |
| Danh mục & Sản phẩm | 5 | Categories, Products, ProductImages, ProductUnits, ProductPriceHistory |
| Kho hàng & Giao dịch | 8 | WarehouseLocations, Inventory, StockReceipts, StockReceiptDetails, SalesOrders, OrderDetails, StockDispatches, InventoryLogs |
| AI & Media | 3 | AIInsights, AIChatHistory, MediaAudits |
| Optional | 1 | Notifications |

### Thống kê Constraints

| Loại              | Số lượng | Mục đích                      |
| ----------------- | -------- | ----------------------------- |
| PRIMARY KEY       | 23       | Định danh duy nhất mỗi bảng   |
| UNIQUE            | 13       | Ngăn trùng dữ liệu            |
| FOREIGN KEY       | 42       | Đảm bảo tham chiếu toàn vẹn   |
| CHECK             | 18       | Validate dữ liệu tại DB level |
| INDEX             | 30+      | Tối ưu tốc độ query           |
| Generated Columns | 3        | Tự động tính toán             |
| Triggers          | 12       | Auto-update timestamps        |

---

## 📊 Sơ đồ quan hệ tổng quan

```
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│   Roles     │         │  Categories  │         │  Suppliers   │
└──────┬──────┘         └──────┬───────┘         └──────┬───────┘
       │                       │                        │
       │         ┌─────────────┼────────────────────────┘
       │         │             │
       ▼         ▼             ▼
┌──────────────────────────────────────┐         ┌──────────────┐
│            Users                     │         │  Customers   │
└──────────┬───────────────────────────┘         └──────┬───────┘
           │                                             │
           │         ┌───────────────────────────────────┘
           │         │
           ▼         ▼
┌──────────────────────────────────────────────────────────┐
│                      Products                            │
└────┬──────────────┬──────────────────┬───────────────────┘
     │              │                   │
     │              │                   │
     ▼              ▼                   ▼
┌─────────┐  ┌──────────────┐   ┌──────────────────┐
│ Product │  │ProductUnits  │   │ProductPriceHistory│
│ Units   │  │              │   │                   │
└────┬────┘  └──────┬───────┘   └───────────────────┘
     │              │
     │              │
     ▼              ▼
┌─────────────────────────────────────────────────────────┐
│                    Inventory                             │
└────────┬───────────────────────┬────────────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌────────────────┐      ┌─────────────────┐
│ StockReceipts  │      │  SalesOrders    │
│  + Details     │      │  + Details      │
└────────┬───────┘      └────────┬────────┘
         │                       │
         │                       │
         ▼                       ▼
┌────────────────────────────────────────────────────────┐
│               StockDispatches                          │
└────────────────────────┬───────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────┐
│                InventoryLogs                           │
└────────────────────────────────────────────────────────┘

AI & Media Tables (độc lập):
- AIInsights (Users → AIInsights)
- AIChatHistory (Users → AIChatHistory)
- MediaAudits (Users → MediaAudits, polymorphic)
- FinanceLedger (Users → FinanceLedger, polymorphic)
- Notifications (Users → Notifications)
- SystemLogs (Users → SystemLogs)
- WarehouseLocations (độc lập, referenced bởi Inventory)
- AlertSettings (Users → AlertSettings)
```

---

## 📋 Chi tiết từng bảng

### 1. Roles (Vai trò người dùng)

**Mục đích**: Định nghĩa các vai trò và quyền hạn trong hệ thống  
**Use Cases**: UC3 (Manage Staff Accounts)  
**Nhóm**: Quản trị & Người dùng

#### Columns

| Cột           | Kiểu dữ liệu | Ràng buộc        | Mặc định          | Mô tả                            |
| ------------- | ------------ | ---------------- | ----------------- | -------------------------------- |
| `id`          | SERIAL       | PRIMARY KEY      | Auto              | Khóa chính tự tăng               |
| `name`        | VARCHAR(50)  | NOT NULL, UNIQUE | -                 | Tên vai trò: Owner, Staff, Admin |
| `permissions` | JSONB        | NOT NULL         | `'{}'`            | JSON quyền hạn chi tiết          |
| `created_at`  | TIMESTAMP    | NOT NULL         | CURRENT_TIMESTAMP | Thời điểm tạo                    |

#### JSON Structure: `permissions`

```json
{
  "can_view_dashboard": true,
  "can_manage_staff": true,
  "can_approve": true,
  "can_configure_alerts": true,
  "can_view_finance": true,
  "can_manage_products": true,
  "can_manage_inventory": true,
  "can_manage_orders": true,
  "can_use_ai": true
}
```

#### Indexes

- Implicit UNIQUE index trên `name` (từ UNIQUE constraint)

#### Relationships

| Quan hệ | Bảng  | Loại   | ON DELETE                              |
| ------- | ----- | ------ | -------------------------------------- |
| 1 → N   | Users | Parent | RESTRICT (không xóa được khi còn user) |

#### Business Rules

1. Phải có ít nhất 1 role là "Owner"
2. `permissions` JSON phải valid
3. Không xóa role khi còn user sử dụng

#### Example Data

```sql
INSERT INTO Roles (name, permissions) VALUES
('Owner', '{"can_approve": true, "can_manage_staff": true}'),
('Staff', '{"can_manage_products": true, "can_manage_inventory": true}');
```

---

### 2. Categories (Danh mục sản phẩm)

**Mục đích**: Phân loại sản phẩm theo cấu trúc cây phân cấp  
**Use Cases**: UC6, UC8  
**Nhóm**: Danh mục & Sản phẩm

#### Columns

| Cột             | Kiểu dữ liệu | Ràng buộc               | Mặc định          | Mô tả                             |
| --------------- | ------------ | ----------------------- | ----------------- | --------------------------------- |
| `id`            | SERIAL       | PRIMARY KEY             | Auto              | Khóa chính                        |
| `category_code` | VARCHAR(50)  | NOT NULL, UNIQUE        | -                 | Mã danh mục duy nhất (VD: CAT001) |
| `name`          | VARCHAR(255) | NOT NULL                | -                 | Tên danh mục                      |
| `description`   | TEXT         | NULL                    | -                 | Mô tả chi tiết                    |
| `parent_id`     | INT          | FK → Categories(id)     | NULL              | ID danh mục cha (hierarchical)    |
| `sort_order`    | INT          | NOT NULL                | 0                 | Thứ tự hiển thị                   |
| `status`        | VARCHAR(20)  | CHECK (Active/Inactive) | 'Active'          | Trạng thái                        |
| `created_at`    | TIMESTAMP    | NOT NULL                | CURRENT_TIMESTAMP | Thời điểm tạo                     |
| `updated_at`    | TIMESTAMP    | NOT NULL                | CURRENT_TIMESTAMP | Thời điểm cập nhật                |

#### Indexes

- Implicit UNIQUE trên `category_code`

#### Relationships

| Quan hệ  | Bảng       | Loại   | ON DELETE                                     |
| -------- | ---------- | ------ | --------------------------------------------- |
| Self-ref | Categories | Parent | SET NULL (xóa cha → con thành root)           |
| 1 → N    | Products   | Parent | SET NULL (xóa category → products unassigned) |

#### Business Rules

1. `parent_id = NULL` → danh mục gốc
2. Không cho phép circular reference (A → B → A)
3. `sort_order` dùng để sắp xếp khi hiển thị

#### Example Data

```sql
INSERT INTO Categories (category_code, name, parent_id, sort_order) VALUES
('CAT001', 'Thực phẩm', NULL, 1),
('CAT001-01', 'Thực phẩm khô', 1, 1),
('CAT001-02', 'Đồ uống', 1, 2);
```

---

### 3. Suppliers (Nhà cung cấp)

**Mục đích**: Quản lý thông tin nhà cung cấp hàng hóa  
**Use Cases**: UC7, UC8, UC12  
**Nhóm**: Đối tác & Tài chính

#### Columns

| Cột              | Kiểu dữ liệu | Ràng buộc               | Mặc định          | Mô tả                         |
| ---------------- | ------------ | ----------------------- | ----------------- | ----------------------------- |
| `id`             | SERIAL       | PRIMARY KEY             | Auto              | Khóa chính                    |
| `supplier_code`  | VARCHAR(50)  | NOT NULL, UNIQUE        | -                 | Mã NCC duy nhất (VD: NCC0001) |
| `name`           | VARCHAR(255) | NOT NULL                | -                 | Tên nhà cung cấp              |
| `contact_person` | VARCHAR(255) | NULL                    | -                 | Người liên hệ                 |
| `phone`          | VARCHAR(20)  | NULL                    | -                 | Số điện thoại                 |
| `email`          | VARCHAR(255) | NULL                    | -                 | Email liên hệ                 |
| `address`        | TEXT         | NULL                    | -                 | Địa chỉ                       |
| `tax_code`       | VARCHAR(50)  | NULL                    | -                 | Mã số thuế                    |
| `status`         | VARCHAR(20)  | CHECK (Active/Inactive) | 'Active'          | Trạng thái                    |
| `created_at`     | TIMESTAMP    | NOT NULL                | CURRENT_TIMESTAMP | Thời điểm tạo                 |
| `updated_at`     | TIMESTAMP    | NOT NULL                | CURRENT_TIMESTAMP | Thời điểm cập nhật            |

#### Indexes

- `idx_suppliers_name` ON `name`
- `idx_suppliers_phone` ON `phone`
- Implicit UNIQUE trên `supplier_code`

#### Relationships

| Quan hệ | Bảng          | Loại   | ON DELETE                              |
| ------- | ------------- | ------ | -------------------------------------- |
| 1 → N   | StockReceipts | Parent | RESTRICT (không xóa khi có phiếu nhập) |

#### Business Rules

1. `supplier_code` phải duy nhất, format: NCC + 4 digits
2. Không xóa NCC khi còn phiếu nhập liên quan
3. `tax_code` dùng cho báo cáo thuế

---

### 4. Customers (Khách hàng)

**Mục đích**: Quản lý thông tin khách hàng  
**Use Cases**: UC9  
**Nhóm**: Đối tác & Tài chính

#### Columns

| Cột              | Kiểu dữ liệu | Ràng buộc               | Mặc định          | Mô tả                        |
| ---------------- | ------------ | ----------------------- | ----------------- | ---------------------------- |
| `id`             | SERIAL       | PRIMARY KEY             | Auto              | Khóa chính                   |
| `customer_code`  | VARCHAR(50)  | NOT NULL, UNIQUE        | -                 | Mã KH duy nhất (VD: KH00001) |
| `name`           | VARCHAR(255) | NOT NULL                | -                 | Tên khách hàng               |
| `phone`          | VARCHAR(20)  | NOT NULL                | -                 | Số điện thoại                |
| `email`          | VARCHAR(255) | NULL                    | -                 | Email                        |
| `address`        | TEXT         | NULL                    | -                 | Địa chỉ giao hàng            |
| `loyalty_points` | INT          | NOT NULL                | 0                 | Điểm tích lũy                |
| `status`         | VARCHAR(20)  | CHECK (Active/Inactive) | 'Active'          | Trạng thái                   |
| `created_at`     | TIMESTAMP    | NOT NULL                | CURRENT_TIMESTAMP | Thời điểm tạo                |
| `updated_at`     | TIMESTAMP    | NOT NULL                | CURRENT_TIMESTAMP | Thời điểm cập nhật           |

#### Indexes

- `idx_customers_phone` ON `phone`
- Implicit UNIQUE trên `customer_code`

#### Relationships

| Quan hệ | Bảng        | Loại   | ON DELETE                            |
| ------- | ----------- | ------ | ------------------------------------ |
| 1 → N   | SalesOrders | Parent | RESTRICT (không xóa khi có đơn hàng) |

#### Business Rules

1. `phone` là NOT NULL - dùng để tra cứu nhanh
2. `loyalty_points` tính tự động từ lịch sử đơn hàng
3. **Không lưu `total_spent`** → tính qua `SUM(SalesOrders.total_amount)` để đảm bảo consistency

#### Query tính tổng chi tiêu

```sql
SELECT c.id, c.name,
       COALESCE(SUM(so.total_amount), 0) as total_spent
FROM Customers c
LEFT JOIN SalesOrders so ON c.id = so.customer_id
  AND so.status != 'Cancelled'
WHERE c.id = ?
GROUP BY c.id, c.name;
```

---

### 5. WarehouseLocations (Vị trí kho)

**Mục đích**: Định nghĩa vị trí lưu trữ trong kho  
**Use Cases**: UC6, UC10, UC13  
**Nhóm**: Kho hàng & Giao dịch

#### Columns

| Cột              | Kiểu dữ liệu | Ràng buộc                           | Mặc định          | Mô tả              |
| ---------------- | ------------ | ----------------------------------- | ----------------- | ------------------ |
| `id`             | SERIAL       | PRIMARY KEY                         | Auto              | Khóa chính         |
| `warehouse_code` | VARCHAR(20)  | NOT NULL                            | -                 | Mã kho (VD: WH01)  |
| `shelf_code`     | VARCHAR(20)  | NOT NULL                            | -                 | Mã kệ (VD: A1, B2) |
| `description`    | VARCHAR(255) | NULL                                | -                 | Mô tả vị trí       |
| `capacity`       | DECIMAL(8,2) | NULL                                | -                 | Sức chứa (m³)      |
| `status`         | VARCHAR(20)  | CHECK (Active/Maintenance/Inactive) | 'Active'          | Trạng thái         |
| `created_at`     | TIMESTAMP    | NOT NULL                            | CURRENT_TIMESTAMP | Thời điểm tạo      |

#### Constraints

- `uq_warehouse_shelf`: UNIQUE (warehouse_code, shelf_code)

#### Indexes

- Implicit UNIQUE trên composite (warehouse_code, shelf_code)

#### Relationships

| Quan hệ | Bảng                 | Loại   | ON DELETE |
| ------- | -------------------- | ------ | --------- |
| 1 → N   | Inventory            | Parent | RESTRICT  |
| 1 → N   | InventoryLogs (from) | Parent | SET NULL  |
| 1 → N   | InventoryLogs (to)   | Parent | SET NULL  |

#### Business Rules

1. Không trùng (warehouse_code, shelf_code)
2. `status = 'Maintenance'` → không cho xuất/nhập vào vị trí này
3. Format: WH + 2 digits cho kho, alphanumeric cho kệ

#### Example Data

```sql
INSERT INTO WarehouseLocations (warehouse_code, shelf_code, description) VALUES
('WH01', 'A1', 'Kệ A1 - Kho chính - Hàng khô'),
('WH01', 'B1', 'Kệ B1 - Kho chính - Hàng lạnh');
```

---

### 6. Users (Người dùng)

**Mục đích**: Tài khoản đăng nhập và phân quyền  
**Use Cases**: UC1-UC13 (tất cả)  
**Nhóm**: Quản trị & Người dùng

#### Columns

| Cột             | Kiểu dữ liệu | Ràng buộc                | Mặc định          | Mô tả                  |
| --------------- | ------------ | ------------------------ | ----------------- | ---------------------- |
| `id`            | SERIAL       | PRIMARY KEY              | Auto              | Khóa chính             |
| `staff_code`    | VARCHAR(50)  | NULL, UNIQUE             | NULL              | Mã nhân viên hiển thị (NV001) — map FE `employeeCode` |
| `username`      | VARCHAR(100) | NOT NULL, UNIQUE         | -                 | Tên đăng nhập          |
| `password_hash` | VARCHAR(255) | NOT NULL                 | -                 | Mật khẩu bcrypt/argon2 |
| `full_name`     | VARCHAR(255) | NOT NULL                 | -                 | Họ và tên              |
| `email`         | VARCHAR(255) | NOT NULL, UNIQUE         | -                 | Email                  |
| `phone`         | VARCHAR(20)  | NULL                     | -                 | Số điện thoại          |
| `role_id`       | INT          | NOT NULL, FK → Roles(id) | -                 | Vai trò                |
| `status`        | VARCHAR(20)  | CHECK (Active/Locked)    | 'Active'          | Trạng thái             |
| `last_login`    | TIMESTAMP    | NULL                     | -                 | Lần đăng nhập cuối     |
| `created_at`    | TIMESTAMP    | NOT NULL                 | CURRENT_TIMESTAMP | Thời điểm tạo          |
| `updated_at`    | TIMESTAMP    | NOT NULL                 | CURRENT_TIMESTAMP | Thời điểm cập nhật     |

#### Indexes

- Implicit UNIQUE trên `username`, `email`
- `idx_users_phone` ON `phone`

#### Relationships

| Quan hệ | Bảng                        | Loại   | ON DELETE |
| ------- | --------------------------- | ------ | --------- |
| N → 1   | Roles                       | Child  | RESTRICT  |
| 1 → 1   | StoreProfiles               | Parent | CASCADE   |
| 1 → N   | AlertSettings               | Parent | CASCADE   |
| 1 → N   | SystemLogs                  | Parent | SET NULL  |
| 1 → N   | FinanceLedger (created_by)  | Parent | RESTRICT  |
| 1 → N   | AIInsights                  | Parent | CASCADE   |
| 1 → N   | AIChatHistory               | Parent | CASCADE   |
| 1 → N   | MediaAudits (uploaded_by)   | Parent | SET NULL  |
| 1 → N   | StockReceipts (staff_id)    | Parent | RESTRICT  |
| 1 → N   | StockReceipts (approved_by) | Parent | SET NULL  |
| 1 → N   | SalesOrders (user_id)       | Parent | RESTRICT  |
| 1 → N   | SalesOrders (cancelled_by)  | Parent | SET NULL  |
| 1 → N   | StockDispatches             | Parent | RESTRICT  |
| 1 → N   | InventoryLogs               | Parent | SET NULL  |
| 1 → N   | Notifications               | Parent | CASCADE   |

#### Business Rules

1. `username` và `email` phải duy nhất
2. `password_hash` dùng bcrypt hoặc argon2 (KHÔNG lưu plaintext)
3. `status = 'Locked'` → không cho đăng nhập
4. `last_login` cập nhật mỗi lần đăng nhập thành công

#### Security Notes

- Password phải hash trước khi lưu
- Dùng bcrypt với cost >= 10 hoặc argon2id
- KHÔNG dùng MD5 hoặc SHA1

---

### 6.1 StoreProfiles (Thông tin cửa hàng / thương hiệu)

**Mục đích**: Một bản ghi **hồ sơ cửa hàng** trên mỗi tài khoản Owner (logo, MST, địa chỉ, mạng xã hội — hiển thị hóa đơn / POS).  
**Use Cases**: UC1 (nhận diện), UC3 (cài đặt)  
**Nhóm**: Quản trị & Người dùng

#### Columns

| Cột | Kiểu | Ràng buộc | Mặc định | Mô tả |
| --- | --- | --- | --- | --- |
| `id` | SERIAL | PRIMARY KEY | Auto | |
| `owner_id` | INT | NOT NULL, UNIQUE, FK → Users(id) | - | Owner sở hữu cửa hàng |
| `name` | VARCHAR(255) | NOT NULL | - | Tên hiển thị |
| `business_category` | VARCHAR(255) | NULL | - | Lĩnh vực / ngành |
| `address` | TEXT | NULL | - | Địa chỉ |
| `phone` | VARCHAR(30) | NULL | - | |
| `email` | VARCHAR(255) | NULL | - | |
| `website` | VARCHAR(500) | NULL | - | |
| `tax_code` | VARCHAR(50) | NULL | - | MST |
| `footer_note` | TEXT | NULL | - | Ghi chú cuối hóa đơn |
| `logo_url` | VARCHAR(500) | NULL | - | URL logo (CDN / object storage) |
| `facebook_url` | VARCHAR(500) | NULL | - | |
| `instagram_handle` | VARCHAR(255) | NULL | - | |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | |
| `updated_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | |

#### Migration (PostgreSQL)

```sql
CREATE TABLE store_profiles (
  id SERIAL PRIMARY KEY,
  owner_id INT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  business_category VARCHAR(255),
  address TEXT,
  phone VARCHAR(30),
  email VARCHAR(255),
  website VARCHAR(500),
  tax_code VARCHAR(50),
  footer_note TEXT,
  logo_url VARCHAR(500),
  facebook_url VARCHAR(500),
  instagram_handle VARCHAR(255),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

### 7. Products (Sản phẩm)

**Mục đích**: Quản lý danh sách sản phẩm hàng hóa  
**Use Cases**: UC1, UC6, UC7, UC8, UC9, UC10, UC11, UC12, UC13  
**Nhóm**: Danh mục & Sản phẩm

#### Columns

| Cột           | Kiểu dữ liệu | Ràng buộc               | Mặc định          | Mô tả                 |
| ------------- | ------------ | ----------------------- | ----------------- | --------------------- |
| `id`          | SERIAL       | PRIMARY KEY             | Auto              | Khóa chính            |
| `category_id` | INT          | FK → Categories(id)     | NULL              | Danh mục              |
| `sku_code`    | VARCHAR(50)  | NOT NULL, UNIQUE        | -                 | Mã SKU nội bộ         |
| `barcode`     | VARCHAR(100) | NULL                    | -                 | Mã vạch               |
| `name`        | VARCHAR(255) | NOT NULL                | -                 | Tên sản phẩm          |
| `image_url`   | VARCHAR(500) | NULL                    | -                 | URL hình ảnh          |
| `description` | TEXT         | NULL                    | -                 | Mô tả chi tiết        |
| `weight`      | DECIMAL(8,2) | NULL                    | -                 | Trọng lượng (gram)    |
| `status`      | VARCHAR(20)  | CHECK (Active/Inactive) | 'Active'          | Trạng thái kinh doanh |
| `created_at`  | TIMESTAMP    | NOT NULL                | CURRENT_TIMESTAMP | Thời điểm tạo         |
| `updated_at`  | TIMESTAMP    | NOT NULL                | CURRENT_TIMESTAMP | Thời điểm cập nhật    |

#### Indexes

- `idx_products_sku` ON `sku_code`
- `idx_products_barcode` ON `barcode`
- `idx_products_name` ON `name`
- `idx_products_status` ON `status`
- `idx_products_category` ON `category_id` (recommended)
- Implicit UNIQUE trên `sku_code`

#### Relationships

| Quan hệ | Bảng                | Loại   | ON DELETE |
| ------- | ------------------- | ------ | --------- |
| N → 1   | Categories          | Child  | SET NULL  |
| 1 → N   | ProductUnits        | Parent | CASCADE   |
| 1 → N   | ProductPriceHistory | Parent | CASCADE   |
| 1 → N   | Inventory           | Parent | CASCADE   |
| 1 → N   | StockReceiptDetails | Parent | RESTRICT  |
| 1 → N   | OrderDetails        | Parent | RESTRICT  |
| 1 → N   | InventoryLogs       | Parent | RESTRICT  |

#### Business Rules

1. `sku_code` phải duy nhất trong toàn hệ thống
2. `barcode` có thể trùng (nhiều SP có cùng barcode nhà sản xuất)
3. `status = 'Inactive'` → không cho bán/nhập mới
4. `weight` dùng cho tính phí vận chuyển

---

### 8. ProductUnits (Đơn vị tính quy đổi)

**Mục đích**: Định nghĩa các đơn vị tính khác nhau của cùng 1 sản phẩm  
**Use Cases**: UC6, UC7, UC8, UC9, UC10, UC13  
**Nhóm**: Danh mục & Sản phẩm

#### Columns

| Cột               | Kiểu dữ liệu  | Ràng buộc                   | Mặc định          | Mô tả                        |
| ----------------- | ------------- | --------------------------- | ----------------- | ---------------------------- |
| `id`              | SERIAL        | PRIMARY KEY                 | Auto              | Khóa chính                   |
| `product_id`      | INT           | NOT NULL, FK → Products(id) | -                 | Sản phẩm                     |
| `unit_name`       | VARCHAR(50)   | NOT NULL                    | -                 | Tên đơn vị (Thùng, Hộp, Cái) |
| `conversion_rate` | DECIMAL(10,4) | NOT NULL, CHECK (> 0)       | -                 | Tỷ lệ quy đổi                |
| `is_base_unit`    | BOOLEAN       | NOT NULL                    | FALSE             | Là đơn vị cơ sở              |
| `created_at`      | TIMESTAMP     | NOT NULL                    | CURRENT_TIMESTAMP | Thời điểm tạo                |
| `updated_at`      | TIMESTAMP     | NOT NULL                    | CURRENT_TIMESTAMP | Thời điểm cập nhật           |

#### Constraints

- `uq_product_unit_name`: UNIQUE (product_id, unit_name)
- `chk_conversion_rate`: CHECK (conversion_rate > 0)

#### Indexes

- `idx_pu_product` ON `product_id`
- Implicit UNIQUE trên (product_id, unit_name)

#### Relationships

| Quan hệ | Bảng                | Loại   | ON DELETE |
| ------- | ------------------- | ------ | --------- |
| N → 1   | Products            | Child  | CASCADE   |
| 1 → N   | ProductPriceHistory | Parent | CASCADE   |
| 1 → N   | StockReceiptDetails | Parent | RESTRICT  |
| 1 → N   | OrderDetails        | Parent | RESTRICT  |
| 1 → N   | InventoryLogs       | Parent | RESTRICT  |

#### Business Rules

1. **Mỗi product có ĐÚNG 1 row với `is_base_unit = TRUE`**
2. `conversion_rate` = số đơn vị cơ sở trong 1 đơn vị này
3. VD: 1 Thùng = 24 Cái → conversion_rate = 24
4. `Inventory.quantity` LUÔN lưu theo đơn vị cơ sở

#### Unit Conversion Logic

```
Nhập 1 Thùng (conversion_rate = 24):
→ Inventory.quantity += 1 * 24 = 24 (đơn vị cơ sở)

Bán 1 Hộp (conversion_rate = 6):
→ Inventory.quantity -= 1 * 6 = 6 (đơn vị cơ sở)
```

#### Example Data

```sql
INSERT INTO ProductUnits (product_id, unit_name, conversion_rate, is_base_unit) VALUES
(1, 'Cái', 1, TRUE),       -- Đơn vị cơ sở
(1, 'Hộp', 12, FALSE),     -- 1 Hộp = 12 Cái
(1, 'Thùng', 120, FALSE);  -- 1 Thùng = 120 Cái
```

---

### 9. ProductPriceHistory (Lịch sử giá)

**Mục đích**: Lưu vết thay đổi giá vốn và giá bán theo thời gian  
**Use Cases**: UC1, UC8  
**Nhóm**: Danh mục & Sản phẩm

#### Columns

| Cột              | Kiểu dữ liệu  | Ràng buộc                       | Mặc định          | Mô tả              |
| ---------------- | ------------- | ------------------------------- | ----------------- | ------------------ |
| `id`             | BIGSERIAL     | PRIMARY KEY                     | Auto              | Khóa chính         |
| `product_id`     | INT           | NOT NULL, FK → Products(id)     | -                 | Sản phẩm           |
| `unit_id`        | INT           | NOT NULL, FK → ProductUnits(id) | -                 | Đơn vị tính        |
| `cost_price`     | DECIMAL(15,2) | NOT NULL, CHECK (>= 0)          | -                 | Giá vốn            |
| `sale_price`     | DECIMAL(15,2) | NOT NULL, CHECK (>= 0)          | -                 | Giá bán đề nghị    |
| `effective_date` | DATE          | NOT NULL                        | -                 | Ngày áp dụng       |
| `created_at`     | TIMESTAMP     | NOT NULL                        | CURRENT_TIMESTAMP | Thời điểm ghi nhận |

#### Indexes

- `idx_price_lookup` ON (product_id, unit_id, effective_date DESC)

#### Relationships

| Quan hệ | Bảng         | Loại  | ON DELETE |
| ------- | ------------ | ----- | --------- |
| N → 1   | Products     | Child | CASCADE   |
| N → 1   | ProductUnits | Child | CASCADE   |

#### Business Rules

1. `cost_price` dùng để tính lãi lỗ chính xác
2. `sale_price` là giá niêm yết, có thể thay đổi
3. Khi query giá tại thời điểm X, lấy row có `effective_date` gần nhất <= X

#### Query giá hiện tại

```sql
SELECT cost_price, sale_price
FROM ProductPriceHistory
WHERE product_id = ? AND unit_id = ?
  AND effective_date <= CURRENT_DATE
ORDER BY effective_date DESC
LIMIT 1;
```

#### Query giá lịch sử cho báo cáo

```sql
-- Tính lãi lỗ cho đơn hàng cũ
SELECT
  od.quantity,
  pph.cost_price,
  od.price_at_time as sale_price,
  (od.price_at_time - pph.cost_price) * od.quantity as profit
FROM OrderDetails od
JOIN ProductPriceHistory pph ON od.product_id = pph.product_id
  AND od.unit_id = pph.unit_id
WHERE pph.effective_date = (
  SELECT MAX(effective_date)
  FROM ProductPriceHistory
  WHERE product_id = od.product_id
    AND unit_id = od.unit_id
    AND effective_date <= so.created_at
)
AND od.order_id = ?;
```

---

### 10. AlertSettings (Cấu hình cảnh báo)

**Mục đích**: Lưu ngưỡng cảnh báo do Owner cấu hình  
**Use Cases**: UC5  
**Nhóm**: Quản trị & Người dùng

#### Columns

| Cột               | Kiểu dữ liệu  | Ràng buộc                    | Mặc định          | Mô tả              |
| ----------------- | ------------- | ---------------------------- | ----------------- | ------------------ |
| `id`              | SERIAL        | PRIMARY KEY                  | Auto              | Khóa chính         |
| `owner_id`        | INT           | NOT NULL, FK → Users(id)     | -                 | Owner cấu hình     |
| `alert_type`      | VARCHAR(30)   | NOT NULL, CHECK (4 types)    | -                 | Loại cảnh báo      |
| `threshold_value` | DECIMAL(10,2) | NULL                         | -                 | Ngưỡng kích hoạt   |
| `channel`         | VARCHAR(20)   | NOT NULL, CHECK (4 channels) | -                 | Kênh thông báo     |
| `frequency`       | VARCHAR(20)   | NOT NULL, CHECK (3 types)    | 'Realtime'        | Tần suất           |
| `is_enabled`      | BOOLEAN       | NOT NULL                     | TRUE              | Kích hoạt          |
| `recipients`      | JSONB         | NULL                         | -                 | Người nhận bổ sung |
| `created_at`      | TIMESTAMP     | NOT NULL                     | CURRENT_TIMESTAMP | Thời điểm tạo      |
| `updated_at`      | TIMESTAMP     | NOT NULL                     | CURRENT_TIMESTAMP | Thời điểm cập nhật |

#### CHECK Values

- `alert_type`: 'LowStock', 'ExpiryDate', 'HighValueTransaction', 'PendingApproval', 'OverStock', 'SalesOrderCreated', 'PartnerDebtDueSoon', 'SystemHealth' _(mở rộng cho màn **Cấu hình cảnh báo** — migration trước khi ghi các loại mới)_
- `channel`: 'App', 'Email', 'SMS', 'Zalo'
- `frequency`: 'Realtime', 'Daily', 'Weekly'

#### Indexes

- `idx_alert_owner` ON `owner_id`

#### Relationships

| Quan hệ | Bảng  | Loại  | ON DELETE |
| ------- | ----- | ----- | --------- |
| N → 1   | Users | Child | CASCADE   |

#### JSON Structure: `recipients`

```json
["user_2", "user_5", "user_8"]
```

#### Business Rules

1. Mỗi Owner có thể có nhiều alert settings (cho mỗi loại)
2. `threshold_value` tùy theo alert_type:
   - LowStock: số lượng (VD: 10)
   - ExpiryDate: số ngày (VD: 15)
   - HighValueTransaction: số tiền (VD: 50000000)
3. `is_enabled = FALSE` → không gửi cảnh báo này

---

### 11. SystemLogs (Nhật ký hệ thống)

**Mục đích**: Ghi nhận lỗi và sự kiện hệ thống  
**Use Cases**: UC4, UC6  
**Nhóm**: Quản trị & Người dùng

#### Columns

| Cột            | Kiểu dữ liệu | Ràng buộc                  | Mặc định          | Mô tả                 |
| -------------- | ------------ | -------------------------- | ----------------- | --------------------- |
| `id`           | SERIAL       | PRIMARY KEY                | Auto              | Khóa chính            |
| `log_level`    | VARCHAR(20)  | NOT NULL, CHECK (4 levels) | -                 | Mức độ                |
| `module`       | VARCHAR(100) | NOT NULL                   | -                 | Mô đun phát sinh      |
| `action`       | VARCHAR(255) | NOT NULL                   | -                 | Hành động gây log     |
| `user_id`      | INT          | FK → Users(id)             | NULL              | Người dùng            |
| `message`      | TEXT         | NOT NULL                   | -                 | Thông báo chi tiết    |
| `stack_trace`  | TEXT         | NULL                       | -                 | Lỗi chi tiết (nếu có) |
| `context_data` | JSONB        | NULL                       | -                 | Dữ liệu ngữ cảnh (có thể chứa `clientIp`) |
| `ip_address`   | VARCHAR(45)  | NULL                       | NULL              | IP client (đề xuất migration — map FE `ipAddress`) |
| `created_at`   | TIMESTAMP    | NOT NULL                   | CURRENT_TIMESTAMP | Thời điểm ghi log     |

#### CHECK Values

- `log_level`: 'INFO', 'WARNING', 'ERROR', 'CRITICAL'

#### Indexes

- `idx_syslog_level` ON `log_level`
- `idx_syslog_created_at` ON `created_at`

#### Relationships

| Quan hệ | Bảng  | Loại  | ON DELETE |
| ------- | ----- | ----- | --------- |
| N → 1   | Users | Child | SET NULL  |

#### Business Rules

1. Bảng này tăng nhanh → cân nhắc archiving sau 90 ngày
2. `log_level = 'CRITICAL'` → nên gửi alert ngay lập tức
3. `context_data` JSON lưu payload tại thời điểm log

#### Example context_data

```json
{
  "receipt_id": 123,
  "action": "approve",
  "before_status": "Pending",
  "after_status": "Approved"
}
```

---

### 12. FinanceLedger (Sổ cái tài chính)

**Mục đích**: Ghi nhận mọi giao dịch thu/chi  
**Use Cases**: UC1, UC4  
**Nhóm**: Đối tác & Tài chính

#### Columns

| Cột                | Kiểu dữ liệu  | Ràng buộc                 | Mặc định          | Mô tả                  |
| ------------------ | ------------- | ------------------------- | ----------------- | ---------------------- |
| `id`               | BIGSERIAL     | PRIMARY KEY               | Auto              | Khóa chính             |
| `transaction_date` | DATE          | NOT NULL                  | -                 | Ngày giao dịch         |
| `transaction_type` | VARCHAR(30)   | NOT NULL, CHECK (4 types) | -                 | Loại giao dịch         |
| `reference_type`   | VARCHAR(50)   | NULL                      | -                 | Loại chứng từ          |
| `reference_id`     | INT           | NOT NULL                  | -                 | ID chứng từ            |
| `amount`           | DECIMAL(15,2) | NOT NULL                  | -                 | Số tiền (+ thu, - chi) |
| `description`      | TEXT          | NULL                      | -                 | Mô tả                  |
| `created_by`       | INT           | NOT NULL, FK → Users(id)  | -                 | Người thực hiện        |
| `created_at`       | TIMESTAMP     | NOT NULL                  | CURRENT_TIMESTAMP | Thời điểm tạo          |
| `updated_at`       | TIMESTAMP     | NOT NULL                  | CURRENT_TIMESTAMP | Thời điểm cập nhật     |

#### CHECK Values

- `transaction_type`: 'SalesRevenue', 'PurchaseCost', 'OperatingExpense', 'Refund'

#### Indexes

- `idx_finance_date` ON `transaction_date`
- `idx_finance_type` ON `transaction_type`

#### Relationships

| Quan hệ     | Bảng                             | Loại    | ON DELETE |
| ----------- | -------------------------------- | ------- | --------- |
| N → 1       | Users                            | Child   | RESTRICT  |
| Polymorphic | StockReceipts, SalesOrders, etc. | Soft FK | N/A       |

#### Polymorphic FK Note

⚠️ **`reference_type` + `reference_id` là Polymorphic Association**:

- KHÔNG có database FK constraint
- Validation thực hiện ở **application layer**
- Khi query, luôn kiểm tra `reference_type` trước khi JOIN

#### Example Values

| reference_type   | reference_id | Ý nghĩa                        |
| ---------------- | ------------ | ------------------------------ |
| 'StockReceipt'   | 45           | Phiếu nhập kho ID 45           |
| 'SalesOrder'     | 123          | Đơn hàng ID 123                |
| 'CashTransaction'| 7            | Giao dịch thu chi thủ công §12.1 |

#### Business Rules

1. `amount > 0` → thu tiền (doanh thu)
2. `amount < 0` → chi tiền (chi phí nhập hàng, chi phí vận hành)
3. Chỉ ghi nhận khi giao dịch đã được phê duyệt
4. KHÔNG được xóa/sửa sau khi đã ghi nhận (immutable)

---

### 12.1 CashTransactions (Giao dịch thu chi thủ công)

**Mục đích**: Ghi nhận các khoản **thu / chi** nhập tay trên màn **Giao dịch thu chi** (bổ sung cho các bút toán tự động từ `FinanceLedger` do phiếu nhập, đơn hàng, …).  
**Use Cases**: UC1, UC4 (tài chính)  
**Nhóm**: Đối tác & Tài chính

#### Columns

| Cột | Kiểu dữ liệu | Ràng buộc | Mặc định | Mô tả |
| --- | --- | --- | --- | --- |
| `id` | SERIAL | PRIMARY KEY | Auto | Khóa chính (INT — tương thích `FinanceLedger.reference_id`) |
| `transaction_code` | VARCHAR(50) | NOT NULL, UNIQUE | - | Mã giao dịch (VD: PT-2026-0001, PC-2026-0001) |
| `direction` | VARCHAR(10) | NOT NULL, CHECK | - | `Income` (thu) \| `Expense` (chi) |
| `amount` | DECIMAL(15,2) | NOT NULL, CHECK (> 0) | - | Số tiền luôn dương; dấu khi ghi `FinanceLedger` do `direction` quyết định |
| `category` | VARCHAR(100) | NOT NULL | - | Nhóm thu/chi (VD: Thu tiền khách hàng) |
| `description` | TEXT | NULL | - | Diễn giải |
| `payment_method` | VARCHAR(30) | NOT NULL | `'Cash'` | `Cash`, `BankTransfer`, … |
| `status` | VARCHAR(20) | NOT NULL, CHECK | `'Pending'` | `Pending`, `Completed`, `Cancelled` |
| `transaction_date` | DATE | NOT NULL | - | Ngày giao dịch nghiệp vụ |
| `finance_ledger_id` | INT | NULL, FK → FinanceLedger(id) | NULL | Liên kết bút toán sổ cái sau khi **hoàn tất** (khớp Flyway V1: `FinanceLedger.id` SERIAL) |
| `created_by` | INT | NOT NULL, FK → Users(id) | - | Người tạo phiếu; **chỉ** user này được PATCH/DELETE (SRS Task064–068 Approved) |
| `performed_by` | INT | NOT NULL, FK → Users(id) | = `created_by` lúc tạo | Người thực hiện thao tác gần nhất (PATCH cập nhật); Flyway **V25** |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | |
| `updated_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | |

#### Business Rules

1. Khi `status` chuyển sang **`Completed`**: trong **một transaction** — `INSERT FinanceLedger` (`amount` > 0 nếu `Income`, `amount` < 0 nếu `Expense`), `reference_type = 'CashTransaction'`, `reference_id = cash_transactions.id`, `transaction_type` = `SalesRevenue` (Income) hoặc `OperatingExpense` (Expense) theo policy; ghi `finance_ledger_id`.  
2. `Pending` → cho phép **PATCH** / **DELETE** (bởi **người tạo**); `Completed` → **không** sửa/xóa (chỉ đọc); `Cancelled` → không ghi sổ; cho phép PATCH **mô tả** theo SRS.  
3. `transaction_code` sinh theo tiền tố PT/PC + quy tắc năm + sequence.  
4. **Đọc** danh sách/chi tiết: mọi user có quyền xem tài chính; **ghi** (PATCH/DELETE): chỉ `created_by` = user hiện tại (xem SRS Task064–068).

#### Migration (PostgreSQL)

```sql
CREATE TABLE cash_transactions (
  id SERIAL PRIMARY KEY,
  transaction_code VARCHAR(50) NOT NULL UNIQUE,
  direction VARCHAR(10) NOT NULL CHECK (direction IN ('Income','Expense')),
  amount DECIMAL(15,2) NOT NULL CHECK (amount > 0),
  category VARCHAR(100) NOT NULL,
  description TEXT,
  payment_method VARCHAR(30) NOT NULL DEFAULT 'Cash',
  status VARCHAR(20) NOT NULL DEFAULT 'Pending'
    CHECK (status IN ('Pending','Completed','Cancelled')),
  transaction_date DATE NOT NULL,
  finance_ledger_id INT NULL REFERENCES finance_ledger(id),
  created_by INT NOT NULL REFERENCES users(id),
  performed_by INT NOT NULL REFERENCES users(id),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_cash_tx_date ON cash_transactions (transaction_date DESC);
CREATE INDEX idx_cash_tx_status ON cash_transactions (status);
CREATE INDEX idx_cash_tx_created_at ON cash_transactions (created_at DESC, id DESC);
```

---

### 12.2 PartnerDebts (Sổ nợ đối tác)

**Mục đích**: Theo dõi **công nợ** phải thu / phải trả theo **Khách hàng** hoặc **NCC** (màn **Sổ nợ**).  
**Use Cases**: UC1, UC9  
**Nhóm**: Đối tác & Tài chính

#### Columns

| Cột | Kiểu dữ liệu | Ràng buộc | Mặc định | Mô tả |
| --- | --- | --- | --- | --- |
| `id` | SERIAL | PRIMARY KEY | Auto | |
| `debt_code` | VARCHAR(50) | NOT NULL, UNIQUE | - | Mã khoản nợ (NO-2026-0001) |
| `partner_type` | VARCHAR(20) | NOT NULL, CHECK | - | `Customer` \| `Supplier` |
| `customer_id` | INT | NULL, FK → Customers(id) | NULL | Bắt buộc khi `partner_type = Customer` |
| `supplier_id` | INT | NULL, FK → Suppliers(id) | NULL | Bắt buộc khi `partner_type = Supplier` |
| `total_amount` | DECIMAL(15,2) | NOT NULL, CHECK (>= 0) | - | Tổng phát sinh nợ |
| `paid_amount` | DECIMAL(15,2) | NOT NULL, CHECK (>= 0) | 0 | Đã thanh toán |
| `due_date` | DATE | NULL | - | Hạn thanh toán (UI) |
| `status` | VARCHAR(20) | NOT NULL, CHECK | `'InDebt'` | `InDebt` \| `Cleared` |
| `notes` | TEXT | NULL | - | |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | |
| `updated_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | |

CHK: `(partner_type = 'Customer' AND customer_id IS NOT NULL AND supplier_id IS NULL) OR (partner_type = 'Supplier' AND supplier_id IS NOT NULL AND customer_id IS NULL)`.

#### Business Rules

1. **`remaining_amount`** = `total_amount - paid_amount` (cột generated hoặc tính ở API).  
2. `status = Cleared` khi `paid_amount >= total_amount`.  
3. Ghi nhận thanh toán có thể đồng bộ `INSERT FinanceLedger` (Task backlog) — tùy policy.

#### Migration (PostgreSQL)

```sql
CREATE TABLE partner_debts (
  id SERIAL PRIMARY KEY,
  debt_code VARCHAR(50) NOT NULL UNIQUE,
  partner_type VARCHAR(20) NOT NULL CHECK (partner_type IN ('Customer','Supplier')),
  customer_id INT NULL REFERENCES customers(id),
  supplier_id INT NULL REFERENCES suppliers(id),
  total_amount DECIMAL(15,2) NOT NULL CHECK (total_amount >= 0),
  paid_amount DECIMAL(15,2) NOT NULL DEFAULT 0 CHECK (paid_amount >= 0),
  due_date DATE NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'InDebt' CHECK (status IN ('InDebt','Cleared')),
  notes TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT chk_partner_debts_partner CHECK (
    (partner_type = 'Customer' AND customer_id IS NOT NULL AND supplier_id IS NULL)
    OR (partner_type = 'Supplier' AND supplier_id IS NOT NULL AND customer_id IS NULL)
  ),
  CONSTRAINT chk_paid_le_total CHECK (paid_amount <= total_amount)
);
CREATE INDEX idx_partner_debts_status ON partner_debts (status);
CREATE INDEX idx_partner_debts_customer ON partner_debts (customer_id);
CREATE INDEX idx_partner_debts_supplier ON partner_debts (supplier_id);
```

---

### 13. AIInsights (Lịch sử phân tích AI)

**Mục đích**: Lưu kết quả phân tích kinh doanh từ AI  
**Use Cases**: UC1, UC2  
**Nhóm**: AI & Media

#### Columns

| Cột                  | Kiểu dữ liệu | Ràng buộc                | Mặc định          | Mô tả                      |
| -------------------- | ------------ | ------------------------ | ----------------- | -------------------------- |
| `id`                 | BIGSERIAL    | PRIMARY KEY              | Auto              | Khóa chính                 |
| `owner_id`           | INT          | NOT NULL, FK → Users(id) | -                 | Owner yêu cầu              |
| `dashboard_snapshot` | JSONB        | NOT NULL                 | -                 | Snapshot dữ liệu dashboard |
| `prompt`             | TEXT         | NOT NULL                 | -                 | Câu lệnh gửi AI            |
| `ai_advice`          | TEXT         | NOT NULL                 | -                 | Kết quả trả về (Markdown)  |
| `model_used`         | VARCHAR(100) | NULL                     | -                 | Model AI sử dụng           |
| `tokens_used`        | INT          | NULL                     | -                 | Số token tiêu thụ          |
| `created_at`         | TIMESTAMP    | NOT NULL                 | CURRENT_TIMESTAMP | Thời điểm phân tích        |

#### Indexes

- `idx_ai_insight_owner` ON `owner_id`

#### Relationships

| Quan hệ | Bảng  | Loại  | ON DELETE |
| ------- | ----- | ----- | --------- |
| N → 1   | Users | Child | CASCADE   |

#### JSON Structure: `dashboard_snapshot`

```json
{
  "date_range": "2026-04-01 to 2026-04-30",
  "total_revenue": 150000000,
  "total_expenses": 120000000,
  "inventory_value": 500000000,
  "low_stock_items": 15,
  "expiring_soon": 8,
  "top_products": ["SP001", "SP002", "SP003"]
}
```

#### Business Rules

1. `ai_advice` lưu dưới dạng Markdown
2. `dashboard_snapshot` lưu context tại thời điểm hỏi
3. Dùng để Owner xem lại lịch sử phân tích cũ

---

### 14. AIChatHistory (Lịch sử Chat Bot)

**Mục đích**: Lưu lịch sử hội thoại với AI Chat Bot  
**Use Cases**: UC2, UC11  
**Nhóm**: AI & Media

#### Columns

| Cột                | Kiểu dữ liệu | Ràng buộc                  | Mặc định          | Mô tả                   |
| ------------------ | ------------ | -------------------------- | ----------------- | ----------------------- |
| `id`               | BIGSERIAL    | PRIMARY KEY                | Auto              | Khóa chính              |
| `user_id`          | INT          | NOT NULL, FK → Users(id)   | -                 | Người dùng              |
| `session_id`       | VARCHAR(100) | NULL                       | -                 | Phiên chat              |
| `message`          | TEXT         | NOT NULL                   | -                 | Nội dung tin nhắn       |
| `sender`           | VARCHAR(10)  | NOT NULL, CHECK (User/Bot) | -                 | Người gửi               |
| `intent`           | JSONB        | NULL                       | -                 | Ý định nhận dạng        |
| `response_time_ms` | INT          | NULL                       | -                 | Thời gian phản hồi (ms) |
| `created_at`       | TIMESTAMP    | NOT NULL                   | CURRENT_TIMESTAMP | Thời điểm nhắn          |

#### CHECK Values

- `sender`: 'User', 'Bot'

#### Indexes

- `idx_chat_user` ON `user_id`
- `idx_chat_session` ON `session_id`
- `idx_chat_created_at` ON `created_at`

#### Relationships

| Quan hệ | Bảng  | Loại  | ON DELETE |
| ------- | ----- | ----- | --------- |
| N → 1   | Users | Child | CASCADE   |

#### JSON Structure: `intent`

```json
{
  "action": "check_stock",
  "product": "Sữa ông Thọ",
  "location": "A1",
  "unit": "Thùng"
}
```

#### Business Rules

1. `session_id` gom nhóm các message trong 1 phiên
2. Bảng này tăng rất nhanh → cân nhắc partitioning theo tháng
3. `response_time_ms` dùng để monitor AI performance

---

### 15. MediaAudits (Lưu vết Media Cloud)

**Mục đích**: Lưu URL và metadata của file media (ảnh, audio)  
**Use Cases**: UC12, UC13  
**Nhóm**: AI & Media

#### Columns

| Cột               | Kiểu dữ liệu  | Ràng buộc                 | Mặc định          | Mô tả                   |
| ----------------- | ------------- | ------------------------- | ----------------- | ----------------------- |
| `id`              | BIGSERIAL     | PRIMARY KEY               | Auto              | Khóa chính              |
| `file_type`       | VARCHAR(20)   | NOT NULL, CHECK (2 types) | -                 | Loại file               |
| `cloud_url`       | VARCHAR(1000) | NOT NULL                  | -                 | URL Cloud (S3/Firebase) |
| `entity_type`     | VARCHAR(50)   | NOT NULL                  | -                 | Loại đối tượng          |
| `entity_id`       | INT           | NOT NULL                  | -                 | ID đối tượng            |
| `file_size_bytes` | BIGINT        | NULL                      | -                 | Kích thước file         |
| `mime_type`       | VARCHAR(100)  | NULL                      | -                 | Định dạng file          |
| `uploaded_by`     | INT           | FK → Users(id)            | NULL              | Người tải lên           |
| `created_at`      | TIMESTAMP     | NOT NULL                  | CURRENT_TIMESTAMP | Thời điểm upload        |

#### CHECK Values

- `file_type`: 'OCR_Image', 'Voice_Audio'

#### Relationships

| Quan hệ     | Bảng                                  | Loại    | ON DELETE |
| ----------- | ------------------------------------- | ------- | --------- |
| N → 1       | Users                                 | Child   | SET NULL  |
| Polymorphic | StockReceipts, SalesOrders, Inventory | Soft FK | N/A       |

#### Polymorphic FK Note

⚠️ **`entity_type` + `entity_id` là Soft FK**:

- KHÔNG có database FK constraint
- Validation thực hiện ở **application layer**
- Luôn kiểm tra `entity_type` trước khi JOIN

#### Example Values

| entity_type    | entity_id | Ý nghĩa                      |
| -------------- | --------- | ---------------------------- |
| 'StockReceipt' | 45        | Ảnh hóa đơn phiếu nhập ID 45 |
| 'SalesOrder'   | 123       | Ảnh đơn hàng ID 123          |
| 'Inventory'    | 67        | Audio kiểm kê vị trí ID 67   |

#### Business Rules

1. Chỉ lưu URL, KHÔNG lưu BLOB trong database
2. File thực tế lưu trên Cloud (S3, Firebase Storage, etc.)
3. Dùng cho audit trail - bằng chứng chứng từ

---

### 16. Inventory (Tồn kho vật lý)

**Mục đích**: Lưu số lượng tồn kho thực tế theo vị trí và lô  
**Use Cases**: UC1, UC4, UC6, UC9, UC10  
**Nhóm**: Kho hàng & Giao dịch

#### Columns

| Cột            | Kiểu dữ liệu  | Ràng buộc                             | Mặc định          | Mô tả             |
| -------------- | ------------- | ------------------------------------- | ----------------- | ----------------- |
| `id`           | BIGSERIAL     | PRIMARY KEY                           | Auto              | Khóa chính        |
| `product_id`   | INT           | NOT NULL, FK → Products(id)           | -                 | Sản phẩm          |
| `location_id`  | INT           | NOT NULL, FK → WarehouseLocations(id) | -                 | Vị trí kệ         |
| `batch_number` | VARCHAR(100)  | NULL                                  | -                 | Số lô             |
| `expiry_date`  | DATE          | NULL                                  | -                 | Hạn sử dụng       |
| `quantity`     | DECIMAL(12,4) | NOT NULL, CHECK (>= 0)                | 0                 | Số lượng tồn      |
| `min_quantity` | DECIMAL(12,4) | NOT NULL                              | 0                 | Mức tối thiểu     |
| `updated_at`   | TIMESTAMP     | NOT NULL                              | CURRENT_TIMESTAMP | Lần cập nhật cuối |

#### Constraints

- `uq_inventory_product_location_batch`: UNIQUE (product_id, location_id, batch_number)
- `chk_quantity`: CHECK (quantity >= 0)

#### Indexes

- `idx_inv_product` ON `product_id`
- `idx_inv_expiry_date` ON `expiry_date`

#### Relationships

| Quan hệ | Bảng               | Loại  | ON DELETE |
| ------- | ------------------ | ----- | --------- |
| N → 1   | Products           | Child | CASCADE   |
| N → 1   | WarehouseLocations | Child | RESTRICT  |

#### Business Rules

1. **`quantity` LUÔN theo đơn vị cơ sở** (base unit)
2. Không cho phép `quantity < 0`
3. `min_quantity` dùng cho cảnh báo LowStock
4. UNIQUE (product_id, location_id, batch_number) → tránh trùng tồn kho
5. Cùng 1 sản phẩm có thể ở nhiều vị trí khác nhau

#### Query cảnh báo hết hạn

```sql
SELECT p.name, i.quantity, i.expiry_date
FROM Inventory i
JOIN Products p ON i.product_id = p.id
WHERE i.expiry_date IS NOT NULL
  AND i.expiry_date <= DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY)
  AND i.quantity > 0;
```

---

### 17. StockReceipts (Phiếu Nhập kho)

**Mục đích**: Quản lý phiếu nhập kho từ nhà cung cấp  
**Use Cases**: UC4, UC7, UC12  
**Nhóm**: Kho hàng & Giao dịch

#### Columns

| Cột              | Kiểu dữ liệu  | Ràng buộc                    | Mặc định          | Mô tả                   |
| ---------------- | ------------- | ---------------------------- | ----------------- | ----------------------- |
| `id`             | SERIAL        | PRIMARY KEY                  | Auto              | Khóa chính              |
| `receipt_code`   | VARCHAR(50)   | NOT NULL, UNIQUE             | -                 | Mã phiếu (PN-2026-0001) |
| `supplier_id`    | INT           | NOT NULL, FK → Suppliers(id) | -                 | Nhà cung cấp            |
| `staff_id`       | INT           | NOT NULL, FK → Users(id)     | -                 | Nhân viên nhập          |
| `receipt_date`   | DATE          | NOT NULL                     | -                 | Ngày nhập kho           |
| `status`         | VARCHAR(20)   | NOT NULL, CHECK (4 statuses) | 'Draft'           | Trạng thái              |
| `invoice_number` | VARCHAR(100)  | NULL                         | -                 | Số hóa đơn              |
| `total_amount`   | DECIMAL(15,2) | NOT NULL, CHECK (>= 0)       | 0                 | Tổng giá trị            |
| `notes`          | TEXT          | NULL                         | -                 | Ghi chú nghiệp vụ (không thay thế lý do từ chối có cấu trúc) |
| `approved_by`    | INT           | FK → Users(id)               | NULL              | Người duyệt (phiên bản cũ; giữ để tương thích báo cáo) |
| `approved_at`    | TIMESTAMP     | NULL                         | -                 | Thời điểm duyệt (khi `Approved`) |
| `rejection_reason` | TEXT        | NULL                         | -                 | Lý do từ chối — **bắt buộc có nội dung** khi `status = 'Rejected'` |
| `reviewed_at`    | TIMESTAMP     | NULL                         | -                 | Thời điểm **quyết định** phê duyệt hoặc từ chối (ghi **một lần**, không phụ thuộc chỉnh sửa `notes` sau) |
| `reviewed_by`    | INT           | FK → Users(id)               | NULL              | User thực hiện phê duyệt hoặc từ chối (UC4) |
| `created_at`     | TIMESTAMP     | NOT NULL                     | CURRENT_TIMESTAMP | Thời điểm tạo           |
| `updated_at`     | TIMESTAMP     | NOT NULL                     | CURRENT_TIMESTAMP | Thời điểm cập nhật      |

#### CHECK Values

- `status`: 'Draft', 'Pending', 'Approved', 'Rejected'

#### Indexes

- `idx_sr_supplier` ON `supplier_id`
- `idx_sr_status` ON `status`
- `idx_sr_reviewed_at` ON `reviewed_at` (khuyến nghị — màn lịch sử phê duyệt / báo cáo)
- Implicit UNIQUE trên `receipt_code`

#### Relationships

| Quan hệ | Bảng                | Loại   | ON DELETE |
| ------- | ------------------- | ------ | --------- |
| N → 1   | Suppliers           | Child  | RESTRICT  |
| N → 1   | Users (staff)       | Child  | RESTRICT  |
| N → 1   | Users (approver)    | Child  | SET NULL  |
| N → 1   | Users (reviewer)    | Child  | SET NULL  |
| 1 → N   | StockReceiptDetails | Parent | CASCADE   |

#### Business Rules

1. Chỉ khi `status = 'Approved'` mới:
   - Cộng vào `Inventory`
   - Ghi nhận `FinanceLedger`
2. `status = 'Draft'` hoặc `'Pending'` → được sửa/xóa
3. `status = 'Approved'` → KHÔNG cho sửa (application check)
4. `receipt_code` format: PN-YYYY-NNNN
5. Khi chuyển `Pending` → `Approved`: ghi **`reviewed_at`**, **`reviewed_by`** (trùng logic `approved_at` / `approved_by` nếu giữ cả hai cột).
6. Khi chuyển `Pending` → `Rejected`: ghi **`rejection_reason`** (NOT NULL ở tầng ứng dụng), **`reviewed_at`**, **`reviewed_by`**; `approved_by` / `approved_at` giữ **NULL**.
7. **`reviewed_at`** là nguồn sự thật cho **lịch sử phê duyệt** và lọc ngày trên API `GET /approvals/history` — không dùng `updated_at` thay thế.

#### Migration (PostgreSQL) — bổ sung cột

```sql
ALTER TABLE stock_receipts
  ADD COLUMN IF NOT EXISTS rejection_reason TEXT NULL,
  ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP NULL,
  ADD COLUMN IF NOT EXISTS reviewed_by INT NULL REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_sr_reviewed_at ON stock_receipts (reviewed_at DESC NULLS LAST);

-- Backfill từ dữ liệu cũ (chạy một lần sau deploy)
UPDATE stock_receipts
SET reviewed_at = approved_at, reviewed_by = approved_by
WHERE status = 'Approved' AND reviewed_at IS NULL AND approved_at IS NOT NULL;
```

---

### 18. StockReceiptDetails (Chi tiết Phiếu Nhập)

**Mục đích**: Lưu chi tiết từng dòng hàng trong phiếu nhập  
**Use Cases**: UC7, UC12  
**Nhóm**: Kho hàng & Giao dịch

#### Columns

| Cột            | Kiểu dữ liệu  | Ràng buộc                        | Mặc định          | Mô tả          |
| -------------- | ------------- | -------------------------------- | ----------------- | -------------- |
| `id`           | BIGSERIAL     | PRIMARY KEY                      | Auto              | Khóa chính     |
| `receipt_id`   | INT           | NOT NULL, FK → StockReceipts(id) | -                 | Phiếu nhập cha |
| `product_id`   | INT           | NOT NULL, FK → Products(id)      | -                 | Sản phẩm       |
| `unit_id`      | INT           | NOT NULL, FK → ProductUnits(id)  | -                 | Đơn vị nhập    |
| `quantity`     | DECIMAL(10,2) | NOT NULL, CHECK (> 0)            | -                 | Số lượng       |
| `cost_price`   | DECIMAL(15,2) | NOT NULL, CHECK (>= 0)           | -                 | Giá vốn        |
| `batch_number` | VARCHAR(100)  | NULL                             | -                 | Số lô          |
| `expiry_date`  | DATE          | NULL                             | -                 | Hạn sử dụng    |
| `line_total`   | DECIMAL(15,2) | GENERATED                        | -                 | Thành tiền     |
| `created_at`   | TIMESTAMP     | NOT NULL                         | CURRENT_TIMESTAMP | Thời điểm tạo  |

#### Generated Column

- `line_total` = `quantity * cost_price` (STORED)

#### Constraints

- `uq_srd_receipt_product_batch`: UNIQUE (receipt_id, product_id, batch_number)

#### Indexes

- `idx_srd_receipt` ON `receipt_id`
- `idx_srd_product` ON `product_id` (recommended)
- `idx_srd_unit` ON `unit_id` (recommended)

#### Relationships

| Quan hệ | Bảng          | Loại  | ON DELETE |
| ------- | ------------- | ----- | --------- |
| N → 1   | StockReceipts | Child | CASCADE   |
| N → 1   | Products      | Child | RESTRICT  |
| N → 1   | ProductUnits  | Child | RESTRICT  |

#### Business Rules

1. `line_total` tự động tính, không cần INSERT/UPDATE
2. UNIQUE (receipt_id, product_id, batch_number) → tránh nhập trùng lô
3. `batch_number` và `expiry_date` dùng cho quản lý lô/hạn

---

### 19. SalesOrders (Đơn hàng bán)

**Mục đích**: Quản lý đơn hàng bán cho khách  
**Use Cases**: UC1, UC4, UC9, UC10  
**Nhóm**: Kho hàng & Giao dịch

#### Columns

| Cột                | Kiểu dữ liệu  | Ràng buộc                    | Mặc định          | Mô tả                 |
| ------------------ | ------------- | ---------------------------- | ----------------- | --------------------- |
| `id`               | SERIAL        | PRIMARY KEY                  | Auto              | Khóa chính            |
| `order_code`       | VARCHAR(50)   | NOT NULL, UNIQUE             | -                 | Mã đơn (SO-2026-0001) |
| `customer_id`      | INT           | NOT NULL, FK → Customers(id) | -                 | Khách hàng            |
| `user_id`          | INT           | NOT NULL, FK → Users(id)     | -                 | Nhân viên tạo         |
| `total_amount`     | DECIMAL(15,2) | NOT NULL, CHECK (>= 0)       | 0                 | Tổng tiền             |
| `discount_amount`  | DECIMAL(15,2) | NOT NULL, CHECK (>= 0)       | 0                 | Giảm giá              |
| `final_amount`     | DECIMAL(15,2) | GENERATED                    | -                 | Thực thu              |
| `status`           | VARCHAR(20)   | NOT NULL, CHECK (6 statuses) | 'Pending'         | Trạng thái            |
| `parent_order_id`  | INT           | FK → SalesOrders(id)         | NULL              | Đơn cha (Backorder)   |
| `shipping_address` | TEXT          | NULL                         | -                 | Địa chỉ giao hàng     |
| `notes`            | TEXT          | NULL                         | -                 | Ghi chú               |
| `created_at`       | TIMESTAMP     | NOT NULL                     | CURRENT_TIMESTAMP | Thời điểm tạo         |
| `updated_at`       | TIMESTAMP     | NOT NULL                     | CURRENT_TIMESTAMP | Thời điểm cập nhật    |
| `cancelled_at`     | TIMESTAMP     | NULL                         | -                 | Ngày hủy              |
| `cancelled_by`     | INT           | FK → Users(id)               | NULL              | Người hủy             |

#### Generated Column

- `final_amount` = `total_amount - discount_amount` (STORED)

#### CHECK Values

- `status`: 'Pending', 'Processing', 'Partial', 'Shipped', 'Delivered', 'Cancelled'

#### Constraints

- `chk_discount`: CHECK (discount_amount <= total_amount)

#### Indexes

- `idx_so_customer` ON `customer_id`
- `idx_so_user` ON `user_id`
- `idx_so_status` ON `status`
- `idx_so_parent` ON `parent_order_id`
- `idx_so_created_at` ON `created_at`
- Implicit UNIQUE trên `order_code`

#### Relationships

| Quan hệ  | Bảng                 | Loại   | ON DELETE |
| -------- | -------------------- | ------ | --------- |
| N → 1    | Customers            | Child  | RESTRICT  |
| N → 1    | Users (creator)      | Child  | RESTRICT  |
| N → 1    | Users (canceller)    | Child  | SET NULL  |
| Self-ref | SalesOrders (parent) | Self   | SET NULL  |
| 1 → N    | OrderDetails         | Parent | CASCADE   |
| 1 → N    | StockDispatches      | Parent | RESTRICT  |

#### Business Rules

1. Backorder: `parent_order_id` trỏ về đơn cha
2. `status = 'Cancelled'` → KHÔNG cho sửa, hoàn kho
3. `final_amount` tự động tính
4. `order_code` format: SO-YYYY-NNNN

---

### 20. OrderDetails (Chi tiết Đơn hàng)

**Mục đích**: Lưu chi tiết từng dòng hàng trong đơn hàng  
**Use Cases**: UC9, UC10  
**Nhóm**: Kho hàng & Giao dịch

#### Columns

| Cột              | Kiểu dữ liệu  | Ràng buộc                       | Mặc định          | Mô tả             |
| ---------------- | ------------- | ------------------------------- | ----------------- | ----------------- |
| `id`             | BIGSERIAL     | PRIMARY KEY                     | Auto              | Khóa chính        |
| `order_id`       | INT           | NOT NULL, FK → SalesOrders(id)  | -                 | Đơn hàng cha      |
| `product_id`     | INT           | NOT NULL, FK → Products(id)     | -                 | Sản phẩm          |
| `unit_id`        | INT           | NOT NULL, FK → ProductUnits(id) | -                 | Đơn vị bán        |
| `quantity`       | DECIMAL(10,2) | NOT NULL, CHECK (> 0)           | -                 | Số lượng đặt      |
| `price_at_time`  | DECIMAL(15,2) | NOT NULL, CHECK (>= 0)          | -                 | Giá tại thời điểm |
| `line_total`     | DECIMAL(15,2) | GENERATED                       | -                 | Thành tiền        |
| `dispatched_qty` | DECIMAL(10,2) | NOT NULL, CHECK (>= 0)          | 0                 | Đã xuất kho       |
| `created_at`     | TIMESTAMP     | NOT NULL                        | CURRENT_TIMESTAMP | Thời điểm tạo     |

#### Generated Column

- `line_total` = `quantity * price_at_time` (STORED)

#### Constraints

- `uq_od_order_product_unit`: UNIQUE (order_id, product_id, unit_id)
- `chk_dispatched_qty`: CHECK (dispatched_qty <= quantity)

#### Indexes

- `idx_od_order` ON `order_id`
- `idx_od_product` ON `product_id` (recommended)
- `idx_od_unit` ON `unit_id` (recommended)

#### Relationships

| Quan hệ | Bảng         | Loại  | ON DELETE |
| ------- | ------------ | ----- | --------- |
| N → 1   | SalesOrders  | Child | CASCADE   |
| N → 1   | Products     | Child | RESTRICT  |
| N → 1   | ProductUnits | Child | RESTRICT  |

#### Business Rules

1. `price_at_time` KHÔNG ĐỔI khi giá sản phẩm thay đổi
2. `dispatched_qty` track số lượng đã xuất kho
3. `dispatched_qty = quantity` → đủ hàng
4. `dispatched_qty < quantity` → cần backorder

---

### 21. StockDispatches (Phiếu Xuất kho)

**Mục đích**: Quản lý phiếu xuất kho  
**Use Cases**: UC4, UC10  
**Nhóm**: Kho hàng & Giao dịch

#### Columns

| Cột             | Kiểu dữ liệu | Ràng buộc                      | Mặc định          | Mô tả                   |
| --------------- | ------------ | ------------------------------ | ----------------- | ----------------------- |
| `id`            | SERIAL       | PRIMARY KEY                    | Auto              | Khóa chính              |
| `dispatch_code` | VARCHAR(50)  | NOT NULL, UNIQUE               | -                 | Mã phiếu (PX-2026-0001) |
| `order_id`      | INT          | NOT NULL, FK → SalesOrders(id) | -                 | Đơn hàng liên quan      |
| `user_id`       | INT          | NOT NULL, FK → Users(id)       | -                 | Nhân viên xuất          |
| `dispatch_date` | DATE         | NOT NULL                       | -                 | Ngày xuất               |
| `status`        | VARCHAR(20)  | NOT NULL, CHECK (4 statuses)   | 'Pending'         | Trạng thái              |
| `notes`         | TEXT         | NULL                           | -                 | Ghi chú                 |
| `created_at`    | TIMESTAMP    | NOT NULL                       | CURRENT_TIMESTAMP | Thời điểm tạo           |
| `updated_at`    | TIMESTAMP    | NOT NULL                       | CURRENT_TIMESTAMP | Thời điểm cập nhật      |

#### CHECK Values

- `status`: 'Pending', 'Full', 'Partial', 'Cancelled'

#### Indexes

- `idx_sd_order` ON `order_id`
- `idx_sd_status` ON `status`
- Implicit UNIQUE trên `dispatch_code`

#### Relationships

| Quan hệ | Bảng          | Loại   | ON DELETE |
| ------- | ------------- | ------ | --------- |
| N → 1   | SalesOrders   | Child  | RESTRICT  |
| N → 1   | Users         | Child  | RESTRICT  |
| 1 → N   | InventoryLogs | Parent | SET NULL  |

#### Business Rules

1. 1 StockDispatch → N InventoryLogs
2. `status = 'Full'` → đã xuất đủ
3. `status = 'Partial'` → xuất thiếu (có backorder)
4. `dispatch_code` format: PX-YYYY-NNNN

---

### 22. InventoryLogs (Nhật ký biến động Kho)

**Mục đích**: Ghi nhận mọi biến động tồn kho  
**Use Cases**: UC6, UC10  
**Nhóm**: Kho hàng & Giao dịch

#### Columns

| Cột                | Kiểu dữ liệu  | Ràng buộc                       | Mặc định          | Mô tả               |
| ------------------ | ------------- | ------------------------------- | ----------------- | ------------------- |
| `id`               | BIGSERIAL     | PRIMARY KEY                     | Auto              | Khóa chính          |
| `product_id`       | INT           | NOT NULL, FK → Products(id)     | -                 | Sản phẩm            |
| `action_type`      | VARCHAR(20)   | NOT NULL, CHECK (4 types)       | -                 | Loại biến động      |
| `quantity_change`  | DECIMAL(12,4) | NOT NULL                        | -                 | Số lượng thay đổi   |
| `unit_id`          | INT           | NOT NULL, FK → ProductUnits(id) | -                 | Đơn vị              |
| `user_id`          | INT           | FK → Users(id)                  | NULL              | Người thực hiện     |
| `dispatch_id`      | INT           | FK → StockDispatches(id)        | NULL              | Liên kết phiếu xuất |
| `receipt_id`       | INT           | FK → StockReceipts(id)          | NULL              | Liên kết phiếu nhập |
| `from_location_id` | INT           | FK → WarehouseLocations(id)     | NULL              | Vị trí nguồn        |
| `to_location_id`   | INT           | FK → WarehouseLocations(id)     | NULL              | Vị trí đích         |
| `reference_note`   | VARCHAR(255)  | NULL                            | -                 | Ghi chú tham chiếu  |
| `created_at`       | TIMESTAMP     | NOT NULL                        | CURRENT_TIMESTAMP | Thời điểm ghi log   |

#### CHECK Values

- `action_type`: 'INBOUND', 'OUTBOUND', 'TRANSFER', 'ADJUSTMENT'

#### Indexes

- `idx_il_product` ON `product_id`
- `idx_il_created_at` ON `created_at`
- `idx_il_dispatch` ON `dispatch_id`
- `idx_il_receipt` ON `receipt_id`
- `idx_il_user` ON `user_id` (recommended)

#### Relationships

| Quan hệ | Bảng                      | Loại  | ON DELETE |
| ------- | ------------------------- | ----- | --------- |
| N → 1   | Products                  | Child | RESTRICT  |
| N → 1   | ProductUnits              | Child | RESTRICT  |
| N → 1   | Users                     | Child | SET NULL  |
| N → 1   | StockDispatches           | Child | SET NULL  |
| N → 1   | StockReceipts             | Child | SET NULL  |
| N → 1   | WarehouseLocations (from) | Child | SET NULL  |
| N → 1   | WarehouseLocations (to)   | Child | SET NULL  |

#### Business Rules

1. `quantity_change > 0` → nhập kho (INBOUND)
2. `quantity_change < 0` → xuất kho (OUTBOUND)
3. `action_type = 'TRANSFER'` → quantity_change = 0, chỉ đổi from/to
4. `action_type = 'ADJUSTMENT'` → điều chỉnh kiểm kê (+/-)
5. Bảng này tăng rất nhanh → cân nhắc partitioning

---

### 23. Notifications (Quản lý thông báo) - OPTIONAL

**Mục đích**: Lưu thông báo in-app cho người dùng  
**Use Cases**: UC4  
**Nhóm**: Optional

#### Columns

| Cột                 | Kiểu dữ liệu | Ràng buộc                 | Mặc định          | Mô tả          |
| ------------------- | ------------ | ------------------------- | ----------------- | -------------- |
| `id`                | BIGSERIAL    | PRIMARY KEY               | Auto              | Khóa chính     |
| `user_id`           | INT          | NOT NULL, FK → Users(id)  | -                 | Người nhận     |
| `notification_type` | VARCHAR(30)  | NOT NULL, CHECK (4 types) | -                 | Loại thông báo |
| `title`             | VARCHAR(255) | NOT NULL                  | -                 | Tiêu đề        |
| `message`           | TEXT         | NOT NULL                  | -                 | Nội dung       |
| `is_read`           | BOOLEAN      | NOT NULL                  | FALSE             | Đã đọc         |
| `reference_type`    | VARCHAR(50)  | NULL                      | -                 | Loại chứng từ  |
| `reference_id`      | INT          | NULL                      | -                 | ID chứng từ    |
| `created_at`        | TIMESTAMP    | NOT NULL                  | CURRENT_TIMESTAMP | Thời điểm tạo  |
| `read_at`           | TIMESTAMP    | NULL                      | -                 | Thời điểm đọc  |

#### CHECK Values

- `notification_type`: 'ApprovalResult', 'LowStock', 'ExpiryWarning', 'SystemAlert'

#### Indexes

- `idx_notif_user_unread` ON (user_id, is_read)
- `idx_notif_reference` ON (reference_type, reference_id) (recommended)

#### Relationships

| Quan hệ | Bảng  | Loại  | ON DELETE |
| ------- | ----- | ----- | --------- |
| N → 1   | Users | Child | CASCADE   |

---

## 🔗 Tổng hợp Relationships

### Foreign Key Matrix

| Bảng (Child) | Cột FK | Bảng (Parent) | Cột PK | ON DELETE | ON UPDATE |
| ------------ | ------ | ------------- | ------ | --------- | --------- |
