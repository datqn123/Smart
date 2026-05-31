# Notifications Table (Optional)

## 📋 Overview

**Purpose**: User notifications  
**Use Cases**: UC4  
**Group**: Optional

---

## 📊 Schema

| Column | Data Type | Constraint | Default | Description |
|--------|-----------|------------|---------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto | Auto-increment primary key |
| `user_id` | INT | NOT NULL, FK → Users(id) | - | User who receives notification |
| `notification_type` | VARCHAR(30) | NOT NULL, CHECK (ApprovalResult/LowStock/ExpiryWarning/SystemAlert) | - | Notification type |
| `title` | VARCHAR(255) | NOT NULL | - | Notification title |
| `message` | TEXT | NOT NULL | - | Notification message |
| `is_read` | BOOLEAN | NOT NULL | FALSE | Read status |
| `reference_type` | VARCHAR(50) | NULL | - | Related entity type |
| `reference_id` | INT | NULL | - | Related entity ID |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |
| `read_at` | TIMESTAMP | NULL | - | Read timestamp |

---

## 🔗 Relationships

| Relation | Table | Type | ON DELETE |
|----------|-------|------|-----------|
| N → 1 | Users | Child | CASCADE |

---

## 📝 Business Rules

1. Deleting user cascades to delete their notifications
2. `reference_type` + `reference_id` links to related entity
3. `is_read` tracks notification read status

---

## 📦 TypeScript Interface

```typescript
interface Notification {
  id: number;
  userId: number; // FK → User
  notificationType:
    | "ApprovalResult"
    | "LowStock"
    | "ExpiryWarning"
    | "SystemAlert";
  title: string;
  message: string;
  isRead: boolean;
  referenceType?: string;
  referenceId?: number;
  createdAt: Date;
  readAt?: Date;

  // Relations
  user?: User;
}
```

---

## 🔍 Indexes

- `idx_notif_user_unread` ON (user_id, is_read) - Composite index for unread notifications
- `idx_notif_reference` ON (reference_type, reference_id) - Composite index for related notifications
