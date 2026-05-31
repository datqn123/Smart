## 🔗 Tổng hợp Relationships (tiếp theo)

### Foreign Key Matrix hoàn chỉnh

| Child Table | FK Column | Parent Table | ON DELETE | ON UPDATE | Ghi chú |
|------------|-----------|--------------|-----------|-----------|---------|
| **Categories** | parent_id | Categories(id) | SET NULL | CASCADE | Self-reference |
| **Users** | role_id | Roles(id) | RESTRICT | CASCADE | Không xóa role khi còn user |
| **Products** | category_id | Categories(id) | SET NULL | CASCADE | Unassigned khi xóa category |
| **AlertSettings** | owner_id | Users(id) | CASCADE | CASCADE | Xóa user → xóa alerts |
| **SystemLogs** | user_id | Users(id) | SET NULL | CASCADE | Giữ log khi xóa user |
| **FinanceLedger** | created_by | Users(id) | RESTRICT | CASCADE | Không xóa user tạo giao dịch |
| **AIInsights** | owner_id | Users(id) | CASCADE | CASCADE | Xóa user → xóa insights |
| **AIChatHistory** | user_id | Users(id) | CASCADE | CASCADE | Xóa user → xóa chat history |
| **MediaAudits** | uploaded_by | Users(id) | SET NULL | CASCADE | Giữ media khi xóa user |
| **ProductUnits** | product_id | Products(id) | CASCADE | CASCADE | Xóa product → xóa units |
| **ProductPriceHistory** | product_id | Products(id) | CASCADE | CASCADE | Xóa product → xóa history |
| **ProductPriceHistory** | unit_id | ProductUnits(id) | CASCADE | CASCADE | Xóa unit → xóa history |
| **Inventory** | product_id | Products(id) | CASCADE | CASCADE | Xóa product → xóa inventory |
| **Inventory** | location_id | WarehouseLocations(id) | RESTRICT | CASCADE | Không xóa location khi còn tồn kho |
| **StockReceipts** | supplier_id | Suppliers(id) | RESTRICT | CASCADE | Không xóa NCC khi có phiếu |
| **StockReceipts** | staff_id | Users(id) | RESTRICT | CASCADE | Audit trail |
| **StockReceipts** | approved_by | Users(id) | SET NULL | CASCADE | Giữ phiếu khi xóa approver |
| **StockReceiptDetails** | receipt_id | StockReceipts(id) | CASCADE | CASCADE | Xóa phiếu → xóa details |
| **StockReceiptDetails** | product_id | Products(id) | RESTRICT | CASCADE | Không xóa product khi có details |
| **StockReceiptDetails** | unit_id | ProductUnits(id) | RESTRICT | CASCADE | Không xóa unit khi có details |
| **SalesOrders** | customer_id | Customers(id) | RESTRICT | CASCADE | Không xóa KH khi có đơn |
| **SalesOrders** | user_id | Users(id) | RESTRICT | CASCADE | Audit trail |
| **SalesOrders** | parent_order_id | SalesOrders(id) | SET NULL | CASCADE | Backorder reference |
| **SalesOrders** | cancelled_by | Users(id) | SET NULL | CASCADE | Giữ đơn khi xóa canceller |
| **OrderDetails** | order_id | SalesOrders(id) | CASCADE | CASCADE | Xóa đơn → xóa details |
| **OrderDetails** | product_id | Products(id) | RESTRICT | CASCADE | Không xóa product khi có details |
| **OrderDetails** | unit_id | ProductUnits(id) | RESTRICT | CASCADE | Không xóa unit khi có details |
| **StockDispatches** | order_id | SalesOrders(id) | RESTRICT | CASCADE | Không xóa đơn khi có dispatch |
| **StockDispatches** | user_id | Users(id) | RESTRICT | CASCADE | Audit trail |
| **InventoryLogs** | product_id | Products(id) | RESTRICT | CASCADE | Giữ log khi xóa product |
| **InventoryLogs** | unit_id | ProductUnits(id) | RESTRICT | CASCADE | Giữ log khi xóa unit |
| **InventoryLogs** | user_id | Users(id) | SET NULL | CASCADE | Giữ log khi xóa user |
| **InventoryLogs** | dispatch_id | StockDispatches(id) | SET NULL | CASCADE | Giữ log khi xóa dispatch |
| **InventoryLogs** | receipt_id | StockReceipts(id) | SET NULL | CASCADE | Giữ log khi xóa receipt |
| **InventoryLogs** | from_location_id | WarehouseLocations(id) | SET NULL | CASCADE | Giữ log khi xóa location |
| **InventoryLogs** | to_location_id | WarehouseLocations(id) | SET NULL | CASCADE | Giữ log khi xóa location |
| **Notifications** | user_id | Users(id) | CASCADE | CASCADE | Xóa user → xóa notifications |

---

## 📈 Relationship Diagrams

### 1. Quan hệ phân quyền (UC3)

```
Roles (1) ────< (N) Users (N) ────< (1) AlertSettings
                     │
                     ├────< (N) FinanceLedger (created_by)
                     ├────< (N) AIInsights
                     ├────< (N) AIChatHistory
                     ├────< (N) MediaAudits (uploaded_by)
                     ├────< (N) StockReceipts (staff_id, approved_by)
                     ├────< (N) SalesOrders (user_id, cancelled_by)
                     ├────< (N) StockDispatches
                     ├────< (N) InventoryLogs
                     ├────< (N) SystemLogs
                     └────< (N) Notifications
```

### 2. Quan hệ sản phẩm & tồn kho (UC6, UC8)

```
Categories (1) ────< (N) Products (N) ────< (1) Inventory
                        │                       │
                        ├────< (N) ProductUnits  │
                        │        │               │
                        │        └────< (N) ProductPriceHistory
                        │
                        ├────< (N) StockReceiptDetails
                        ├────< (N) OrderDetails
                        └────< (N) InventoryLogs
```

### 3. Quan hệ nhập kho (UC7)

```
Suppliers (1) ────< (N) StockReceipts (N) ────< (1) StockReceiptDetails
     │                      │                          │
     │                      ├────< (1) Users (staff)   ├────< (1) Products
     │                      └────< (1) Users (approver)└────< (1) ProductUnits
     │
     └────< (N) FinanceLedger (khi Approved)
```

### 4. Quan hệ bán hàng & xuất kho (UC9, UC10)

```
Customers (1) ────< (N) SalesOrders ────< (1) OrderDetails
                         │                     │
                         │                     ├────< (1) Products
                         │                     └────< (1) ProductUnits
                         │
                         ├────< (N) StockDispatches ────< (N) InventoryLogs
                         │
                         └────< (Self) SalesOrders (parent_order_id - Backorder)
```

### 5. Quan hệ biến động kho (UC6, UC10)

```
Products (1) ────< (N) InventoryLogs (N) ────< (1) Users
                        │                          │
                        ├────< (1) ProductUnits     │
                        ├────< (1) StockDispatches  │
                        ├────< (1) StockReceipts    │
                        └────< (2) WarehouseLocations (from, to)
```

### 6. Quan hệ AI & Media (UC2, UC11, UC12, UC13)

```
Users (1) ────< (N) AIInsights
       │
       ├────< (N) AIChatHistory
       │
       └────< (N) MediaAudits ────< Polymorphic (StockReceipts, SalesOrders, Inventory)
```

---

## 🎯 Cascade Delete Scenarios

### Scenario 1: Xóa Product

```
DELETE FROM Products WHERE id = 123;

Kết quả:
✅ ProductUnits (cùng product_id) → XÓA (CASCADE)
✅ ProductPriceHistory (cùng product_id) → XÓA (CASCADE)
✅ Inventory (cùng product_id) → XÓA (CASCADE)
❌ StockReceiptDetails → BLOCKED (RESTRICT)
❌ OrderDetails → BLOCKED (RESTRICT)
❌ InventoryLogs → BLOCKED (RESTRICT)
```

**Business Logic**: Không cho xóa product khi đã có giao dịch (receipts, orders, logs).

### Scenario 2: Xóa Customer

```
DELETE FROM Customers WHERE id = 456;

Kết quả:
❌ SalesOrders (cùng customer_id) → BLOCKED (RESTRICT)
```

**Business Logic**: Không xóa customer khi còn đơn hàng. Phải hủy/chuyển đơn hàng trước.

### Scenario 3: Xóa User (Staff)

```
DELETE FROM Users WHERE id = 789;

Kết quả:
✅ AlertSettings (cùng owner_id) → XÓA (CASCADE)
✅ AIInsights (cùng owner_id) → XÓA (CASCADE)
✅ AIChatHistory (cùng user_id) → XÓA (CASCADE)
✅ Notifications (cùng user_id) → XÓA (CASCADE)
❌ StockReceipts (staff_id) → BLOCKED (RESTRICT)
❌ SalesOrders (user_id) → BLOCKED (RESTRICT)
❌ FinanceLedger (created_by) → BLOCKED (RESTRICT)
✅ SystemLogs (user_id) → SET NULL
✅ MediaAudits (uploaded_by) → SET NULL
✅ InventoryLogs (user_id) → SET NULL
```

**Business Logic**: 
- Xóa user → xóa dữ liệu cá nhân (alerts, chat, insights, notifications)
- Giữ audit trail (receipts, orders, finance, logs) nhưng null user_id
- KHÔNG cho xóa khi còn giao dịch quan trọng

### Scenario 4: Xóa SalesOrder

```
DELETE FROM SalesOrders WHERE id = 100;

Kết quả:
✅ OrderDetails (cùng order_id) → XÓA (CASCADE)
❌ StockDispatches (cùng order_id) → BLOCKED (RESTRICT)
✅ SalesOrders con (parent_order_id) → SET NULL (backorder thành đơn độc lập)
```

**Business Logic**: Không xóa đơn khi đã có phiếu xuất kho. Phải hủy dispatch trước.

---

## 📊 Index Strategy Summary

### High-traffic Queries Indexes

| Bảng | Index | Columns | Query Type | Use Case |
|------|-------|---------|-----------|----------|
| Products | idx_products_sku | sku_code | UNIQUE lookup | UC8: Search by SKU |
| Products | idx_products_barcode | barcode | UNIQUE lookup | UC8: Barcode scan |
| Products | idx_products_name | name | LIKE query | UC8: Search by name |
| Products | idx_products_status | status | Filter | UC8: Filter active |
| Products | idx_products_category | category_id | Filter | UC6, UC8: Filter by category |
| Customers | idx_customers_phone | phone | UNIQUE lookup | UC9: Search by phone |
| Suppliers | idx_suppliers_name | name | Filter | UC7: Search by name |
| Suppliers | idx_suppliers_phone | phone | Filter | UC7: Search by phone |
| SalesOrders | idx_so_customer | customer_id | Filter | UC9: Orders by customer |
| SalesOrders | idx_so_user | user_id | Filter | UC9: Orders by staff |
| SalesOrders | idx_so_status | status | Filter | UC9: Filter by status |
| SalesOrders | idx_so_parent | parent_order_id | Filter | UC10: Backorders |
| SalesOrders | idx_so_created_at | created_at | Range | UC1, UC9: Date range |
| StockReceipts | idx_sr_supplier | supplier_id | Filter | UC7: Receipts by supplier |
| StockReceipts | idx_sr_status | status | Filter | UC4, UC7: Pending approvals |
| StockDispatches | idx_sd_order | order_id | Filter | UC10: Dispatches by order |
| StockDispatches | idx_sd_status | status | Filter | UC10: Pending dispatches |
| Inventory | idx_inv_product | product_id | Filter | UC1, UC6: Stock by product |
| Inventory | idx_inv_expiry_date | expiry_date | Range | UC1, UC6: Expiry alerts |
| InventoryLogs | idx_il_product | product_id | Filter | UC6, UC10: Product history |
| InventoryLogs | idx_il_created_at | created_at | Range | UC6: Time-based history |
| InventoryLogs | idx_il_dispatch | dispatch_id | Filter | UC10: Dispatch logs |
| InventoryLogs | idx_il_receipt | receipt_id | Filter | UC7: Receipt logs |
| InventoryLogs | idx_il_user | user_id | Filter | UC4, UC6: User audit trail |
| ProductPriceHistory | idx_price_lookup | (product_id, unit_id, effective_date DESC) | Composite | UC1, UC8: Latest price |
| AIChatHistory | idx_chat_user | user_id | Filter | UC11: User chat history |
| AIChatHistory | idx_chat_session | session_id | Filter | UC11: Session context |
| AIChatHistory | idx_chat_created_at | created_at | Range | UC11: Recent messages |
| AIInsights | idx_ai_insight_owner | owner_id | Filter | UC2: Owner insights |
| AlertSettings | idx_alert_owner | owner_id | Filter | UC5: Owner settings |
| SystemLogs | idx_syslog_level | log_level | Filter | UC4, UC6: Error filtering |
| SystemLogs | idx_syslog_created_at | created_at | Range | UC4, UC6: Time-based logs |
| Notifications | idx_notif_user_unread | (user_id, is_read) | Composite | UC4: Unread notifications |
| Notifications | idx_notif_reference | (reference_type, reference_id) | Composite | UC4: Related notifications |

### Index Types Used

| Type | Count | Example |
|------|-------|---------|
| UNIQUE (implicit) | 13 | sku_code, barcode, email, etc. |
| Single column | 25+ | idx_products_name, idx_so_status, etc. |
| Composite | 4 | idx_price_lookup, idx_notif_user_unread, etc. |
| **Total** | **42+** | |

---

## 🔐 Security & Data Integrity

### Password Security
```sql
-- KHÔNG BAO GIỜ lưu plaintext password
-- Dùng bcrypt với cost >= 10 hoặc argon2id
-- Example (application layer):
bcrypt.hash('user_password', 10) → '$2a$10$...'
argon2.hash('user_password') → '$argon2id$v=19$m=65536,t=3,p=4$...'
```

### SQL Injection Prevention
- Sử dụng **parameterized queries** (prepared statements)
- KHÔNG concatenate SQL strings
- Dùng ORM (Prisma, Sequelize, SQLAlchemy) nếu có thể

### Transaction Safety
```sql
-- UC4: Approve Transaction với rollback
BEGIN TRANSACTION;

UPDATE StockReceipts SET status = 'Approved', approved_by = ?, approved_at = NOW()
WHERE id = ?;

-- Update Inventory
UPDATE Inventory SET quantity = quantity + ?
WHERE product_id = ? AND location_id = ?;

-- Record FinanceLedger
INSERT INTO FinanceLedger (transaction_date, transaction_type, reference_type, reference_id, amount, created_by)
VALUES (?, 'PurchaseCost', 'StockReceipt', ?, ?, ?);

-- If any error → ROLLBACK
-- If success → COMMIT
COMMIT;
```

### Data Validation Layers
1. **Database level**: CHECK constraints, NOT NULL, UNIQUE, FK
2. **Application level**: Input validation, business rules
3. **API level**: Request validation (Joi, Zod, Pydantic)

---

## 📈 Performance Optimization

### Query Optimization Tips

#### 1. Use EXPLAIN ANALYZE
```sql
EXPLAIN ANALYZE
SELECT * FROM SalesOrders
WHERE customer_id = 123 AND status = 'Pending';
```

#### 2. Avoid SELECT *
```sql
-- Bad
SELECT * FROM Products WHERE id = ?;

-- Good
SELECT id, name, sku_code, price, status FROM Products WHERE id = ?;
```

#### 3. Use LIMIT for pagination
```sql
SELECT id, name, sku_code, status
FROM Products
WHERE status = 'Active'
ORDER BY name
LIMIT 20 OFFSET 0;
```

#### 4. Use JOIN instead of subqueries
```sql
-- Bad (subquery)
SELECT p.name, 
       (SELECT quantity FROM Inventory WHERE product_id = p.id LIMIT 1) as qty
FROM Products p;

-- Good (JOIN)
SELECT p.name, i.quantity
FROM Products p
LEFT JOIN Inventory i ON p.id = i.product_id;
```

### Caching Strategy
- **Redis** cho frequently accessed data (product list, inventory counts)
- **Materialized Views** cho dashboard aggregates
- **Application-level cache** cho static data (roles, categories)

### Partitioning (Future)
```sql
-- SystemLogs partitioning by month
CREATE TABLE SystemLogs (
    id BIGSERIAL,
    log_level VARCHAR(20),
    ...
    created_at TIMESTAMP
) PARTITION BY RANGE (created_at);

CREATE TABLE SystemLogs_2026_04 PARTITION OF SystemLogs
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
```

---

## 📝 Business Logic Summary

### Key Business Rules

| Rule | Description | Enforcement |
|------|-------------|-------------|
| **Base Unit Rule** | Mỗi product có ĐÚNG 1 base unit | Application validation |
| **Inventory Quantity** | LUÔN lưu theo base unit | Database design |
| **Price History** | Không sửa giá lịch sử | CHECK constraints + application |
| **Backorder Logic** | Đơn con trỏ về đơn cha | Self-referencing FK |
| **Approval Workflow** | Chỉ Approved mới cập nhật kho | Application logic |
| **Immutable Records** | FinanceLedger không sửa sau khi ghi | Application logic |
| **No Negative Stock** | quantity >= 0 | CHECK constraint |
| **Unique Codes** | SKU, barcode, receipt_code, order_code | UNIQUE constraints |

### Status Flow Diagrams

#### StockReceipt Status Flow
```
Draft ────> Pending ────> Approved
              │              │
              │              └───> Update Inventory & FinanceLedger
              │
              └───> Rejected
```

#### SalesOrder Status Flow
```
Pending ────> Processing ────> Partial ────> Shipped ────> Delivered
    │             │
    │             └───> Cancelled (Restock)
    │
    └───> Cancelled
```

#### StockDispatch Status Flow
```
Pending ────> Full
    │
    ├───> Partial ────> Create Backorder
    │
    └───> Cancelled
```

---

## 🎯 Use Case to Table Mapping

| Use Case | Primary Tables | Secondary Tables |
|----------|---------------|------------------|
| UC1: Dashboard | Inventory, FinanceLedger, SalesOrders | Products, ProductPriceHistory, AlertSettings |
| UC2: AI Insight | AIInsights, AIChatHistory | FinanceLedger, Inventory, SalesOrders |
| UC3: Manage Staff | Users, Roles | - |
| UC4: Approve Transactions | StockReceipts, FinanceLedger | Inventory, SystemLogs, Notifications |
| UC5: Alert Settings | AlertSettings | Users |
| UC6: Inventory List | Inventory, InventoryLogs | Products, WarehouseLocations, SystemLogs |
| UC7: Stock Receipts | StockReceipts, StockReceiptDetails | Suppliers, Products, ProductUnits |
| UC8: Manage Products | Products, ProductUnits, ProductPriceHistory | Categories, Suppliers |
| UC9: Sales Orders | SalesOrders, OrderDetails | Customers, Products, Inventory |
| UC10: Dispatch | StockDispatches, InventoryLogs | SalesOrders, Inventory, Products |
| UC11: Chat Bot | AIChatHistory | Products, Inventory, AIInsights |
| UC12: Update via Image | MediaAudits, StockReceipts | Products, Suppliers |
| UC13: Update via Voice | MediaAudits, InventoryLogs | Products, WarehouseLocations, AIChatHistory |

---

## 📋 Checklist Implementation

### Database Setup
- [x] 23 tables created
- [x] 42+ foreign keys
- [x] 13 UNIQUE constraints
- [x] 18+ CHECK constraints
- [x] 30+ indexes
- [x] 3 generated columns
- [x] 12 triggers for updated_at
- [x] Seed data (Roles, Users, Locations, Categories)

### Business Logic
- [x] Multi-UoM conversion
- [x] Price history tracking
- [x] Backorder handling
- [x] Approval workflow
- [x] Inventory audit trail
- [x] Finance ledger
- [x] AI interaction logging
- [x] Media audit trail

### Performance
- [x] Indexes on FK columns
- [x] Composite indexes for common queries
- [x] Generated columns for calculations
- [x] Partitioning notes for large tables

### Security
- [x] Password hash requirement
- [x] FK constraints prevent orphan records
- [x] CHECK constraints validate data
- [x] RESTRICT deletes protect important records

---

## 🏆 Kết luận

Tài liệu đặc tả này cung cấp:
- ✅ **Chi tiết đầy đủ** cho từng 23 bảng
- ✅ **42+ relationships** với ON DELETE/UPDATE rules
- ✅ **30+ indexes** optimized cho queries
- ✅ **Business rules** và validation logic
- ✅ **Use case mapping** rõ ràng
- ✅ **Security & performance** guidelines

**Trạng thái**: ✅ **PRODUCTION READY**  
**Bước tiếp theo**: Implement application layer với spec này làm reference

---

**Tác giả**: AI Assistant  
**Ngày**: 11/04/2026  
**Phiên bản**: 5.0 - COMPLETE SPECIFICATION  
**Tham chiếu**: schema.sql, Database_Schema_Detail.md v4.0, UseCase_Database_Coverage.md
