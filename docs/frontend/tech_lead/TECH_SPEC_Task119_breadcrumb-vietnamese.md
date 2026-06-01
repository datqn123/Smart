# Tech Spec / Coding Handoff — Task119 — Breadcrumb Vietnamese

> **File:** `docs/frontend/tech_lead/TECH_SPEC_Task119_breadcrumb-vietnamese.md`
> **Source SRS:** `docs/frontend/srs/SRS_Task119_breadcrumb-vietnamese.md`
> **Scope:** Frontend only
> **Agent:** Tech Spec Writer
> **Date:** 31/05/2026
> **Readiness:** READY_FOR_CODING

---

## 1. Goal

Breadcrumb trên Header hiển thị tiếng Việt thay vì tiếng Anh: "Trang chủ / Tồn kho" thay vì "Home / Stock".

---

## 2. Evidence Read

| Type | Path / symbol | Notes |
| :--- | :--- | :--- |
| SRS | `docs/frontend/srs/SRS_Task119_breadcrumb-vietnamese.md` | Source requirement |
| Component | `frontend/mini-erp/src/components/shared/layout/Header.tsx:130-135` | currentPage computation |
| Component | `frontend/mini-erp/src/components/shared/layout/Header.tsx:205-210` | Breadcrumb JSX |
| Sidebar | `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx:52-121` | Vietnamese labels reference |

---

## 3. Scope Boundary

### In Scope
- `Header.tsx`: Breadcrumb text (Home + currentPage)

### Out of Scope
- CategoryBreadcrumb (data-driven, uses API data)
- Sidebar labels (already Vietnamese)
- Document title / page title
- Tests (no existing test for Header breadcrumb; not adding new)

### Ownership

| Layer | Owner responsibility |
| :--- | :--- |
| Frontend | UI string mapping, breadcrumb render |
| Backend | N/A |
| AI | N/A |

---

## 4. Horizontal Analysis

| Pattern / risk | Similar scopes checked | Finding | Action |
| :--- | :--- | :--- | :--- |
| i18n approach | Sidebar.tsx | Sidebar uses hardcoded Vietnamese strings, not i18n library | Follow same pattern: hardcoded map |
| Path-to-label mapping | None in codebase | New local pattern | Create `PAGE_TITLE_VI` constant map |

---

## 5. Architecture Decision

### Decision
Use a hardcoded TypeScript `Record<string, string>` map inside `Header.tsx` to translate path segments to Vietnamese.

### Rationale
- Matches existing pattern in `Sidebar.tsx` (hardcoded Vietnamese labels)
- No i18n library in project
- Single file change, no new dependencies

### Alternatives Considered

| Option | Pros | Cons | Decision |
| :--- | :--- | :--- | :--- |
| A: Map inside Header.tsx | Single file, no import, matches sidebar pattern | Slightly larger file | **Accepted** |
| B: Shared constants file | Reusable | Overkill for 1 consumer | Rejected |

### ADR Required?
- Required: No
- Reason: Follows existing pattern (Sidebar.tsx hardcoded labels)

---

## 6. Implementation Slices

| Slice | User-visible result | Frontend | Backend | DB | AI |
| :--- | :--- | :--- | :--- | :--- | :--- |
| S1 | Breadcrumb shows Vietnamese text | `Header.tsx` edit | — | — | — |

---

## 7. Contracts

### 7.1 HTTP / API
N/A

### 7.2 Data / SQL
N/A

### 7.3 Frontend State
N/A (no new state)

---

## 8. Files For Coding Agent

### Read First
- `frontend/mini-erp/src/components/shared/layout/Header.tsx`
- `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx` (reference for label mapping)

### Expected To Edit
- `frontend/mini-erp/src/components/shared/layout/Header.tsx`

### Do Not Edit
- Any files in `backend/`, `ai_python/`, `.cursor/`, `ai_python/AGENTS/`

---

## 9. Test Plan

N/A — no existing test for this breadcrumb region. Visual verification only.

---

## 10. Failure Modes

| Failure | Expected behavior |
| :--- | :--- |
| Unknown path segment | Fallback to capitalized segment (e.g. "/new-page" → "New-page") |
| Empty path | "Trang chủ / Bảng điều khiển" |

---

## 11. Open Questions / Gaps

None.

---

## 12. Coding Readiness

**Status:** READY_FOR_CODING

**Reason:** SRS clear, single file change, pattern already established in Sidebar.tsx.

**Instructions to Coding Agent:**

1. In `Header.tsx`, add a `PAGE_TITLE_VI` constant map (or `const` object) after imports.
2. Replace the `currentPage` computed variable logic to look up the map, falling back to capitalized segment.
3. Change `"Home"` to `"Trang chủ"` in the breadcrumb `<span>`.
4. Change `"Dashboard"` fallback to `"Bảng điều khiển"`.
5. Do not modify any other file.
