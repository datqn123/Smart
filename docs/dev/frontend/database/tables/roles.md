# Roles Table

## 📋 Overview

**Purpose**: Define user roles and permissions in the system  
**Use Cases**: UC3 (Manage Staff Accounts)  
**Group**: Admin & Users

---

## 📊 Schema

| Column | Data Type | Constraint | Default | Description |
|--------|-----------|------------|---------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto | Auto-increment primary key |
| `name` | VARCHAR(50) | NOT NULL, UNIQUE | - | Role name: Owner, Staff, Admin |
| `permissions` | JSONB | NOT NULL | `'{}'` | Detailed permissions JSON |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |

---

## 🔗 Relationships

| Relation | Table | Type | ON DELETE |
|----------|-------|------|-----------|
| 1 → N | Users | Parent | RESTRICT (cannot delete when users exist) |

---

## 💡 Permissions JSON Structure

```json
{
  "can_view_dashboard": true,
  "can_manage_staff": true,
  "can_approve": true,
  "can_configure_alerts": true,
  "can_view_finance": true,
  "can_manage_products": true,
  "can_manage_inventory": true,
  "can_manage_orders": true,
  "can_use_ai": true
}
```

---

## 📝 Business Rules

1. Must have at least 1 role as "Owner"
2. `permissions` JSON must be valid
3. Cannot delete role when users are using it

---

## 📦 TypeScript Interface

```typescript
interface Role {
  id: number;
  name: "Owner" | "Staff" | "Admin";
  permissions: RolePermissions;
  createdAt: Date;
}

interface RolePermissions {
  can_view_dashboard: boolean;
  can_manage_staff: boolean;
  can_approve: boolean;
  can_configure_alerts: boolean;
  can_view_finance: boolean;
  can_manage_products: boolean;
  can_manage_inventory: boolean;
  can_manage_orders: boolean;
  can_use_ai: boolean;
}
```

---

## 💾 Example Data

```sql
INSERT INTO Roles (name, permissions) VALUES
('Owner', '{"can_approve": true, "can_manage_staff": true}'),
('Staff', '{"can_manage_products": true, "can_manage_inventory": true}');
```
