# ProductPriceHistory Table

## 📋 Overview

**Purpose**: Track cost price and sale price changes over time  
**Use Cases**: UC1, UC8  
**Group**: Categories & Products

---

## 📊 Schema

| Column           | Data Type     | Constraint                      | Default           | Description                |
| ---------------- | ------------- | ------------------------------- | ----------------- | -------------------------- |
| `id`             | SERIAL        | PRIMARY KEY                     | Auto              | Auto-increment primary key |
| `product_id`     | INT           | NOT NULL, FK → Products(id)     | -                 | Product reference          |
| `unit_id`        | INT           | NOT NULL, FK → ProductUnits(id) | -                 | Unit reference             |
| `cost_price`     | DECIMAL(15,2) | NOT NULL, CHECK (>= 0)          | -                 | Cost price                 |
| `sale_price`     | DECIMAL(15,2) | NOT NULL, CHECK (>= 0)          | -                 | Sale price                 |
| `effective_date` | DATE          | NOT NULL                        | -                 | Effective date             |
| `created_at`     | TIMESTAMP     | NOT NULL                        | CURRENT_TIMESTAMP | Recording timestamp        |

---

## 🔗 Relationships

| Relation | Table        | Type  | ON DELETE |
| -------- | ------------ | ----- | --------- |
| N → 1    | Products     | Child | CASCADE   |
| N → 1    | ProductUnits | Child | CASCADE   |

---

## 📝 Business Rules

1. `cost_price` used for accurate profit calculation
2. `sale_price` is the listed price, can be changed
3. When querying price at time X, get row with nearest `effective_date` <= X

---

## 📦 TypeScript Interface

```typescript
interface ProductPriceHistory {
  id: number;
  productId: number; // FK → Product
  unitId: number; // FK → ProductUnit
  costPrice: number; // cost price
  salePrice: number; // sale price
  effectiveDate: Date; // effective date
  createdAt: Date;

  // Relations
  product?: Product;
  unit?: ProductUnit;
}
```

---

## 💡 Query Current Price

```sql
SELECT cost_price, sale_price
FROM ProductPriceHistory
WHERE product_id = ? AND unit_id = ?
  AND effective_date <= CURRENT_DATE
ORDER BY effective_date DESC
LIMIT 1;
```

---

## 🔍 Indexes

- `idx_price_lookup` ON (product_id, unit_id, effective_date DESC)
