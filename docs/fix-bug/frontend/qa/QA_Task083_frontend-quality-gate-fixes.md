# QA Test Plan - Task083: Frontend Quality Gate Fixes

> **Source SRS**: `docs/frontend/srs/SRS_Task083_frontend-quality-gate-fixes.md`  
> **Scope**: Frontend Mini-ERP quality gates  
> **Author**: Agent QA  
> **Date**: 30/05/2026  
> **Status**: Draft

## 1. QA Objective

Verify that Task083 stabilizes Mini-ERP frontend quality gates without changing ERP business behavior. The main objective is to ensure unit tests, build, lint, and e2e runner boundaries are deterministic, while high-risk React hook/ref issues are removed from the blocking path.

## 2. Scope

### In Scope

- Vitest must run only unit/integration tests under `src`.
- Playwright e2e specs must run only through a dedicated e2e command.
- Customer/Supplier phone validation tests must use production validation logic.
- React hook-order error in employee detail dialog must be removed.
- Product Management pages must not write refs during render.
- Lint must ignore generated artifacts and exit with code 0.
- Build must still produce a production bundle.

### Out of Scope

- Backend API correctness.
- Database migrations or seed data.
- Full e2e data setup when Spring backend is not running.
- AI Python, LangGraph, Harness, SQL tool execution.
- Bundle-size optimization beyond recording the warning.

## 3. Test Environment

| Item | Requirement |
| :--- | :--- |
| OS | Windows / PowerShell supported |
| Working directory | `D:\do_an_tot_nghiep\project\frontend\mini-erp` |
| Node deps | `node_modules` installed |
| Unit runner | Vitest via `npm test -- --run` |
| E2E runner | Playwright via `npm run test:e2e` |
| Dev server | Vite on `http://localhost:3000` |
| Backend for full e2e | Spring API on `http://127.0.0.1:8080` |

## 4. Test Data / Roles

| Area | Data / role need |
| :--- | :--- |
| Unit validation | No backend data required |
| Product Management manual QA | Existing Owner/Admin/Staff test users if backend is available |
| Inventory e2e | Backend fixture data for inventory, stock receipts, dispatches |
| Settings employees | Employee records available for detail dialog |

## 5. Automation Commands

```powershell
npm run lint
npm test -- --run
npm run build
npm run test:e2e
```

Expected baseline for this task:

- `npm run lint`: exit code 0; warnings are allowed for existing non-blocking technical debt.
- `npm test -- --run`: exit code 0; Playwright files are not discovered by Vitest.
- `npm run build`: exit code 0; bundle-size warning may remain.
- `npm run test:e2e`: runner starts Playwright only. Full pass requires Spring backend and compatible e2e fixtures/selectors.

## 6. Test Matrix By Root Cause

| Root cause | Test | Expected |
| :--- | :--- | :--- |
| Vitest/Playwright boundary | Run `npm test -- --run` | Only `src/**/*.{test,spec}.{ts,tsx}` files run |
| E2E runner boundary | Run `npm run test:e2e` | Playwright starts with `e2e` testDir and Vite webServer |
| Validation duplicate logic | Customer invalid phone unit test | Uses shared production validator and returns phone format message |
| Validation duplicate logic | Supplier invalid phone unit test | Uses shared production validator and returns phone format message |
| Hook-order safety | Open/close Employee detail with null selected employee | No React hook-order crash |
| Render ref writes | Delete selected product/customer/supplier | Selected/editing dialog closes without render-time ref writes |
| Lint generated artifacts | Run `npm run lint` after coverage/e2e artifacts exist | `coverage`, `dist`, `test-results` ignored |
| Residual compiler rules | Review warnings | Warnings captured as non-blocking debt unless PO marks them blocking |

## 7. Manual Regression Checklist

| Route | Checklist |
| :--- | :--- |
| `/settings/employees` | Open employee detail; close; reopen another employee; verify no white screen |
| `/products/list` | Open product detail/edit; delete same product if allowed; verify dialog/form closes |
| `/products/suppliers` | Open supplier detail/edit; single/bulk delete if allowed; verify stale dialogs close |
| `/products/customers` | Open customer detail/edit; delete if allowed; verify stale dialogs close |
| `/orders/retail` | Change search/filter/sort while paginated; verify page resets sanely |
| `/orders/wholesale` | Change date/search/sort history filters; verify no repeated fetch loop |
| `/approvals/pending` | Change search/date/type; verify table remains stable |
| `/approvals/history` | Change result/type/date filters; verify page indicator resets |
| `/cashflow/transactions` | Change status/type/search; verify list reload and selection behavior |
| `/inventory/stock` | Change stock filters; verify selection clears only when intended |

## 8. Acceptance Mapping

| SRS AC | QA verification |
| :--- | :--- |
| Lint exits 0 | `npm run lint` |
| Vitest excludes e2e | `npm test -- --run` output has 43 src test files, no e2e suites |
| Employee dialog hook safe | Manual QA + lint no `rules-of-hooks` error |
| Product/customer/supplier stale state cleared | Manual QA delete selected/editing item |
| Filter page reset | Manual QA on listed routes; warnings documented if not fully refactored |
| Phone validation uses source of truth | Unit tests import shared validation module |

## 9. Defect Severity Rubric

| Severity | Definition | Example |
| :--- | :--- | :--- |
| S0 Blocker | Main quality gate cannot run | `npm test` still executes Playwright specs |
| S1 Critical | Runtime crash or data-affecting UI bug | Hook-order crash on employee dialog |
| S2 Major | Wrong validation or stale dialog state | Invalid phone accepted; edit dialog remains open after delete |
| S3 Minor | Non-blocking warning/noise | Unused import warning |
| S4 Trivial | Documentation/test wording mismatch | QA doc typo |

## 10. Current Execution Notes

- Unit tests pass: 313 tests across 43 files.
- Build passes.
- Lint exits 0 with warnings.
- Playwright runner is separated, but full e2e currently fails when Spring backend is unavailable at `127.0.0.1:8080`; several legacy selectors also need e2e maintenance.

## 11. AI Agentic Applicability

Not applicable for this task. No `ai_python`, LangGraph, Harness, or tool integration should be changed.

If an AI-related regression appears later, classify it by layer:

| Layer | QA focus |
| :--- | :--- |
| LangGraph orchestrator | State transition, routing, retry cap |
| Harness executor | Deterministic validation, guardrails, audit boundary |
| Tools | Scoped integration, auth relay, safe input/output |

## 12. Exit Criteria

- [ ] `npm run lint` exits 0.
- [ ] `npm test -- --run` exits 0.
- [ ] `npm run build` exits 0.
- [ ] `npm run test:e2e` is runnable through Playwright only.
- [ ] Any e2e failures are classified as backend fixture/selector debt, not Vitest boundary failure.
- [ ] Manual smoke checklist is complete for changed routes when backend is available.

## 13. Open Questions

| ID | Question | Impact | Blocker? |
| :--- | :--- | :--- | :---: |
| QA-OQ-1 | Should existing `react-hooks/set-state-in-effect` warnings become blocking later? | May require reducer/state refactor across many pages | No |
| QA-OQ-2 | What canonical fixture/login setup should Playwright use? | Required for full e2e pass | Yes for e2e release gate |
| QA-OQ-3 | Are legacy UI selector expectations still valid after UI standardization tasks? | Required to update e2e assertions | Yes for e2e release gate |
