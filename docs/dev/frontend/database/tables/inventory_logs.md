# InventoryLogs Table

## 📋 Overview

**Purpose**: Inventory audit trail for all stock movements  
**Use Cases**: UC6, UC10  
**Group**: Warehouse & Transactions

---

## 📊 Schema

| Column             | Data Type   | Constraint                                             | Default           | Description                             |
| ------------------ | ----------- | ------------------------------------------------------ | ----------------- | --------------------------------------- |
| `id`               | SERIAL      | PRIMARY KEY                                            | Auto              | Auto-increment primary key              |
| `product_id`       | INT         | NOT NULL, FK → Products(id)                            | -                 | Product reference                       |
| `action_type`      | VARCHAR(20) | NOT NULL, CHECK (INBOUND/OUTBOUND/TRANSFER/ADJUSTMENT) | -                 | Action type                             |
| `quantity_change`  | INT         | NOT NULL                                               | -                 | Quantity change (+ inbound, - outbound) |
| `unit_id`          | INT         | NOT NULL, FK → ProductUnits(id)                        | -                 | Unit reference                          |
| `user_id`          | INT         | NULL, FK → Users(id)                                   | -                 | User who performed action               |
| `dispatch_id`      | INT         | NULL, FK → StockDispatches(id)                         | -                 | Dispatch reference                      |
| `receipt_id`       | INT         | NULL, FK → StockReceipts(id)                           | -                 | Receipt reference                       |
| `from_location_id` | INT         | NULL, FK → WarehouseLocations(id)                      | -                 | Source location                         |
| `to_location_id`   | INT         | NULL, FK → WarehouseLocations(id)                      | -                 | Destination location                    |
| `reference_note`   | TEXT        | NULL                                                   | -                 | Reference note                          |
| `created_at`       | TIMESTAMP   | NOT NULL                                               | CURRENT_TIMESTAMP | Creation timestamp                      |

---

## 🔗 Relationships

| Relation | Table                     | Type  | ON DELETE |
| -------- | ------------------------- | ----- | --------- |
| N → 1    | Products                  | Child | RESTRICT  |
| N → 1    | ProductUnits              | Child | RESTRICT  |
| N → 1    | Users                     | Child | SET NULL  |
| N → 1    | StockDispatches           | Child | SET NULL  |
| N → 1    | StockReceipts             | Child | SET NULL  |
| N → 1    | WarehouseLocations (from) | Child | SET NULL  |
| N → 1    | WarehouseLocations (to)   | Child | SET NULL  |

---

## 📝 Business Rules

1. `quantity_change` positive for inbound, negative for outbound
2. Records every inventory movement for audit trail
3. Cannot delete logs when they exist (data integrity)

---

## 📦 TypeScript Interface

```typescript
interface InventoryLog {
  id: number;
  productId: number; // FK → Product
  actionType: "INBOUND" | "OUTBOUND" | "TRANSFER" | "ADJUSTMENT";
  quantityChange: number; // + inbound, - outbound
  unitId: number; // FK → ProductUnit
  userId?: number; // FK → User
  dispatchId?: number; // FK → StockDispatch
  receiptId?: number; // FK → StockReceipt
  fromLocationId?: number; // FK → WarehouseLocation
  toLocationId?: number; // FK → WarehouseLocation
  referenceNote?: string;
  createdAt: Date;

  // Relations
  product?: Product;
  unit?: ProductUnit;
  user?: User;
  dispatch?: StockDispatch;
  receipt?: StockReceipt;
  fromLocation?: WarehouseLocation;
  toLocation?: WarehouseLocation;
}
```

---

## 🔍 Indexes

- `idx_il_product` ON `product_id`
- `idx_il_created_at` ON `created_at`
- `idx_il_dispatch` ON `dispatch_id`
- `idx_il_receipt` ON `receipt_id`
- `idx_il_user` ON `user_id`
