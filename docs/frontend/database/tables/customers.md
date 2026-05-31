# Customers Table

## 📋 Overview

**Purpose**: Manage customer information  
**Use Cases**: UC9  
**Group**: Partners & Finance

---

## 📊 Schema

| Column | Data Type | Constraint | Default | Description |
|--------|-----------|------------|---------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto | Auto-increment primary key |
| `customer_code` | VARCHAR(50) | NOT NULL, UNIQUE | - | Unique customer code (e.g., KH00001) |
| `name` | VARCHAR(255) | NOT NULL | - | Customer name |
| `phone` | VARCHAR(20) | NOT NULL | - | Phone number |
| `email` | VARCHAR(255) | NULL | - | Email address |
| `address` | TEXT | NULL | - | Shipping address |
| `loyalty_points` | INT | NOT NULL | 0 | Loyalty points |
| `status` | VARCHAR(20) | CHECK (Active/Inactive) | 'Active' | Status |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Update timestamp |

---

## 🔗 Relationships

| Relation | Table | Type | ON DELETE |
|----------|-------|------|-----------|
| 1 → N | SalesOrders | Parent | RESTRICT (cannot delete when orders exist) |

---

## 📝 Business Rules

1. `phone` is NOT NULL - used for quick lookup
2. `loyalty_points` calculated automatically from order history
3. **Do NOT store `total_spent`** → calculate via `SUM(SalesOrders.total_amount)` for consistency

---

## 📦 TypeScript Interface

```typescript
interface Customer {
  id: number;
  customerCode: string; // KH00001
  name: string;
  phone: string;
  email?: string;
  address?: string;
  loyaltyPoints: number;
  status: "Active" | "Inactive";
  createdAt: Date;
  updatedAt: Date;

  // Computed (not stored in DB)
  totalSpent?: number; // SUM(SalesOrder.totalAmount)
  orderCount?: number;

  // Relations
  orders?: SalesOrder[];
}
```

---

## 💡 Query to Calculate Total Spent

```sql
SELECT c.id, c.name,
       COALESCE(SUM(so.total_amount), 0) as total_spent
FROM Customers c
LEFT JOIN SalesOrders so ON c.id = so.customer_id
  AND so.status != 'Cancelled'
WHERE c.id = ?
GROUP BY c.id, c.name;
```

---

## 🔍 Indexes

- `idx_customers_phone` ON `phone`
- Implicit UNIQUE on `customer_code`
