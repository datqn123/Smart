# SalesOrders Table

## 📋 Overview

**Purpose**: Sales order management  
**Use Cases**: UC1, UC4, UC9, UC10  
**Group**: Warehouse & Transactions

---

## 📊 Schema

| Column | Data Type | Constraint | Default | Description |
|--------|-----------|------------|---------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto | Auto-increment primary key |
| `order_code` | VARCHAR(50) | NOT NULL, UNIQUE | - | Order code (e.g., SO-2026-0001) |
| `customer_id` | INT | NOT NULL, FK → Customers(id) | - | Customer reference |
| `user_id` | INT | NOT NULL, FK → Users(id) | - | User who created |
| `total_amount` | DECIMAL(10,2) | NOT NULL, CHECK (>= 0) | 0 | Total amount |
| `discount_amount` | DECIMAL(10,2) | NOT NULL, CHECK (>= 0) | 0 | Discount amount |
| `final_amount` | DECIMAL(10,2) | GENERATED ALWAYS AS (total_amount - discount_amount) STORED | - | Final amount (auto-calculated) |
| `status` | VARCHAR(20) | NOT NULL, CHECK (Pending/Processing/Partial/Shipped/Delivered/Cancelled) | 'Pending' | Status |
| `parent_order_id` | INT | NULL, FK → SalesOrders(id) | - | Parent order (for backorders) |
| `shipping_address` | TEXT | NULL | - | Shipping address |
| `notes` | TEXT | NULL | - | Notes |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Update timestamp |
| `cancelled_at` | TIMESTAMP | NULL | - | Cancellation timestamp |
| `cancelled_by` | INT | NULL, FK → Users(id) | - | User who cancelled |

---

## 🔗 Relationships

| Relation | Table | Type | ON DELETE |
|----------|-------|------|-----------|
| N → 1 | Customers | Child | RESTRICT |
| N → 1 | Users (creator) | Child | RESTRICT |
| N → 1 | Users (canceller) | Child | SET NULL |
| N → 1 | SalesOrders (parent) | Child | SET NULL |
| 1 → N | OrderDetails | Parent | CASCADE |
| 1 → N | StockDispatches | Parent | RESTRICT |
| 1 → N | SalesOrders (children) | Parent | SET NULL |

---

## 📝 Business Rules

1. `order_code` format: SO-YYYY-NNNN
2. Backorder: child orders point to parent via `parent_order_id`
3. `final_amount` auto-calculated: total_amount - discount_amount
4. Cannot delete order when dispatches exist

---

## 📦 TypeScript Interface

```typescript
interface SalesOrder {
  id: number;
  orderCode: string; // SO-2026-0001
  customerId: number; // FK → Customer
  userId: number; // FK → User
  totalAmount: number;
  discountAmount: number;
  finalAmount: number; // auto: totalAmount - discountAmount
  status:
    | "Pending"
    | "Processing"
    | "Partial"
    | "Shipped"
    | "Delivered"
    | "Cancelled";
  parentOrderId?: number; // FK → SalesOrder (Backorder)
  shippingAddress?: string;
  notes?: string;

  createdAt: Date;
  updatedAt: Date;
  cancelledAt?: Date;
  cancelledBy?: number; // FK → User

  // Relations
  customer?: Customer;
  user?: User;
  canceller?: User;
  details?: OrderDetail[];
  dispatches?: StockDispatch[];
  childOrders?: SalesOrder[]; // backorders
  parentOrder?: SalesOrder; // if this is backorder
}
```

---

## 📈 Status Flow

```
Pending ────> Processing ────> Partial ────> Shipped ────> Delivered
    │             │
    │             └───> Cancelled (Restock)
    │
    └───> Cancelled
```

---

## 🔍 Indexes

- `idx_so_customer` ON `customer_id`
- `idx_so_user` ON `user_id`
- `idx_so_status` ON `status`
- `idx_so_parent` ON `parent_order_id`
- `idx_so_created_at` ON `created_at`
