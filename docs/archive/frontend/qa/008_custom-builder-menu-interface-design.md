# QA Spec / Test Plan - Custom Builder Menu Interface

> **File:** `docs/frontend/qa/008_custom-builder-menu-interface-design.md`  
> **Source SRS:** `docs/frontend/srs/010_custom-builder-menu-interface-design.md`  
> **Tech Spec / Handoff:** `docs/frontend/tech_lead/008_custom-builder-menu-interface-design.md`  
> **Scope:** Frontend  
> **Agent:** QA Spec Writer  
> **Date:** 03/06/2026  
> **Readiness:** QA_READY_FOR_CODING

---

## 1. Test Objective

Prove that `/settings/custom-builder` provides the folder/file menu builder experience and that published custom metadata can enter the runtime UI through dynamic sidebar merge plus `/custom/:pageKey` route resolution without requiring backend API.

---

## 2. Evidence Read

| Type | Path / symbol | Notes |
| :--- | :--- | :--- |
| SRS | `docs/frontend/srs/010_custom-builder-menu-interface-design.md` | Requirement source |
| Tech Spec | `docs/frontend/tech_lead/008_custom-builder-menu-interface-design.md` | Coding handoff |
| CodeGraph | `Sidebar`, `App` context/impact | Affected route/sidebar scope |
| Code | `frontend/mini-erp/src/App.tsx` | Route registration |
| Code | `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx` | Settings menu integration |

---

## 3. Test Scope

### In Scope

- Route and sidebar navigation.
- Builder page render.
- Folder and page creation with validation.
- Selected item detail editing.
- Reorder controls.
- Dirty/pending/publish guardrails.
- Responsive layout sanity.
- Static + dynamic sidebar merge.
- Runtime custom route resolver and safe 403/404 states.
- Version/draft/publish metadata display.

### Out of Scope

- Backend API integration.
- Database persistence.
- AI Copilot behavior.
- Real inventory/workflow execution.

---

## 4. Horizontal QA Analysis

| Risk / pattern | Similar scopes checked | Finding | Required test |
| :--- | :--- | :--- | :--- |
| Sidebar route drift | Existing settings links | Static sidebar needs route in `App.tsx` | Build + manual navigation |
| Permission display | `Sidebar.tsx` permission filtering | New item can be demo-visible; backend RBAC future | Verify existing settings items still render |
| Validation | Product/category forms | Empty/duplicate key should block | Manual validation cases |
| UI state | Settings interface page | Dirty footer and disabled pending buttons are common pattern | Save/publish pending checks |
| Responsive | Recent table unification work | Layout must not overlap on smaller viewport | Browser/mobile screenshot check if server available |
| Runtime sidebar | Static sidebar config | Dynamic custom menu must not hide static menu | Manual navigation + route active check |
| Runtime permissions | Auth role/menu permissions | Folder visible only when child visible; page hidden/403 when denied | Role/filter checks with mock metadata |

---

## 5. Test Matrix

| ID | Level | Scenario | Input / setup | Expected result | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TC-001 | Build | Compile frontend | `npm run build` | No TS/build errors | P0 |
| TC-002 | Frontend | Open route | Navigate `/settings/custom-builder` | Builder page renders | P0 |
| TC-003 | Frontend | Primary actions visible | Initial page | Buttons `Tao danh muc menu cha`, `Tao giao dien menu con` visible | P0 |
| TC-004 | Frontend | Create page disabled with no folder | Empty-state scenario | Page button disabled and helper text shown | P1 |
| TC-005 | Frontend | Create folder | Valid name/key | Folder appears, selected detail shows folder | P0 |
| TC-006 | Frontend | Create page in selected folder | Valid page fields | Page appears under folder, selected detail shows page | P0 |
| TC-007 | Frontend | Duplicate key validation | Use existing folder/page key | Inline error, no duplicate created | P1 |
| TC-008 | Frontend | Reorder | Select non-boundary item and move | Item order changes; boundary buttons disabled | P1 |
| TC-009 | Frontend | Dirty state | Edit any selected field | Footer shows unsaved state | P1 |
| TC-010 | Frontend | Publish incomplete page | Page missing required config | Publish blocked with warning list | P1 |
| TC-011 | Regression | Existing settings routes | Navigate existing settings links | No route removed/broken | P1 |
| TC-012 | Frontend | Dynamic sidebar visible | User with allowed role opens app | Custom folder and page route visible without removing static menu | P0 |
| TC-013 | Frontend | Runtime route success | Open `/custom/phieu_kiem_hang_hong` | Runtime placeholder renders metadata, version, preview info | P0 |
| TC-014 | Frontend | Runtime route missing | Open unknown `/custom/not_found` | In-app 404 safe state | P1 |
| TC-015 | Frontend | Runtime denied | Open page denied by mock role/permission | In-app 403 safe state | P1 |
| TC-016 | Frontend | Version metadata | Open builder/runtime | Version/hasDraft/publishedAt/etag info visible where relevant | P1 |

---

## 6. Failure Modes

| Failure | Classification | Expected behavior | Test ID |
| :--- | :--- | :--- | :--- |
| Missing folder for page create | UX validation | Button disabled and reason visible | TC-004 |
| Duplicate key | Validation | Inline error and no mutation | TC-007 |
| Save double click | UI guardrail | Button disabled while saving | TC-009 |
| Publish invalid page | Business rule | User sees checklist warnings | TC-010 |
| Route not wired | Integration | Build/manual navigation catches it | TC-001/TC-002 |
| Runtime page missing | UX/data | Safe 404 inside shell | TC-014 |
| Runtime permission denied | Permission | Safe 403 without metadata leak | TC-015 |

---

## 7. AI Agentic Tests

AI is out of scope for this coding task. No LangGraph, Harness, or tool tests required.

---

## 8. Test Data / Mocks

| Data / mock | Purpose | Location / creation |
| :--- | :--- | :--- |
| Seed folder `Kiem hang` | Demonstrates folder tree | Page-local constant |
| Seed page `Phieu kiem hang hong` | Demonstrates page detail/tabs | Page-local constant |
| Shared runtime mock folder/page | Demonstrates dynamic sidebar and runtime resolver | `features/custom-builder/runtime/customMenuRuntime.ts` |
| Empty state | Verify disabled create-page behavior | Can be reached after future backend empty data; manual reasoning for MVP |

---

## 9. Verification Commands

```powershell
cd frontend/mini-erp
npm run build
```

Optional if dev server is available:

```powershell
cd frontend/mini-erp
npm run dev
```

Then open `/settings/custom-builder`, `/custom/phieu_kiem_hang_hong`, and an unknown `/custom/not_found`; run TC-002 through TC-016 manually.

---

## 10. Open Questions / Gaps

| ID | Question / gap | Impact | Blocker? | Owner |
| :--- | :--- | :--- | :---: | :--- |
| OQ-1 | No backend/localStorage persistence in MVP | Page resets on reload | No | Product/backend future task |
| OQ-2 | No automated UI test framework confirmed | Manual QA may be needed | No | Frontend |
| OQ-3 | Runtime denied state depends on current login role | Manual QA may need a known session/user | No | Frontend |

---

## 11. QA Readiness

**Status:** QA_READY_FOR_CODING

**Reason:** P0 verification is build plus route/page interaction; remaining cases are manual UI checks and do not block coding.

**Instructions to Coding Agent:**

1. Prioritize TC-001 through TC-006.
2. Report any manual-only verification that could not be performed.
3. Keep frontend-only scope; do not add backend mocks beyond page-local data.
