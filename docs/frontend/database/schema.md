# Database Schema Overview - Smart Inventory Management

## 📋 Document Information

- **Project**: Smart Inventory Management
- **Database**: PostgreSQL 15+
- **Version**: 5.0 - PRODUCTION SPECIFICATION
- **Total Tables**: 24 (23 main + 1 optional)
- **Created**: 11/04/2026

---

## 🎯 Architecture Overview

### Table Groups

| Group | Count | Tables |
|-------|-------|--------|
| Admin & Users | 4 | Roles, Users, AlertSettings, SystemLogs |
| Partners & Finance | 3 | Customers, Suppliers, FinanceLedger |
| Categories & Products | 5 | Categories, Products, ProductImages, ProductUnits, ProductPriceHistory |
| Warehouse & Transactions | 8 | WarehouseLocations, Inventory, StockReceipts, StockReceiptDetails, SalesOrders, OrderDetails, StockDispatches, InventoryLogs |
| AI & Media | 3 | AIInsights, AIChatHistory, MediaAudits |
| Optional | 1 | Notifications |

### Constraints Statistics

| Type | Count | Purpose |
|------|-------|---------|
| PRIMARY KEY | 23 | Unique identification per table |
| UNIQUE | 13 | Prevent data duplication |
| FOREIGN KEY | 42 | Referential integrity |
| CHECK | 18 | Data validation at DB level |
| INDEX | 30+ | Query optimization |
| Generated Columns | 3 | Auto-calculation |
| Triggers | 12 | Auto-update timestamps |

---

## 📊 Entity Relationship Diagram

```
┌──────────┐         ┌──────────┐         ┌──────────┐
│   Role   │         │ Category │         │ Supplier │
└────┬─────┘         └────┬─────┘         └────┬─────┘
     │ 1:N               │ 1:N                │ 1:N
     ▼                   ▼                    ▼
┌──────────────────────────────────────────────────────────┐
│                          User                            │
└────────┬─────────────────────────────────────┬───────────┘
         │ 1:N                                 │ 1:N
         ▼                                     ▼
┌─────────────────────┐              ┌─────────────────────┐
│  AlertSetting       │              │     Product         │
│  SystemLog          │              └────────┬────────────┘
│  FinanceLedger      │                       │ 1:N
│  AIInsight          │           ┌───────────┼──────────────┐
│  AIChatHistory      │           ▼           ▼              ▼
│  Notification       │    ProductImage  ProductUnit   PriceHistory
│  StockReceipt       │                       ▼
│  SalesOrder         │                  Inventory
│  StockDispatch      │              (WarehouseLocation)
│  InventoryLog       │
│  MediaAudit         │
└─────────────────────┘

┌──────────┐
│ Customer │
└────┬─────┘
     │ 1:N
     ▼
┌─────────────────────┐
│   SalesOrder        │◄──── self-ref (parentOrderId: Backorder)
└────────┬────────────┘
         │ 1:N
         ▼
┌─────────────────────┐         ┌─────────────────┐
│   OrderDetail       │         │ StockDispatch   │
└─────────────────────┘         └────────┬────────┘
                                         │ 1:N
                                         ▼
                                  ┌─────────────────┐
                                  │ InventoryLog    │
                                  └─────────────────┘
```

---

## 🔗 Core Relationships

### Primary Relationships

```
Role ──────────────── 1:N ──→ User
                        │
Category ───────────── 1:N ──→ Product
                        │
Supplier ───────────── 1:N ──→ StockReceipt ─── 1:N ──→ StockReceiptDetail
                        │           │
Customer ───────────── 1:N ──→ SalesOrder ──── 1:N ──→ OrderDetail
                        │           │
WarehouseLocation ──── 1:N ──→ Inventory
```

### Self-References

```
Category:     parent ← children (hierarchical tree)
SalesOrder:   parentOrder ← childOrders (backorders)
```

### Polymorphic Relationships

```
FinanceLedger:  referenceType + referenceId → SalesOrder | StockReceipt | ...
MediaAudit:     entityType + entityId → StockReceipt | SalesOrder | Inventory
```

---

## 📋 Quick Table Reference

### Admin & Users
1. [Roles](./tables/roles.md) - User roles and permissions
2. [Users](./tables/users.md) - User accounts
3. [AlertSettings](./tables/alert_settings.md) - Alert configurations
4. [SystemLogs](./tables/system_logs.md) - System logs

### Partners & Finance
5. [Customers](./tables/customers.md) - Customer information
6. [Suppliers](./tables/suppliers.md) - Supplier information
7. [FinanceLedger](./tables/finance_ledger.md) - Financial transactions

### Categories & Products
8. [Categories](./tables/categories.md) - Product categories (hierarchical)
9. [Products](./tables/products.md) - Product catalog
10. [ProductImages](./tables/product_images.md) - Product images
11. [ProductUnits](./tables/product_units.md) - Unit conversions
12. [ProductPriceHistory](./tables/price_history.md) - Price history tracking

### Warehouse & Transactions
13. [WarehouseLocations](./tables/warehouse_locations.md) - Warehouse locations
14. [Inventory](./tables/inventory.md) - Current inventory
15. [StockReceipts](./tables/stock_receipts.md) - Stock receipts (header)
16. [StockReceiptDetails](./tables/stock_receipt_details.md) - Stock receipt details
17. [SalesOrders](./tables/sales_orders.md) - Sales orders (header)
18. [OrderDetails](./tables/order_details.md) - Sales order details
19. [StockDispatches](./tables/stock_dispatches.md) - Stock dispatches
20. [InventoryLogs](./tables/inventory_logs.md) - Inventory audit logs

### AI & Media
21. [AIInsights](./tables/ai_insights.md) - AI business insights
22. [AIChatHistory](./tables/ai_chat_history.md) - AI chat history
23. [MediaAudits](./tables/media_audits.md) - Media audit trails
24. [Notifications](./tables/notifications.md) - User notifications (optional)

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

## 📝 Key Business Rules

| Rule | Description | Enforcement |
|------|-------------|-------------|
| **Base Unit Rule** | Each product has EXACTLY 1 base unit | Application validation |
| **Inventory Quantity** | ALWAYS stored in base unit | Database design |
| **Price History** | Cannot modify historical prices | CHECK constraints + application |
| **Backorder Logic** | Child orders point to parent | Self-referencing FK |
| **Approval Workflow** | Only Approved updates inventory | Application logic |
| **Immutable Records** | FinanceLedger cannot be modified | Application logic |
| **No Negative Stock** | quantity >= 0 | CHECK constraint |
| **Unique Codes** | SKU, barcode, receipt_code, order_code | UNIQUE constraints |

---

## 🔐 Security Notes

### Password Security
- NEVER store plaintext passwords
- Use bcrypt with cost >= 10 or argon2id
- Password hash only in Users table

### SQL Injection Prevention
- Use **parameterized queries** (prepared statements)
- NEVER concatenate SQL strings
- Use ORM (Prisma, Sequelize, SQLAlchemy) when possible

### Transaction Safety
```sql
BEGIN TRANSACTION;
-- Perform operations
-- If error → ROLLBACK
-- If success → COMMIT
COMMIT;
```

---

**Status**: ✅ PRODUCTION READY  
**Reference**: schema.sql, Database_Specification.md, Entity_Relationships.md
