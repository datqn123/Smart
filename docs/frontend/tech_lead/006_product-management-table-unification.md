# Tech Spec - Product Management Table Unification

> Agent: TECH_SPEC_WRITER  
> Ngay cap nhat: 01/06/2026  
> Trang thai: READY_FOR_CODING

## 1. Handoff

- Source SRS: `docs/frontend/srs/007_product-management-table-unification.md`
- Scope:
  - `/products/categories`
  - `/products/list`
  - `/products/suppliers`
  - `/products/customers`
- Out of scope: backend/API contract, role rules, table column settings feature.

## 2. Files Edit

- `frontend/mini-erp/src/lib/data-table-layout.ts`
- `frontend/mini-erp/src/features/product-management/components/CategoryTable.tsx`
- `frontend/mini-erp/src/features/product-management/components/ProductTable.tsx`
- `frontend/mini-erp/src/features/product-management/components/SupplierTable.tsx`
- `frontend/mini-erp/src/features/product-management/components/CustomerTable.tsx`
- `frontend/mini-erp/src/features/product-management/components/CategoryToolbar.tsx`
- `frontend/mini-erp/src/features/product-management/components/ProductToolbar.tsx`
- `frontend/mini-erp/src/features/product-management/components/SupplierToolbar.tsx`
- `frontend/mini-erp/src/features/product-management/components/CustomerToolbar.tsx`
- `frontend/mini-erp/src/features/product-management/pages/CategoriesPage.tsx`
- `frontend/mini-erp/src/features/product-management/pages/ProductsPage.tsx`
- `frontend/mini-erp/src/features/product-management/pages/SuppliersPage.tsx`
- `frontend/mini-erp/src/features/product-management/pages/CustomersPage.tsx`

## 3. Design Decisions

- Reuse table contract from inventory:
  - `DATA_TABLE_SHELL_CLASS`
  - `DATA_TABLE_SCROLL_CLASS`
  - `DATA_TABLE_CHECKBOX_CLASS`
  - unified footer area in table shell.
- Remove blue-heavy focus/selection from product-management tables/toolbars; use slate neutral.
- Keep action column width stable by always rendering action icons and disabling by permission instead of hiding.
- Keep category hierarchical expand/collapse behavior unchanged.
- Keep API calls and query keys unchanged.

## 4. Implementation Plan

1. **Token/layout layer**
   - Normalize column widths in `data-table-layout.ts` for category/supplier/customer/product.
   - Use `DATA_TABLE_CHECKBOX_CLASS` in all 4 tables.
2. **Table layer**
   - Rename abbreviated labels to full Vietnamese labels.
   - Standardize row/header/action style.
   - Always render delete icon; disable based on `canDelete`.
3. **Toolbar layer**
   - Rename create button labels:
     - `Tao san pham`, `Tao nha cung cap`, `Tao khach hang`.
   - Remove blue-focused input/select classes; align with neutral style.
4. **Page shell/footer layer**
   - Ensure loading/error rendered inside shell for all 4 pages.
   - Add/normalize footer counters:
     - products/suppliers/customers: `dang hien thi X / Y ...`
     - categories: flattened count.
   - Keep footer position and height consistent.

## 5. Risks

- Action icon disable requires ensuring handlers are not invoked when disabled.
- Category table uses recursive rows; update must not break expand/collapse and select-all flatten behavior.
- Width rebalance can affect mobile overflow; verify with build and manual quick check.

## 6. Verification

- `npm run build`
- `npm run lint` (allow existing warnings, no new errors)
