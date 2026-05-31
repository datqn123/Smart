# AIInsights Table

## 📋 Overview

**Purpose**: AI business insights history  
**Use Cases**: UC1, UC2  
**Group**: AI & Media

---

## 📊 Schema

| Column               | Data Type    | Constraint               | Default           | Description                              |
| -------------------- | ------------ | ------------------------ | ----------------- | ---------------------------------------- |
| `id`                 | BIGSERIAL    | PRIMARY KEY              | Auto              | Auto-increment primary key               |
| `owner_id`           | INT          | NOT NULL, FK → Users(id) | -                 | User who requested analysis              |
| `dashboard_snapshot` | JSONB        | NOT NULL                 | -                 | Dashboard snapshot JSON at analysis time |
| `prompt`             | TEXT         | NOT NULL                 | -                 | User prompt                              |
| `ai_advice`          | TEXT         | NOT NULL                 | -                 | AI advice in Markdown format             |
| `model_used`         | VARCHAR(100) | NULL                     | -                 | AI model used                            |
| `tokens_used`        | INT          | NULL                     | -                 | Token count                              |
| `created_at`         | TIMESTAMP    | NOT NULL                 | CURRENT_TIMESTAMP | Creation timestamp                       |

---

## 🔗 Relationships

| Relation | Table | Type  | ON DELETE |
| -------- | ----- | ----- | --------- |
| N → 1    | Users | Child | CASCADE   |

---

## 📝 Business Rules

1. `dashboard_snapshot` stores context at time of analysis
2. `ai_advice` in Markdown format
3. Deleting user cascades to delete their insights

---

## 📦 TypeScript Interface

```typescript
interface AIInsight {
  id: number;
  ownerId: number; // FK → User
  dashboardSnapshot: DashboardData;
  prompt: string;
  aiAdvice: string; // Markdown
  modelUsed?: string;
  tokensUsed?: number;
  createdAt: Date;

  // Relations
  owner?: User;
}

interface DashboardData {
  dateRange: string;
  totalRevenue: number;
  totalExpenses: number;
  inventoryValue: number;
  lowStockItems: number;
  expiringSoon: number;
  topProducts: string[];
}
```

---

## 🔍 Indexes

- `idx_ai_insight_owner` ON `owner_id`
