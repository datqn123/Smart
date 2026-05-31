# SystemLogs Table

## 📋 Overview

**Purpose**: System logging and error tracking  
**Use Cases**: UC4, UC6  
**Group**: Admin & Users

---

## 📊 Schema

| Column | Data Type | Constraint | Default | Description |
|--------|-----------|------------|---------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto | Auto-increment primary key |
| `log_level` | VARCHAR(20) | NOT NULL, CHECK (INFO/WARNING/ERROR/CRITICAL) | - | Log level |
| `module` | VARCHAR(100) | NOT NULL | - | Module name |
| `action` | VARCHAR(255) | NOT NULL | - | Action performed |
| `user_id` | INT | NULL, FK → Users(id) | - | User who performed action |
| `message` | TEXT | NOT NULL | - | Log message |
| `stack_trace` | TEXT | NULL | - | Stack trace (for errors) |
| `context_data` | JSONB | NULL | - | Additional context data |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |

---

## 🔗 Relationships

| Relation | Table | Type | ON DELETE |
|----------|-------|------|-----------|
| N → 1 | Users | Child | SET NULL |

---

## 📝 Business Rules

1. Consider partitioning by month or archiving after 90 days
2. `context_data` is JSON for flexible additional info
3. Keep logs even when user is deleted (null user_id)

---

## 📦 TypeScript Interface

```typescript
interface SystemLog {
  id: number;
  logLevel: "INFO" | "WARNING" | "ERROR" | "CRITICAL";
  module: string;
  action: string;
  userId?: number; // FK → User
  message: string;
  stackTrace?: string;
  contextData?: Record<string, any>;
  createdAt: Date;

  // Relations
  user?: User;
}
```

---

## 🔍 Indexes

- `idx_syslog_level` ON `log_level`
- `idx_syslog_created_at` ON `created_at`
