# SRS - Phan Tich Loi Pham Vi Ap Dung Cau Hinh Cot

> Agent: SRS_WRITER  
> Ngay cap nhat: 31/05/2026  
> Trang thai: Draft bug analysis  
> Scope chinh: `frontend/mini-erp`  
> Lien quan backend: `backend/smart-erp` table column settings API  
> Anh dau vao: Admin thay doi cot `Vi tri`, Staff khong thay doi, trang cau hinh cua Admin da luu dung thu tu.

## 1. Tom Tat

Qua 3 anh:

- Anh 1: account Admin vao `Ton kho`, cot `Vi tri` da doi vi tri theo cau hinh mong muon.
- Anh 2: account Staff vao `Ton kho`, cot `Vi tri` van o thu tu cu.
- Anh 3: account Admin vao `Cau hinh giao dien`, thu tu cot da luu dung: `Ma SP`, `Ten san pham`, `Ton kho`, `Han SD`, `Trang thai`, `Vi tri`.

Ket luan SRS: day khong phai loi render rieng cua `StockTable`. Day la conflict ve pham vi ap dung cau hinh:

- Code/frontend hien tai doc/ghi cau hinh bang `localStorage`, theo browser/profile hien tai.
- Backend moi duoc thiet ke luu theo `user_id + table_key`, nghia la cau hinh ca nhan tung user.
- Ky vong tu anh va mo ta cua user lai la Admin cau hinh mot lan thi Staff cung phai thay doi theo.

Vi vay bug can duoc chot lai theo business rule: cau hinh cot la `user-specific`, `role-specific`, hay `global/store-wide`.

## 2. Evidence Va Traceability

### Frontend

- `frontend/mini-erp/src/lib/table-column-settings.ts`
  - `STORAGE_KEY = "mini_erp_table_column_settings_v1"`.
  - `getTableColumnSettings()` doc tu `window.localStorage`.
  - `saveTableColumnSettings()` ghi lai vao `window.localStorage`.
  - Khong goi `/api/v1/interface-settings/table-columns`.
- `frontend/mini-erp/src/features/settings/pages/InterfaceSettingsPage.tsx`
  - Load setting bang `getTableColumnSettings()`.
  - Save setting bang `saveTableColumnSettings()`.
- `frontend/mini-erp/src/features/inventory/components/StockTable.tsx`
  - Render theo prop `visibleColumnKeys`.
  - Neu `visibleColumnKeys` khac nhau theo account/browser thi table render khac nhau la dung logic hien tai.

### Backend

- `docs/backend/srs/001_user-interface-table-column-settings.md`
  - Ghi ro muc tieu backend luu cau hinh "theo user".
- `backend/smart-erp/src/main/resources/db/migration/V53__task121_user_table_column_settings.sql`
  - Unique `(user_id, table_key)`.
- `backend/smart-erp/src/main/java/com/example/smart_erp/settings/tablecolumns/service/TableColumnSettingsService.java`
  - `getInventoryScope(jwt)` lay `userId` tu JWT.
  - `saveInventoryScope(jwt, request)` upsert theo `userId`.
- `backend/smart-erp/src/main/java/com/example/smart_erp/settings/tablecolumns/repository/UserTableColumnSettingsJdbcRepository.java`
  - `findByUserId(int userId)`.
  - `upsert(userId, tableKey, ...)`.

## 3. GAP / Source Conflict Analysis

| Source | Dang noi gi | Tac dong |
| :--- | :--- | :--- |
| Anh user cung cap | Admin doi cot, Staff duoc ky vong cung thay doi | Ky vong nghiep vu nghieng ve global/role setting |
| Frontend code hien tai | Luu `localStorage` theo browser/profile | Khong dong bo giua account, browser, device |
| Backend SRS + DB moi | Luu theo `user_id` | Admin thay doi khong tac dong Staff |
| Trang `Cau hinh giao dien` | Copy noi dung noi "tuy chinh cot..." khong noi ro "cho rieng toi" hay "cho toan bo nhan vien" | UX gay hieu nham ve pham vi ap dung |

Root cause: thieu quyet dinh source-of-truth va scope ownership cho table column settings. Frontend tam thoi local-only; backend moi la user-only; user expectation la Admin-controlled shared setting.

## 4. Phan Loai Loi

### Neu requirement la "moi user tu cau hinh rieng"

- Hanh vi Staff khong thay doi la dung.
- Loi con lai: UI wording chua noi ro "Cau hinh nay chi ap dung cho tai khoan hien tai".
- Loi ky thuat: frontend chua wire backend API, nen Admin cung chi luu theo browser localStorage, khong dong bo sang device khac cua chinh Admin.

### Neu requirement la "Admin cau hinh cho toan bo nhan vien"

- Hanh vi Staff khong thay doi la bug P1 ve business expectation.
- Backend schema hien tai sai scope vi unique theo `(user_id, table_key)`.
- Frontend localStorage sai source-of-truth vi khong doc shared config tu backend.

### Neu requirement la "Admin cau hinh theo role"

- Can scope moi: `(role_id, table_key)` hoac `(scope_type, scope_id, table_key)`.
- Staff cung role se thay doi, role khac khong thay doi.
- Can UI cho Admin chon doi tuong ap dung: `Tai khoan cua toi`, `Tat ca Staff`, `Tat ca nguoi dung`, hoac `Theo vai tro`.

## 5. De Xuat Requirement Chot

Khuyen nghi cho ERP noi bo: tach 2 lop cau hinh.

1. Admin default setting theo role/toan he thong.
2. User personal override neu duoc phep.

Thu tu uu tien khi render:

```text
personal user setting -> role setting -> global setting -> default metadata
```

Neu muon lam nhanh dung voi ky vong hien tai, de xuat scope `global/store-wide`:

- Admin/Owner luu cau hinh cho `inventory_stock`.
- Staff doc cung cau hinh global.
- Staff khong co quyen sua cau hinh global, chi xem ket qua tren table.

## 6. Functional Requirements

### FR-1: Backend phai co source-of-truth shared setting

- Backend can ho tro it nhat mot shared scope:
  - `GLOBAL`: ap dung cho tat ca user co quyen xem table.
  - Hoac `ROLE`: ap dung theo role.
- Data khong duoc chi nam trong `localStorage`.

### FR-2: Frontend phai doc cau hinh tu backend

- Khi vao `Ton kho`, frontend can lay setting tu API hoac cache chung da preload.
- `StockTable` nhan `visibleColumnKeys` tu backend-normalized settings.
- Neu API loi, fallback default metadata va hien toast user-functional.

### FR-3: Trang cau hinh phai hien ro pham vi ap dung

- Neu global: hien label `Ap dung cho tat ca nguoi dung co quyen Kho hang`.
- Neu personal: hien label `Chi ap dung cho tai khoan hien tai`.
- Neu role-based: co select role va chi Admin/Owner thay doi duoc.

### FR-4: Save phai invalidate/cap nhat cac man lien quan

- Sau khi Admin save, cac table inventory doc lai setting moi.
- Neu user dang mo tab khac cung browser, can dispatch event hoac query invalidation.
- Neu user khac/browser khac, setting moi co hieu luc o lan reload/refetch tiep theo.

## 7. Backend HTTP Contract De Xuat

### GET effective setting

```http
GET /api/v1/interface-settings/table-columns?scope=inventory
Authorization: Bearer <token>
```

Response nen tra effective setting sau khi resolve scope:

```json
{
  "items": [
    {
      "tableKey": "inventory_stock",
      "tableLabel": "Ton kho",
      "scopeType": "GLOBAL",
      "columns": [
        { "key": "skuCode", "label": "Ma SP", "required": true, "visible": true, "order": 0 },
        { "key": "productName", "label": "Ten san pham", "required": true, "visible": true, "order": 1 },
        { "key": "quantity", "label": "Ton kho", "required": false, "visible": true, "order": 2 },
        { "key": "expiryDate", "label": "Han SD", "required": false, "visible": true, "order": 3 },
        { "key": "status", "label": "Trang thai", "required": false, "visible": true, "order": 4 },
        { "key": "location", "label": "Vi tri", "required": false, "visible": true, "order": 5 }
      ],
      "updatedAt": "2026-05-31T11:57:00Z",
      "updatedByName": "Nguyenx Chi Dat"
    }
  ]
}
```

### PUT shared setting

```http
PUT /api/v1/interface-settings/table-columns
Authorization: Bearer <admin_or_owner_token>
Content-Type: application/json
```

Request:

```json
{
  "scope": "inventory",
  "scopeType": "GLOBAL",
  "items": [
    {
      "tableKey": "inventory_stock",
      "hiddenColumns": [],
      "columnOrder": ["skuCode", "productName", "quantity", "expiryDate", "status", "location"]
    }
  ]
}
```

RBAC:

- GET: `can_manage_inventory` hoac quyen xem inventory.
- PUT global/role: Owner/Admin only, de xuat permission moi `can_manage_interface_settings`.
- Staff khong duoc ghi global setting.

## 8. Data Model De Xuat

Neu chot global/role, bang hien tai `user_table_column_settings` khong du:

Option A - Bang moi de ro nghia:

```text
table_column_settings
- id
- scope_type: GLOBAL | ROLE | USER
- scope_id: nullable, role_id/user_id tuy scope_type
- table_key
- hidden_columns
- column_order
- updated_by
- created_at
- updated_at
- unique(scope_type, scope_id, table_key)
```

Option B - Giu bang cu va them bang global:

```text
global_table_column_settings
- table_key unique
- hidden_columns
- column_order
- updated_by
- timestamps
```

De xuat A neu muon mo rong lau dai; de xuat B neu can fix nhanh.

## 9. Horizontal Analysis

- `inventory_receipts` va `inventory_dispatch` se gap y chang vi cung dung `TableColumnSetting`.
- Neu chi sua `StockTable`, bug se lap lai o `ReceiptTable` va `DispatchTable`.
- Neu chi sua backend ma frontend van localStorage, user/browser khac van khong thay doi.
- Neu chi sua frontend goi backend user-specific endpoint, Staff van khong thay doi vi backend dang luu theo `user_id`.
- Settings wording va RBAC dang chua noi ro ai duoc cau hinh cho ai.

## 10. Acceptance Criteria

```gherkin
Given Admin thay doi thu tu cot Ton kho thanh Ma SP, Ten san pham, Ton kho, Han SD, Trang thai, Vi tri
When Admin bam Luu thay doi
Then backend luu cau hinh vao shared scope da chot
And Admin reload /inventory/stock van thay cot Vi tri o cuoi
```

```gherkin
Given Staff co quyen xem Ton kho
And Admin da luu shared setting cho Ton kho
When Staff reload /inventory/stock
Then Staff thay cung thu tu cot voi shared setting
```

```gherkin
Given Staff khong co quyen quan ly cau hinh giao dien global
When Staff truy cap thao tac save global table column settings
Then backend tra 403
And frontend hien thong bao Ban khong co quyen cau hinh giao dien.
```

```gherkin
Given backend settings API tam thoi loi
When user vao /inventory/stock
Then frontend fallback ve default column order
And hien message khong lam sap trang.
```

## 11. Test Strategy

- Unit FE:
  - Resolve visible columns tu API setting.
  - Fallback default khi API fail.
  - Khong doc/ghi localStorage lam source-of-truth chinh neu da wire backend.
- Integration FE:
  - Mock Admin save global setting, Staff reload thay doi dung thu tu.
- Backend service:
  - Resolve effective setting theo thu tu scope da chot.
  - PUT global reject Staff.
  - Normalize duplicate/missing/unknown column keys.
- Regression:
  - `inventory_stock`, `inventory_receipts`, `inventory_dispatch`.
  - Khong anh huong checkbox/action column.

## 12. Open Questions

- OQ-1: PO chot scope mong muon la `GLOBAL`, `ROLE`, hay `USER`? Day la blocker truoc khi coding.
- OQ-2: Staff co duoc tu cau hinh ca nhan de override setting Admin khong?
- OQ-3: Menu `Cau hinh giao dien` co nen chi hien voi Admin/Owner khong neu setting la global?
- OQ-4: Co can migration chuyen data cu tu `user_table_column_settings` cua Admin sang global setting khong?

## 13. Ket Luan SRS

Hien tuong trong anh la dau hieu lech source-of-truth va lech pham vi ap dung. Neu muc tieu san pham la Admin cau hinh de Staff cung thay doi, can sua ca backend data model/API va frontend integration. Neu muc tieu la cau hinh ca nhan, can sua wording UI va wire frontend vao backend user-specific API de tranh localStorage-only.

De xuat mac dinh cho task fix tiep theo: chot `GLOBAL` scope cho 3 bang Kho hang, Admin/Owner duoc save, Staff chi doc effective setting.

