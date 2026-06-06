# Test Plan - Task002 - Dashboard API

> **File:** `docs/backend/task002/04-tester/001_dashboard-api-test-plan.md`  
> **Source SRS:** `docs/backend/002_srs_dashboard-api.md`  
> **Tech Spec:** `docs/backend/task002/02-tech-lead/001_dashboard-api-tech-spec.md`  
> **Agent:** QA Spec Writer  
> **Date:** 06/06/2026  
> **Readiness:** QA_READY_FOR_CODING

## 1. Scope

Validate consolidated `GET /api/v1/dashboard` behavior, financial masking, query parameter handling, and frontend replacement of multiple dashboard queries with one dashboard API query.

## 2. CodeGraph / Evidence

- `codegraph affected` on expected dashboard backend/frontend files returned no existing direct tests.
- `codegraph context` did not find dashboard-specific test coverage, so QA must rely on new focused checks plus backend compile and frontend build.
- Source read: SRS, tech spec, current `DashboardPage.tsx`, inventory, sales, approvals, and cashflow backend patterns.

## 3. P0 Test Matrix

| ID | Case | Setup | Expected |
| :--- | :--- | :--- | :--- |
| P0-1 | Owner/Admin calls default dashboard | JWT has `can_view_dashboard`, role Owner/Admin | 200, all requested sections present, financial sections non-null |
| P0-2 | Staff/non-financial role calls dashboard | JWT has `can_view_dashboard`, role Staff | 200, `financial`, `revenueTrend`, `channelBreakdown`, `cashflow` are `null`; KPI/list sections present |
| P0-3 | Missing dashboard permission | Authenticated JWT lacks `can_view_dashboard` | 403 |
| P0-4 | `trendDays=30` | Financial role | `revenueTrend` has exactly 30 points |
| P0-5 | `include=kpis,orders` | Any dashboard-authorized role | Only `kpis` and `recentOrders` populated; excluded sections are `null`/empty by contract |
| P0-6 | Invalid include token | `include=kpis,bad` | 400 validation error |
| P0-7 | Empty data DB | No orders/ledger/cash rows | Zero values and empty lists, no 500 |
| P0-8 | Frontend build | Dashboard page imports new API | TypeScript/Vite build passes |

## 4. P1 / Regression Matrix

| ID | Area | Expected |
| :--- | :--- | :--- |
| P1-1 | Top customers | Sorted by `totalSpent` desc, limited by `topCustomerLimit` max 20 |
| P1-2 | Cashflow month-to-date | Includes current month start through current date only |
| P1-3 | Revenue pct change | `null` when yesterday revenue is zero |
| P1-4 | Recent orders | Sorted newest first, limit max 20 |
| P1-5 | Low-stock alerts | Sorted quantity asc, limited by `alertLimit` |
| P1-6 | Existing inventory/sales/approvals pages | Compile/build unaffected |

## 5. Expected New/Updated Tests

| Level | File | Purpose |
| :--- | :--- | :--- |
| Backend unit | `DashboardServiceTest` if lightweight mocking is feasible | Param parsing, include parsing, financial masking |
| Backend compile | Maven compile | New response records/controller/repository compile |
| Frontend build | `npm run build` | API type and page wiring |

If a full repository integration test is too heavy for this pass, document it as residual risk and keep SQL parameterized/read-only.

## 6. Failure Modes

| Failure | Classification | Expected behavior |
| :--- | :--- | :--- |
| Missing JWT | Backend/RBAC | 401 via project exception handling |
| Missing permission | Backend/RBAC | 403 |
| Bad query param | Validation | 400 with Vietnamese message |
| Contract drift with FE | Integration | Build fails before completion |
| Large data volume | Performance | Endpoint avoids list over-fetch; cache deferred |

## 7. QA Readiness

**Status:** QA_READY_FOR_CODING

**Reason:** Acceptance criteria map to concrete validation paths. Lack of existing direct tests is non-blocking if Coding Agent adds a lightweight service test or explicitly verifies compile/build and records repository integration risk.
