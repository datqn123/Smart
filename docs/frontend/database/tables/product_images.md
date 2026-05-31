# ProductImages Table

## 📋 Overview

**Purpose**: Multiple images per product management  
**Use Cases**: UC8, UC12  
**Group**: Categories & Products

---

## 📊 Schema

| Column | Data Type | Constraint | Default | Description |
|--------|-----------|------------|---------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto | Auto-increment primary key |
| `product_id` | INT | NOT NULL, FK → Products(id) | - | Product reference |
| `image_url` | VARCHAR(500) | NOT NULL | - | Image URL on Cloud |
| `alt_text` | VARCHAR(255) | NULL | - | Alt text for SEO |
| `is_primary` | BOOLEAN | NOT NULL | FALSE | Primary image (only 1 TRUE per product) |
| `sort_order` | INT | NOT NULL | 0 | Display order |
| `file_size_bytes` | INT | NULL | - | File size |
| `mime_type` | VARCHAR(100) | NULL | - | MIME type (image/jpeg, image/png) |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |

---

## 🔗 Relationships

| Relation | Table | Type | ON DELETE |
|----------|-------|------|-----------|
| N → 1 | Products | Child | CASCADE |

---

## 📝 Business Rules

1. Each product can have multiple images
2. Only ONE image with `is_primary = true` per product
3. `sort_order` used for display ordering
4. Images stored on Cloud (S3, Firebase, etc.)

---

## 📦 TypeScript Interface

```typescript
interface ProductImage {
  id: number;
  productId: number; // FK → Product
  imageUrl: string; // URL on Cloud
  altText?: string; // SEO description
  isPrimary: boolean; // Primary image (only 1 TRUE per product)
  sortOrder: number; // Display order
  fileSizeBytes?: number; // File size
  mimeType?: string; // image/jpeg, image/png
  createdAt: Date;

  // Relations
  product?: Product;
}
```

---

## 🔍 Indexes

- `idx_pi_product` ON `product_id`
- `idx_pi_primary` ON `product_id, is_primary`
