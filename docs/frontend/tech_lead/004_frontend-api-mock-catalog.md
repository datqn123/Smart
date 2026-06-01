# Tech Spec - Frontend API Mock Catalog

> Agent: TECH_SPEC_WRITER  
> Ngay cap nhat: 31/05/2026  
> Trang thai: READY_FOR_CODING

## 1. Handoff

- Source SRS: `docs/frontend/srs/004_frontend-api-mock-catalog.md`.
- Scope: frontend-only catalog module, khong wire MSW/runtime fetch.
- Output: typed mock API catalog de FE/dev/test co mot source-of-truth ve endpoints, envelope va sample payload.

## 2. Implementation

- Them module `frontend/mini-erp/src/lib/api/mockCatalog.ts`.
- Export:
  - `mockSuccess(data)`
  - `mockError(error, message, details?)`
  - `mockList(items, page?, limit?)`
  - `frontendApiMockCatalog`
  - `getMockCatalogEntry(method, path)`
- Moi catalog entry gom:
  - `method`
  - `path`
  - `permission?`
  - `auth`
  - `kind`
  - `description`
  - `sampleData`
- Path dung template style nhu `/api/v1/products/{id}` de khop SRS.
- Include endpoint groups: auth, notifications, inventory, product management, orders/POS, approvals, cashflow, settings, AI.

## 3. Constraints

- Khong sua `apiJson`/`apiFormData`.
- Khong them dependency MSW.
- Khong goi backend.
- Sample data phai du field toi thieu de table/card/dialog render.

