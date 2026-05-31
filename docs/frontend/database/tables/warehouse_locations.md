# WarehouseLocations Table

## 📋 Overview

**Purpose**: Define storage locations in warehouse  
**Use Cases**: UC6, UC10, UC13  
**Group**: Warehouse & Transactions

---

## 📊 Schema

| Column           | Data Type    | Constraint                          | Default           | Description                 |
| ---------------- | ------------ | ----------------------------------- | ----------------- | --------------------------- |
| `id`             | SERIAL       | PRIMARY KEY                         | Auto              | Auto-increment primary key  |
| `warehouse_code` | VARCHAR(20)  | NOT NULL                            | -                 | Warehouse code (e.g., WH01) |
| `shelf_code`     | VARCHAR(20)  | NOT NULL                            | -                 | Shelf code (e.g., A1, B2)   |
| `description`    | VARCHAR(255) | NULL                                | -                 | Location description        |
| `capacity`       | DECIMAL(5,2) | NULL                                | -                 | Capacity (m³)               |
| `status`         | VARCHAR(20)  | CHECK (Active/Maintenance/Inactive) | 'Active'          | Status                      |
| `created_at`     | TIMESTAMP    | NOT NULL                            | CURRENT_TIMESTAMP | Creation timestamp          |

---

## 🔗 Relationships

| Relation | Table                | Type   | ON DELETE |
| -------- | -------------------- | ------ | --------- |
| 1 → N    | Inventory            | Parent | RESTRICT  |
| 1 → N    | InventoryLogs (from) | Parent | SET NULL  |
| 1 → N    | InventoryLogs (to)   | Parent | SET NULL  |

---

## 📝 Business Rules

1. No duplicate (warehouse_code, shelf_code)
2. `status = 'Maintenance'` → cannot dispatch/receive to this location
3. Format: WH + 2 digits for warehouse, alphanumeric for shelf

---

## 📦 TypeScript Interface

```typescript
interface WarehouseLocation {
  id: number;
  warehouseCode: string; // WH01
  shelfCode: string; // A1, B2
  description?: string;
  capacity?: number; // m³
  status: "Active" | "Maintenance" | "Inactive";
  createdAt: Date;

  // Relations
  inventories?: Inventory[];
}
```

---

## 💾 Example Data

```sql
INSERT INTO WarehouseLocations (warehouse_code, shelf_code, description) VALUES
('WH01', 'A1', 'Shelf A1 - Main warehouse - Dry goods'),
('WH01', 'B1', 'Shelf B1 - Main warehouse - Cold storage');
```

---

## ⚠️ Constraints

- `uq_warehouse_shelf`: UNIQUE (warehouse_code, shelf_code)
