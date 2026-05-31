# Users Table

## 📋 Overview

**Purpose**: User accounts and authentication  
**Use Cases**: UC1-UC13 (all)  
**Group**: Admin & Users

---

## 📊 Schema

| Column | Data Type | Constraint | Default | Description |
|--------|-----------|------------|---------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto | Auto-increment primary key |
| `username` | VARCHAR(100) | NOT NULL, UNIQUE | - | Login username |
| `password_hash` | VARCHAR(255) | NOT NULL | - | Bcrypt/argon2 hashed password |
| `full_name` | VARCHAR(255) | NOT NULL | - | Full name |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE | - | Email address |
| `phone` | VARCHAR(20) | NULL | - | Phone number |
| `role_id` | INT | NOT NULL, FK → Roles(id) | - | Role assignment |
| `status` | VARCHAR(20) | CHECK (Active/Locked) | 'Active' | Account status |
| `last_login` | TIMESTAMP | NULL | - | Last login timestamp |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Update timestamp |

---

## 🔗 Relationships

| Relation | Table | Type | ON DELETE |
|----------|-------|------|-----------|
| N → 1 | Roles | Child | RESTRICT |
| 1 → N | AlertSettings | Parent | CASCADE |
| 1 → N | SystemLogs | Parent | SET NULL |
| 1 → N | FinanceLedger (created_by) | Parent | RESTRICT |
| 1 → N | AIInsights | Parent | CASCADE |
| 1 → N | AIChatHistory | Parent | CASCADE |
| 1 → N | MediaAudits (uploaded_by) | Parent | SET NULL |
| 1 → N | StockReceipts (staff_id) | Parent | RESTRICT |
| 1 → N | StockReceipts (approved_by) | Parent | SET NULL |
| 1 → N | SalesOrders (user_id) | Parent | RESTRICT |
| 1 → N | SalesOrders (cancelled_by) | Parent | SET NULL |
| 1 → N | StockDispatches | Parent | RESTRICT |
| 1 → N | InventoryLogs | Parent | SET NULL |
| 1 → N | Notifications | Parent | CASCADE |

---

## 📝 Business Rules

1. `username` and `email` must be unique
2. `password_hash` must use bcrypt or argon2 (NEVER store plaintext)
3. `status = 'Locked'` → cannot login
4. `last_login` updates on each successful login

---

## 🔐 Security Notes

- Password must be hashed before storing
- Use bcrypt with cost >= 10 or argon2id
- NEVER use MD5 or SHA1

---

## 📦 TypeScript Interface

```typescript
interface User {
  id: number;
  username: string;
  passwordHash: string; // NEVER return to frontend
  fullName: string;
  email: string;
  phone?: string;
  roleId: number; // FK → Role
  status: "Active" | "Locked";
  lastLogin?: Date;
  createdAt: Date;
  updatedAt: Date;

  // Relations (loaded when needed)
  role?: Role;
  alertSettings?: AlertSetting[];
  createdReceipts?: StockReceipt[];
  approvedReceipts?: StockReceipt[];
  createdOrders?: SalesOrder[];
  dispatchedOrders?: StockDispatch[];
}
```

---

## 🔍 Indexes

- Implicit UNIQUE on `username`, `email`
- `idx_users_phone` ON `phone`
