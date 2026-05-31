# StockReceiptDetails Table

## 📋 Overview

**Purpose**: Stock receipt line items  
**Use Cases**: UC7, UC12  
**Group**: Warehouse & Transactions

---

## 📊 Schema

| Column | Data Type | Constraint | Default | Description |
|--------|-----------|------------|---------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto | Auto-increment primary key |
| `receipt_id` | INT | NOT NULL, FK → StockReceipts(id) | - | Receipt reference |
| `product_id` | INT | NOT NULL, FK → Products(id) | - | Product reference |
| `unit_id` | INT | NOT NULL, FK → ProductUnits(id) | - | Unit reference |
| `quantity` | INT | NOT NULL, CHECK (> 0) | - | Quantity |
| `cost_price` | DECIMAL(10,2) | NOT NULL, CHECK (>= 0) | - | Cost price |
| `batch_number` | VARCHAR(100) | NULL | - | Batch number |
| `expiry_date` | DATE | NULL | - | Expiry date |
| `line_total` | DECIMAL(10,2) | GENERATED ALWAYS AS (quantity * cost_price) STORED | - | Auto-calculated total |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |

---

## 🔗 Relationships

| Relation | Table | Type | ON DELETE |
|----------|-------|------|-----------|
| N → 1 | StockReceipts | Child | CASCADE |
| N → 1 | Products | Child | RESTRICT |
| N → 1 | ProductUnits | Child | RESTRICT |

---

## 📝 Business Rules

1. `line_total` auto-calculated: quantity × cost_price
2. UNIQUE: (receipt_id, product_id, batch_number)
3. Each detail line represents one product batch in the receipt

---

## 📦 TypeScript Interface

```typescript
interface StockReceiptDetail {
  id: number;
  receiptId: number; // FK → StockReceipt
  productId: number; // FK → Product
  unitId: number; // FK → ProductUnit
  quantity: number;
  costPrice: number;
  batchNumber?: string;
  expiryDate?: Date;
  lineTotal: number; // auto: quantity * costPrice
  createdAt: Date;

  // Relations
  receipt?: StockReceipt;
  product?: Product;
  unit?: ProductUnit;
}
```

---

## 🔍 Indexes

- `idx_srd_receipt` ON `receipt_id`

---

## ⚠️ Constraints

- `uq_srd_receipt_product_batch`: UNIQUE (receipt_id, product_id, batch_number)
- `chk_quantity_positive`: CHECK (quantity > 0)
- `chk_cost_price_non_negative`: CHECK (cost_price >= 0)
