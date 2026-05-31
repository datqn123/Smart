# SRS — Sổ nợ đối tác — `GET|POST|GET|PATCH /api/v1/debts` — Task069–Task072

> **File (Spring / `smart-erp`):** `backend/docs/srs/SRS_Task069-072_debts-api.md`  
> **Người soạn:** Agent BA (+ SQL theo `backend/AGENTS/BA_AGENT_INSTRUCTIONS.md`, `backend/AGENTS/SQL_AGENT_INSTRUCTIONS.md`)  
> **Ngày:** 30/04/2026  
> **Trạng thái:** `Approved`  
> **PO duyệt (khi Approved):** PO (chốt §4 — 30/04/2026), `30/04/2026`

---

## 0. Đầu vào & traceability

| Nguồn | Đường dẫn / ghi chú |
| :--- | :--- |
| API Task069 | [`../../../frontend/docs/api/API_Task069_debts_get_list.md`](../../../frontend/docs/api/API_Task069_debts_get_list.md) — **Approved** (đồng bộ SRS 30/04/2026) |
| API Task070 | [`../../../frontend/docs/api/API_Task070_debts_post.md`](../../../frontend/docs/api/API_Task070_debts_post.md) — **Approved** (đồng bộ SRS 30/04/2026) |
| API Task071 | [`../../../frontend/docs/api/API_Task071_debts_get_by_id.md`](../../../frontend/docs/api/API_Task071_debts_get_by_id.md) — **Approved** (đồng bộ SRS 30/04/2026) |
| API Task072 | [`../../../frontend/docs/api/API_Task072_debts_patch.md`](../../../frontend/docs/api/API_Task072_debts_patch.md) — **Approved** (đồng bộ SRS 30/04/2026) |
| Khung API | [`../../../frontend/docs/api/API_PROJECT_DESIGN.md`](../../../frontend/docs/api/API_PROJECT_DESIGN.md) §4.14 |
| Envelope | [`../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md`](../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md) |
| UC / DB (mô tả) | [`../../../frontend/docs/UC/Database_Specification.md`](../../../frontend/docs/UC/Database_Specification.md) §12.2 `PartnerDebts` |
| Flyway thực tế | [`../../smart-erp/src/main/resources/db/migration/V1__baseline_smart_inventory.sql`](../../smart-erp/src/main/resources/db/migration/V1__baseline_smart_inventory.sql) — bảng **`PartnerDebts`** (tên vật lý PostgreSQL mặc định: **`partnerdebts`**), CHECK `chk_partner_debts_partner`, `chk_paid_le_total`, FK `customers` / `suppliers` |
| JWT / quyền | [`../../smart-erp/src/main/java/com/example/smart_erp/auth/support/MenuPermissionClaims.java`](../../smart-erp/src/main/java/com/example/smart_erp/auth/support/MenuPermissionClaims.java) — **`can_view_finance`**; Staff bật qua **V25** (đồng bộ [`SRS_Task064-068_cash-transactions-api.md`](SRS_Task064-068_cash-transactions-api.md) **OQ-1**) |
| Code đã tham chiếu `partnerdebts` | [`CustomerJdbcRepository.java`](../../smart-erp/src/main/java/com/example/smart_erp/catalog/repository/CustomerJdbcRepository.java), [`SupplierJdbcRepository.java`](../../smart-erp/src/main/java/com/example/smart_erp/catalog/repository/SupplierJdbcRepository.java) — `HAS_PARTNER_DEBTS` khi xóa đối tác |
| UI index | [`../../../frontend/mini-erp/src/features/FEATURES_UI_INDEX.md`](../../../frontend/mini-erp/src/features/FEATURES_UI_INDEX.md) — `/cashflow/debt`, `DebtPage` |

---

## 1. Tóm tắt điều hành

- **Vấn đề:** Màn **Sổ nợ** (`DebtPage`) đang mock; cần bốn endpoint REST thống nhất envelope, đọc/ghi bảng công nợ đối tác, join tên KH/NCC, tính **`remainingAmount`**, phân trang và ghi nhận trả nợ an toàn khi đồng thời.
- **Mục tiêu nghiệp vụ:** Người dùng đủ quyền tài chính xem danh sách/chi tiết, tạo khoản nợ (mã `debtCode` server), cập nhật/ghi nhận thanh toán; trạng thái **`Cleared`** khi đã trả đủ; ràng buộc đối tác và `paid ≤ total` khớp DB.
- **Đối tượng:** User có JWT **`mp.can_view_finance === true`** (Owner / Admin / Staff sau V25). **POST:** mọi user đủ quyền tạo khoản, **`created_by = sub`**. **PATCH:** chỉ khi **`created_by = sub`** (**§4 OQ-2 đã chốt**); cần Flyway **`created_by`** trên `partnerdebts`.

### 1.1 Giao diện Mini-ERP

| Nhãn menu (Sidebar) | Route | Page (export) | Component / vùng chính | File (dưới `frontend/mini-erp/src/features/`) |
| :--- | :--- | :--- | :--- | :--- |
| Sổ nợ (nhóm Thu chi) | `/cashflow/debt` | `DebtPage` | `DebtTable`, `DebtToolbar`, `DebtFormDialog`, `DebtDetailDialog` | `cashflow/pages/DebtPage.tsx`; `cashflow/components/DebtTable.tsx`, `DebtToolbar.tsx`, `DebtFormDialog.tsx`, `DebtDetailDialog.tsx` |

---

## 2. Bóc tách nghiệp vụ (capabilities)

| # | Capability | Endpoint | Kết quả |
| :---: | :--- | :--- | :--- |
| C1 | Xác thực JWT | Tất cả | **401** nếu thiếu/sai/hết hạn |
| C2 | Kiểm tra **`can_view_finance`** | Tất cả | **403** nếu thiếu (**§6**, đồng bộ Task063/Task064) |
| C3 | Kiểm tra quyền **ghi** | POST, PATCH | **POST:** `can_view_finance`. **PATCH:** `can_view_finance` **và** `created_by = sub`; không khớp → **403** |
| C4 | Liệt kê có lọc + phân trang; `remainingAmount` = `total_amount - paid_amount` (read-model) | GET list | **200** + `data.items`, `page`, `limit`, `total` |
| C5 | Lọc `search`: `ILIKE` trên `debt_code`, `customers.name` / `suppliers.name`, **`customer_code` / `supplier_code`** (đề xuất — **BR-3**) | GET list | Kết quả khớp tìm kiếm mã + tên |
| C6 | Lọc khoảng hạn thanh toán; validate `dueDateFrom` ≤ `dueDateTo` | GET list | **400** nếu ngược khoảng |
| C7 | Tạo bản ghi; sinh **`debtCode`** unique; set **`status`** theo paid/total | POST | **201** + bản ghi đầy đủ |
| C8 | Kiểm tra FK `customer_id` / `supplier_id` tồn tại và khớp `partner_type` | POST | **400** nếu id không tồn tại hoặc vi phạm cặp KH/NCC |
| C9 | Đọc một `id`; join tên đối tác | GET by id | **200** hoặc **404** |
| C10 | Cập nhật một phần; **`SELECT … FOR UPDATE`**; cấm `paidAmount` **và** `paymentAmount` đồng thời (**BR-4**); cập nhật **`status`** | PATCH | **200** hoặc **4xx** |
| C11 | Khi **`paymentAmount`**: `newPaid = LEAST(paid_amount + paymentAmount, total_amount)` — **cắt trần** (**BR-5**, **OQ-4 đã chốt**) | PATCH | **200**; không **400** vì vượt `remaining` |
| C12 | **Không** INSERT `financeledger` trong phạm vi Task069–072 (**GAP / backlog** — Task072 §1) | — | Ghi rõ trong §12 |

---

## 3. Phạm vi

### 3.1 In-scope

- `GET /api/v1/debts`, `POST /api/v1/debts`, `GET /api/v1/debts/{id}`, `PATCH /api/v1/debts/{id}`.  
- Đọc/ghi bảng **`partnerdebts`**; đọc **`customers`**, **`suppliers`** (join tên/mã).  
- Flyway **`V26`**: cột **`created_by`** (bắt buộc theo **§4 OQ-2**).  
- Envelope và mã lỗi theo `API_RESPONSE_ENVELOPE.md`.

### 3.2 Out-of-scope

- Ghi **`financeledger`** khi trả nợ (backlog; cần policy + CR riêng).  
- Xóa khoản nợ (`DELETE`) — không có trong API Task069–072.  
- Tự động tạo công nợ từ đơn mua/bán — luồng khác (nếu có).

---

## 4. Quyết định PO (đã chốt — 30/04/2026)

> Không còn OQ mở cho triển khai Task069–072; Dev/Tester bám **§6–§11** và bảng **BR**.

| ID | Quyết định PO | Diễn giải kỹ thuật |
| :--- | :--- | :--- |
| **OQ-1** | **(a)** | Khi **`status = Cleared`**: nếu body có **`totalAmount`**, **`paidAmount`** hoặc **`paymentAmount`** (bất kỳ giá trị, kể cả trùng số hiện tại) → **409** `CONFLICT`, message nghiệp vụ (không ghi nhận thêm thanh toán / không sửa số tiền). Cho phép PATCH **chỉ** **`notes`** và/hoặc **`dueDate`** → **200** nếu hợp lệ. |
| **OQ-2** | **(a)** | Flyway thêm **`created_by INT NOT NULL`** FK **`users(id)`** (ON DELETE RESTRICT). **Backfill** dòng cũ: gán `created_by = (SELECT id FROM users ORDER BY id LIMIT 1)` (user seed đầu tiên) trước khi `NOT NULL` nếu cần. **POST:** mọi user có **`can_view_finance`** — `created_by = sub`. **PATCH:** chỉ khi **`created_by = sub`**; không → **403** (cùng tinh thần Task064-068 **BR-9** cho thao tác ghi theo chủ sở hữu bản ghi). |
| **OQ-3** | **(a)** | Sinh **`debtCode`** dạng `NO-YYYY-NNNN`: trong **một transaction** POST, đọc **`MAX(debt_code)`** (hoặc `MAX` seq) theo năm hiện tại, tăng dần; chấp nhận rủi ro tranh chấp cực hiếm khi QPS ghi cao (v1). |
| **OQ-4** | **Cắt trần (theo đề xuất BA)** | `paymentAmount`: **`newPaid = LEAST(paid_amount + paymentAmount, total_amount)`** — **không** trả **400** chỉ vì tổng thanh toán vượt số còn lại; UI đọc **`remainingAmount`** sau response. |

### 4.1 Bảng chữ ký (mẫu)

| ID | Quyết định PO | Ngày |
| :--- | :--- | :--- |
| OQ-1 | (a) — Cleared: 409 nếu có trường tiền; cho `notes` / `dueDate` | 30/04/2026 |
| OQ-2 | (a) — `created_by` + POST mọi finance; PATCH chỉ người tạo | 30/04/2026 |
| OQ-3 | (a) — Transaction + MAX seq theo năm | 30/04/2026 |
| OQ-4 | Cắt trần `paymentAmount`, không 400 vì vượt remaining | 30/04/2026 |

---

## 5. Phân tích scope tệp & bằng chứng (Evidence scope)

### 5.1 Tài liệu đã đối chiếu (read)

- Bốn file `API_Task069` … `API_Task072`; `API_RESPONSE_ENVELOPE.md`; `API_PROJECT_DESIGN.md` §4.14.  
- Flyway V1: `PartnerDebts`, `Customers`, `Suppliers`.  
- `SRS_Task063`, `SRS_Task064-068` — RBAC `can_view_finance` + pattern lỗi.  
- `FEATURES_UI_INDEX.md` — route Sổ nợ.

### 5.2 Mã / migration dự kiến (write / verify)

- Controller + service + JDBC (package `finance` / `cashflow` — theo convention đã dùng cho ledger/cash nếu có).  
- **Bắt buộc Flyway** (vd. `V26__partner_debts_created_by.sql`): thêm **`created_by`**, backfill theo **§4 OQ-2**, FK `users`.  
- **Index (§10.3):** `CREATE INDEX` trên **`(updated_at DESC, id DESC)`** khi triển khai list.

### 5.3 Rủi ro phát hiện sớm

- **Sinh `debtCode` (OQ-3a):** hai POST đồng thời có thể va chạm unique — xử lý retry khi **23505** hoặc chuyển OQ-3(b) sau nếu PO yêu cầu.  
- **PATCH đồng thời:** bắt buộc **`SELECT … FOR UPDATE`** trong transaction (**Task072**).  
- **Decimal:** map `DECIMAL(15,2)` ↔ JSON number; làm tròn hiển thị theo chuẩn dự án.

---

## 6. Persona & RBAC

| Vai trò / quyền | Điều kiện | HTTP khi từ chối |
| :--- | :--- | :--- |
| Đã đăng nhập | JWT hợp lệ | **401** nếu không |
| Xem sổ nợ | **`mp.can_view_finance === true`** | **403** |
| **POST** khoản nợ | **`can_view_finance`** | **403** nếu thiếu |
| **PATCH** khoản nợ | **`can_view_finance`** và **`created_by` = `sub` (JWT)** | **403** nếu thiếu quyền xem tài chính **hoặc** không phải người tạo bản ghi |

**GAP đã xử lý trong API markdown (30/04/2026):** Task069 ghi “`can_view_finance` hoặc quyền đối tác tương đương” **lệch** chuỗi Task063/064 — đồng bộ về **`can_view_finance` duy nhất** cho cả bốn endpoint (sidebar **Thu chi** = domain tài chính).

---

## 7. Actor & luồng nghiệp vụ

### 7.1 Danh sách actor

| Actor | Mô tả |
| :--- | :--- |
| End user | Nhân viên / chủ cửa hàng thao tác Sổ nợ |
| Client | Mini-ERP (`DebtPage`, dialog) |
| API | `smart-erp` REST |
| Database | PostgreSQL — `partnerdebts`, `customers`, `suppliers` |

### 7.2 Luồng chính (PATCH trả nợ)

1. User mở chi tiết khoản nợ → Client gọi **GET** `…/debts/{id}`.  
2. User nhập “Ghi nhận thanh toán” → Client **PATCH** `{ "paymentAmount": x }`.  
3. API xác thực, RBAC (**`can_view_finance`** + **`created_by = sub`**), mở transaction, **`SELECT … FOR UPDATE`**, nếu **Cleared** và có trường tiền → **409**; nếu không: tính `newPaid` (**BR-5** cắt trần), `UPDATE`, commit.  
4. Trả **200** + bản ghi mới (`remainingAmount`, `status`).

### 7.3 Sơ đồ (PATCH)

```mermaid
sequenceDiagram
  participant U as User
  participant C as Client
  participant A as API
  participant D as DB
  U->>C: Ghi nhận thanh toán
  C->>A: PATCH /api/v1/debts/{id} + JSON
  A->>A: JWT + can_view_finance + created_by = sub
  A->>D: BEGIN
  A->>D: SELECT FROM partnerdebts WHERE id = :id FOR UPDATE
  D-->>A: row
  A->>D: UPDATE partnerdebts SET paid_amount = ..., status = ..., updated_at = now()
  A->>D: COMMIT
  D-->>A: ok
  A-->>C: 200 + envelope data
```

---

## 8. Hợp đồng HTTP & ví dụ JSON

### 8.0 Quy ước chung

- Base path: **`/api/v1/debts`**.  
- `amount` / `totalAmount` / `paidAmount` / `remainingAmount` / `paymentAmount`: số không âm (scale 2 trong DB).  
- Ngày: `dueDate` **chuỗi `YYYY-MM-DD`** (ISO date); timestamp `createdAt` / `updatedAt` **ISO-8601 UTC** (khớp ví dụ Task070).

---

### 8.1 `GET /api/v1/debts` (Task069)

#### Query — schema logic

| Param | Kiểu | Bắt buộc | Validation |
| :--- | :--- | :---: | :--- |
| `partnerType` | `Customer` \| `Supplier` | Không | Enum |
| `status` | `InDebt` \| `Cleared` | Không | Enum |
| `search` | string | Không | Độ dài hợp lý (vd. ≤ 200) |
| `dueDateFrom`, `dueDateTo` | date | Không | Nếu cả hai có → `dueDateFrom` ≤ `dueDateTo` |
| `page` | int | Không | Mặc định **1**, ≥ 1 |
| `limit` | int | Không | Mặc định **20**, 1–100 |

#### Ví dụ **200**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 5,
        "debtCode": "NO-2026-0001",
        "partnerType": "Customer",
        "customerId": 12,
        "supplierId": null,
        "partnerName": "CT TNHH ABC",
        "totalAmount": 10000000,
        "paidAmount": 2000000,
        "remainingAmount": 8000000,
        "dueDate": "2026-05-01",
        "status": "InDebt",
        "notes": "Công nợ bán sỉ T4",
        "updatedAt": "2026-04-20T15:30:00Z"
      }
    ],
    "page": 1,
    "limit": 20,
    "total": 8
  },
  "message": "Thành công"
}
```

#### Lỗi — **400** (khoảng ngày sai)

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Khoảng ngày không hợp lệ: ngày bắt đầu không được sau ngày kết thúc.",
  "details": {
    "dueDateFrom": "Phải nhỏ hơn hoặc bằng dueDateTo"
  }
}
```

#### Lỗi — **401** / **403** / **500**

```json
{
  "success": false,
  "error": "UNAUTHORIZED",
  "message": "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại."
}
```

```json
{
  "success": false,
  "error": "FORBIDDEN",
  "message": "Bạn không có quyền thực hiện thao tác này."
}
```

```json
{
  "success": false,
  "error": "INTERNAL_SERVER_ERROR",
  "message": "Không thể hoàn tất thao tác. Vui lòng thử lại hoặc liên hệ quản trị."
}
```

---

### 8.2 `POST /api/v1/debts` (Task070)

#### Body — schema logic

| Field | Kiểu | Bắt buộc | Ghi chú |
| :--- | :--- | :---: | :--- |
| `partnerType` | enum | Có | |
| `customerId` | int | Điều kiện | Bắt buộc nếu `Customer` |
| `supplierId` | int | Điều kiện | Bắt buộc nếu `Supplier` |
| `totalAmount` | number ≥ 0 | Có | |
| `paidAmount` | number ≥ 0 | Không | Mặc định **0**; ≤ `totalAmount` |
| `dueDate` | date \| null | Không | |
| `notes` | string \| null | Không | Max **5000** ký tự (Zod Task070) |

#### Ví dụ request **đầy đủ**

```json
{
  "partnerType": "Supplier",
  "supplierId": 3,
  "totalAmount": 5000000,
  "paidAmount": 0,
  "dueDate": "2026-04-30",
  "notes": null
}
```

#### Ví dụ **201**

```json
{
  "success": true,
  "data": {
    "id": 6,
    "debtCode": "NO-2026-0004",
    "partnerType": "Supplier",
    "customerId": null,
    "supplierId": 3,
    "partnerName": "NCC XYZ",
    "totalAmount": 5000000,
    "paidAmount": 0,
    "remainingAmount": 5000000,
    "dueDate": "2026-04-30",
    "status": "InDebt",
    "notes": null,
    "createdAt": "2026-04-23T09:00:00Z",
    "updatedAt": "2026-04-23T09:00:00Z"
  },
  "message": "Đã tạo khoản nợ"
}
```

#### Lỗi — **400** (FK / cặp partner)

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Thông tin đối tác không hợp lệ hoặc không tồn tại.",
  "details": {
    "supplierId": "Không tìm thấy nhà cung cấp tương ứng"
  }
}
```

---

### 8.3 `GET /api/v1/debts/{id}` (Task071)

**Shape:** Giống một phần tử `items` của §8.1; **bắt buộc** có thêm **`createdAt`** (đồng bộ audit với POST).

#### Ví dụ **200**

```json
{
  "success": true,
  "data": {
    "id": 5,
    "debtCode": "NO-2026-0001",
    "partnerType": "Customer",
    "customerId": 12,
    "supplierId": null,
    "partnerName": "CT TNHH ABC",
    "totalAmount": 10000000,
    "paidAmount": 2000000,
    "remainingAmount": 8000000,
    "dueDate": "2026-05-01",
    "status": "InDebt",
    "notes": "Công nợ bán sỉ T4",
    "createdAt": "2026-04-01T08:00:00Z",
    "updatedAt": "2026-04-20T15:30:00Z"
  },
  "message": "Thành công"
}
```

#### Lỗi — **404**

```json
{
  "success": false,
  "error": "NOT_FOUND",
  "message": "Không tìm thấy khoản nợ"
}
```

---

### 8.4 `PATCH /api/v1/debts/{id}` (Task072)

#### Body — schema logic

| Field | Kiểu | Ghi chú |
| :--- | :--- | :--- |
| `totalAmount` | number ≥ 0 | Không được nhỏ hơn `paidAmount` sau cập nhật |
| `paidAmount` | number ≥ 0 | Set tuyệt đối; **không** dùng cùng lúc với `paymentAmount` |
| `paymentAmount` | number > 0 | Cộng dồn; **mutually exclusive** với `paidAmount` |
| `dueDate` | date \| null | |
| `notes` | string \| null | max 5000 |

Ít nhất một trường trong body (không gửi `{}`).

#### Ví dụ request (trả một phần)

```json
{
  "paymentAmount": 1500000
}
```

#### Ví dụ **200** (sau PATCH)

```json
{
  "success": true,
  "data": {
    "id": 5,
    "debtCode": "NO-2026-0001",
    "partnerType": "Customer",
    "customerId": 12,
    "supplierId": null,
    "partnerName": "CT TNHH ABC",
    "totalAmount": 10000000,
    "paidAmount": 3500000,
    "remainingAmount": 6500000,
    "dueDate": "2026-05-01",
    "status": "InDebt",
    "notes": "Công nợ bán sỉ T4",
    "createdAt": "2026-04-01T08:00:00Z",
    "updatedAt": "2026-04-30T10:15:00Z"
  },
  "message": "Đã cập nhật khoản nợ"
}
```

#### Lỗi — **400** (cả `paidAmount` và `paymentAmount`)

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Thông tin không hợp lệ: chỉ được dùng một trong hai trường paidAmount hoặc paymentAmount.",
  "details": {}
}
```

#### Lỗi — **403** (PATCH khi không phải người tạo bản ghi)

```json
{
  "success": false,
  "error": "FORBIDDEN",
  "message": "Bạn không có quyền thực hiện thao tác này."
}
```

#### Lỗi — **409** (khoản **Cleared** — có trường số tiền trong body; **OQ-1**)

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Khoản nợ đã được thanh toán đủ. Không thể thay đổi số tiền trên phiếu này. Bạn vẫn có thể cập nhật ghi chú hoặc hạn thanh toán nếu cần."
}
```

---

### 8.5 Ghi chú envelope

- Khớp `API_RESPONSE_ENVELOPE.md`; không trả **200** kèm `success: false`.

---

## 9. Quy tắc nghiệp vụ (bảng)

| Mã | Điều kiện | Hành động / kết quả |
| :--- | :--- | :--- |
| BR-1 | `partner_type = Customer` | `customer_id` NOT NULL, `supplier_id` NULL |
| BR-2 | `partner_type = Supplier` | Ngược lại BR-1 |
| BR-3 | `search` không rỗng | `ILIKE` trên `d.debt_code`, `c.name`, `c.customer_code`, `s.name`, `s.supplier_code` (đề xuất đồng bộ UI “mã hoặc tên”) |
| BR-4 | Body PATCH | Không đồng thời `paidAmount` và `paymentAmount` |
| BR-5 | Body có **`paymentAmount`** và **không** vướng **BR-9** | **`newPaid = LEAST(paid_amount + paymentAmount, total_amount)`** (**OQ-4**); không **400** chỉ vì vượt `remaining` |
| BR-6 | Sau mọi thay đổi `paid`/`total` | Nếu `newPaid >= total` → `status = Cleared`; else `InDebt` |
| BR-7 | `totalAmount` PATCH | `newTotal >= newPaid` (hoặc hiện tại `paid_amount`); vi phạm → **400** |
| BR-8 | Sort list mặc định | `ORDER BY d.updated_at DESC, d.id DESC` |
| BR-9 | **`status = Cleared`** và body có `totalAmount` / `paidAmount` / `paymentAmount` | **409**; chỉ cho **`notes`** / **`dueDate`** (**OQ-1**) |
| BR-10 | **POST** sinh `debtCode` | Trong **một transaction**: đọc max theo năm → tăng seq (**OQ-3**); unique `debt_code` |
| BR-11 | **POST** | `INSERT` kèm **`created_by = sub`** (**OQ-2**) |

---

## 10. Dữ liệu & SQL tham chiếu (Agent SQL)

### 10.1 Bảng / quan hệ (tên dùng trong JDBC — chữ thường)

| Bảng | Read / Write | Ghi chú |
| :--- | :--- | :--- |
| `partnerdebts` | R/W | DDL Flyway: `PartnerDebts` |
| `customers` | R | `name`, `customer_code` |
| `suppliers` | R | `name`, `supplier_code` |

**Cột chính `partnerdebts`:** `id`, `debt_code`, `partner_type`, `customer_id`, `supplier_id`, `total_amount`, `paid_amount`, `due_date`, `status`, `notes`, **`created_by`** (Flyway **V26** — **§4**), `created_at`, `updated_at`.

### 10.2 SQL mẫu — list (Task069)

```sql
SELECT d.id,
       d.debt_code,
       d.partner_type,
       d.customer_id,
       d.supplier_id,
       COALESCE(c.name, s.name) AS partner_name,
       d.total_amount,
       d.paid_amount,
       (d.total_amount - d.paid_amount) AS remaining_amount,
       d.due_date,
       d.status,
       d.notes,
       d.updated_at
FROM partnerdebts d
LEFT JOIN customers c ON d.customer_id = c.id
LEFT JOIN suppliers s ON d.supplier_id = s.id
WHERE (:partner_type IS NULL OR d.partner_type = :partner_type)
  AND (:status IS NULL OR d.status = :status)
  AND (:due_from IS NULL OR d.due_date >= :due_from)
  AND (:due_to IS NULL OR d.due_date <= :due_to)
  AND (
    :search IS NULL
    OR d.debt_code ILIKE '%' || :search || '%'
    OR c.name ILIKE '%' || :search || '%'
    OR c.customer_code ILIKE '%' || :search || '%'
    OR s.name ILIKE '%' || :search || '%'
    OR s.supplier_code ILIKE '%' || :search || '%'
  )
ORDER BY d.updated_at DESC, d.id DESC
LIMIT :limit OFFSET :offset;
```

Đếm `total`: `SELECT COUNT(*) FROM (` cùng `WHERE` `) t`.

### 10.3 SQL mẫu — PATCH (Task072)

```sql
BEGIN;
SELECT id, total_amount, paid_amount, status, created_by
FROM partnerdebts
WHERE id = :id
FOR UPDATE;
-- Kiểm tra created_by = :sub (JWT) trước khi UPDATE; nếu Cleared + có trường tiền → 409 (BR-9)
-- ứng dụng tính new_paid, new_total, new_status trong service; sau đó:
UPDATE partnerdebts
SET total_amount = :new_total,
    paid_amount = :new_paid,
    due_date = :due_date,
    notes = :notes,
    status = :new_status,
    updated_at = CURRENT_TIMESTAMP
WHERE id = :id;
COMMIT;
```

### 10.4 Index đề xuất

- **`idx_partnerdebts_updated_id`** ON **`partnerdebts (updated_at DESC, id DESC)`** — phục vụ list mặc định (V1 chưa có; thêm Flyway khi triển khai).  
- Giữ index V1: `idx_partner_debts_status`, `idx_partner_debts_customer`, `idx_partner_debts_supplier`.

### 10.5 Transaction & khóa

- **GET:** `readOnly = true`, không khóa.  
- **PATCH:** một transaction; **`SELECT … FOR UPDATE`** trước `UPDATE` — tránh lost update trên `paid_amount` / `total_amount`.

### 10.6 Kiểm chứng dữ liệu cho Tester

- Tạo KH/NCC mẫu → POST debt → GET list thấy `partnerName` đúng.  
- PATCH `paymentAmount` lớn hơn `remaining` → **cắt trần** (**OQ-4**); `paidAmount` sau cùng = `totalAmount`; **200**.  
- PATCH khoản **Cleared** với `{ "paymentAmount": 1 }` → **409**; với `{ "notes": "…" }` → **200**.  
- PATCH bởi user khác `created_by` → **403**.  
- Khi `paid = total` → `status = Cleared`; GET by id trả đúng.

---

## 11. Acceptance criteria (Given / When / Then)

```text
Given JWT hợp lệ và can_view_finance
When GET /api/v1/debts?page=1&limit=20
Then 200 và data.items là mảng; data.total là số nguyên ≥ 0; mỗi item có remainingAmount = totalAmount - paidAmount
```

```text
Given can_view_finance và POST body hợp lệ Supplier + supplierId tồn tại
When POST /api/v1/debts
Then 201; debtCode khớp pattern NO-YYYY-; status InDebt nếu paid < total; partnerName khớp suppliers.name
```

```text
Given id không tồn tại
When GET /api/v1/debts/999999
Then 404 NOT_FOUND và message tiếng Việt chức năng
```

```text
Given khoản nợ tồn tại và PATCH chỉ paymentAmount
When PATCH với paymentAmount dương
Then 200; paidAmount tăng đúng rule OQ-4; status Cleared khi paid >= total
```

```text
Given JWT không có can_view_finance
When bất kỳ GET/POST/PATCH debts
Then 403 FORBIDDEN
```

```text
Given PATCH gửi cả paidAmount và paymentAmount
Then 400 BAD_REQUEST
```

```text
Given khoản nợ Cleared và user là người tạo
When PATCH chỉ notes hoặc dueDate
Then 200
```

```text
Given khoản nợ Cleared và user là người tạo
When PATCH có paymentAmount hoặc paidAmount hoặc totalAmount
Then 409 CONFLICT
```

```text
Given khoản nợ do user A tạo và JWT là user B (cùng can_view_finance)
When PATCH bất kỳ
Then 403 FORBIDDEN
```

---

## 12. GAP & giả định

| GAP / Giả định | Tác động | Hành động đề xuất |
| :--- | :--- | :--- |
| API / tài liệu cũ ghi `partner_debts` | Lệch JDBC thực tế (`partnerdebts`) | Đã sửa `API_Task069`–`072` (30/04/2026) |
| Task069 RBAC mơ hồ “quyền đối tác” | Không đồng bộ Task063 | Đã thu hẹp về **`can_view_finance`** trong API |
| Không ghi `financeledger` khi trả nợ | Sổ cái không phản ánh tiền trả nợ | Backlog + SRS tài chính riêng khi PO yêu cầu |
| List **chưa** có index sort `updated_at` | Full scan khi bảng lớn | Flyway index §10.4 khi Dev triển khai |

---

## 13. PO sign-off (chỉ điền khi Approved)

- [x] Đã trả lời / đóng các **OQ** (**§4** — 30/04/2026)
- [x] JSON request/response khớp ý đồ sản phẩm
- [x] Phạm vi In/Out đã đồng ý

**Chữ ký / nhãn PR:** PO — SRS Approved Task069–072 — `30/04/2026`
