# StockDispatches Table

## 📋 Overview

**Purpose**: Stock dispatch (outbound goods)  
**Use Cases**: UC4, UC10  
**Group**: Warehouse & Transactions

---

## 📊 Schema

| Column | Data Type | Constraint | Default | Description |
|--------|-----------|------------|---------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto | Auto-increment primary key |
| `dispatch_code` | VARCHAR(50) | NOT NULL, UNIQUE | - | Dispatch code (e.g., PX-2026-0001) |
| `order_id` | INT | NOT NULL, FK → SalesOrders(id) | - | Order reference |
| `user_id` | INT | NOT NULL, FK → Users(id) | - | User who created |
| `dispatch_date` | DATE | NOT NULL | - | Dispatch date |
| `status` | VARCHAR(20) | NOT NULL, CHECK (Pending/Full/Partial/Cancelled) | 'Pending' | Status |
| `notes` | TEXT | NULL | - | Notes |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Update timestamp |

---

## 🔗 Relationships

| Relation | Table | Type | ON DELETE |
|----------|-------|------|-----------|
| N → 1 | SalesOrders | Child | RESTRICT |
| N → 1 | Users | Child | RESTRICT |
| 1 → N | InventoryLogs | Parent | CASCADE |

---

## 📝 Business Rules

1. `dispatch_code` format: PX-YYYY-NNNN
2. Partial dispatch → creates backorder
3. Cannot delete dispatch when inventory logs exist

---

## 📦 TypeScript Interface

```typescript
interface StockDispatch {
  id: number;
  dispatchCode: string; // PX-2026-0001
  orderId: number; // FK → SalesOrder
  userId: number; // FK → User
  dispatchDate: Date;
  status: "Pending" | "Full" | "Partial" | "Cancelled";
  notes?: string;
  createdAt: Date;
  updatedAt: Date;

  // Relations
  order?: SalesOrder;
  user?: User;
  logs?: InventoryLog[];
}
```

---

## 📈 Status Flow

```
Pending ────> Full
    │
    ├───> Partial ────> Create Backorder
    │
    └───> Cancelled
```

---

## 🔍 Indexes

- `idx_sd_order` ON `order_id`
- `idx_sd_status` ON `status`
