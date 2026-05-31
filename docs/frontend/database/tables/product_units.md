# ProductUnits Table

## 📋 Overview

**Purpose**: Define different units of measurement for the same product  
**Use Cases**: UC6, UC7, UC8, UC9, UC10, UC13  
**Group**: Categories & Products

---

## 📊 Schema

| Column | Data Type | Constraint | Default | Description |
|--------|-----------|------------|---------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto | Auto-increment primary key |
| `product_id` | INT | NOT NULL, FK → Products(id) | - | Product reference |
| `unit_name` | VARCHAR(50) | NOT NULL | - | Unit name (Box, Pack, Piece) |
| `conversion_rate` | DECIMAL(10,4) | NOT NULL, CHECK (> 0) | - | Conversion rate |
| `is_base_unit` | BOOLEAN | NOT NULL | FALSE | Is base unit |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Update timestamp |

---

## 🔗 Relationships

| Relation | Table | Type | ON DELETE |
|----------|-------|------|-----------|
| N → 1 | Products | Child | CASCADE |
| 1 → N | ProductPriceHistory | Parent | CASCADE |
| 1 → N | StockReceiptDetails | Parent | RESTRICT |
| 1 → N | OrderDetails | Parent | RESTRICT |
| 1 → N | InventoryLogs | Parent | RESTRICT |

---

## 📝 Business Rules

1. **Each product has EXACTLY 1 row with `is_base_unit = TRUE`**
2. `conversion_rate` = number of base units in 1 unit
3. Example: 1 Box = 24 Pieces → conversion_rate = 24
4. `Inventory.quantity` ALWAYS stored in base unit

---

## 💡 Unit Conversion Logic

```
Receive 1 Box (conversion_rate = 24):
→ Inventory.quantity += 1 * 24 = 24 (base units)

Sell 1 Pack (conversion_rate = 6):
→ Inventory.quantity -= 1 * 6 = 6 (base units)
```

---

## 📦 TypeScript Interface

```typescript
interface ProductUnit {
  id: number;
  productId: number; // FK → Product
  unitName: string; // Box, Pack, Piece
  conversionRate: number; // > 0
  isBaseUnit: boolean; // EXACTLY 1 per product
  createdAt: Date;
  updatedAt: Date;

  // Relations
  product?: Product;
}
```

---

## 💾 Example Data

```sql
INSERT INTO ProductUnits (product_id, unit_name, conversion_rate, is_base_unit) VALUES
(1, 'Piece', 1, TRUE),       -- Base unit
(1, 'Pack', 12, FALSE),     -- 1 Pack = 12 Pieces
(1, 'Box', 120, FALSE);     -- 1 Box = 120 Pieces
```

---

## 🔍 Indexes

- `idx_pu_product` ON `product_id`
- Implicit UNIQUE on (product_id, unit_name)

---

## ⚠️ Constraints

- `uq_product_unit_name`: UNIQUE (product_id, unit_name)
- `chk_conversion_rate`: CHECK (conversion_rate > 0)
