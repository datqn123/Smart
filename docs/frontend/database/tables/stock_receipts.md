# StockReceipts Table

## 📋 Overview

**Purpose**: Stock receipts (incoming goods)  
**Use Cases**: UC4, UC7, UC12  
**Group**: Warehouse & Transactions

---

## 📊 Schema

| Column | Data Type | Constraint | Default | Description |
|--------|-----------|------------|---------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto | Auto-increment primary key |
| `receipt_code` | VARCHAR(50) | NOT NULL, UNIQUE | - | Receipt code (e.g., PN-2026-0001) |
| `supplier_id` | INT | NOT NULL, FK → Suppliers(id) | - | Supplier reference |
| `staff_id` | INT | NOT NULL, FK → Users(id) | - | Staff who created |
| `receipt_date` | DATE | NOT NULL | - | Receipt date |
| `status` | VARCHAR(20) | NOT NULL, CHECK (Draft/Pending/Approved/Rejected) | 'Draft' | Status |
| `invoice_number` | VARCHAR(100) | NULL | - | Invoice number |
| `total_amount` | DECIMAL(10,2) | NOT NULL, CHECK (>= 0) | 0 | Total amount |
| `notes` | TEXT | NULL | - | Notes |
| `approved_by` | INT | NULL, FK → Users(id) | - | Approver |
| `approved_at` | TIMESTAMP | NULL | - | Approval timestamp |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Update timestamp |

---

## 🔗 Relationships

| Relation | Table | Type | ON DELETE |
|----------|-------|------|-----------|
| N → 1 | Suppliers | Child | RESTRICT |
| N → 1 | Users (staff) | Child | RESTRICT |
| N → 1 | Users (approver) | Child | SET NULL |
| 1 → N | StockReceiptDetails | Parent | CASCADE |
| 1 → N | InventoryLogs | Parent | CASCADE |
| 1 → N | MediaAudits | Parent | CASCADE |

---

## 📝 Business Rules

1. Only when `status = 'Approved'` does inventory update and FinanceLedger record
2. `receipt_code` format: PN-YYYY-NNNN
3. Approval workflow: Draft → Pending → Approved/Rejected

---

## 📦 TypeScript Interface

```typescript
interface StockReceipt {
  id: number;
  receiptCode: string; // PN-2026-0001
  supplierId: number; // FK → Supplier
  staffId: number; // FK → User
  receiptDate: Date;
  status: "Draft" | "Pending" | "Approved" | "Rejected";
  invoiceNumber?: string;
  totalAmount: number;
  notes?: string;
  approvedBy?: number; // FK → User
  approvedAt?: Date;
  createdAt: Date;
  updatedAt: Date;

  // Relations
  supplier?: Supplier;
  staff?: User;
  approver?: User;
  details?: StockReceiptDetail[];
  mediaAudits?: MediaAudit[];
}
```

---

## 📈 Status Flow

```
Draft ────> Pending ────> Approved
              │              │
              │              └───> Update Inventory & FinanceLedger
              │
              └───> Rejected
```

---

## 🔍 Indexes

- `idx_sr_supplier` ON `supplier_id`
- `idx_sr_status` ON `status`
