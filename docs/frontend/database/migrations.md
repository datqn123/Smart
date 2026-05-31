# Database Migrations & Schema

## 📋 Overview

This document tracks database schema changes and provides the complete schema reference.

---

## 📊 Schema Statistics

| Metric | Count |
|--------|-------|
| Total Tables | 24 |
| Primary Keys | 23 |
| Foreign Keys | 42+ |
| UNIQUE Constraints | 13 |
| CHECK Constraints | 18+ |
| Indexes | 42+ |
| Generated Columns | 3 |
| Triggers | 12 |

---

## 📝 Schema File Reference

The complete database schema is available in:

- **File**: `../UC/schema.sql`
- **Version**: 5.1 SIMPLIFIED + ProductImages
- **Database**: PostgreSQL 15+
- **Created**: 11/04/2026

---

## 🏗️ Table Creation Order

The schema is created in 5 steps to handle dependencies:

### Step 1: Core Tables (No Foreign Keys)
1. Roles
2. Categories
3. Suppliers
4. Customers
5. WarehouseLocations

### Step 2: Routing Tables (Depend on Step 1)
6. Users
7. Products
7.1. ProductImages

### Step 3: Satellite & System Tables (Depend on Users & Products)
8. AlertSettings
9. SystemLogs
10. FinanceLedger
11. AIInsights
12. AIChatHistory
13. MediaAudits
14. ProductUnits
15. ProductPriceHistory

### Step 4: Transaction Headers & Inventory (Depend on Step 2 & 3)
16. Inventory
17. StockReceipts
18. SalesOrders

### Step 5: Transaction Details (Depend on Step 4)
19. StockReceiptDetails
20. OrderDetails
21. StockDispatches
22. InventoryLogs
23. Notifications (Optional)

---

## 🔄 Migration Best Practices

### Creating a New Migration

1. **Always use transactions**:
```sql
BEGIN;
-- Your migration SQL
COMMIT;
```

2. **Test rollback** (if applicable)

3. **Add comments** explaining the change

4. **Update this document** with migration number

### Migration Template

```sql
-- Migration: <description>
-- Date: <YYYY-MM-DD>
-- Description: <what and why>

BEGIN;

-- Your SQL here

COMMIT;
```

---

## 📊 Index Strategy

### High-Traffic Query Indexes

| Table | Index | Columns | Query Type | Use Case |
|-------|-------|---------|-----------|----------|
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

## 🔐 Security Constraints

### Password Security

```sql
-- NEVER store plaintext passwords
-- Use bcrypt with cost >= 10 or argon2id
-- Example (application layer):
bcrypt.hash('user_password', 10) → '$2a$10$...'
argon2.hash('user_password') → '$argon2id$v=19$m=65536,t=3,p=4$...'
```

### CHECK Constraints Summary

| Table | Constraint | Purpose |
|-------|-----------|---------|
| Products | status CHECK (Active/Inactive) | Valid status values |
| Users | status CHECK (Active/Locked) | Valid status values |
| Inventory | quantity CHECK (>= 0) | No negative stock |
| ProductUnits | conversion_rate CHECK (> 0) | Positive conversion rate |
| ProductPriceHistory | cost_price CHECK (>= 0) | Non-negative prices |
| ProductPriceHistory | sale_price CHECK (>= 0) | Non-negative prices |
| StockReceipts | status CHECK (Draft/Pending/Approved/Rejected) | Valid status values |
| StockReceipts | total_amount CHECK (>= 0) | Non-negative amounts |
| SalesOrders | status CHECK (Pending/Processing/Partial/Shipped/Delivered/Cancelled) | Valid status values |
| SalesOrders | total_amount CHECK (>= 0) | Non-negative amounts |
| SalesOrders | discount_amount CHECK (>= 0) | Non-negative discounts |
| OrderDetails | quantity CHECK (> 0) | Positive quantities |
| OrderDetails | price_at_time CHECK (>= 0) | Non-negative prices |
| OrderDetails | dispatched_qty CHECK (>= 0) | Non-negative dispatched qty |
| OrderDetails | dispatched_qty <= quantity | Cannot dispatch more than ordered |
| StockDispatches | status CHECK (Pending/Full/Partial/Cancelled) | Valid status values |
| AlertSettings | alert_type CHECK (...) | Valid alert types |
| AlertSettings | channel CHECK (...) | Valid channels |
| AlertSettings | frequency CHECK (...) | Valid frequencies |

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
SELECT id, name, sku_code, status FROM Products WHERE id = ?;
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

- **Redis** for frequently accessed data (product list, inventory counts)
- **Materialized Views** for dashboard aggregates
- **Application-level cache** for static data (roles, categories)

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

## ✅ Implementation Checklist

### Database Setup
- [x] 24 tables created
- [x] 42+ foreign keys
- [x] 13 UNIQUE constraints
- [x] 18+ CHECK constraints
- [x] 42+ indexes
- [x] 3 generated columns
- [x] 12 triggers for updated_at
- [x] Seed data (Roles, Users, Locations, Categories)

---

**Reference**: schema.sql, Database_Specification.md
