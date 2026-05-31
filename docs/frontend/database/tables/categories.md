# Categories Table

## 📋 Overview

**Purpose**: Hierarchical product categorization  
**Use Cases**: UC6, UC8  
**Group**: Categories & Products

---

## 📊 Schema

| Column | Data Type | Constraint | Default | Description |
|--------|-----------|------------|---------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto | Auto-increment primary key |
| `category_code` | VARCHAR(50) | NOT NULL, UNIQUE | - | Unique category code (e.g., CAT001) |
| `name` | VARCHAR(255) | NOT NULL | - | Category name |
| `description` | TEXT | NULL | - | Detailed description |
| `parent_id` | INT | FK → Categories(id) | NULL | Parent category ID (hierarchical) |
| `sort_order` | INT | NOT NULL | 0 | Display order |
| `status` | VARCHAR(20) | CHECK (Active/Inactive) | 'Active' | Status |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Update timestamp |

---

## 🔗 Relationships

| Relation | Table | Type | ON DELETE |
|----------|-------|------|-----------|
| Self-ref | Categories | Parent | SET NULL (delete parent → children become root) |
| 1 → N | Products | Parent | SET NULL (delete category → products unassigned) |

---

## 📝 Business Rules

1. `parent_id = NULL` → root category
2. No circular references allowed (A → B → A)
3. `sort_order` used for display ordering

---

## 📦 TypeScript Interface

```typescript
interface Category {
  id: number;
  categoryCode: string; // CAT001
  name: string;
  description?: string;
  parentId?: number; // FK → Category (self-reference)
  sortOrder: number;
  status: "Active" | "Inactive";
  createdAt: Date;
  updatedAt: Date;

  // Relations
  parent?: Category;
  children?: Category[];
  products?: Product[];
}
```

---

## 💾 Example Data

```sql
INSERT INTO Categories (category_code, name, parent_id, sort_order) VALUES
('CAT001', 'Food Products', NULL, 1),
('CAT001-01', 'Dry Food', 1, 1),
('CAT001-02', 'Beverages', 1, 2);
```
