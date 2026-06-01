# Tech Spec - Table Column Settings Global Scope

> Agent: TECH_SPEC_WRITER  
> Ngay cap nhat: 01/06/2026  
> Trang thai: READY_FOR_CODING

## 1. Handoff

- Source SRS: `docs/frontend/srs/005_srs_table-column-settings-scope-conflict.md`.
- Muc tieu: Admin/Owner cau hinh cot inventory 1 lan, Staff thay doi theo (shared scope).
- Pham vi: `frontend/mini-erp` + `backend/smart-erp` cho endpoint `/api/v1/interface-settings/table-columns`.

## 2. Scope Chot

- Scope save/load: `GLOBAL` cho 3 table:
  - `inventory_stock`
  - `inventory_receipts`
  - `inventory_dispatch`
- Thu tu resolve hien tai:
  - global setting -> default metadata.
- Khong trien khai personal override trong dot nay.

## 3. Backend Changes

- Them bang global settings moi:
  - `global_table_column_settings`
  - unique theo `table_key`.
- Them JDBC repository global:
  - `findAll()`
  - `upsert(tableKey, hiddenColumns, columnOrder, updatedBy)`
- Refactor `TableColumnSettingsService`:
  - `getInventoryScope(jwt)` doc global.
  - `saveInventoryScope(jwt, request)` ghi global.
  - Validate payload giu nguyen (unknown key, duplicate key, required column).
  - Save global chi cho role `Owner|Admin`.
- Controller:
  - `GET` giu `can_manage_inventory`.
  - `PUT` them gate `can_manage_staff` + role check trong service.

## 4. Frontend Changes

- `table-column-settings.ts`:
  - bo localStorage lam source-of-truth.
  - goi backend GET/PUT bang `apiJson`.
  - giu `TABLE_COLUMN_SETTINGS_UPDATED_EVENT` de invalidation tab/hook.
  - fallback default metadata neu GET fail (khong crash page).
- `InterfaceSettingsPage.tsx`:
  - copy text ro scope global.
  - toast loi khi save fail/403.
- `useTableVisibleColumns.ts`:
  - tiep tuc reload theo custom event (khong phu thuoc localStorage key).

## 5. Risk Va Mitigation

- Risk: role claim khong dong bo voi authority.
  - Mitigation: gate 2 lop (`@PreAuthorize` + role check trong service).
- Risk: data cu o `user_table_column_settings` khong duoc dung nua.
  - Mitigation: chap nhan bo qua trong dot nay, co the migration data sau.
- Risk ngang: inventory stock/receipts/dispatch can dong bo.
  - Mitigation: hook dung chung `useTableVisibleColumns` nen fix 1 lan cho 3 man.

## 6. Ready For QA

- Admin save -> Staff reload thay doi thu tu cung nhau.
- Staff save -> 403.
- API fail GET -> table van render default columns.
