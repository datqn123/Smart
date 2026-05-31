# Products Table

## 📋 Overview

**Purpose**: Product catalog management  
**Use Cases**: UC1, UC6, UC7, UC8, UC9, UC10, UC11, UC12, UC13  
**Group**: Categories & Products

---

## 📊 Schema

| Column        | Data Type    | Constraint              | Default           | Description                |
| ------------- | ------------ | ----------------------- | ----------------- | -------------------------- |
| `id`          | SERIAL       | PRIMARY KEY             | Auto              | Auto-increment primary key |
| `category_id` | INT          | FK → Categories(id)     | NULL              | Category                   |
| `sku_code`    | VARCHAR(50)  | NOT NULL, UNIQUE        | -                 | Internal SKU code          |
| `barcode`     | VARCHAR(100) | NULL                    | -                 | Barcode                    |
| `name`        | VARCHAR(255) | NOT NULL                | -                 | Product name               |
| `image_url`   | VARCHAR(500) | NULL                    | -                 | Image URL (legacy)         |
| `description` | TEXT         | NULL                    | -                 | Detailed description       |
| `weight`      | DECIMAL(6,2) | NULL                    | -                 | Weight (kilograms)         |
| `status`      | VARCHAR(20)  | CHECK (Active/Inactive) | 'Active'          | Business status            |
| `created_at`  | TIMESTAMP    | NOT NULL                | CURRENT_TIMESTAMP | Creation timestamp         |
| `updated_at`  | TIMESTAMP    | NOT NULL                | CURRENT_TIMESTAMP | Update timestamp           |

---

## 🔗 Relationships

| Relation | Table               | Type   | ON DELETE |
| -------- | ------------------- | ------ | --------- |
| N → 1    | Categories          | Child  | SET NULL  |
| 1 → N    | ProductUnits        | Parent | CASCADE   |
| 1 → N    | ProductPriceHistory | Parent | CASCADE   |
| 1 → N    | Inventory           | Parent | CASCADE   |
| 1 → N    | StockReceiptDetails | Parent | RESTRICT  |
| 1 → N    | OrderDetails        | Parent | RESTRICT  |
| 1 → N    | InventoryLogs       | Parent | RESTRICT  |

---

## 📝 Business Rules

1. `sku_code` must be unique system-wide
2. `barcode` can be duplicated (multiple products may share manufacturer barcode)
3. `status = 'Inactive'` → cannot sell/receive new stock
4. `weight` used for shipping cost calculation

---

## 📦 TypeScript Interface

```typescript
interface Product {
  id: number;
  categoryId?: number; // FK → Category
  skuCode: string; // unique
  barcode?: string;
  name: string;
  imageUrl?: string; // Legacy URL (primary image)
  description?: string;
  weight?: number; // grams
  status: "Active" | "Inactive";
  createdAt: Date;
  updatedAt: Date;

  // Relations
  category?: Category;
  images?: ProductImage[]; // Multiple product images
  units?: ProductUnit[];
  priceHistory?: ProductPriceHistory[];
  inventories?: Inventory[];

  // Computed
  currentStock?: number; // SUM(Inventory.quantity)
  primaryImage?: ProductImage;
  currentPrice?: ProductPriceHistory;
}
```

---

## 🔍 Indexes

- `idx_products_sku` ON `sku_code`
- `idx_products_barcode` ON `barcode`
- `idx_products_name` ON `name`
- `idx_products_status` ON `status`
- `idx_products_category` ON `category_id` (recommended)
- Implicit UNIQUE on `sku_code`
