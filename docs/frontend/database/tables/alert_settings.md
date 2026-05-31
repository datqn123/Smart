# AlertSettings Table

## 📋 Overview

**Purpose**: Alert configuration per user  
**Use Cases**: UC5  
**Group**: Admin & Users

---

## 📊 Schema

| Column | Data Type | Constraint | Default | Description |
|--------|-----------|------------|---------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto | Auto-increment primary key |
| `owner_id` | INT | NOT NULL, FK → Users(id) | - | User who owns this setting |
| `alert_type` | VARCHAR(30) | NOT NULL, CHECK (LowStock/ExpiryDate/HighValueTransaction/PendingApproval) | - | Alert type |
| `threshold_value` | DECIMAL(10,2) | NULL | - | Threshold value |
| `channel` | VARCHAR(20) | NOT NULL, CHECK (App/Email/SMS/Zalo) | - | Notification channel |
| `frequency` | VARCHAR(20) | NOT NULL, CHECK (Realtime/Daily/Weekly) | 'Realtime' | Notification frequency |
| `is_enabled` | BOOLEAN | NOT NULL | TRUE | Is enabled |
| `recipients` | JSONB | NULL | - | Additional recipients |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Update timestamp |

---

## 🔗 Relationships

| Relation | Table | Type | ON DELETE |
|----------|-------|------|-----------|
| N → 1 | Users | Child | CASCADE |

---

## 📝 Business Rules

1. Each user can have multiple alert settings
2. `recipients` is JSON array of user IDs
3. Deleting user cascades to delete their alert settings

---

## 📦 TypeScript Interface

```typescript
interface AlertSetting {
  id: number;
  ownerId: number; // FK → User
  alertType:
    | "LowStock"
    | "ExpiryDate"
    | "HighValueTransaction"
    | "PendingApproval";
  thresholdValue?: number;
  channel: "App" | "Email" | "SMS" | "Zalo";
  frequency: "Realtime" | "Daily" | "Weekly";
  isEnabled: boolean;
  recipients?: string[]; // user IDs
  createdAt: Date;
  updatedAt: Date;

  // Relations
  owner?: User;
}
```

---

## 🔍 Indexes

- `idx_alert_owner` ON `owner_id`
