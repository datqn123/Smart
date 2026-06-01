# QA SPEC - Backend User Interface Table Column Settings

> Agent: QA_SPEC_WRITER  
> Ngay cap nhat: 31/05/2026  
> Input: `docs/backend/tech_lead/001_user-interface-table-column-settings.md`

## 1. Test Scope

- Unit test service validation + normalization.
- Repository upsert/read.
- Controller authz/authn + happy path + bad request.
- Migration schema validation.

## 2. Test Cases

1. GET khi user chua co settings:
   - Expect 200 + 3 table defaults.
2. PUT payload hop le:
   - Expect 200 + normalized response.
   - Verify DB upsert row theo `(user_id, table_key)`.
3. PUT hidden required column:
   - Expect 400 + details field ro key loi.
4. PUT unknown column key:
   - Expect 400.
5. PUT duplicate key trong `columnOrder`:
   - Expect 400.
6. GET/PUT khong token:
   - Expect 401.
7. GET/PUT khong quyen inventory:
   - Expect 403.

## 3. Regression Matrix (Horizontal)

- Khong duoc anh huong API:
  - `InventoryController`
  - `StockReceiptsController`
  - `StockDispatchesController`
- Khong thay doi behavior cua alert settings va auth flow.

## 4. Exit Criteria

- Unit tests cho service pass.
- Build backend pass.
- Co it nhat 1 lan manual verify GET/PUT voi token hop le.

