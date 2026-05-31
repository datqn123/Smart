# OrderDetails Table

## 📋 Overview

**Purpose**: Sales order line items  
**Use Cases**: UC9, UC10  
**Group**: Warehouse & Transactions

---

## 📊 Schema

| Column | Data Type | Constraint | Default | Description |
|--------|-----------|------------|---------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto | Auto-increment primary key |
| `order_id` | INT | NOT NULL, FK → SalesOrders(id) | - | Order reference |
| `product_id` | INT | NOT NULL, FK → Products(id) | - | Product reference |
| `unit_id` | INT | NOT NULL, FK → ProductUnits(id) | - | Unit reference |
| `quantity` | INT | NOT NULL, CHECK (> 0) | - | Quantity ordered |
| `price_at_time` | DECIMAL(10,2) | NOT NULL, CHECK (>= 0) | - | Price at order time |
| `line_total` | DECIMAL(10,2) | GENERATED ALWAYS AS (quantity * price_at_time) STORED | - | Auto-calculated total |
| `dispatched_qty` | INT | NOT NULL, CHECK (>= 0) | 0 | Quantity dispatched |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |

---

## 🔗 Relationships

| Relation | Table | Type | ON DELETE |
|----------|-------|------|-----------|
| N → 1 | SalesOrders | Child | CASCADE |
| N → 1 | Products | Child | RESTRICT |
| N → 1 | ProductUnits | Child | RESTRICT |

---

## 📝 Business Rules

1. `line_total` auto-calculated: quantity × price_at_time
2. `dispatched_qty = quantity` → fully dispatched
3. `dispatched_qty < quantity` → needs backorder
4. UNIQUE: (order_id, product_id, unit_id)

---

## 📦 TypeScript Interface

```typescript
interface OrderDetail {
  id: number;
  orderId: number; // FK → SalesOrder
  productId: number; // FK → Product
  unitId: number; // FK → ProductUnit
  quantity: number;
  priceAtTime: number; // price at order time
  lineTotal: number; // auto: quantity * priceAtTime
  dispatchedQty: number; // dispatched quantity
  createdAt: Date;

  // Computed
  remainingQty?: number; // quantity - dispatchedQty
  isFullyDispatched?: boolean; // dispatchedQty == quantity

  // Relations
  order?: SalesOrder;
  product?: Product;
  unit?: ProductUnit;
}
```

---

## 🔍 Indexes

- `idx_od_order` ON `order_id`

---

## ⚠️ Constraints

- `uq_od_order_product_unit`: UNIQUE (order_id, product_id, unit_id)
- `chk_dispatched_qty`: CHECK (dispatched_qty <= quantity)
- `chk_quantity_positive`: CHECK (quantity > 0)
- `chk_price_non_negative`: CHECK (price_at_time >= 0)
