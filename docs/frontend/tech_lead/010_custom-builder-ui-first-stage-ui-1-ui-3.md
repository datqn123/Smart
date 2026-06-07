# Tech Spec / Coding Handoff - Custom Builder - UI-first Stage UI-1 to UI-3

> **File:** `docs/frontend/tech_lead/009_custom-builder-ui-first-stage-ui-1-ui-3.md`  
> **Source SRS:** `docs/frontend/srs/011_custom-builder-ui-gap-plan.md`  
> **Scope:** Frontend  
> **Agent:** Tech Spec Writer  
> **Date:** 03/06/2026  
> **Readiness:** READY_FOR_CODING

---

## 1. Goal

Implement a UI-first Custom Builder prototype for Stage UI-1 through UI-3 so an admin can create or inspect a custom menu page, configure entity fields and list/form views, and open a metadata-driven runtime record page using a frontend fixture/mock adapter. Backend and `ai_python` are out of scope.

---

## 2. Evidence Read

| Type | Path / symbol | Notes |
| :--- | :--- | :--- |
| SRS | `docs/frontend/srs/011_custom-builder-ui-gap-plan.md` | Stage UI-1 to UI-3, fixture/mock adapter rules, DoD |
| Frontend | `CustomBuilderPage` | Current builder is local state heavy and menu-only |
| Frontend | `CustomRuntimePage` | Current runtime is placeholder resolver |
| Frontend | `customMenuRuntime` | Runtime catalog is hard-coded and shared by sidebar/runtime |
| Frontend | `customInterfaceApi` | Existing API wrapper paths may remain but need mock fallback boundary |
| Frontend | `Sidebar` | Dynamic menu already reads runtime menu API/fallback |
| CodeGraph | `status + context + query + impact` | Entry points: builder page, runtime page, runtime catalog |

---

## 3. Scope Boundary

### In Scope

- Stage UI-1: builder shell, hardened explorer states, validation badges, preview as role, context actions as frontend mock operations.
- Stage UI-2: page creation wizard, entity info, field designer, reference picker shape, list/form layout designer, sample record preview, scale/index warnings.
- Stage UI-3: runtime `/custom/:pageKey` list/detail/create/edit UI from published metadata fixture with loading/error/empty/no-permission states and audit/timeline placeholder.
- A dedicated frontend fixture/mock adapter that simulates loading, success, 403, 409, and 422 style UI paths without becoming component-local source of truth.

### Out of Scope

- Backend controllers/services/database/migrations.
- `ai_python` runtime, LangGraph nodes, Harness executor, or tools.
- Stage UI-4 to UI-6 workflow, connector, inventory effect, and AI copilot beyond disabled placeholder tabs.

### Ownership

| Layer | Owner responsibility | Must not own |
| :--- | :--- | :--- |
| Frontend | UI state, metadata rendering, mock adapter, visible permissions/errors | Server-side authorization or persistence |
| Backend | Future RBAC/business rules/persistence | This UI prototype |
| LangGraph | Future iterative AI orchestration | Builder UI rendering |
| Harness | Future deterministic execution/validation | Draft form state |
| Tools | Future scoped integrations | Orchestration or policy |

---

## 4. Horizontal Analysis

| Pattern / risk | Similar scopes checked | Finding | Action |
| :--- | :--- | :--- | :--- |
| Mock source of truth | `customMenuRuntime`, `customInterfaceApi`, `Sidebar` | Mock data is split between component fallback and runtime catalog | Add one custom-builder mock adapter and route all builder/runtime/sidebar fallback through it |
| Permission display | `Sidebar`, `CustomRuntimePage` | Frontend hides pages by role/permission but backend remains authority later | Keep visible no-permission states and role preview; do not imply real enforcement |
| Validation | SRS validation summary contract | Current UI only validates label/key/route/entity | Add sectioned validation summary for menu/data/view/runtime and disable publish on errors |
| Error/pending states | Existing builder save/publish | Loading and retry are thin; 409/422 not visible | Simulate adapter states and display retry/conflict/validation grouped feedback |
| AI agentic boundaries | SRS Stage UI-6 references | AI is out of current scope | Show disabled future tabs only; no LangGraph/Harness/tool changes |

---

## 5. Architecture Decision

### Decision

Use a frontend-only Custom Builder mock adapter containing canonical fixture types and async functions for builder tree, page bundles, runtime menu, runtime page metadata, and records. `CustomBuilderPage`, `CustomRuntimePage`, and `customMenuRuntime` should consume that shared shape or adapt from the existing API wrapper without introducing backend edits.

### Rationale

This matches the SRS requirement that mock data sit behind an adapter and keeps future backend replacement localized. It also removes the current root cause where large local state inside the component and a separate runtime catalog can drift.

### Alternatives Considered

| Option | Pros | Cons | Decision |
| :--- | :--- | :--- | :--- |
| Keep local state in `CustomBuilderPage` | Fast | Repeats current drift and hides API-state guardrails | Rejected |
| Wire real backend now | More realistic | User explicitly forbids backend changes and SRS says UI-first fixture | Rejected |
| Shared frontend mock adapter | Backend-like shape, testable, replaceable | Slightly more frontend code | Accepted |

### ADR Required?

- Required: No
- ADR path: N/A
- Reason: Frontend prototype follows existing API/mock pattern and does not change architecture boundaries.

---

## 6. Implementation Slices

| Slice | User-visible result | Backend | Frontend | DB | AI |
| :--- | :--- | :--- | :--- | :--- | :--- |
| S1 | Builder shell and menu explorer with loading/error/empty/filter/role preview | No change | Replace builder layout and read via adapter | No | No |
| S2 | Wizard creates a draft page/entity bundle with permissions | No change | Add wizard state and adapter mutation | No | No |
| S3 | Data tab and field designer with reference/line_items/index warnings | No change | Add metadata editor UI | No | No |
| S4 | View tab for list/form layout and sample preview | No change | Add layout designer UI | No | No |
| S5 | Runtime page renders records/list/form/detail from published fixture | No change | Replace placeholder runtime UI | No | No |

---

## 7. Contracts

### 7.1 HTTP / API

No backend contract is implemented in this stage. The frontend adapter must mirror future shapes from the SRS: `BuilderMenuNode`, `BuilderPageBundle`, `ValidationSummary`, `RuntimeCustomMenuFolder`, page metadata, permissions, and mock records.

### 7.2 Frontend State

| UI action | State owner | Success behavior | Error behavior |
| :--- | :--- | :--- | :--- |
| Load builder tree | mock adapter | Render explorer and overview | Show retry; keep destructive actions disabled |
| Create page wizard | mock adapter | Add `NeedsConfig` page and open `Du lieu` tab | Show validation/permission/conflict style message |
| Save draft | mock adapter | Clear dirty and refresh validation summary | Show grouped 422 or conflict banner |
| Publish | mock adapter | Only allowed when validation valid | Disabled on errors/warnings |
| Open runtime page | mock adapter through runtime helper | Render list/detail/form | Show loading/error/empty/no-permission |

### 7.3 AI State / Tool Contract

AI is not implemented in UI-1 to UI-3. Disabled future tabs must preserve the boundary that AI may suggest/diff/draft only in later stages; it cannot publish, transition, or apply inventory effects.

---

## 8. Files For Coding Agent

### Read First

- `frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx`
- `frontend/mini-erp/src/features/custom-builder/pages/CustomRuntimePage.tsx`
- `frontend/mini-erp/src/features/custom-builder/runtime/customMenuRuntime.ts`
- `frontend/mini-erp/src/features/custom-builder/api/customInterfaceApi.ts`
- `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx`

### Expected To Edit

- `frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx`
- `frontend/mini-erp/src/features/custom-builder/pages/CustomRuntimePage.tsx`
- `frontend/mini-erp/src/features/custom-builder/runtime/customMenuRuntime.ts`
- `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx` only if needed to consume adapter consistently.

### Expected To Add

- `frontend/mini-erp/src/features/custom-builder/api/customBuilderMockAdapter.ts`

### Do Not Edit

- `backend/**`
- `ai_python/**`
- Database migrations

---

## 9. Test Plan

| Level | Test | Expected coverage |
| :--- | :--- | :--- |
| Unit/typecheck | `npm run build` | Type safety for fixture contracts and pages |
| Frontend manual | `/settings/custom-builder` desktop/mobile | Builder shell, explorer, wizard, data/view tabs, pending states |
| Frontend manual | `/custom/phieu_kiem_hang_hong` | Runtime list/detail/form/no-permission/error style states |
| Regression | Sidebar custom menu | Fixture menu still visible based on role/permission |

---

## 10. Failure Modes

| Failure | Classification | Expected behavior |
| :--- | :--- | :--- |
| Missing permission | Frontend permission display | Hide/disable action or no-permission state |
| Invalid metadata | Validation | Group errors by tab/section, disable publish |
| Conflict | Contract drift/concurrency simulation | Show reload/compare guidance, do not overwrite |
| Backend absent | UI-first adapter | Continue using fixture through adapter |
| AI action requested | Scope boundary | Disabled placeholder, no mutation |

---

## 11. Open Questions / Gaps

| ID | Question / gap | Impact | Blocker? | Owner |
| :--- | :--- | :--- | :---: | :--- |
| GAP-UI3-01 | Final backend endpoints for records are not available | Adapter must remain replaceable later | No | Backend future task |
| GAP-UI3-02 | Workflow/connector/inventory/AI are later stages | Tabs must stay disabled/placeholder | No | Product/future workflow |

---

## 12. Coding Readiness

**Status:** READY_FOR_CODING

**Reason:** Scope is frontend-only, contracts can be simulated with fixture adapter, and no owner decision is needed for UI-1 to UI-3.

**Instructions to Coding Agent:**

1. Implement S1 to S5 only.
2. Preserve adapter boundary and do not edit backend or `ai_python`.
3. Keep risky future stages disabled.
4. Run `npm run build` and browser verification for builder/runtime routes.
