# Smart ERP - Project Architecture

> Agent: SRS_WRITER  
> Ngày cập nhật: 06/06/2026  
> Mục đích: Tài liệu kiến trúc tổng quan cho toàn bộ dự án Smart ERP.  
> Các agent nên đọc tài liệu này trước khi thực hiện bất kỳ tác vụ nào liên quan đến production code, tests, migrations, runtime config, API contracts, UI behavior, hoặc AI runtime behavior.

## 1. Tổng quan

Smart ERP là hệ thống quản lý doanh nghiệp vừa và nhỏ (ERP), gồm 3 tầng:

| Tầng | Công nghệ | Thư mục |
|------|-----------|---------|
| **Backend** | Java 21, Spring Boot 3.5, PostgreSQL | `backend/smart-erp/` |
| **Frontend** | React 19, Vite, TypeScript, Tailwind CSS | `frontend/mini-erp/` |
| **AI** | Python 3.12, FastAPI, LangGraph | `ai_python/` |

## 2. Backend Architecture

### 2.1. Tech Stack

- **Java 21** với Spring Boot 3.5.14
- **Spring Security** + OAuth2 Resource Server (JWT Bearer)
- **PostgreSQL** với Flyway migrations (55+ migration files)
- **JDBC Template** (`NamedParameterJdbcTemplate`) — không dùng JPA/Hibernate
- **jjwt 0.12.6** cho HS256 token sign/verify
- **Maven** build tool

### 2.2. Package Structure

```
com.example.smart_erp
├── ai/                  # AI relay controllers (chat, catalog draft, inventory draft, db query)
├── auth/                # Authentication, login, refresh, roles, JWT
├── catalog/             # Products, categories, customers, suppliers
├── common/              # Shared API response wrapper, error codes, exception handling
├── config/              # Security configuration, method security, beans
├── custominterface/     # Custom entity/interface builder
├── dashboard/           # Dashboard aggregated API
├── finance/             # Cashflow, cash funds, cash transactions, debts, ledger
├── inventory/           # Inventory stock, stock receipts, stock dispatches, audit, approvals
├── notifications/       # Notifications (password resets, entity dialogs)
├── sales/               # Sales orders, vouchers, POS products, retail stock
├── settings/            # Store profile, system logs, alert settings, table column settings
└── users/               # User management, staff codes
```

### 2.3. Layer Pattern

Mỗi feature package tuân theo pattern:

```
feature/
├── controller/    # REST controller (@RestController, @RequestMapping /api/v1/...)
├── service/       # Business logic (@Service, @Transactional)
├── repository/    # Data access (JdbcTemplate)
├── response/      # Response DTOs (Java records, @JsonInclude)
├── request/       # Request DTOs / bodies (for POST/PUT/PATCH)
└── model/         # Domain models / enums (if needed)
```

### 2.4. API Design Conventions

- **Base path**: `/api/v1/`
- **Response wrapper**: `ApiSuccessResponse<T>` — `{ "success": true, "data": T, "message": "..." }`
- **Error wrapper**: `ApiErrorResponse` — `{ "success": false, "error": { "code": "...", "message": "..." } }`
- **Paginated list**: Response type `*PageData` chứa `items`, `total`, `page`, `limit`
- **Authorization**: `@PreAuthorize("hasAuthority('can_xxx')")` hoặc access policy class
- **JWT extraction**: Mỗi controller có phương thức `requireJwt(Authentication)` riêng
- **Language**: API messages bằng tiếng Việt

### 2.5. Authentication & Authorization

- **Login**: `POST /api/v1/auth/login` → trả về access token + refresh token + user profile
- **Refresh**: `POST /api/v1/auth/refresh`
- **Access token**: HS256 signed JWT, claims chứa `role`, `userId`, `permissions`
- **Permissions**: Đọc từ `roles.permissions` JSONB, map thành `GrantedAuthority` qua `MenuPermissionClaims`
- **Refresh tokens**: Lưu trong DB bảng `refresh_tokens`, có TTL
- **Security modes**: `permit-all` (dev) hoặc `jwt-api` (production), config qua `APP_SECURITY_MODE`

### 2.6. Database Design

- **RDBMS**: PostgreSQL
- **Migrations**: Flyway (55+ files, định danh `V<number>__<description>.sql`)
- **Naming conventions**:
  - Bảng: `snake_case` (vd: `sales_orders`, `inventory_stock`)
  - FK constraint: `fk_<table>_<ref_table>`
  - Column: `snake_case`
- **JSONB columns** dùng cho:
  - `roles.permissions` — menu-level permission flags
  - `users.metadata` — extended user info
- **Key tables**: `users`, `roles`, `products`, `customers`, `suppliers`, `categories`,
  `inventory`, `sales_orders`, `stock_receipts`, `stock_dispatches`,
  `financeledger`, `cash_transactions`, `partner_debts`,
  `notifications`, `approvals`, `system_logs`

## 3. Frontend Architecture

### 3.1. Tech Stack

- **React 19** + TypeScript
- **Vite** build tool
- **Tailwind CSS 4** styling
- **React Router v7** (file-based routing-like via `Routes.tsx`)
- **TanStack React Query v5** — server state management
- **Zustand v5** — client state (auth, sidebar, UI)
- **react-hook-form** + **zod** — form validation
- **recharts** — charts (revenue, analytics)
- **lucide-react** — icons
- **sonner** — toast notifications
- **shadcn/ui** — Radix-based component library

### 3.2. Directory Structure

```
src/
├── App.tsx                    # Root component + router setup
├── components/                # Shared components
│   ├── shared/layout/         # MainLayout, Header, Sidebar
│   └── ui/                    # shadcn/ui components (button, dialog, table, select, etc.)
├── context/                   # React context providers (PageTitleContext)
├── features/                  # Feature-based modules (domain)
│   ├── dashboard/             # Dashboard page + analytics utils
│   ├── inventory/             # Stock, receipts, dispatches, audit
│   ├── orders/                # Sales orders (wholesale, retail, returns)
│   ├── product-management/    # Products, categories, customers, suppliers
│   ├── cashflow/              # Transactions, funds, ledger, debts
│   ├── approvals/             # Pending + history
│   ├── analytics/             # Revenue, top products
│   ├── auth/                  # Login, session, permissions
│   ├── ai/                    # AI chat, catalog draft, inventory draft
│   ├── notifications/         # Notification list + polling
│   ├── custom-builder/        # Custom entity/interface builder
│   └── settings/              # Store profile, employees, logs, alerts, interface
├── lib/                       # Shared utilities
│   ├── api/                   # HTTP client (apiJson), token refresh, mock catalog
│   ├── data-table-layout.ts   # Reusable table layout class constants
│   ├── table-column-settings.ts
│   └── query-provider.tsx     # TanStack Query provider setup
└── store/                     # Global Zustand stores (sidebar, UI)
```

### 3.3. Routing

- React Router v7 với `createBrowserRouter`/`Routes`
- Layout: `MainLayout` chứa `Header` + `Sidebar` + `<Outlet />`
- Sidebar permission-gated dựa trên `can_view_xxx` claims từ JWT
- Lazy-loaded feature pages

### 3.4. State Management Pattern

- **Server state**: TanStack Query với `queryKey` convention `["domain", "subdomain", ...params]`
- **Auth state**: Zustand store (`useAuthStore`) — user, tokens, permissions
- **Form state**: react-hook-form local state
- **UI state**: Zustand (`useSidebarStore`, `useUIStore`) — sidebar collapsed, modals

### 3.5. API Layer

- **HTTP client**: `apiJson<T>(url, options)` — tự động gắn `Authorization: Bearer <token>`, handle refresh
- **Feature API files**: mỗi feature có `api/*.ts` chứa typed functions gọi backend
- **Mock**: `mockCatalog.ts` fallback khi backend chưa sẵn sàng

## 4. AI Architecture

### 4.1. Tech Stack

- **Python 3.12** + FastAPI
- **LangGraph** — agent orchestration graph
- **FPT AI** — LLM, STT (Whisper), TTS (VITS)
- **OpenAI-compatible** adapter cho LLM switching
- **Pydantic** — data validation, schemas
- **httpx** — async HTTP client gọi backend
- **Ruff** — linting
- **Pytest** — testing

### 4.2. Directory Structure

```
ai_python/
├── app/
│   ├── api/           # FastAPI routes (relay endpoints)
│   ├── cli/           # CLI tools (dbmeta CLI)
│   ├── config/        # Settings, graph settings
│   ├── graph/         # LangGraph agent graph
│   │   ├── nodes/     # Graph nodes (intent, sql_pipeline, catalog_draft, inventory_draft, etc.)
│   │   └── *.py       # Graph support modules
│   ├── harness/       # Agent execution harness
│   ├── llm/           # LLM adapters (OpenAI-compatible, registry)
│   ├── prompts/       # System prompts (agent instructions)
│   ├── stt/           # Speech-to-text (FPT Whisper)
│   └── tts/           # Text-to-speech (FPT VITS)
├── scripts/           # Dev scripts (run-dev.ps1, build ERP index)
└── tests/             # Pytest tests
```

### 4.3. Graph Architecture

- **Main graph**: `app/graph/main_graph.py` — định nghĩa LangGraph StateGraph
- **Subgraphs**:
  - `sql_subgraph.py` — text-to-SQL pipeline
  - `catalog_draft_subgraph.py` — AI draft catalog entities
  - `inventory_draft_subgraph.py` — AI draft inventory docs
- **State**: TypedDict `AgentState` — messages, context, intermediate results
- **Error handling**: Retry policy, fallback logic, safety guardrails

### 4.4. Relay Controllers (Backend AI)

Backend có 4 AI relay controller endpoints:

| Endpoint | AI Backend | Mục đích |
|----------|-----------|----------|
| `POST /api/v1/ai/chat/relay` | `ai_python` | Chat relay (text query → SQL → response) |
| `POST /api/v1/ai/catalog-draft/relay` | `ai_python` | AI tạo draft catalog entity |
| `POST /api/v1/ai/inventory-draft/relay` | `ai_python` | AI tạo draft inventory document |
| `GET /api/v1/ai/db-readonly/query` | `ai_python` | Query DB readonly qua AI |

## 5. Cross-Cutting Concerns

### 5.1. API Response Format

```json
// Success
{ "success": true, "data": { ... }, "message": "Thành công" }

// Error
{ "success": false, "error": { "code": "BAD_REQUEST", "message": "Chi tiết lỗi" } }
```

### 5.2. Error Codes

- `UNAUTHORIZED` (401) — hết hạn / không hợp lệ
- `FORBIDDEN` (403) — không có quyền
- `BAD_REQUEST` (400) — validation fail
- `NOT_FOUND` (404) — resource not found
- `CONFLICT` (409) — duplicate / conflict
- `INTERNAL_ERROR` (500) — server error

### 5.3. Pagination

- Request params: `page` (1-indexed), `limit` (default 20, max ~100), `sort`
- Response: `{ items: [...], total: number, page: number, limit: number }`

### 5.4. Testing Strategy

**Backend**:
- `@WebMvcTest` cho controllers (MockMvc + JWT mock)
- Unit test cho services, helpers
- `application-test.properties` với H2 hoặc PostgreSQL test config

**Frontend**:
- **Vitest** — unit tests cho logic, hooks, utils
- **@testing-library/react** — component tests
- **Playwright** — E2E tests cho luồng chính

**AI**:
- **Pytest** — graph node tests, integration tests
- Fake LLM implementation cho deterministic testing

### 5.5. Developer Workflow

- **Backend**: Maven (`mvn spring-boot:run`), cổng 8080
- **Frontend**: Vite dev server (`npm run dev`), cổng 3000, proxy `/api` → backend
- **AI**: FastAPI (`uvicorn app.api.routes:app`), cổng 8000
- **Docker**: `docker-compose.yml` cho PostgreSQL, MinIO (nếu có)
- **Environment**: `APP_SECURITY_MODE=permit-all` cho dev backend

## 6. Architecture Diagrams (Text)

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React + Vite)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐ │
│  │ Dashboard │  │Inventory │  │  Orders  │  │  Settings    │ │
│  │  Pages    │  │  Pages   │  │  Pages   │  │  Pages       │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬──────┘ │
│       │              │              │                │        │
│  ┌────┴──────────────┴──────────────┴────────────────┴────┐  │
│  │             TanStack Query + Zustand                    │  │
│  └────┬─────────────────────────────────────────────┬─────┘  │
│       │ apiJson()                                  │         │
└───────┼─────────────────────────────────────────────┼─────────┘
        │ HTTP (proxy /api)                          │
┌───────┼─────────────────────────────────────────────┼─────────┐
│  ┌────┴─────────────────────────────────────────────┴─────┐  │
│  │         Backend (Spring Boot, port 8080)                │  │
│  │                                                          │  │
│  │  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌─────────┐   │  │
│  │  │ Auth     │ │ Catalog   │ │Inventory │ │ Finance │   │  │
│  │  │Controller│ │Controller │ │Controller│ │Controller│   │  │
│  │  └────┬─────┘ └─────┬─────┘ └────┬─────┘ └────┬────┘   │  │
│  │       │              │            │             │        │  │
│  │  ┌────┴──────────────┴────────────┴─────────────┴────┐  │  │
│  │  │        Service Layer (@Service)                    │  │  │
│  │  └────┬──────────────┬────────────┬───────────────────┘  │  │
│  │       │              │            │                       │  │
│  │  ┌────┴──────┐ ┌─────┴──────┐ ┌──┴───────────┐           │  │
│  │  │JdbcRepos. │ │Flyway      │ │JwtTokenService│          │  │
│  │  │(PostgreSQL)│ │Migrations │ │(jjwt HS256)  │           │  │
│  │  └───────────┘ └───────────┘ └──────────────┘           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│              ┌───────────┴──────────────┐                       │
│              │  PostgreSQL (5432)       │                       │
│              │  Database: smart_erp     │                       │
│              └──────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
                        │
              ┌─────────┴──────────┐
              │  AI (FastAPI, 8000)│
              │  ┌───────────────┐ │
              │  │ LangGraph     │ │
              │  │ Agent Graph   │ │
              │  └───────┬───────┘ │
              │  ┌───────┴───────┐ │
              │  │ FPT AI LLM   │ │
              │  │ + STT + TTS  │ │
              │  └───────────────┘ │
              └────────────────────┘
```

## 7. Key Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| ORM | JdbcTemplate (không JPA) | Kiểm soát truy vấn, hiệu năng, phù hợp với JSONB + aggregate queries |
| Auth | JWT + OAuth2 Resource Server | Stateless, phù hợp với REST API |
| Token | HS256 symmetric | Đơn giản, không cần PKI infrastructure |
| FE state | TanStack Query + Zustand | Phân tách rõ server state vs client state |
| Styling | Tailwind CSS utility-first | Consistent design, tránh CSS overhead |
| AI orchestration | LangGraph | State machine rõ ràng, dễ debug, mở rộng |
| DB migrations | Flyway | Version control cho schema, rollback friendly |
| Response format | Unified wrapper class | Consistent error handling, dễ parse FE |


## 8. Agent Usage Guide

Khi làm việc với codebase:

1. **Đọc architecture document này** trước khi thực hiện bất kỳ thay đổi nào.
2. **Sử dụng CodeGraph** (`codegraph context`, `codegraph query`, `codegraph impact`, `codegraph affected`) để khám phá codebase.
3. **Backend changes**: Xác định feature package, tạo/ sửa Controller → Service → Repository → Response DTO → Test.
4. **Frontend changes**: Xác định feature module, tạo/sửa Page → Component → API → Test.
5. **Database changes**: Tạo Flyway migration mới (`V<next>__<description>.sql`), update repository queries.
6. **AI changes**: Sửa graph nodes, prompts, hoặc relay endpoints.
7. **Workflow**: Luôn chạy qua `SRS_WRITER → TECH_SPEC_WRITER → QA_SPEC_WRITER → CODING_AGENT → CODE_REVIEW_AGENT` cho mọi code change.
