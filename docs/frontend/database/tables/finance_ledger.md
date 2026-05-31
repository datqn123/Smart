# FinanceLedger Table

## 📋 Overview

**Purpose**: Financial transaction ledger  
**Use Cases**: UC1, UC4  
**Group**: Partners & Finance

---

## 📊 Schema

| Column | Data Type | Constraint | Default | Description |
|--------|-----------|------------|---------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto | Auto-increment primary key |
| `transaction_date` | DATE | NOT NULL | - | Transaction date |
| `transaction_type` | VARCHAR(30) | NOT NULL, CHECK (SalesRevenue/PurchaseCost/OperatingExpense/Refund) | - | Transaction type |
| `reference_type` | VARCHAR(50) | NULL | - | Reference type (polymorphic) |
| `reference_id` | INT | NOT NULL | - | Reference ID (polymorphic) |
| `amount` | DECIMAL(10,2) | NOT NULL | - | Amount (+ revenue, - expense) |
| `description` | TEXT | NULL | - | Description |
| `created_by` | INT | NOT NULL, FK → Users(id) | - | User who created |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Update timestamp |

---

## 🔗 Relationships

| Relation | Table | Type | ON DELETE |
|----------|-------|------|-----------|
| N → 1 | Users (created_by) | Child | RESTRICT |

---

## 📝 Business Rules

1. `reference_type` + `reference_id` is polymorphic FK (validated at application layer)
2. Positive amount = revenue, negative = expense
3. Cannot delete user who created financial records
4. Records are immutable after creation (application logic)

---

## 📦 TypeScript Interface

```typescript
interface FinanceLedger {
  id: number;
  transactionDate: Date;
  transactionType:
    | "SalesRevenue"
    | "PurchaseCost"
    | "OperatingExpense"
    | "Refund";
  referenceType?: string; // 'SalesOrder', 'StockReceipt'
  referenceId?: number; // Document ID
  amount: number; // + revenue, - expense
  description?: string;
  createdBy: number; // FK → User
  createdAt: Date;
  updatedAt: Date;

  // Relations
  creator?: User;
}
```

---

## 💡 Polymorphic Reference Examples

```
reference_type = 'SalesOrder', reference_id = 123 → SalesOrders table
reference_type = 'StockReceipt', reference_id = 456 → StockReceipts table
```

---

## 🔍 Indexes

- `idx_finance_date` ON `transaction_date`
- `idx_finance_type` ON `transaction_type`
