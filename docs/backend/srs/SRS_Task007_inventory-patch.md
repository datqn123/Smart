# SRS — Task007 — `PATCH /api/v1/inventory/{id}` — Cập nhật meta một dòng tồn

> **File:** `backend/docs/srs/SRS_Task007_inventory-patch.md`  
> **Người soạn:** Agent BA + SQL (Draft)  
> **Ngày:** 26/04/2026  
> **Trạng thái:** Draft  
> **PO duyệt (khi Approved):** Approved

---

## 0. Đầu vào & traceability

| Nguồn | Đường dẫn / ghi chú |
| :--- | :--- |
| API spec | [`../../../frontend/docs/api/API_Task007_inventory_patch.md`](../../../frontend/docs/api/API_Task007_inventory_patch.md) |
| Thiết kế API | [`../../../frontend/docs/api/API_PROJECT_DESIGN.md`](../../../frontend/docs/api/API_PROJECT_DESIGN.md) §4.7 |
| UC / DB (mô tả) | [`../../../frontend/docs/UC/Database_Specification.md`](../../../frontend/docs/UC/Database_Specification.md) §16 `Inventory`, §5 `WarehouseLocations`, §7 `Products` |
| Flyway V1 (chân lý triển khai) | [`../../smart-erp/src/main/resources/db/migration/V1__baseline_smart_inventory.sql`](../../smart-erp/src/main/resources/db/migration/V1__baseline_smart_inventory.sql) — `Inventory`, `Products`, `WarehouseLocations`, `SystemLogs`, `Notifications` |
| Liên quan | Task005 list; Task006 GET by id; Task008 bulk PATCH; Task010 điều chỉnh `quantity`; Task011/012 audit/notify (hậu xử lý) |

---

## 1. Tóm tắt điều hành

- **Vấn đề:** Cần API **ghi một phần** meta tồn (vị trí, định mức, lô, HSD) cho **một** `Inventory.id` mà **không** đổi `quantity` tại endpoint này (tránh thiếu `InventoryLogs` / nghiệp vụ Task010).
- **Mục tiêu:** `PATCH /api/v1/inventory/{id}` partial JSON; **200** trả `data` cùng **shape** phần tử list Task005 (join read-model); lỗi **400 / 401 / 403 / 404 / 409 / 500** theo envelope.
- **Đối tượng:** Owner / Staff (UC6 — theo API); Admin nếu policy đồng nhất Task005/006.

---

## 2. Bóc tách nghiệp vụ (capabilities)

| # | Capability | Kích hoạt | Kết quả |
| :---: | :--- | :--- | :--- |
| C1 | Xác thực JWT | Mọi request | 401 nếu token không hợp lệ |
| C2 | RBAC sửa tồn UC6 | Sau JWT | 403 nếu không đủ quyền |
| C3 | Validate path `id` | Trước ghi | 400 nếu `id` không phải số nguyên dương |
| C4 | Validate JSON body | Trước ghi | 400 nếu rỗng / field lạ / field cấm (`quantity`, `costPrice`, …) / `expiryDate` sai format |
| C5 | Đọc + khóa dòng `Inventory` | Trong transaction | 404 nếu không có dòng; 409 nếu vị trí SP/location policy chặn (theo API §7.1) |
| C6 | Kiểm tra `locationId` đích (nếu gửi) | Trước UPDATE | **400** + `details.locationId` nếu không tồn tại (OQ-1); **409** nếu `Maintenance` / policy chặn |
| C7 | Kiểm tra UNIQUE `(product_id, location_id, batch_number)` sau merge | Trước UPDATE | 409 nếu trùng dòng khác |
| C8 | `UPDATE` chỉ cột cho phép | Body hợp lệ | `location_id`, `min_quantity`, `batch_number`, `expiry_date` — **không** `quantity` |
| C9 | Trả read-model sau commit | Sau UPDATE | 200 + `data` giống field list Task005 + message thành công |
| C10 | Hậu xử lý Task011 + Task012 | Sau commit (cùng transaction hoặc ngay sau — OQ-3) | **Bắt buộc** `INSERT systemlogs`; `INSERT notifications` khi actor Staff (chi tiết Task012); có thể tách sprint **Task007_02** nếu PM chia nhỏ |

---

## 3. Phạm vi

### 3.1 In-scope

- `PATCH /api/v1/inventory/{id}`, Bearer, `Content-Type: application/json`.
- Body (camelCase): `locationId`, `minQuantity`, `batchNumber`, `expiryDate`, `unitId` (sau migration OQ-2).
- Một transaction ghi + kiểm tra trùng + đọc lại/join cho response + **hậu xử lý log/notify** (OQ-3).
- **Migration (OQ-2):** thêm cột `inventory.unit_id` (FK → `productunits`, ràng buộc `productunits.product_id = inventory.product_id`) — Flyway `V{n}__task007_inventory_unit_id.sql` (tên file theo convention team).

### 3.2 Out-of-scope

- Bulk nhiều `id` — Task008.
- Đổi `quantity` — Task010 / phiếu nhập-xuất.
- Đổi giá vốn sản phẩm — API giá / `ProductPriceHistory` (endpoint riêng).
- Chi tiết đọc trước sửa — Task006 (GET).

---

## 4. Câu hỏi làm rõ cho PO (Open Questions) — **đã chốt**

| ID | Câu hỏi | Ảnh hưởng | Blocker? |
| :--- | :--- | :--- | :---: |
| OQ-1 | `locationId` không tồn tại: **400** hay **404**? | Assert HTTP / thông điệp | ~~Có~~ → đã chốt |
| OQ-2 | `unitId` trên API: V1 chưa có cột `inventory.unit_id` — xử lý thế nào? | Migration + validation | ~~Có~~ → đã chốt |
| OQ-3 | Task011 `SystemLogs` + Task012 `Notifications`: bắt buộc hay tách task? | Scope / nhánh release | ~~Không~~ → đã chốt |

**Quyết định PO (nguồn sự thật triển khai):**

| ID | Quyết định PO | Ngày |
| :--- | :--- | :--- |
| OQ-1 | **`locationId` trỏ tới `warehouselocations.id` không tồn tại → HTTP 400** + `details.locationId` (không dùng 404 để phân biệt với “không có dòng tồn”). | 26/04/2026 |
| OQ-2 | **Tiến hành bổ sung:** thêm cột `unit_id` trên `inventory` (migration Flyway) + cập nhật UC/ERD sau; PATCH được phép gửi `unitId` khi thỏa FK và `productunits.product_id` khớp `inventory.product_id`. | 26/04/2026 |
| OQ-3 | **Bắt buộc** thực hiện ghi **SystemLogs** (Task011) và luồng **Notifications** cho Staff (Task012) sau khi PATCH thành công. Nếu gộp một Task007 quá nặng, **PM được tách** thành **Task007_01** (PATCH + migration + read-model) và **Task007_02** (audit log + notify / outbox) — hợp đồng API `PATCH` vẫn thuộc 007_01; 007_02 là hậu xử lý đồng bộ. | 26/04/2026 |

---

## 5. Phân tích scope tệp & bằng chứng

### 5.1 Đã đối chiếu

- `API_Task007_inventory_patch.md`, `API_Task005_inventory_get_list.md` (shape `data`).
- Flyway: `Inventory` (`id` SERIAL, `product_id`, `location_id`, `batch_number`, `expiry_date`, `quantity` INT, `min_quantity` INT, `updated_at`), `Products.status` (`Active`|`Inactive`), `WarehouseLocations.status` (`Active`|`Maintenance`|`Inactive`), `SystemLogs`, `Notifications`.

### 5.2 Dự kiến chỉnh mã (`smart-erp`)

- `inventory/controller/InventoryController.java` — thêm `PATCH /inventory/{id}`.
- Service + validation (body partial, deny-list fields).
- JDBC/JPA cập nhật + SELECT read-model (có thể tái sử dụng query join giống Task005/006 sau UPDATE).
- **Migration bắt buộc (OQ-2):** `ALTER TABLE inventory ADD COLUMN unit_id …` + FK/index theo Tech Lead.
- Service/handler **SystemLogs** + **Notifications** (OQ-3) — hoặc module riêng Task007_02 nếu PM tách.

### 5.3 Rủi ro

- **GAP UC vs Flyway:** `Database_Specification` §16 ghi `quantity`/`min_quantity` DECIMAL; V1 `Inventory` dùng **INT** — SRS bám **Flyway** khi code & AC.

---

## 6. Persona & RBAC

| Điều kiện | HTTP |
| :--- | :--- |
| Không token / token sai | **401** |
| Không quyền sửa tồn UC6 | **403** |
| Dòng không tồn tại (hoặc ngoài phạm vi nếu sau này đa-tenant) | **404** (có thể đồng nhất Task006 OQ-1) |

**Task101 (chốt mặc định SRS — chỉnh nếu PO ra addendum):** **Cùng** authority **`can_manage_inventory`** cho `PATCH` như GET list / GET by id (Task005/006); chưa tách quyền “chỉ đọc”.

---

## 7. Actor & luồng nghiệp vụ

### 7.1 Actor

| Actor | Vai trò |
| :--- | :--- |
| User | Sửa form một dòng tồn |
| Client | `PATCH` + JSON |
| API | Validate, transaction, UPDATE |
| DB | `Inventory`, join kiểm tra SP/location |

### 7.2 Sơ đồ

```mermaid
sequenceDiagram
  participant U as User
  participant C as Client
  participant A as API
  participant D as DB
  U->>C: Submit sửa meta
  C->>A: PATCH /inventory/{id} + JSON
  A->>D: BEGIN; SELECT ... FOR UPDATE
  D-->>A: row / empty
  alt Hợp lệ
    A->>D: CHECK unique + UPDATE (+ unit_id nếu có)
    A->>D: INSERT systemlogs / notifications (OQ-3)
    A->>D: COMMIT; SELECT read-model
    A-->>C: 200 + data
  else Lỗi nghiệp vụ
    A->>D: ROLLBACK
    A-->>C: 4xx
  end
```

---

## 8. Hợp đồng HTTP & ví dụ JSON

### 8.1 Tổng quan

| Thuộc tính | Giá trị |
| :--- | :--- |
| Method + path | `PATCH /api/v1/inventory/{id}` |
| Auth | `Bearer` |
| Content-Type | `application/json` |

### 8.2 Path

| Param | Kiểu | Bắt buộc |
| :--- | :--- | :---: |
| `id` | int > 0 | Có |

### 8.3 Body — schema (field-level)

| Field | Kiểu | Ghi chú |
| :--- | :--- | :--- |
| `locationId` | int | FK `warehouselocations.id` |
| `minQuantity` | number | `>= 0` (INT trên V1) |
| `batchNumber` | string \| null | max 100; UNIQUE với `product_id` + `location_id` |
| `expiryDate` | string \| null | `YYYY-MM-DD` |
| `unitId` | int | Sau migration OQ-2 — FK `productunits`; bắt buộc `productunits.product_id = inventory.product_id` |

### 8.4 Request — ví dụ đầy đủ

```http
PATCH /api/v1/inventory/101 HTTP/1.1
Host: <api-host>
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "locationId": 3,
  "minQuantity": 60,
  "batchNumber": "LOT-2026-01",
  "expiryDate": "2026-12-31"
}
```

### 8.5 Response `200` — ví dụ đầy đủ

```json
{
  "success": true,
  "data": {
    "id": 101,
    "productId": 12,
    "productName": "Nước suối 500ml",
    "skuCode": "SKU-WAT-500",
    "barcode": "8934563123456",
    "locationId": 3,
    "warehouseCode": "WH01",
    "shelfCode": "A1",
    "batchNumber": "LOT-2026-01",
    "expiryDate": "2026-12-31",
    "quantity": 240,
    "minQuantity": 60,
    "unitId": 5,
    "unitName": "Chai",
    "costPrice": 4500,
    "updatedAt": "2026-04-23T10:15:00Z",
    "isLowStock": false,
    "isExpiringSoon": false,
    "totalValue": 1080000
  },
  "message": "Đã cập nhật thông tin tồn kho"
}
```

### 8.6 Response lỗi — mẫu

**400 — body rỗng / field cấm**

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Dữ liệu không hợp lệ",
  "details": {
    "body": "Cần ít nhất một trường để cập nhật",
    "quantity": "Thay đổi số lượng thực tế phải dùng POST /api/v1/inventory/adjustments (Task010)"
  }
}
```

**400 — `locationId` không tồn tại (OQ-1)**

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Dữ liệu không hợp lệ",
  "details": {
    "locationId": "Vị trí kho không tồn tại"
  }
}
```

**400 — `unitId` không hợp lệ (sai SP / không có trong `productunits`)**

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Dữ liệu không hợp lệ",
  "details": {
    "unitId": "Đơn vị không thuộc sản phẩm của dòng tồn này"
  }
}
```

**401 / 403 / 404 / 409 / 500** — khớp mẫu [`API_Task007_inventory_patch.md`](../../../frontend/docs/api/API_Task007_inventory_patch.md) §8.

---

## 9. Quy tắc nghiệp vụ

| Mã | Quy tắc |
| :--- | :--- |
| BR-1 | **Cấm** `quantity`, `costPrice`, `productId`, … trong body — 400 + `details`. |
| BR-2 | Ít nhất **một** field được phép phải có trong body (sau khi loại field cấm). |
| BR-3 | `min_quantity >= 0`; `expiry_date` parse DATE UTC/ngày theo convention dự án. |
| BR-4 | Sau merge logic, `(product_id, effective_location_id, effective_batch)` không trùng dòng khác — 409 nếu vi phạm `uq_inventory_product_location_batch`. |
| BR-5 | Nếu `Products.status = 'Inactive'` hoặc location `Maintenance` và policy chặn sửa meta → **409** (theo API). |
| BR-6 | `unitId` (OQ-2): chỉ khi migration đã deploy; giá trị phải là `productunits.id` với **cùng** `product_id` với dòng tồn — sai → **400** `details.unitId`. |
| BR-7 | OQ-3: sau `UPDATE` thành công, ghi **SystemLogs** (level/module/action/message/`context_data` JSON before/after tối thiểu); nếu actor là Staff thì tạo **Notifications** theo Task012 (cùng transaction hoặc transaction liền kề — chốt Dev; nếu tách Task007_02 thì 007_01 publish sự kiện / gọi dịch vụ 007_02). |

---

## 10. Dữ liệu & SQL tham chiếu (PostgreSQL / V1)

> Placeholder `:id`, transaction bắt buộc; `/* rbac */` nếu sau này đa-tenant.

### 10.1 Bảng

| Bảng | Read / Write |
| :--- | :--- |
| `inventory` | Read + UPDATE (gồm `unit_id` sau migration OQ-2) |
| `products` | Read (status) |
| `warehouselocations` | Read (status), validate `location_id` mới |
| `productunits` / `productpricehistory` | Read (response read-model giống Task005) |
| `systemlogs` | INSERT — **bắt buộc** (OQ-3 / Task011) |
| `notifications` | INSERT — **bắt buộc** khi điều kiện Staff (OQ-3 / Task012) |

### 10.2 Đọc khóa dòng (API §7.1 — dialect PG)

```sql
SELECT
  i.id,
  i.product_id,
  i.location_id,
  i.batch_number,
  i.expiry_date,
  i.min_quantity,
  i.quantity,
  p.status AS product_status,
  wl.status AS location_status
FROM inventory i
JOIN products p ON p.id = i.product_id
JOIN warehouselocations wl ON wl.id = i.location_id
WHERE i.id = :id
FOR UPDATE OF i;
```

### 10.3 Kiểm tra trùng UNIQUE (sau merge hiệu lực)

```sql
SELECT COUNT(*)::int AS cnt
FROM inventory
WHERE product_id = :product_id
  AND location_id = :effective_location_id
  AND COALESCE(batch_number, '') = COALESCE(:effective_batch_number, '')
  AND id <> :id;
```

_(Cảnh báo: so khớp NULL `batch_number` theo rule nghiệp vụ/seed — có thể khác COUNT nếu nhiều NULL; ghi GAP §12.)_

### 10.4 Migration gợi ý (OQ-2 — PostgreSQL)

```sql
ALTER TABLE inventory
  ADD COLUMN unit_id INT NULL
    REFERENCES productunits(id) ON DELETE SET NULL;

CREATE INDEX idx_inv_unit ON inventory(unit_id);

COMMENT ON COLUMN inventory.unit_id IS 'Đơn vị hiển thị/ghi nhận meta; quantity vẫn theo đơn vị cơ sở (nghiệp vụ UC).';
```

Ứng dụng: `CHECK` hoặc trigger đảm bảo mọi `unit_id` NOT NULL thỏa `productunits.product_id = inventory.product_id` (hoặc chỉ cho phép đơn vị thuộc SP trong service layer).

### 10.5 UPDATE động (ví dụ `min_quantity` + `unit_id`)

```sql
UPDATE inventory
SET min_quantity = :min_quantity,
    unit_id = :unit_id,
    updated_at = CURRENT_TIMESTAMP
WHERE id = :id;
```

_(Chỉ SET các cột có trong body hợp lệ; `unit_id` chỉ khi client gửi và đã qua validate.)_

### 10.6 Hậu xử lý — `systemlogs` (mẫu tối thiểu)

```sql
INSERT INTO systemlogs (log_level, module, action, user_id, message, context_data)
VALUES (
  'INFO',
  'inventory',
  'PATCH_INVENTORY',
  :user_id,
  'Cập nhật meta tồn kho',
  :context_jsonb
);
```

`context_jsonb`: `{ "inventoryId": …, "before": {…}, "after": {…} }` — chi tiết cột theo Task011.

### 10.7 Transaction

- Chuỗi khuyến nghị: `BEGIN` → `SELECT … FOR UPDATE` → validate → duplicate check → `UPDATE` → `INSERT systemlogs` → (điều kiện Staff) `INSERT notifications` → `COMMIT` → `SELECT` read-model trả 200.
- Nếu **Task007_02** tách khỏi 007_01: 007_01 `COMMIT` sau UPDATE + read-model; 007_02 nhận payload (async/outbox) để log/notify — **không** làm thay đổi hợp đồng HTTP PATCH.
- Lỗi unique từ DB: map **409** nếu chưa bắt ở tầng ứng dụng.

### 10.8 Đọc lại response (join giống Task005/006)

- Sau UPDATE, chạy lại SELECT list-row (LATERAL giá) theo `id` để map `InventoryListItemData` / DTO tương đương; **`unit_id` trong response** phải khớp cột mới (FE/API Task005 có field `unitId` — đồng bộ).

---

## 11. Acceptance criteria (Given / When / Then)

```text
Given JWT hợp lệ và đủ quyền, tồn tại inventory id=101
When PATCH với body hợp lệ chỉ minQuantity
Then 200, data.id=101, data.minQuantity mới, quantity không đổi
```

```text
Given cùng điều kiện
When PATCH body chứa quantity
Then 400, details.quantity chứa hướng dẫn Task010
```

```text
Given id không tồn tại
When PATCH
Then 404
```

```text
Given PATCH tạo trùng (product_id, location_id, batch_number) với dòng khác
Then 409
```

```text
Given body rỗng {}
When PATCH
Then 400
```

```text
Given location đích Maintenance và policy chặn
When PATCH đổi locationId
Then 409
```

```text
Given token không hợp lệ
When PATCH
Then 401
```

```text
Given JWT hợp lệ và locationId trỏ tới id không tồn tại
When PATCH chỉ đổi locationId
Then 400, details.locationId (OQ-1)
```

```text
Given migration unit_id đã deploy và unitId không thuộc product_id của dòng tồn
When PATCH có unitId
Then 400, details.unitId
```

```text
Given PATCH thành công
When đọc systemlogs
Then có bản ghi INFO module inventory action PATCH_INVENTORY với context before/after (OQ-3)
```

---

## 12. GAP & giả định

| GAP | Ghi chú |
| :--- | :--- |
| UC §16 DECIMAL vs Flyway INT | Code & test bám Flyway V1 |
| `batch_number` NULL + UNIQUE | Hành vi PostgreSQL / seed — đồng Task005 GAP |
| Tách Task007_01 / 007_02 | PM cần cập nhật `docs/task007/` + dependency — tránh lệch gate G-PM |
| Đồng bộ `Database_Specification` §16 | Bổ sung cột `unit_id` trong tài liệu UC khi migration merge |

---

## 13. PO sign-off (khi Approved)

- [x] OQ-1–OQ-3 đã chốt (§4, 26/04/2026)
- [x] Bổ sung mẫu JSON 400 `locationId` / `unitId` (§8.6)
- [ ] JSON §8 toàn bộ đã rà soát với PO lần cuối trước merge triển khai
- [x] RBAC PATCH mặc định `can_manage_inventory` (§6) — addendum nếu đổi

**Chữ ký / nhãn PR:** _chờ PO ký bản Approved_

---

**Kết bản:** vẫn **Draft** cho đến khi PO đổi header **Approved** + ký §13; có thể chuyển **PM** lập kế hoạch **Task007_01 / 007_02** theo OQ-3.
