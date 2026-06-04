# QA Spec / Test Plan - Custom Builder - UI-first Stage UI-1 to UI-3

> **File:** `docs/frontend/qa/009_custom-builder-ui-first-stage-ui-1-ui-3.md`  
> **Source SRS:** `docs/frontend/srs/011_custom-builder-ui-gap-plan.md`  
> **Tech Spec / Handoff:** `docs/frontend/tech_lead/009_custom-builder-ui-first-stage-ui-1-ui-3.md`  
> **Scope:** Frontend  
> **Agent:** QA Spec Writer  
> **Date:** 03/06/2026  
> **Readiness:** QA_READY_FOR_CODING

---

## 1. Test Objective

Prove that the UI-first Custom Builder flow works from menu/page creation through entity/view configuration and runtime record preview using a replaceable frontend mock adapter, while backend, database, and `ai_python` remain untouched.

---

## 2. Evidence Read

| Type | Path / symbol | Notes |
| :--- | :--- | :--- |
| SRS | `docs/frontend/srs/011_custom-builder-ui-gap-plan.md` | UI-1 to UI-3 acceptance and fixture rules |
| Tech Spec | `docs/frontend/tech_lead/009_custom-builder-ui-first-stage-ui-1-ui-3.md` | Implementation slices S1-S5 |
| CodeGraph | `affected + context` | Affected tests none; runtime helpers are central |
| Code | `CustomBuilderPage`, `CustomRuntimePage`, `customMenuRuntime`, `Sidebar` | Current manual/browser verification targets |
| Existing tests | `frontend/mini-erp/src/lib/api/mockCatalog.test.ts` | Existing mock adapter style, no Custom Builder tests |

---

## 3. Test Scope

### In Scope

- Builder shell, explorer, loading/error/empty/filter states.
- Create page wizard and mock mutation behavior.
- Entity/field/reference/line_items metadata UI.
- List/form layout designer and sample preview.
- Runtime record list/detail/create/edit UI from fixture.
- Sidebar custom menu regression.

### Out of Scope

- Backend integration, real persistence, database state.
- Workflow/connector/inventory/AI implementation.
- `ai_python` LangGraph/Harness/tool tests.

---

## 4. Horizontal QA Analysis

| Risk / pattern | Similar scopes checked | Finding | Required test |
| :--- | :--- | :--- | :--- |
| Mock contract drift | `mockCatalog.test.ts`, `customInterfaceApi` | Existing mocks use API-shaped data; Custom Builder needs same discipline | Typecheck/build and adapter shape review |
| Permission visibility | `Sidebar`, `CustomRuntimePage` | Frontend role filtering exists but is display-only | Browser no-permission/preview-as-role smoke |
| Validation grouping | SRS validation summary | Publish must not enable when required sections fail | Manual field/view validation smoke |
| Runtime states | Inventory/product pages | Runtime pages usually show table/detail/forms | Browser runtime list/detail/form smoke |
| AI boundaries | SRS Stage UI-6 | AI must not mutate in this stage | Confirm future tabs disabled and no AI tool/backend code changed |

---

## 5. Test Matrix

| ID | Level | Scenario | Input / setup | Expected result | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TC-001 | Build | Typecheck Custom Builder adapter and pages | `npm run build` | Build passes with no TS errors | P0 |
| TC-002 | Browser | Open `/settings/custom-builder` | Admin/Owner account fixture | Shell shows command bar, explorer, workspace, inspector, safety bar | P0 |
| TC-003 | Browser | Run page wizard | Create management page path | Draft page/entity appears and `Du lieu` tab opens | P0 |
| TC-004 | Browser/manual | Configure reference and line_items fields | Fixture fields | Reference uses `{refType, refEntityKey}` and line_items warning is visible | P0 |
| TC-005 | Browser/manual | Configure list/form view | Select fields/sections | Preview renders sample record and publish remains disabled on validation errors | P0 |
| TC-006 | Browser | Open `/custom/phieu_kiem_hang_hong` | Published fixture page | Runtime table, detail panel, form controls, timeline placeholder render | P0 |
| TC-007 | Browser/manual | Check pending/disabled actions | Trigger save/publish/create | Risky buttons disable while pending | P1 |
| TC-008 | Regression | Sidebar custom menu | Runtime fixture | Published custom menu appears only when role/permission allows | P1 |
| TC-009 | Negative | Unknown custom route | `/custom/not-found` | Safe not-found/error state | P1 |

---

## 6. Failure Modes

| Failure | Classification | Expected behavior | Test ID |
| :--- | :--- | :--- | :--- |
| Missing permission | Frontend permission display | No-permission message and disabled actions | TC-002, TC-008 |
| Invalid metadata | Validation | Errors grouped by section; publish disabled | TC-004, TC-005 |
| Conflict | Contract drift simulation | Conflict banner/reload guidance; no overwrite | TC-007 |
| Empty result | UX/data | Stable empty state in explorer/runtime | TC-002, TC-009 |
| Backend absent | Adapter fallback | Fixture still renders through adapter | TC-001, TC-006 |

---

## 7. AI Agentic Tests

AI agentic runtime is out of scope for UI-1 to UI-3. No LangGraph, Harness, or tool tests are required. Regression expectation: no `ai_python/**` edits and future AI controls remain disabled placeholders.

---

## 8. Test Data / Mocks

| Data / mock | Purpose | Location / creation |
| :--- | :--- | :--- |
| Custom Builder fixture tree | Explorer/sidebar/runtime menu | `frontend/mini-erp/src/features/custom-builder/api/customBuilderMockAdapter.ts` |
| Page bundle fixture | Entity fields, views, permissions, validation | Same adapter |
| Runtime records | List/detail/form preview | Same adapter |
| Role preview fixture | Admin/Warehouse/Staff visibility | Same adapter or page state |

---

## 9. Verification Commands

```powershell
cd frontend/mini-erp
npm run build
```

Manual/browser routes:

```text
http://localhost:3000/settings/custom-builder
http://localhost:3000/custom/phieu_kiem_hang_hong
http://localhost:3000/custom/not-found
```

---

## 10. Open Questions / Gaps

| ID | Question / gap | Impact | Blocker? | Owner |
| :--- | :--- | :--- | :---: | :--- |
| GAP-QA-01 | No existing Custom Builder unit tests | Browser/build verification carries first UI sprint | No | Coding/QA |
| GAP-QA-02 | Real backend endpoints absent | Contract errors are simulated only | No | Backend future task |

---

## 11. QA Readiness

**Status:** QA_READY_FOR_CODING

**Reason:** P0 behavior can be verified with build and browser smoke against the fixture adapter; gaps are non-blocking for a UI-first prototype.

**Instructions to Coding Agent:**

1. Keep P0 scenarios traceable in the implementation.
2. Run `npm run build`.
3. Use browser verification for builder and runtime routes.
4. Report any skipped browser or test coverage explicitly.
