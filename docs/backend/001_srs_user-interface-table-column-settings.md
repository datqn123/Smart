# SRS - Backend User Interface Table Column Settings

> Agent: SRS_WRITER  
> Ngay cap nhat: 31/05/2026  
> Trang thai: Draft for backend implementation  
> Scope chinh: `backend/smart-erp`  
> Lien quan frontend: `frontend/mini-erp/src/lib/table-column-settings.ts`

## 1. Tom tat

- **Van de**: Frontend da co tinh nang `Cau hinh giao dien` cho 3 table Kho hang, hien dang luu tam bang `localStorage`, nen cau hinh khong dong bo theo tai khoan va mat khi user doi trinh duyet/thiet bi.
- **Muc tieu**: Backend can cung cap data/API de luu va doc cau hinh an/hien cot + thu tu cot theo tung user dang dang nhap.
- **Doi tuong**: Owner/Admin/Staff dang dang nhap va su dung 3 man hinh Kho hang.
- **Pham vi table UI**:
  - `inventory_stock`
  - `inventory_receipts`
  - `inventory_dispatch`

## 2. Input va traceability

- Frontend contract hien tai:

```ts
type TableKey =
  | "inventory_stock"
  | "inventory_receipts"
  | "inventory_dispatch"

type SaveTableColumnSettingsBody = {
  items: {
    tableKey: TableKey
    hiddenColumns: string[]
    columnOrder: string[]
  }[]
}
```

- Metadata cot hien tai nam o `frontend/mini-erp/src/lib/table-column-settings.ts`.
- Cac API Kho hang dang dung permission `can_manage_inventory` tai:
  - `InventoryController`
  - `StockReceiptsController`
  - `StockDispatchesController`
- Hien chua co backend endpoint/table rieng cho interface settings.

## 3. Pham vi

### 3.1 In-scope

- Tao DB table luu cau hinh cot table theo `user_id + table_key`.
- Tao API doc/save cau hinh cot cho frontend.
- Validate table key, column key, required column, duplicate order.
- Tra response du metadata de frontend render truc tiep neu backend muon lam source of truth.
- Ghi audit log he thong khi user luu thay doi cau hinh.

### 3.2 Out-of-scope

- Khong lam UI keo tha drag-and-drop.
- Khong luu width cot.
- Khong ap dung ngoai 3 table Kho hang.
- Khong cau hinh checkbox chon dong, cot `Thao tac`, footer so ban ghi.
- Khong thay doi API nghiep vu ton kho/phieu nhap/phieu xuat.

## 4. Persona va RBAC

- API yeu cau user da dang nhap hop le.
- De tranh user khong co quyen Kho hang cau hinh table Kho hang, backend nen yeu cau:
  - `GET /api/v1/interface-settings/table-columns` -> authenticated + `can_manage_inventory`
  - `PUT /api/v1/interface-settings/table-columns` -> authenticated + `can_manage_inventory`
- 401:
  - `Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.`
- 403:
  - `Bạn không có quyền cấu hình giao diện Kho hàng.`

## 5. Backend HTTP Contract

### 5.1 GET table column settings

```http
GET /api/v1/interface-settings/table-columns?scope=inventory
Authorization: Bearer <access_token>
```

Response 200:

```json
{
  "items": [
    {
      "tableKey": "inventory_stock",
      "tableLabel": "Tồn kho",
      "columns": [
        {
          "key": "skuCode",
          "label": "Mã SP",
          "required": true,
          "visible": true,
          "order": 0
        }
      ],
      "updatedAt": "2026-05-31T10:20:30Z",
      "updatedByName": "Nguyenx Chí Đạt"
    }
  ]
}
```

Rules:

- Neu user chua tung luu setting, tra ve default metadata cho ca 3 table.
- Required columns luon `visible=true`.
- `columns` phai du tat ca cot configurable cua table, da sap xep theo `order`.
- Backend khong tra ve checkbox/action/footer trong `columns`.

### 5.2 Save table column settings

```http
PUT /api/v1/interface-settings/table-columns
Authorization: Bearer <access_token>
Content-Type: application/json
```

Request:

```json
{
  "items": [
    {
      "tableKey": "inventory_dispatch",
      "hiddenColumns": ["dispatchDate"],
      "columnOrder": [
        "dispatchCode",
        "orderCode",
        "customerName",
        "userName",
        "itemCount",
        "status",
        "dispatchDate"
      ]
    }
  ]
}
```

Response 200: tra lai cung shape voi GET sau khi normalize.

Validation:

- `items` bat buoc co 1-3 phan tu.
- `tableKey` chi chap nhan 3 gia tri trong scope.
- `hiddenColumns` chi gom optional column keys cua table.
- Required columns khong duoc nam trong `hiddenColumns`.
- `columnOrder` khong duoc co duplicate.
- Backend bo qua hoac reject unknown column key. Yeu cau uu tien: reject 400 de FE sua bug som.
- Neu `columnOrder` thieu cot hop le, backend noi cac cot thieu vao cuoi theo default order.

Error 400 example:

```json
{
  "message": "Dữ liệu cấu hình cột không hợp lệ. Vui lòng kiểm tra lại.",
  "details": {
    "items[0].hiddenColumns": "Cột bắt buộc dispatchCode không thể bị ẩn."
  }
}
```

## 6. Data va SQL

### 6.1 Table moi de xuat

Ten table: `user_table_column_settings`

Columns:

| Column | Type | Required | Note |
| :--- | :--- | :--- | :--- |
| `id` | `BIGSERIAL` | yes | Primary key |
| `user_id` | `BIGINT` | yes | FK `users(id)` ON DELETE CASCADE |
| `table_key` | `VARCHAR(80)` | yes | UI table key |
| `hidden_columns` | `JSONB` | yes | Array string, default `[]` |
| `column_order` | `JSONB` | yes | Array string, default `[]` |
| `created_at` | `TIMESTAMPTZ` | yes | default `now()` |
| `updated_at` | `TIMESTAMPTZ` | yes | update khi save |

Constraints/indexes:

- Unique: `(user_id, table_key)`.
- Check `table_key IN ('inventory_stock', 'inventory_receipts', 'inventory_dispatch')`.
- Index: `(user_id)`.
- JSON shape validation co the lam o service layer thay vi SQL check phuc tap.

### 6.2 Default metadata backend can biet

`inventory_stock`:

- Required: `skuCode`, `productName`
- Optional: `location`, `quantity`, `expiryDate`, `status`

`inventory_receipts`:

- Required: `receiptCode`
- Optional: `supplierName`, `receiptDate`, `staffName`, `invoiceNumber`, `lineCount`, `totalAmount`, `status`

`inventory_dispatch`:

- Required: `dispatchCode`
- Optional: `orderCode`, `customerName`, `dispatchDate`, `userName`, `itemCount`, `status`

## 7. Business Rules

- BR-1: Setting la theo user, khong phai global cua cua hang.
- BR-2: Mot user co toi da 1 record cho moi `table_key`.
- BR-3: Save la upsert theo `(user_id, table_key)`.
- BR-4: Required columns luon hien thi, khong duoc an.
- BR-5: `column_order` dai dien thu tu full list configurable columns, bao gom ca visible va hidden.
- BR-6: Neu data DB bi lech voi metadata hien tai, backend normalize khi GET:
  - Loai unknown key.
  - Them missing known key theo default order.
  - Bat lai required columns ve visible.
- BR-7: System columns (checkbox, action, footer) khong bao gio luu vao setting.
- BR-8: Moi save thanh cong nen ghi `system_logs` voi entity `UserTableColumnSettings` hoac ten tuong duong.

## 8. Horizontal analysis

- Pattern gan giong `alertsettings`: user/owner-specific configuration.
- Khac voi inventory transaction tables: setting nay khong anh huong so lieu kho, khong can transaction lien quan inventory/receipts/dispatches.
- Can dong bo voi RBAC/menu permission vi UI setting nam trong Settings nhung du lieu ap dung cho Kho hang.
- Khong lien quan AI runtime; LangGraph/Harness/tools khong bi anh huong.

## 9. Non-functional requirements

- NFR-1: GET phai nhanh, chi query theo current user; response nho.
- NFR-2: Save phai idempotent: gui cung payload nhieu lan cho cung ket qua.
- NFR-3: Khong log raw JWT, stack trace, SQL error ra client.
- NFR-4: API response dung envelope/error convention hien co cua backend.
- NFR-5: Migration phai rollback-safe ve mat data: them table moi, khong sua bang nghiep vu cu.

## 10. Acceptance Criteria

```gherkin
Given user chua co cau hinh cot
When GET /api/v1/interface-settings/table-columns?scope=inventory
Then backend tra default settings cho 3 table Kho hang
```

```gherkin
Given user da an cot dispatchDate cua inventory_dispatch
When user luu cau hinh
Then backend upsert record theo user_id + table_key
And GET lan sau tra dispatchDate visible=false
```

```gherkin
Given request hiddenColumns co required column dispatchCode
When PUT /api/v1/interface-settings/table-columns
Then backend tra 400
And khong ghi thay doi vao DB
```

```gherkin
Given request columnOrder thieu optional column
When PUT /api/v1/interface-settings/table-columns
Then backend normalize bang cach noi cot thieu vao cuoi theo default order
```

## 11. Test strategy

- Unit tests:
  - Validate allowed table keys.
  - Validate required columns cannot be hidden.
  - Normalize missing/unknown/duplicate column order.
- Repository/service tests:
  - Upsert insert moi.
  - Upsert update record cu.
  - Read defaults khi user chua co record.
- Controller tests:
  - 200 GET.
  - 200 PUT.
  - 400 invalid required hidden.
  - 401 unauthenticated.
  - 403 missing `can_manage_inventory`.
- Migration test:
  - Table, unique constraint, FK users, check table key.

## 12. Open Questions

- OQ-1: API co nen yeu cau `can_manage_inventory` hay chi authenticated user? De xuat: `can_manage_inventory`, vi setting chi ap dung cho 3 bang Kho hang.
- OQ-2: Co can endpoint reset default rieng khong? De xuat: chua can, frontend co the save payload default.

