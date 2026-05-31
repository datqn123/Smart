# Suppliers Table

## 📋 Overview

**Purpose**: Manage supplier information  
**Use Cases**: UC7, UC8, UC12  
**Group**: Partners & Finance

---

## 📊 Schema

| Column | Data Type | Constraint | Default | Description |
|--------|-----------|------------|---------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto | Auto-increment primary key |
| `supplier_code` | VARCHAR(50) | NOT NULL, UNIQUE | - | Unique supplier code (e.g., NCC0001) |
| `name` | VARCHAR(255) | NOT NULL | - | Supplier name |
| `contact_person` | VARCHAR(255) | NULL | - | Contact person |
| `phone` | VARCHAR(20) | NULL | - | Phone number |
| `email` | VARCHAR(255) | NULL | - | Contact email |
| `address` | TEXT | NULL | - | Address |
| `tax_code` | VARCHAR(50) | NULL | - | Tax code |
| `status` | VARCHAR(20) | CHECK (Active/Inactive) | 'Active' | Status |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Update timestamp |

---

## 🔗 Relationships

| Relation | Table | Type | ON DELETE |
|----------|-------|------|-----------|
| 1 → N | StockReceipts | Parent | RESTRICT (cannot delete when receipts exist) |

---

## 📝 Business Rules

1. `supplier_code` must be unique, format: NCC + 4 digits
2. Cannot delete supplier when related receipts exist
3. `tax_code` used for tax reporting

---

## 📦 TypeScript Interface

```typescript
interface Supplier {
  id: number;
  supplierCode: string; // NCC0001
  name: string;
  contactPerson?: string;
  phone?: string;
  email?: string;
  address?: string;
  taxCode?: string;
  status: "Active" | "Inactive";
  createdAt: Date;
  updatedAt: Date;

  // Relations
  receipts?: StockReceipt[];
}
```

---

## 🔍 Indexes

- `idx_suppliers_name` ON `name`
- `idx_suppliers_phone` ON `phone`
- Implicit UNIQUE on `supplier_code`
