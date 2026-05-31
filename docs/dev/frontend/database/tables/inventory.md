# Inventory Table

## 📋 Overview

**Purpose**: Physical inventory tracking  
**Use Cases**: UC1, UC4, UC6, UC9, UC10  
**Group**: Warehouse & Transactions

---

## 📊 Schema

| Column | Data Type | Constraint | Default | Description |
|--------|-----------|------------|---------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto | Auto-increment primary key |
| `product_id` | INT | NOT NULL, FK → Products(id) | - | Product reference |
| `location_id` | INT | NOT NULL, FK → WarehouseLocations(id) | - | Location reference |
| `batch_number` | VARCHAR(100) | NULL | - | Batch number |
| `expiry_date` | DATE | NULL | - | Expiry date |
| `quantity` | INT | NOT NULL, CHECK (>= 0) | 0 | Quantity (in base unit) |
| `min_quantity` | INT | NOT NULL | 0 | Minimum quantity (low stock threshold) |
| `updated_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Update timestamp |

---

## 🔗 Relationships

| Relation | Table | Type | ON DELETE |
|----------|-------|------|-----------|
| N → 1 | Products | Child | CASCADE |
| N → 1 | WarehouseLocations | Child | RESTRICT |

---

## 📝 Business Rules

1. `quantity` always stored in base unit
2. `min_quantity` triggers LowStock alert when quantity falls below
3. UNIQUE: (product_id, location_id, batch_number)

---

## 📦 TypeScript Interface

```typescript
interface Inventory {
  id: number;
  productId: number; // FK → Product
  locationId: number; // FK → WarehouseLocation
  batchNumber?: string;
  expiryDate?: Date;
  quantity: number; // in base unit, >= 0
  minQuantity: number; // alert threshold
  updatedAt: Date;

  // Computed
  isLowStock?: boolean; // quantity <= minQuantity
  isExpiringSoon?: boolean; // expiryDate <= now + 30 days

  // Relations
  product?: Product;
  location?: WarehouseLocation;
}
```

---

## 🔍 Indexes

- `idx_inv_product` ON `product_id`
- `idx_inv_expiry_date` ON `expiry_date`

---

## ⚠️ Constraints

- `uq_inventory_product_location_batch`: UNIQUE (product_id, location_id, batch_number)
- `chk_quantity_non_negative`: CHECK (quantity >= 0)
