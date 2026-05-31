# Database Relationships

## 📋 Overview

This document provides a comprehensive view of all database relationships in the Smart Inventory Management system.

---

## 🔗 Foreign Key Matrix

| Child Table | FK Column | Parent Table | ON DELETE | ON UPDATE | Notes |
|------------|-----------|--------------|-----------|-----------|-------|
| **Categories** | parent_id | Categories(id) | SET NULL | CASCADE | Self-reference |
| **Users** | role_id | Roles(id) | RESTRICT | CASCADE | Cannot delete role when users exist |
| **Products** | category_id | Categories(id) | SET NULL | CASCADE | Unassigned when category deleted |
| **AlertSettings** | owner_id | Users(id) | CASCADE | CASCADE | Delete user → delete alerts |
| **SystemLogs** | user_id | Users(id) | SET NULL | CASCADE | Keep logs when user deleted |
| **FinanceLedger** | created_by | Users(id) | RESTRICT | CASCADE | Cannot delete user who created transactions |
| **AIInsights** | owner_id | Users(id) | CASCADE | CASCADE | Delete user → delete insights |
| **AIChatHistory** | user_id | Users(id) | CASCADE | CASCADE | Delete user → delete chat history |
| **MediaAudits** | uploaded_by | Users(id) | SET NULL | CASCADE | Keep media when user deleted |
| **ProductUnits** | product_id | Products(id) | CASCADE | CASCADE | Delete product → delete units |
| **ProductPriceHistory** | product_id | Products(id) | CASCADE | CASCADE | Delete product → delete history |
| **ProductPriceHistory** | unit_id | ProductUnits(id) | CASCADE | CASCADE | Delete unit → delete history |
| **Inventory** | product_id | Products(id) | CASCADE | CASCADE | Delete product → delete inventory |
| **Inventory** | location_id | WarehouseLocations(id) | RESTRICT | CASCADE | Cannot delete location when inventory exists |
| **StockReceipts** | supplier_id | Suppliers(id) | RESTRICT | CASCADE | Cannot delete supplier when receipts exist |
| **StockReceipts** | staff_id | Users(id) | RESTRICT | CASCADE | Audit trail |
| **StockReceipts** | approved_by | Users(id) | SET NULL | CASCADE | Keep receipts when approver deleted |
| **StockReceiptDetails** | receipt_id | StockReceipts(id) | CASCADE | CASCADE | Delete receipt → delete details |
| **StockReceiptDetails** | product_id | Products(id) | RESTRICT | CASCADE | Cannot delete product when details exist |
| **StockReceiptDetails** | unit_id | ProductUnits(id) | RESTRICT | CASCADE | Cannot delete unit when details exist |
| **SalesOrders** | customer_id | Customers(id) | RESTRICT | CASCADE | Cannot delete customer when orders exist |
| **SalesOrders** | user_id | Users(id) | RESTRICT | CASCADE | Audit trail |
| **SalesOrders** | parent_order_id | SalesOrders(id) | SET NULL | CASCADE | Backorder reference |
| **SalesOrders** | cancelled_by | Users(id) | SET NULL | CASCADE | Keep orders when canceller deleted |
| **OrderDetails** | order_id | SalesOrders(id) | CASCADE | CASCADE | Delete order → delete details |
| **OrderDetails** | product_id | Products(id) | RESTRICT | CASCADE | Cannot delete product when details exist |
| **OrderDetails** | unit_id | ProductUnits(id) | RESTRICT | CASCADE | Cannot delete unit when details exist |
| **StockDispatches** | order_id | SalesOrders(id) | RESTRICT | CASCADE | Cannot delete order when dispatches exist |
| **StockDispatches** | user_id | Users(id) | RESTRICT | CASCADE | Audit trail |
| **InventoryLogs** | product_id | Products(id) | RESTRICT | CASCADE | Keep logs when product deleted |
| **InventoryLogs** | unit_id | ProductUnits(id) | RESTRICT | CASCADE | Keep logs when unit deleted |
| **InventoryLogs** | user_id | Users(id) | SET NULL | CASCADE | Keep logs when user deleted |
| **InventoryLogs** | dispatch_id | StockDispatches(id) | SET NULL | CASCADE | Keep logs when dispatch deleted |
| **InventoryLogs** | receipt_id | StockReceipts(id) | SET NULL | CASCADE | Keep logs when receipt deleted |
| **InventoryLogs** | from_location_id | WarehouseLocations(id) | SET NULL | CASCADE | Keep logs when location deleted |
| **InventoryLogs** | to_location_id | WarehouseLocations(id) | SET NULL | CASCADE | Keep logs when location deleted |
| **Notifications** | user_id | Users(id) | CASCADE | CASCADE | Delete user → delete notifications |

---

## 📊 Relationship Diagrams

### 1. Authorization Relationship (UC3)

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

### 2. Product & Inventory Relationship (UC6, UC8)

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

### 3. Stock Receipt Relationship (UC7)

```
Suppliers (1) ────< (N) StockReceipts (N) ────< (1) StockReceiptDetails
     │                      │                          │
     │                      ├────< (1) Users (staff)   ├────< (1) Products
     │                      └────< (1) Users (approver)└────< (1) ProductUnits
     │
     └────< (N) FinanceLedger (when Approved)
```

### 4. Sales & Dispatch Relationship (UC9, UC10)

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

### 5. Inventory Movement Relationship (UC6, UC10)

```
Products (1) ────< (N) InventoryLogs (N) ────< (1) Users
                        │                          │
                        ├────< (1) ProductUnits     │
                        ├────< (1) StockDispatches  │
                        ├────< (1) StockReceipts    │
                        └────< (2) WarehouseLocations (from, to)
```

### 6. AI & Media Relationship (UC2, UC11, UC12, UC13)

```
Users (1) ────< (N) AIInsights
       │
       ├────< (N) AIChatHistory
       │
       └────< (N) MediaAudits ────< Polymorphic (StockReceipts, SalesOrders, Inventory)
```

---

## 🔄 Self-References

### Categories (Hierarchical Tree)

```typescript
Category {
  id: number;
  parentId?: number; // FK → Category
  parent?: Category;
  children?: Category[];
}
```

**Rules:**
- `parent_id = NULL` → root category
- No circular references allowed
- Delete parent → children become root (SET NULL)

### SalesOrders (Backorders)

```typescript
SalesOrder {
  id: number;
  parentOrderId?: number; // FK → SalesOrder
  parentOrder?: SalesOrder;
  childOrders?: SalesOrder[];
}
```

**Rules:**
- Backorder: child order points to parent order
- Delete parent → children become independent (SET NULL)

---

## 🔀 Polymorphic Relationships

### FinanceLedger

```typescript
FinanceLedger {
  referenceType?: string; // 'SalesOrder', 'StockReceipt'
  referenceId?: number;
}
```

**Mapping:**
- `reference_type = 'SalesOrder'` + `reference_id` → SalesOrders table
- `reference_type = 'StockReceipt'` + `reference_id` → StockReceipts table

**Validation:** Application layer

### MediaAudits

```typescript
MediaAudit {
  entityType: string; // 'StockReceipt', 'SalesOrder', 'Inventory'
  entityId: number;
}
```

**Mapping:**
- `entity_type = 'StockReceipt'` + `entity_id` → StockReceipts table
- `entity_type = 'SalesOrder'` + `entity_id` → SalesOrders table
- `entity_type = 'Inventory'` + `entity_id` → Inventory table

**Validation:** Application layer

---

## 💥 Cascade Delete Scenarios

### Scenario 1: Delete Product

```sql
DELETE FROM Products WHERE id = 123;

Result:
✅ ProductUnits (same product_id) → DELETE (CASCADE)
✅ ProductPriceHistory (same product_id) → DELETE (CASCADE)
✅ Inventory (same product_id) → DELETE (CASCADE)
❌ StockReceiptDetails → BLOCKED (RESTRICT)
❌ OrderDetails → BLOCKED (RESTRICT)
❌ InventoryLogs → BLOCKED (RESTRICT)
```

**Business Logic**: Cannot delete product when transactions exist (receipts, orders, logs).

---

### Scenario 2: Delete Customer

```sql
DELETE FROM Customers WHERE id = 456;

Result:
❌ SalesOrders (same customer_id) → BLOCKED (RESTRICT)
```

**Business Logic**: Cannot delete customer when orders exist. Must cancel/transfer orders first.

---

### Scenario 3: Delete User (Staff)

```sql
DELETE FROM Users WHERE id = 789;

Result:
✅ AlertSettings (same owner_id) → DELETE (CASCADE)
✅ AIInsights (same owner_id) → DELETE (CASCADE)
✅ AIChatHistory (same user_id) → DELETE (CASCADE)
✅ Notifications (same user_id) → DELETE (CASCADE)
❌ StockReceipts (staff_id) → BLOCKED (RESTRICT)
❌ SalesOrders (user_id) → BLOCKED (RESTRICT)
❌ FinanceLedger (created_by) → BLOCKED (RESTRICT)
✅ SystemLogs (user_id) → SET NULL
✅ MediaAudits (uploaded_by) → SET NULL
✅ InventoryLogs (user_id) → SET NULL
```

**Business Logic**:
- Delete user → delete personal data (alerts, chat, insights, notifications)
- Keep audit trail (receipts, orders, finance, logs) but null user_id
- CANNOT delete when important transactions exist

---

### Scenario 4: Delete SalesOrder

```sql
DELETE FROM SalesOrders WHERE id = 100;

Result:
✅ OrderDetails (same order_id) → DELETE (CASCADE)
❌ StockDispatches (same order_id) → BLOCKED (RESTRICT)
✅ SalesOrders children (parent_order_id) → SET NULL (backorders become independent)
```

**Business Logic**: Cannot delete order when dispatches exist. Must cancel dispatches first.

---

## 📈 ON DELETE Strategy Summary

| Strategy | Purpose | Tables |
|----------|---------|--------|
| **CASCADE** | Delete dependent data | AlertSettings, AIInsights, AIChatHistory, Notifications, ProductUnits, ProductPriceHistory, Inventory, Details tables |
| **RESTRICT** | Protect important records | StockReceipts, SalesOrders, FinanceLedger, InventoryLogs, StockDispatches, OrderDetails, StockReceiptDetails |
| **SET NULL** | Keep records, remove reference | SystemLogs, MediaAudits, InventoryLogs, StockReceipts (approver), SalesOrders (canceller), Users |

---

**Reference**: Entity_Relationships.md, Database_Specification.md
