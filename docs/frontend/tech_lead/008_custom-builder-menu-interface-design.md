# Tech Spec / Coding Handoff - Custom Builder Menu Interface

> **File:** `docs/frontend/tech_lead/008_custom-builder-menu-interface-design.md`  
> **Source SRS:** `docs/frontend/srs/010_custom-builder-menu-interface-design.md`  
> **Scope:** Frontend  
> **Agent:** Tech Spec Writer  
> **Date:** 03/06/2026  
> **Readiness:** READY_FOR_CODING

---

## 1. Goal

Implement the Custom Builder menu experience in two frontend slices:

- Builder management UI at `/settings/custom-builder`.
- Runtime integration mock for published custom menu/page metadata: dynamic sidebar merge and `/custom/:pageKey` route resolver.

---

## 2. Evidence Read

| Type | Path / symbol | Notes |
| :--- | :--- | :--- |
| SRS | `docs/frontend/srs/010_custom-builder-menu-interface-design.md` | Source requirement |
| Shared SRS | `docs/dev/common/001_custom-builder-program-overview.md` | Metadata-driven builder, frontend route/menu gap |
| Shared SRS | `docs/dev/common/002_custom-builder-phase1-entity-record-foundation.md` | `/settings/custom-builder`, custom workspace routes |
| Frontend | `frontend/mini-erp/src/App.tsx` | Static route registration |
| Frontend | `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx` | Static sidebar config and permission filtering |
| Frontend | `frontend/mini-erp/src/components/ui/*` | Existing shadcn-style controls |
| CodeGraph | `Sidebar`, `App` context/impact | Confirms route/sidebar blast radius |

---

## 3. Scope Boundary

### In Scope

- Add `/settings/custom-builder` route.
- Add runtime routes `/custom/:pageKey` and `/custom/:pageKey/:recordId`.
- Add sidebar entry under `Cai dat`: `Trinh thiet ke du lieu`.
- Merge static sidebar config with mock dynamic custom menu folders/pages.
- Add `CustomBuilderPage` with:
  - Header actions: `Luu nhap`, `Xem truoc`, `Publish`.
  - Left explorer with two buttons and folder/page tree.
  - Right detail panel for selected folder/page.
  - Create folder/page flows with client-side validation.
  - Reorder selected item with up/down buttons.
  - Dirty state footer and pending button guardrail simulation.
- Use shared frontend mock runtime metadata; no backend API.
- Add version/draft/publish metadata fields to the mock contract.

### Out of Scope

- Backend persistence/API/database.
- AI Copilot, inventory effect builder, real workflow execution.
- Backend-generated dynamic sidebar API.
- Drag-and-drop reorder.
 - Full custom record CRUD runtime.

### Ownership

| Layer | Owner responsibility | Must not own |
| :--- | :--- | :--- |
| Frontend | UI state, mock builder data, validation hints, visible errors | Server-side authorization or persistence |
| Backend | Future RBAC, validation, persistence, publish rules | Current UI mock behavior |
| LangGraph | Future AI orchestration only | UI state or deterministic validation |
| Harness | Future AI/tool execution boundary only | Page rendering |
| Tools | Future scoped integrations only | Policy or orchestration |

---

## 4. Horizontal Analysis

| Pattern / risk | Similar scopes checked | Finding | Action |
| :--- | :--- | :--- | :--- |
| Navigation | `Sidebar.tsx`, `sidebarStore.ts` | Sidebar keys are typed; dynamic custom ids need a safe prefix | Add static settings route and allow `custom-${key}` nav ids |
| Route registration | `App.tsx` | Main layout owns protected app routes | Import and register page inside main layout |
| Tree UI | Product category table | Existing tree is table-oriented; builder needs explorer panel | Reuse interaction idea, not table markup |
| UI controls | settings/product pages | Project uses lucide icons and shadcn controls | Use Button/Input/Select/Textarea/Badge |
| Backend contract | common SRS | Backend will be authoritative later | Keep shared mock shape close to SRS runtime contract |
| AI safety | common AI SRS | Metadata labels are untrusted content | Render text only, no raw HTML |

---

## 5. Architecture Decision

### Decision

Create `frontend/mini-erp/src/features/custom-builder/` with:

- A shared mock runtime catalog for published folder/page metadata.
- A builder page that uses local draft state seeded from the catalog.
- A custom runtime page resolver that reads published mock metadata.
- Sidebar merge logic that appends custom folders with at least one visible published child.

### Rationale

This keeps the implementation demo-ready without inventing backend APIs prematurely, while proving the runtime architecture shape: static menu remains stable, custom menu is derived from published metadata, and route resolver handles 403/404 states.

### Alternatives Considered

| Option | Pros | Cons | Decision |
| :--- | :--- | :--- | :--- |
| Add full API adapter now | Future-ready | Backend not available, higher drift risk | Rejected |
| Store in localStorage | Demo persistence | SRS for this task does not require persistence and can stale quickly | Rejected for MVP |
| Shared runtime mock catalog | Proves sidebar/runtime contracts without backend | No persistence | Accepted |

### ADR Required?

- Required: No
- ADR path: N/A
- Reason: Follows existing frontend route/page pattern and does not change architecture boundaries.

---

## 6. Implementation Slices

| Slice | User-visible result | Backend | Frontend | DB | AI |
| :--- | :--- | :--- | :--- | :--- | :--- |
| S1 Route/menu | User can open builder from Settings | N/A | `App.tsx`, `Sidebar.tsx`, `sidebarStore.ts` | N/A | N/A |
| S2 Builder page layout | Header, explorer, detail panel render | N/A | Add `CustomBuilderPage.tsx` | N/A | N/A |
| S3 Folder/page create | Buttons create valid folder/page items | N/A | Page state + validation | N/A | N/A |
| S4 Detail/edit/reorder | Selected item can be edited/reordered | N/A | Detail panel controls | N/A | N/A |
| S5 Guardrails | Dirty footer, pending disable, publish validation hints | N/A | Page state | N/A | N/A |
| S6 Runtime sidebar | Published custom folder/page appears in sidebar by permission | N/A | `Sidebar.tsx`, runtime catalog | N/A | N/A |
| S7 Runtime route | `/custom/:pageKey` renders runtime placeholder/403/404 | N/A | Add runtime page resolver | N/A | N/A |

---

## 7. Contracts

### 7.1 HTTP / API

No HTTP calls in this implementation. Runtime data comes from a typed mock catalog that mirrors the future `GET /api/v1/custom/runtime-menu` and `GET /api/v1/custom/pages/{pageKey}/runtime` contracts.

### 7.2 Frontend State

| UI action | State | Success behavior | Error behavior |
| :--- | :--- | :--- | :--- |
| Create folder | `folders[]`, `selectedRef` | New folder appears in explorer and detail panel | Inline validation for empty/duplicate key |
| Create page | `folders[].children[]` | New page appears under selected/current folder | Disabled when no folder exists |
| Edit selected | Selected item fields | Dirty footer appears | Inline validation for empty/duplicate key |
| Reorder | `sortOrder` via array move | Explorer order changes | Disable at list boundaries |
| Save draft | `dirty`, `saving` | Dirty clears after simulated save | Button disabled while pending |
| Publish | `status` validation | Page/folder status can become published if valid | Show warning list for incomplete page |
| Runtime menu | `getRuntimeCustomMenuForUser(...)` | Sidebar appends visible custom folders | Static menu remains if mock/filter returns none |
| Runtime page | `resolveRuntimeCustomPage(...)` | Render page metadata placeholder | 404 for missing page, 403 for denied page |

---

## 8. Files For Coding Agent

### Read First

- `docs/frontend/srs/010_custom-builder-menu-interface-design.md`
- `frontend/mini-erp/src/App.tsx`
- `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx`
- `frontend/mini-erp/src/store/sidebarStore.ts`
- `frontend/mini-erp/src/features/settings/pages/InterfaceSettingsPage.tsx`

### Expected To Edit

- `frontend/mini-erp/src/App.tsx`
- `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx`
- `frontend/mini-erp/src/store/sidebarStore.ts`

### Expected To Add

- `frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx`
- `frontend/mini-erp/src/features/custom-builder/pages/CustomRuntimePage.tsx`
- `frontend/mini-erp/src/features/custom-builder/runtime/customMenuRuntime.ts`

### Do Not Edit

- `ai_python/**`
- Backend migrations/API files.
- Unrelated product/inventory/order table code.

---

## 9. Test Plan

| Level | Test | Expected coverage |
| :--- | :--- | :--- |
| Static/build | `npm run build` | TypeScript, route imports, component compile |
| Frontend manual | Open `/settings/custom-builder` | Page renders with two buttons and explorer |
| Frontend manual | Create folder then page | Folder/page tree updates and selected detail changes |
| Frontend manual | Try page before folder | Button disabled with clear helper text |
| Frontend manual | Reorder up/down | Boundary buttons disabled, item order changes |
| Regression | Sidebar settings menu | Existing settings links remain visible |
| Frontend manual | Sidebar dynamic custom menu | Published folder/page visible by role and route active expands parent |
| Frontend manual | Runtime resolver | `/custom/phieu_kiem_hang_hong` renders placeholder; unknown key renders 404 |

---

## 10. Failure Modes

| Failure | Classification | Expected behavior |
| :--- | :--- | :--- |
| No folder exists | UX validation | Page creation disabled and helper shown |
| Empty/duplicate key | Validation | Inline error, no duplicate item created |
| Pending double click | UI guardrail | Save/publish buttons disabled while pending |
| Incomplete page publish | Business rule preview | Publish blocked with section warnings |
| Route missing | Integration | Build fails; verify route exists |
| Runtime permission denied | Permission | 403 safe message |
| Runtime menu empty | UX/data | Static sidebar still renders |

---

## 11. Open Questions / Gaps

| ID | Question / gap | Impact | Blocker? | Owner |
| :--- | :--- | :--- | :---: | :--- |
| OQ-1 | Final backend endpoint names | Future adapter only | No | Backend |
| OQ-2 | Whether builder entry should be Admin-only | Current menu can use `always` for demo; backend later owns RBAC | No | Product |
| OQ-3 | Custom menu root position | Mock appends custom folders after static menu; backend can return sort strategy later | No | Product |

---

## 12. Coding Readiness

**Status:** READY_FOR_CODING

**Reason:** Scope is frontend-only, contracts are mock/local, and route/sidebar/page files are identified.

**Instructions to Coding Agent:**

1. Implement slices S1-S7 in order.
2. Use neutral slate styling and lucide icons.
3. Keep the UI self-contained and backend-replaceable.
4. Run `npm run build` from `frontend/mini-erp`.
