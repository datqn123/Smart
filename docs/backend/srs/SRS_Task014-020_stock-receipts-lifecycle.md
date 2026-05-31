# SRS — Phiếu nhập kho — vòng đời REST (Task014–Task020)

> **File (Spring / `smart-erp`):** `backend/docs/srs/SRS_Task014-020_stock-receipts-lifecycle.md`  
> **Người soạn:** Agent BA + SQL (Draft)  
> **Ngày:** 26/04/2026  
> **Trạng thái:** Draft  
> **PO duyệt (khi Approved):** *chưa*

---

## 0. Đầu vào & traceability


| Nguồn                  | Đường dẫn / ghi chú                                                                                                                                                                                                                                                                                   |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| API Task014            | `[../../../frontend/docs/api/API_Task014_stock_receipts_post.md](../../../frontend/docs/api/API_Task014_stock_receipts_post.md)`                                                                                                                                                                      |
| API Task015            | `[../../../frontend/docs/api/API_Task015_stock_receipts_get_by_id.md](../../../frontend/docs/api/API_Task015_stock_receipts_get_by_id.md)`                                                                                                                                                            |
| API Task016            | `[../../../frontend/docs/api/API_Task016_stock_receipts_patch.md](../../../frontend/docs/api/API_Task016_stock_receipts_patch.md)`                                                                                                                                                                    |
| API Task017            | `[../../../frontend/docs/api/API_Task017_stock_receipts_delete.md](../../../frontend/docs/api/API_Task017_stock_receipts_delete.md)`                                                                                                                                                                  |
| API Task018            | `[../../../frontend/docs/api/API_Task018_stock_receipts_submit.md](../../../frontend/docs/api/API_Task018_stock_receipts_submit.md)`                                                                                                                                                                  |
| API Task019            | `[../../../frontend/docs/api/API_Task019_stock_receipts_approve.md](../../../frontend/docs/api/API_Task019_stock_receipts_approve.md)`                                                                                                                                                                |
| API Task020            | `[../../../frontend/docs/api/API_Task020_stock_receipts_reject.md](../../../frontend/docs/api/API_Task020_stock_receipts_reject.md)`                                                                                                                                                                  |
| List (đã có SRS riêng) | `[SRS_Task013_stock-receipts-get-list.md](SRS_Task013_stock-receipts-get-list.md)`, API Task013                                                                                                                                                                                                       |
| UC / DB mô tả          | `[../../../frontend/docs/UC/Database_Specification.md](../../../frontend/docs/UC/Database_Specification.md)` §17–§18                                                                                                                                                                                  |
| Thiết kế API           | `[../../../frontend/docs/api/API_PROJECT_DESIGN.md](../../../frontend/docs/api/API_PROJECT_DESIGN.md)` §4.8, §4.5                                                                                                                                                                                     |
| Flyway                 | `[../../smart-erp/src/main/resources/db/migration/V1__baseline_smart_inventory.sql](../../smart-erp/src/main/resources/db/migration/V1__baseline_smart_inventory.sql)` — `stockreceipts`, `stockreceiptdetails`, `inventory`, `inventorylogs`, `financeledger`, `systemlogs`, `warehouselocations`, … |
| Cột duyệt/từ chối      | `[../../smart-erp/src/main/resources/db/migration/V9__task013_stock_receipts_review_columns.sql](../../smart-erp/src/main/resources/db/migration/V9__task013_stock_receipts_review_columns.sql)` — `rejection_reason`, `reviewed_at`, `reviewed_by`                                                   |


---

## 1. Tóm tắt điều hành

- **Vấn đề:** Cần một **bộ endpoint thống nhất** cho vòng đời phiếu nhập: tạo (Draft / Pending), đọc chi tiết, sửa Draft, xóa, gửi duyệt, phê duyệt (cộng kho + sổ cái), từ chối — thay mock UI UC7/UC4.
- **Mục tiêu:** Mô tả nghiệp vụ, RBAC, transaction, toàn vẹn DB và **hợp nhất** các chỗ lệch nhỏ giữa các file API (đã ghi trong §12 *Quyết định BA đã hợp nhất*).
- **Đối tượng:** Mọi user có quyền module phiếu nhập **xem toàn bộ** phiếu (list Task013 + chi tiết Task015), kể phiếu do người khác tạo. **Sửa Draft / gửi duyệt** chỉ người tạo (`staff_id`). **Xóa** phiếu Nháp hoặc Chờ duyệt, **phê duyệt / từ chối** phiếu Chờ duyệt — **chỉ Owner** (`JWT role`); JWT Bearer (`role` + claim `mp` theo Task001).

---

## 2. Bóc tách nghiệp vụ (capabilities)


| #   | Capability                                                                               | Endpoint / method                          | Kết quả                                  |
| --- | ---------------------------------------------------------------------------------------- | ------------------------------------------ | ---------------------------------------- |
| C1  | Tạo phiếu + ≥1 dòng chi tiết, `saveMode` draft/pending                                   | `POST /api/v1/stock-receipts`              | `201` + header + details                 |
| C2  | Đọc một phiếu đầy đủ header + details (**mọi** phiếu nếu đủ quyền module — không lọc theo người tạo) | `GET /api/v1/stock-receipts/{id}`          | `200` hoặc `404`                         |
| C3  | Sửa phiếu **chỉ Draft** (partial header; details = replace-all trong transaction)        | `PATCH /api/v1/stock-receipts/{id}`        | `200` shape Task015                      |
| C4  | Xóa phiếu ở trạng thái cho phép (**OQ-1**); **chỉ Owner** (`JWT role`) — tương đương quyền hủy phiếu Chờ duyệt | `DELETE /api/v1/stock-receipts/{id}`       | `200` + envelope; **403** nếu không Owner |
| C5  | Draft → Pending (validate có detail)                                                     | `POST /api/v1/stock-receipts/{id}/submit`  | `200`                                    |
| C6  | Pending → Approved + cộng `inventory` + `inventorylogs` + `financeledger` + audit header; **chỉ Owner** (`JWT role`) | `POST /api/v1/stock-receipts/{id}/approve` | `200`, idempotent `409` nếu đã Approved; **403** nếu không phải Owner |
| C7  | Pending → Rejected + `rejection_reason` + `reviewed_`*; **chỉ Owner** (`JWT role`)                                   | `POST /api/v1/stock-receipts/{id}/reject`  | `200`; **403** nếu không phải Owner |
| C8  | Ghi `systemlogs` (INFO/WARNING) sau thao tác ghi có ý nghĩa nghiệp vụ                    | Mọi endpoint ghi                           | Không fail chính nếu log fail — **OQ-6** |


**Máy trạng thái (tối thiểu):**

```text
Draft ──submit──► Pending ──approve──► Approved (cộng kho + ledger)
   │                  │
   │                  └──reject──► Rejected
   └── (PATCH/submit: chỉ người tạo; DELETE Draft/Pending: chỉ Owner)
```

---

## 3. Phạm vi

### 3.1 In-scope

- Các endpoint Task014–020 như bảng §2; validation đồng bộ Task014 (supplier, product Active, unit thuộc product, quantity, costPrice, expiry ≥ receiptDate, `uq_srd_receipt_product_batch`).
- RBAC: **§6** (hợp nhất với triển khai Task013).

### 3.2 Out-of-scope

- `GET` danh sách — Task013.  
- Từng dòng nhập **khác `inboundLocationId`** (Task019 ghi v2 — migration + UI sau).  
- Hoàn tác (undo) sau Approved; điều chỉnh tồn sau nhập — luồng khác.

---

## 4. Câu hỏi làm rõ cho PO (Open Questions)


| ID   | Câu hỏi                                                                                                                                                                                                                                                                  | Ảnh hưởng nếu không trả lời                  | Blocker? |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------- | -------- |
| OQ-1 | `**DELETE**`: chỉ cho phép xóa khi `status = Draft`, hay **cũng cho phép `Pending`** (hủy yêu cầu duyệt, không đụng kho)? API Task017 để mở Pending “nếu PM cho phép”.                                                                                                   | Dev chọn một → tester không biết kỳ vọng 409 | **Có**   |
| OQ-2 | **Quyền đọc vs ghi** (đã chốt — xem bảng *Quyết định PO* ngay dưới): trước đây từng mô tả “staff chỉ phiếu mình” cho mọi thao tác; PO yêu cầu **đọc toàn bộ** + **Owner** cho xóa/hủy Pending/duyệt.                                                                 | SRS §6 phải khớp triển khai                  | Không    |
| OQ-3 | `**PATCH` gửi `details`**: có cho phép mảng **rỗng** (0 dòng) không? (Khác POST bắt buộc ≥1 dòng.)                                                                                                                                                                       | 400 vs cho phép xóa sạch rồi chặn submit     | Không    |
| OQ-4 | **Phê duyệt (Task019) — đơn vị tính**: **(A)** chỉ chấp nhận `unit_id` là **đơn vị cơ sở** (`is_base_unit = true`) v1; **(B)** cho phép đơn vị khác và quy đổi `quantity * conversion_rate` (cột `ProductUnits.conversion_rate` — “số đơn vị cơ sở trong 1 đơn vị này”). | Công thức tồn kho sai nếu giả định sai       | **Có**   |
| OQ-5 | `**FinanceLedger` khi approve**: **(A)** một dòng tổng `amount = -total_amount` phiếu (một `PurchaseCost`); **(B)** một dòng / dòng detail (mapping chi phí từng SP).                                                                                                    | Báo cáo tài chính / đối soát                 | Không    |
| OQ-6 | `**SystemLogs`**: nếu insert log **lỗi** sau khi transaction nghiệp vụ đã commit — có bắt buộc **fail request** (retry) hay **best-effort** (chỉ server log)?                                                                                                            | Hành vi hiếm, SLA vận hành                   | Không    |


**Trả lời PO (điền khi chốt):**


| ID   | Quyết định PO                                   | Ngày |
| ---- | ----------------------------------------------- | ---- |
| OQ-1 | cũng cho phép `Pending`                         |      |
| OQ-2 | **Đọc** (GET list + GET `{id}`): mọi phiếu nếu có `can_manage_inventory`. **PATCH / submit**: chỉ `staff_id` = JWT subject. **DELETE** (Draft/Pending) + **approve / reject** (Pending): chỉ JWT `role` = Owner. |      |
| OQ-3 | Có cho phép rỗng                                |      |
| OQ-4 | A                                               |      |
| OQ-5 | A                                               |      |
| OQ-6 | Chưa xử lý SystemLogs                           |      |


---

## 5. Phân tích scope tệp & bằng chứng (Evidence scope)

### 5.1 Tài liệu đã đối chiếu

- Toàn bộ `API_Task014` … `API_Task020` (markdown).  
- Flyway V1 + V9 (tên bảng thực tế PostgreSQL: `stockreceipts`, `stockreceiptdetails`, …).

### 5.2 Mã / package dự kiến (Spring)

- `com.example.smart_erp.inventory.controller` — mở rộng `StockReceiptsController` hoặc controller receipt dedicated; `Security` / method security.  
- Service layer: tạo/sửa/xóa/submit/approve/reject — **mỗi luồng ghi một `@Transactional`**.  
- JDBC/JPA repository: `StockReceipts`, `StockReceiptDetails`, `Inventory`, `InventoryLogs`, `FinanceLedger`, `SystemLogs`.  
- Flyway **chỉ khi** schema thiếu (hiện V9 đã bổ sung cột duyệt).

### 5.3 Rủi ro phát hiện sớm

- **Trùng `receipt_code`**: sinh mã theo năm + sequence — cần khóa hoặc retry khi unique violation → **409** (Task014).  
- **Approve 2 lần**: `FOR UPDATE` + kiểm tra `status = Pending` → lần 2 **409**.  
- `**FinanceLedger.amount`**: DB comment “Dương = thu, Âm = chi” — `PurchaseCost` dùng **số âm** (đối chiếu Task019).

---

## 6. Persona & RBAC


| Điều kiện | Endpoint / hành vi |
| --------- | ------------------ |
| `hasAuthority('can_manage_inventory')` | Task014 POST; Task015 GET `{id}` (xem **mọi** phiếu); Task016 PATCH; Task017 DELETE (sau đó service kiểm Owner — §6 dòng dưới); Task018 submit — **đồng bộ** với `[SRS_Task013](SRS_Task013_stock-receipts-get-list.md)` / `StockReceiptsController` list (list không lọc theo người tạo). |
| JWT claim `role` **khớp seed `Owner`** (không phân biệt hoa thường, `trim`) | **Task017** `DELETE` khi `Draft` hoặc `Pending`; **Task019** approve; **Task020** reject — nếu không phải Owner → **403** (message thống nhất §8.3). |
| `staff_id` = `Integer.parseInt(jwt.getSubject())` | **Task016** PATCH và **Task018** submit — chỉ trên phiếu do chính user tạo; khác → **403**. |
| `hasAuthority('can_approve')` **và** `role` = Owner | **Task019** / **Task020** — thiếu `can_approve` → **403**; có `can_approve` nhưng không Owner → **403** sau kiểm `role`. |


**Ghi chú BA (hợp nhất):** Claim `role` trên access token phải khớp bản ghi `Roles.name` (Flyway V1: `Owner`, `Staff`, …). `API_Task015` / `API_Task017` / `API_Task019` / `API_Task020` phải phản ánh **đọc toàn bộ** và **Owner** cho DELETE/approve/reject; mini-erp: ẩn nút xóa/duyệt/từ chối khi user không Owner (§12).

---

## 7. Actor & luồng nghiệp vụ

### 7.1 Actor


| Actor  | Mô tả                   |
| ------ | ----------------------- |
| User   | Staff / Owner đăng nhập |
| Client | mini-erp                |
| API    | `smart-erp`             |
| DB     | PostgreSQL              |


### 7.2 Luồng phê duyệt (tóm tắt)

1. Client gọi approve với `inboundLocationId`.
2. API khóa phiếu `FOR UPDATE`, kiểm `Pending`.
3. Với mỗi detail: quy đổi số lượng **đơn vị cơ sở** theo **OQ-4** → UPSERT `inventory` theo `uq_inventory_product_location_batch`.
4. Insert `inventorylogs` (`action_type = INBOUND`, `quantity_change` > 0, `receipt_id`, `to_location_id`).
5. Insert `financeledger` theo **OQ-5**; `transaction_type = PurchaseCost`, `reference_type = StockReceipt`, `reference_id = receipt.id`, `amount` **âm** (chi).
6. Update `stockreceipts` status Approved + `approved_`* + `reviewed_*` + `rejection_reason = NULL`.
7. `systemlogs` (best-effort theo OQ-6).
8. Commit.

### 7.3 Sơ đồ (approve)

```mermaid
sequenceDiagram
  participant C as Client
  participant A as API
  participant D as DB
  C->>A: POST approve + inboundLocationId
  A->>D: BEGIN; SELECT sr FOR UPDATE
  A->>D: SELECT details + units + inventory rows
  A->>D: UPDATE/INSERT inventory
  A->>D: INSERT inventorylogs
  A->>D: INSERT financeledger
  A->>D: UPDATE stockreceipts Approved
  A->>D: INSERT systemlogs
  A->>D: COMMIT
  A-->>C: 200 + data
```



---

## 8. Hợp đồng HTTP & ví dụ JSON

### 8.1 Bảng endpoint


| Task | Method | Path                                  | Auth   |
| ---- | ------ | ------------------------------------- | ------ |
| 014  | POST   | `/api/v1/stock-receipts`              | Bearer |
| 015  | GET    | `/api/v1/stock-receipts/{id}`         | Bearer |
| 016  | PATCH  | `/api/v1/stock-receipts/{id}`         | Bearer |
| 017  | DELETE | `/api/v1/stock-receipts/{id}`         | Bearer |
| 018  | POST   | `/api/v1/stock-receipts/{id}/submit`  | Bearer |
| 019  | POST   | `/api/v1/stock-receipts/{id}/approve` | Bearer |
| 020  | POST   | `/api/v1/stock-receipts/{id}/reject`  | Bearer |


### 8.2 Quyết định BA đã hợp nhất (không cần PO trừ khi mở OQ)


| Chủ đề                 | Trước (lệch giữa API)       | Sau (SRS chốt)                                                                               |
| ---------------------- | --------------------------- | -------------------------------------------------------------------------------------------- |
| Task018 trạng thái sai | 409 hoặc 400                | Luôn **409 CONFLICT** (đồng nhất Task016/017/019).                                           |
| DELETE thành công      | 200 hoặc 204                | **200** + `ApiSuccessResponse` `{ data: { id, deleted: true } }` để `apiJson` FE thống nhất. |
| RBAC đọc/ghi phiếu     | “Admin” / “Staff” khác nhau | `can_manage_inventory` cho đọc + POST tạo; GET `{id}` **không** lọc owner; PATCH/submit: **creator**; DELETE + Task019/020: **`role` = Owner** (Task019/020 thêm `can_approve`) — §6. |
| FinanceLedger          | Task019 ghi amount < 0      | Khớp comment DB: **âm = chi** (`PurchaseCost`).                                              |


### 8.3 Request / response mẫu (rút gọn — bản đầy đủ từng field: xem file API tương ứng §5–§6)

**Task014 — POST (đủ field)**

```json
{
  "supplierId": 1,
  "receiptDate": "2026-04-23",
  "invoiceNumber": "HD-2026-01",
  "notes": "Ghi chú phiếu",
  "saveMode": "draft",
  "details": [
    {
      "productId": 12,
      "unitId": 5,
      "quantity": 24,
      "costPrice": 45000,
      "batchNumber": "LOT-2026-01",
      "expiryDate": "2027-12-31"
    }
  ]
}
```

**Task019 — POST approve (body bắt buộc)**

```json
{
  "inboundLocationId": 3
}
```

**Task020 — POST reject**

```json
{
  "reason": "Số lượng không khớp hóa đơn gốc"
}
```

**400 validation (chung envelope)**

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Dữ liệu không hợp lệ",
  "details": {
    "saveMode": "Giá trị phải là draft hoặc pending"
  }
}
```

**409 state (ví dụ submit khi không phải Draft)**

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Phiếu không ở trạng thái Nháp"
}
```

**403 — Task017 / Task019 / Task020 khi caller không phải Owner** (có thể vẫn có `can_approve` trên token nhưng `role` ≠ Owner; hoặc DELETE bởi Staff dù là người tạo phiếu)

```json
{
  "success": false,
  "error": "FORBIDDEN",
  "message": "Chỉ tài khoản Owner mới được xóa phiếu (Nháp/Chờ duyệt), phê duyệt hoặc từ chối phiếu Chờ duyệt"
}
```

**403 — Task016 / Task018 khi user không phải người tạo phiếu**

```json
{
  "success": false,
  "error": "FORBIDDEN",
  "message": "Bạn chỉ được thao tác trên phiếu do chính mình tạo"
}
```

---

## 9. Quy tắc nghiệp vụ (bảng)


| Mã   | Điều kiện             | Hành động                                                                                             |
| ---- | --------------------- | ----------------------------------------------------------------------------------------------------- |
| BR-1 | `saveMode = draft`    | `status = Draft`                                                                                      |
| BR-2 | `saveMode = pending`  | `status = Pending`; vẫn validate giống draft; **không** cộng kho                                      |
| BR-3 | `POST …/submit`       | Chỉ từ `Draft`; `COUNT(details) ≥ 1` → `Pending`                                                      |
| BR-4 | `PATCH`               | Chỉ `Draft`; không cho client gửi `approved_`*, `reviewed_*`, `rejection_reason` — nếu gửi → **400**  |
| BR-5 | `DELETE`              | Chỉ trạng thái PO chọn (**OQ-1**); caller **Owner** (`JWT role`); CASCADE `stockreceiptdetails`                                      |
| BR-6 | `approve`             | Chỉ `Pending`; caller **Owner** (`JWT role`); `warehouselocations.status = Active`; một transaction toàn bộ bước §7.2 |
| BR-7 | `reject`              | Chỉ `Pending`; caller **Owner** (`JWT role`); ghi `rejection_reason`, `reviewed_by/at`; **không** set `approved_by/at` |
| BR-8 | `total_amount` header | Luôn khớp tổng `quantity * cost_price` các dòng (sau quy đổi nếu có — theo OQ-4) tại thời điểm commit |


---

## 10. Dữ liệu & SQL tham chiếu (phối hợp SQL Agent)

### 10.1 Bảng / quan hệ (tên Flyway / PostgreSQL)


| Bảng                       | Read / Write | Ghi chú                                                                                     |
| -------------------------- | ------------ | ------------------------------------------------------------------------------------------- |
| `stockreceipts`            | R/W          | `receipt_code` UNIQUE; FK `supplier_id`, `staff_id`, `approved_by`, `reviewed_by`           |
| `stockreceiptdetails`      | R/W          | `line_total` generated; `uq_srd_receipt_product_batch`                                      |
| `suppliers`                | R            | Validate tồn tại; **OQ** có thể bổ sung kiểm `status = Active`                              |
| `products`, `productunits` | R            | Unit thuộc product; `Products.status = Active`                                              |
| `warehouselocations`       | R            | Approve: `status = Active`                                                                  |
| `inventory`                | R/W          | Approve; `uq_inventory_product_location_batch`                                              |
| `inventorylogs`            | W            | `action_type = INBOUND`, `receipt_id`                                                       |
| `financeledger`            | W            | `PurchaseCost`, `reference_type/id`                                                         |
| `systemlogs`               | W            | Cột: `log_level`, `module`, `action`, `user_id`, `message`, `context_data` (JSONB tùy chọn) |


### 10.2 Transaction

- **Task014/016/017/018/019/020 (ghi):** một transaction / request; approve **không** commit từng phần (inventory mà không ledger = cấm).  
- Dùng `SELECT … FROM stockreceipts WHERE id = :id FOR UPDATE` trước khi đổi trạng thái hoặc xóa.

### 10.3 SQL mẫu (pseudo — tham số hóa)

```sql
-- Khóa phiếu trước submit/approve/reject/delete
SELECT id, status FROM stockreceipts WHERE id = :id FOR UPDATE;

-- Replace-all details (PATCH)
DELETE FROM stockreceiptdetails WHERE receipt_id = :id;
INSERT INTO stockreceiptdetails (receipt_id, product_id, unit_id, quantity, cost_price, batch_number, expiry_date)
VALUES (:id, :pid, :uid, :qty, :cost, :batch, :exp);

-- Approve: upsert inventory (logic đầy đủ trong service — quy đổi theo OQ-4)
-- INSERT INTO inventorylogs (...);
-- INSERT INTO financeledger (transaction_date, transaction_type, reference_type, reference_id, amount, description, created_by)
--   VALUES (:receipt_date, 'PurchaseCost', 'StockReceipt', :id, :neg_amount, :desc, :approver_id);
UPDATE stockreceipts SET status = 'Approved', approved_by = :u, approved_at = NOW(),
  reviewed_by = :u, reviewed_at = NOW(), rejection_reason = NULL, updated_at = NOW() WHERE id = :id;
```

### 10.4 Index

- Đã có: `idx_sr_status`, `idx_sr_supplier`, `idx_srd_receipt`.  
- Nếu query theo `staff_id` + `status` nhiều: cân nhắc `(staff_id, status)` — ghi tech debt nếu chưa đo.

### 10.5 Kiểm chứng dữ liệu (Tester)

- Sau approve: `inventory.quantity` tăng đúng base qty; có `inventorylogs` với `receipt_id`; `financeledger` một hoặc N dòng theo OQ-5; `stockreceipts.status = Approved`.  
- Sau reject: không dòng inventory mới; `rejection_reason` không null.  
- Xóa Draft: không còn header + details.

---

## 11. Acceptance criteria (Given / When /Then) — rút gọn

```text
Given supplier và products Active hợp lệ
When POST /stock-receipts với saveMode draft và 1 detail
Then 201 và receipt_code duy nhất và total_amount = tổng dòng

Given phiếu Draft có 2 dòng
When PATCH chỉ đổi invoiceNumber (không gửi details)
Then 200 và details giữ nguyên

Given phiếu Draft
When PATCH gửi details mới (replace-all)
Then 200 và chỉ còn dòng mới; total_amount khớp

Given phiếu Pending
When PATCH bất kỳ
Then 409

Given phiếu Draft và policy xóa cho phép (OQ-1)
When DELETE
Then 200 và không còn receipt_id trong DB

Given phiếu Draft có detail
When POST …/submit
Then 200 và status Pending

Given phiếu Draft không có detail
When POST …/submit
Then 400

Given phiếu Pending và vị trí Active
When POST …/approve với inboundLocationId
Then 200 Approved và inventory tăng và financeledger ghi chi

Given phiếu Pending và JWT `role` = Owner và có `can_approve`
When POST …/approve với inboundLocationId hợp lệ
Then 200 Approved

Given phiếu tồn tại do user A tạo và user B có `can_manage_inventory`
When GET …/{id} bởi user B
Then 200 và payload đúng phiếu

Given phiếu Draft do user A và user B (Staff) có `can_manage_inventory`
When PATCH …/{id} bởi user B
Then 403

Given phiếu Draft hoặc Pending và user là người tạo phiếu nhưng `role` = Staff
When DELETE …/{id}
Then 403

Given phiếu Draft hoặc Pending và JWT `role` = Owner
When DELETE …/{id}
Then 200

Given phiếu Pending và JWT `role` = Staff (dù token có các quyền khác)
When POST …/approve hoặc POST …/reject
Then 403

Given phiếu Pending
When POST …/reject có reason
Then 200 Rejected và không đổi inventory

Given phiếu đã Approved
When POST …/approve lần nữa
Then 409
```

---

## 12. GAP & giả định


| GAP / Giả định                                                        | Tác động                              | Hành động                                                           |
| --------------------------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------- |
| API Task014 đề cập `INSERT SystemLogs` với tuple (INFO, INVENTORY, …) | Cần map sang cột thực `systemlogs`    | Dev map `module`, `action`, `message`; optional `context_data` JSON |
| Task019 response `details: []` hoặc đầy đủ                            | FE hydrate                            | Chốt một trong PR — ưu tiên **đầy đủ như Task015** để đỡ round-trip |
| `staff_id` POST                                                       | Lấy từ JWT `sub` → resolve `users.id` | Giống mô tả Task014                                                 |
| API Task019 / Task020 (đồng bộ RBAC Owner)                             | Đã chỉnh markdown API + BE §6         | Giữ FE `canApprove` + ẩn nút nếu `role` ≠ Owner (mini-erp).          |


---

## 13. PO sign-off (chỉ điền khi Approved)

- Đã trả lời / đóng các **OQ blocker** (OQ-1, OQ-4 tối thiểu)
- Đồng ý bảng RBAC §6 (Owner-only Task019/020) và quy tắc hợp nhất §8.2
- JSON / AC đủ để Tester viết Postman

**Chữ ký / nhãn PR:** …