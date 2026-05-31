# AIChatHistory Table

## 📋 Overview

**Purpose**: AI chatbot interaction history  
**Use Cases**: UC2, UC11  
**Group**: AI & Media

---

## 📊 Schema

| Column | Data Type | Constraint | Default | Description |
|--------|-----------|------------|---------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto | Auto-increment primary key |
| `user_id` | INT | NOT NULL, FK → Users(id) | - | User who chatted |
| `session_id` | VARCHAR(100) | NULL | - | Session identifier |
| `message` | TEXT | NOT NULL | - | Message content |
| `sender` | VARCHAR(10) | NOT NULL, CHECK (User/Bot) | - | Message sender |
| `intent` | JSONB | NULL | - | Recognized intent |
| `response_time_ms` | INT | NULL | - | Response time in ms |
| `created_at` | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |

---

## 🔗 Relationships

| Relation | Table | Type | ON DELETE |
|----------|-------|------|-----------|
| N → 1 | Users | Child | CASCADE |

---

## 📝 Business Rules

1. Consider partitioning by month due to rapid data growth
2. `intent` stores recognized user intent as JSON
3. Deleting user cascades to delete their chat history

---

## 📦 TypeScript Interface

```typescript
interface AIChatHistory {
  id: number;
  userId: number; // FK → User
  sessionId?: string;
  message: string;
  sender: "User" | "Bot";
  intent?: ChatIntent;
  responseTimeMs?: number;
  createdAt: Date;

  // Relations
  user?: User;
}

interface ChatIntent {
  action: string; // 'check_stock', 'create_order', etc.
  product?: string;
  location?: string;
  unit?: string;
  [key: string]: any;
}
```

---

## 💡 Intent JSON Example

```json
{
  "action": "check_stock",
  "product": "Condensed Milk",
  "location": "A1",
  "unit": "Box"
}
```

---

## 🔍 Indexes

- `idx_chat_user` ON `user_id`
- `idx_chat_session` ON `session_id`
- `idx_chat_created_at` ON `created_at`
