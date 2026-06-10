# Tech Spec / Coding Handoff - Task002 - Dashboard API

> **File:** `docs/backend/task002/02-tech-lead/001_dashboard-api-tech-spec.md`  
> **Source SRS:** `docs/backend/002_srs_dashboard-api.md`  
> **Scope:** Full-stack, backend/API primary  
> **Agent:** Tech Spec Writer  
> **Date:** 06/06/2026  
> **Readiness:** READY_FOR_CODING

---

## 1. Goal

Implement one consolidated `GET /api/v1/dashboard` endpoint that returns pre-aggregated dashboard data and wire `DashboardPage` to consume it instead of firing eight list queries and aggregating in the browser.

---

## 2. Evidence Read

| Type | Path / symbol | Notes |
| :--- | :--- | :--- |
| SRS | `docs/backend/002_srs_dashboard-api.md` | Defines sections, params, RBAC, acceptance criteria |
| Backend | `inventory/service/InventoryListService.java` | Existing inventory summary source |
| Backend | `inventory/approvals/ApprovalsService.java` | Existing pending approvals summary/list source |
| Backend | `sales/repository/SalesOrderJdbcRepository.java` | Existing order list fields and sales order schema usage |
| Backend | `finance/cashflow/CashflowMovementJdbcRepository.java` | Existing ledger/cash transaction cashflow read model |
| Backend | `auth/support/MenuPermissionClaims.java` | `can_view_dashboard` already emitted in JWT menu permissions |
| Frontend | `features/dashboard/pages/DashboardPage.tsx` | Currently runs 8 parallel queries and browser aggregates |
| Frontend | `features/dashboard/utils/dashboardAnalytics.ts` | Existing aggregation behavior to replace with API payload |
| Database | `V1__baseline_smart_inventory.sql` | `SalesOrders`, `CashTransactions`, inventory schema |

---

## 3. Scope Boundary

### In Scope

- Add backend dashboard package with controller, service, repository, and response/query records.
- Enforce authenticated user plus `can_view_dashboard`.
- Hide financial sections for non-financial roles by returning `null`.
- Support `trendDays`, `recentLimit`, `topCustomerLimit`, `alertLimit`, and `include`.
- Wire frontend dashboard page to one API query while preserving current UI sections.

### Out of Scope

- Materialized views, Redis/cache manager, API gateway cache.
- New dashboard UI redesign.
- AI insight generation.
- Editing `ai_python`.

### Ownership

| Layer | Owner responsibility | Must not own |
| :--- | :--- | :--- |
| Frontend | UI state, trend-day control, visible loading/error state | Server-side authorization or financial masking |
| Backend | RBAC, aggregation, SQL allowlists, section masking | UI navigation |
| LangGraph | Not in scope | Dashboard deterministic queries |
| Harness | Not in scope | Dashboard aggregation |
| Tools | Not in scope | Business rules |

---

## 4. Horizontal Analysis

| Pattern / risk | Similar scopes checked | Finding | Action |
| :--- | :--- | :--- | :--- |
| Auth/RBAC | Inventory, approvals, sidebar permissions | `can_view_dashboard` already exists; controllers use JWT checks and `@PreAuthorize` or access policy | Use `@PreAuthorize("hasAuthority('can_view_dashboard')")` and require JWT principal |
| Financial visibility | Dashboard FE role gating, finance controllers | FE hides financial sections for Owner/Admin/Manager only | Backend must duplicate this rule and return `null` for financial sections |
| Dashboard financial source | SRS 002 and existing FE dashboard analytics | SRS defines revenue/channel/top customers from `SalesOrders`, cashflow from completed `CashTransactions` | Follow SRS 002 exactly for Task002 |
| Query params | Existing list controllers | Params are strings with validation/clamping | Dashboard service parses and clamps params centrally |
| Performance | Current FE fetches 8 lists | SRS requires section include to skip unused queries | Repository methods per section; service only calls included sections |
| Error envelope | Existing controllers | `ApiSuccessResponse.of(data, "Thành công")` | Keep same envelope |

---

## 5. Architecture Decision

### Decision

Create a dedicated dashboard read-model repository using `NamedParameterJdbcTemplate`. The service orchestrates requested sections and financial masking. Frontend replaces eight `useQueries` calls with one `useQuery`.

### Rationale

Dashboard aggregates cut across inventory, sales, approvals, customers, and cash transactions. Reusing list endpoints would preserve the current over-fetching problem. A dedicated read model keeps SQL explicit, parameterized, and aligned with the existing backend style.

### Alternatives Considered

| Option | Pros | Cons | Decision |
| :--- | :--- | :--- | :--- |
| Reuse existing services only | Less new SQL | Still over-fetches and cannot honor `include` efficiently | Rejected |
| Dedicated dashboard repository | Efficient, explicit section queries | More new response records | Accepted |
| Materialized view/cache now | Fastest for cold path | More migration and invalidation complexity | Deferred |

### ADR Required?

- Required: No
- Reason: Uses existing read-model/controller/repository patterns; no new architectural boundary.

---

## 6. Implementation Slices

| Slice | User-visible result | Backend | Frontend | DB | AI |
| :--- | :--- | :--- | :--- | :--- | :--- |
| S1 | Endpoint returns dashboard sections | Add dashboard controller/service/repository/records | None | Read existing tables only | N/A |
| S2 | Role-based financial masking | Service checks JWT role | UI naturally hides null financial sections | None | N/A |
| S3 | Frontend uses one request | None | Add dashboard API client and replace `useQueries` | None | N/A |
| S4 | Verification | Compile/test | Build | None | N/A |

---

## 7. Contracts

### 7.1 HTTP / API

| Method | Path | Auth | Permission | Request | Response | Errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| GET | `/api/v1/dashboard` | Bearer JWT | `can_view_dashboard` | `trendDays=7|30`, limits max 20, `include` comma list | `DashboardData` in standard envelope | 400, 401, 403 |

### 7.2 Data / SQL

| Table | Read | Write | Rule |
| :--- | :---: | :---: | :--- |
| `salesorders` | Yes | No | Revenue, order counts, recent orders, channel breakdown, top customers; exclude `Cancelled` from revenue/order financial aggregates |
| `customers` | Yes | No | Recent orders and top customers names |
| `inventory`/`products`/`productunits`/`warehouselocations` | Yes | No | Inventory KPI and low-stock alerts |
| `stockreceipts`/approval read model tables | Yes | No | Through `ApprovalsService` or repository-compatible query |
| `cashtransactions` | Yes | No | Month-to-date completed income/expense cashflow |

### 7.3 Frontend State

| UI action | Query key | Success behavior | Error behavior |
| :--- | :--- | :--- | :--- |
| Open `/dashboard` | `["dashboard", "overview", trendDays]` | Render all returned sections | Show existing card/list loading fallback or empty states |
| Toggle 7/30 days | Same key with `trendDays` | Refetch one dashboard payload | Keep previous data while loading if possible |

---

## 8. Files For Coding Agent

### Read First

- `backend/smart-erp/src/main/java/com/example/smart_erp/common/api/ApiSuccessResponse.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/inventory/controller/InventoryController.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/sales/repository/SalesOrderJdbcRepository.java`
- `frontend/mini-erp/src/features/dashboard/pages/DashboardPage.tsx`

### Expected To Edit

- `frontend/mini-erp/src/features/dashboard/pages/DashboardPage.tsx`

### Expected To Add

- `backend/smart-erp/src/main/java/com/example/smart_erp/dashboard/controller/DashboardController.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/dashboard/service/DashboardService.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/dashboard/repository/DashboardJdbcRepository.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/dashboard/response/*.java`
- `frontend/mini-erp/src/features/dashboard/api/dashboardApi.ts`

### Do Not Edit

- `ai_python/**`
- Unrelated generated docs.

---

## 9. Test Plan

| Level | Test | Expected coverage |
| :--- | :--- | :--- |
| Unit | Dashboard query parsing include/limits | `trendDays`, max limits, invalid include |
| Integration/light compile | Controller/service compile with security annotations | API contract compiles |
| Frontend | `npm run build` | Type contract and page wiring |
| Manual | `/dashboard` as Owner/Admin and Staff | Financial visible vs null/hidden behavior |

---

## 10. Failure Modes

| Failure | Classification | Expected behavior |
| :--- | :--- | :--- |
| Missing token | Backend/RBAC | 401 Vietnamese auth message |
| Missing `can_view_dashboard` | Backend/RBAC | 403 |
| Invalid include | Validation | 400 with supported include values |
| Staff financial access | Authorization masking | Non-financial sections remain, financial sections are `null` |
| Empty data | Data edge case | Zero values and empty lists, not 500 |

---

## 11. Open Questions / Gaps

| ID | Question / gap | Impact | Blocker? | Owner |
| :--- | :--- | :--- | :---: | :--- |
| GAP-1 | SRS says cache 30s/5m, but no project cache abstraction is present | Cold path may be slower on large DB | No | Future perf task |
| GAP-2 | SRS names `cash_movements`/`cash_transactions`; actual schema uses `CashTransactions` and `FinanceLedger` | Contract must follow real schema | No | Backend |

---

## 12. Coding Readiness

**Status:** READY_FOR_CODING

**Reason:** Scope, contracts, source files, SQL sources, and tests are clear. Non-blocking cache work is tracked as a future performance gap.

**Instructions to Coding Agent:**

1. Implement slices in order.
2. Use parameterized SQL only.
3. Keep financial masking in backend even if frontend hides sections.
4. Verify with backend compile/focused tests and frontend build.
