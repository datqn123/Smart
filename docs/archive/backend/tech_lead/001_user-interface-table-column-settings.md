# TECH SPEC - Backend User Interface Table Column Settings

> Agent: TECH_SPEC_WRITER  
> Ngay cap nhat: 31/05/2026  
> Input: `docs/backend/srs/001_user-interface-table-column-settings.md`

## 1. Kien truc

- Controller: `InterfaceSettingsTableColumnsController`
- Service: `TableColumnSettingsService`
- Repository: `UserTableColumnSettingsJdbcRepository`
- Metadata source backend: `TableColumnCatalog`
- Migration: `V53__task121_user_table_column_settings.sql`

## 2. API Contract

1. `GET /api/v1/interface-settings/table-columns?scope=inventory`
2. `PUT /api/v1/interface-settings/table-columns`

Response duoc dong goi theo `ApiSuccessResponse`.

## 3. Validation va Normalization

- Reject `scope` khac `inventory`.
- Reject `items` rong hoac > 3.
- Reject table key khong nam trong catalog.
- Reject unknown keys trong `hiddenColumns`/`columnOrder`.
- Reject required keys neu bi an.
- Reject duplicate keys trong `columnOrder`.
- Khi save/read:
  - Loai key la.
  - Noi key thieu vao cuoi theo default order.
  - Required column ep `visible=true`.

## 4. Logging

- Ghi `system_logs` thong qua `SystemLogJdbcRepository.insertInventoryPatch(...)`.
- Entity: `UserTableColumnSettings`.

## 5. Risk va Horizontal Analysis

- Risk 1: Frontend co the gui stale key khi metadata thay doi.
  - Mitigation: reject unknown key + details de FE sua som.
- Risk 2: DB data legacy/thu cong khong dung shape.
  - Mitigation: normalize toan bo du lieu khi GET.
- Risk 3: Scope inventory co the bi truy cap boi user khong quyen.
  - Mitigation: `can_manage_inventory` tren ca GET/PUT.

## 6. Rollout

1. Chay migration `V53`.
2. Deploy backend.
3. Frontend call GET khi mo page va PUT khi save.
4. Theo doi log 400 validation trong 24h dau.

