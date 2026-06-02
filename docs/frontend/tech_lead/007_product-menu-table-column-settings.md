# Tech Spec - Product Menu Table Column Settings

> Agent: TECH_SPEC_WRITER  
> Ngay cap nhat: 01/06/2026  
> Trang thai: READY_FOR_CODING

## 1. Handoff

- Source SRS: `docs/frontend/srs/008_srs_product-menu-table-column-settings.md`.
- Goal: mo rong table column settings tu 3 bang Kho hang thanh 7 bang (them 4 bang San pham).
- Scope: backend + frontend; giu contract save/read hien co, them `scope=all`.

## 2. Backend Plan

- Them 4 `TableKey` moi trong `TableColumnCatalog`:
  - `product_categories`
  - `product_list`
  - `product_suppliers`
  - `product_customers`
- Bo sung metadata columns theo SRS cho 4 bang moi.
- Bo sung helpers scope:
  - `inventoryScope()`
  - `productScope()`
  - `allScope()`
- Controller:
  - GET chap nhan `scope=inventory|products|all`.
  - RBAC GET: `hasAnyAuthority('can_manage_inventory','can_manage_products','can_manage_customers')`.
  - PUT giu gate Admin/Owner nhu hien tai.
- Service:
  - tach method load theo scope (`getByScope(jwt, scope)`).
  - save cho phep toi da 7 items.
  - giu validate duplicate/unknown/required.
- DB:
  - migration moi cap nhat check constraint `global_table_column_settings.table_key` de chap nhan 4 key moi.

## 3. Frontend Plan

- `table-column-settings.ts`:
  - mo rong `TableKey` + defaults thanh 7 bang.
  - GET doi sang `scope=all`.
  - normalize data van fallback default khi API loi.
- Hook:
  - tong quat `useTableColumnOrder` de dung cho inventory + product-management.
  - tiep tuc reload theo `TABLE_COLUMN_SETTINGS_UPDATED_EVENT`.
- Product pages:
  - `ProductsPage`, `CategoriesPage`, `SuppliersPage`, `CustomersPage` truyen `visibleColumnKeys` vao table.
- Product table components:
  - bo sung prop `visibleColumnKeys`.
  - render business columns theo order/visible tu settings.
  - cot `select` va `thao tac` luon hien, khong thuoc settings.
- `InterfaceSettingsPage`:
  - copy text tong quat (khong chi Kho hang).

## 4. Risks

- Risk API scope: user chi co quyen customer co the bi chan neu GET gate sai.
- Risk column-key mismatch giua defaults FE va catalog BE.
- Risk tree table danh muc: khong duoc pha expand/collapse khi reorder columns.

## 5. Verification

- Backend: `mvnw -q -DskipTests compile`
- Frontend: `npm run build`
- Frontend tests chon loc neu co cho table components/settings mapping.
