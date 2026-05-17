## 1. Architecture Overview

### Technology Stack

| Tier | Technology |
|------|-----------|
| **Frontend** | React 19 + TypeScript + Vite + TanStack Query + Zustand + Radix UI + TailwindCSS |
| **Backend** | Spring Boot 3.5.14 + Java 21 + PostgreSQL + Flyway + JWT Auth + Redis |
| **AI Service** | Python FastAPI + LangGraph + LangChain + OpenAI-compatible LLM |

### General Data Flow

```
User → React Frontend (Vite dev server)
        ↓ HTTP/REST (JSON envelope: {success, data})
     Spring Boot Backend (port 8080)
        ↓ JDBC / JPA
     PostgreSQL Database
        ↓
     JSON Response → Frontend render
```

### AI Chat Flow

```
User → React Frontend
        ↓ SSE POST /api/v1/ai/chat/stream
     Spring Boot (relay)
        ↓ HTTP forward (same Bearer token)
     Python FastAPI (port 9000)
        ↓ LangGraph → LLM + SQL execution (calls back Spring JDBC)
     SSE events (delta/chart/draft/done/error)
        ↓
     Frontend renders text / charts / tables
```

### Response Envelope (Spring Boot)

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional"
}
```

**Error:**
```json
{
  "success": false,
  "error": "BAD_REQUEST | UNAUTHORIZED | FORBIDDEN | NOT_FOUND | CONFLICT | UNPROCESSABLE_ENTITY | TOO_MANY_REQUESTS | INTERNAL_SERVER_ERROR",
  "message": "Vietnamese error description",
  "details": { "fieldName": "Error detail" }
}
```

---