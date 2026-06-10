# SRS - Backend User Interface Table Column Settings

> Agent: SRS_WRITER  
> Ngay cap nhat: 31/05/2026  
> Trang thai: Approved for implementation  
> Scope chinh: `backend/smart-erp`  
> Lien quan frontend: `frontend/mini-erp/src/lib/table-column-settings.ts`

## 1. Muc tieu

Backend cung cap API + luu tru theo user cho cau hinh an/hien cot va thu tu cot cua 3 bang Kho hang:

- `inventory_stock`
- `inventory_receipts`
- `inventory_dispatch`

## 2. Functional Scope

- GET settings theo scope `inventory`.
- PUT settings theo payload `items[{tableKey, hiddenColumns, columnOrder}]`.
- Validate:
  - Table key hop le.
  - Column key hop le.
  - Required columns khong duoc an.
  - `columnOrder` khong duplicate.
- Normalize data khi doc/ghi:
  - Loai unknown keys.
  - Noi missing keys vao cuoi.
  - Bat required columns luon visible.
- Ghi he thong log khi save thanh cong.

## 3. Security

- Endpoint yeu cau authenticated user va `can_manage_inventory`.
- 401: phien dang nhap khong hop le/het han.
- 403: khong co quyen cau hinh giao dien Kho.

## 4. Data Model

Bang: `user_table_column_settings`

- Unique `(user_id, table_key)`.
- `hidden_columns` JSONB, default `[]`.
- `column_order` JSONB, default `[]`.
- FK `user_id -> users(id)` ON DELETE CASCADE.
- FK `updated_by -> users(id)` ON DELETE SET NULL.

## 5. Acceptance Criteria

1. User chua co data van nhan duoc default full metadata cho 3 bang.
2. Save payload hop le duoc upsert theo `(user_id, table_key)`.
3. Required column trong hiddenColumns bi reject 400.
4. columnOrder thieu key duoc normalize tu dong.
5. Save thanh cong co ghi system log.

