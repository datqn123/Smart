# 📄 API SPEC: `GET /api/v1/approvals/history` — Lịch sử phê duyệt - Task062

> **Trạng thái**: Draft  
> **Feature**: **UC4** — màn **Lịch sử phê duyệt** (`ApprovalHistoryPage`, `/approvals/history`)  
> **Tags**: RESTful, Approvals, Read, Audit

---

## 1. Mục tiêu Task

- Tra cứu các giao dịch **đã xử lý** (phê duyệt hoặc từ chối), lọc theo **kết quả**, **mã**, **khoảng thời gian theo `reviewed_at`**, và loại (`type`) — **đồng bộ** với cột nguồn trong [`Database_Specification.md`](../UC/Database_Specification.md) **§17** `StockReceipts`.

---

## 2. Phụ thuộc schema

Endpoint này **yêu cầu** các cột: **`rejection_reason`**, **`reviewed_at`**, **`reviewed_by`** trên `stock_receipts` (mục **Migration** trong §17). Backend phải chạy migration **trước** khi bật Task062; dữ liệu cũ dùng script **backfill** `reviewed_at` / `reviewed_by` từ `approved_at` / `approved_by` cho phiếu `Approved`.

Luồng ghi cột: [`API_Task019_stock_receipts_approve.md`](API_Task019_stock_receipts_approve.md), [`API_Task020_stock_receipts_reject.md`](API_Task020_stock_receipts_reject.md).

---

## 3. Mục đích Endpoint

**`GET /api/v1/approvals/history`** thay `approvalHistory` mock; read-model **`resolution`** (`Approved` \| `Rejected`) khớp `Select` trên UI.

**Phạm vi v1 (MVP):** chỉ chứng từ **`stock_receipt`** → `type` trả về luôn **`Inbound`**. Tham số query **`type`**: `Inbound` hoặc `all` — nếu khác `Inbound` thì **trả danh sách rỗng** (chờ UNION loại khác ở Task sau).

---

## 4. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Endpoint** | `/api/v1/approvals/history` |
| **Method** | `GET` |
| **Authentication** | `Bearer` |
| **RBAC** | **Chỉ** `Owner` và `Admin` (UC4 đọc toàn bộ lịch sử). **Staff → 403** (không có endpoint này cho Staff trừ khi mở policy riêng trong backlog). |
| **Use Case Ref** | UC4 |

---

## 5. Query parameters

| Tham số | Kiểu | Mặc định | Mô tả |
| :------ | :--- | :------- | :---- |
| `resolution` | string | `all` | `all` \| `Approved` \| `Rejected` — khớp `StockReceipts.status`. |
| `search` | string | — | ILIKE `receipt_code` **hoặc** `Users.full_name` (người tạo **hoặc** người xét duyệt — `reviewed_by` join). |
| `type` | string | `all` | `all` \| `Inbound` \| `Outbound` \| `Return` \| `Debt`. **v1:** chỉ `all` và `Inbound` trả dữ liệu; `Outbound`/`Return`/`Debt` → `items: []` (cùng `total: 0`). |
| `fromDate` | `YYYY-MM-DD` | — | `reviewed_at::date >= fromDate`. |
| `toDate` | `YYYY-MM-DD` | — | `reviewed_at::date <= toDate` (cuối ngày inclusive). |
| `page` | int ≥ 1 | `1` | |
| `limit` | int 1–100 | `20` | |

**Validation:** nếu có cả `fromDate` và `toDate` mà `fromDate > toDate` → **400**.

---

## 6. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "entityType": "stock_receipt",
        "entityId": 8,
        "transactionCode": "PN-2026-0008",
        "type": "Inbound",
        "creatorName": "Nguyễn Văn Kho",
        "date": "2026-04-18T10:00:00Z",
        "reviewedAt": "2026-04-18T11:30:00Z",
        "totalAmount": 8900000,
        "resolution": "Rejected",
        "rejectionReason": "Sai đơn giá so với hợp đồng",
        "notes": "Nhập bánh kẹo Kinh Đô",
        "reviewedByUserId": 2,
        "reviewerName": "Chủ hệ thống",
        "approvedByUserId": null,
        "approvedAt": null
      },
      {
        "entityType": "stock_receipt",
        "entityId": 7,
        "transactionCode": "PN-2026-0007",
        "type": "Inbound",
        "creatorName": "Nguyễn Văn Kho",
        "date": "2026-04-17T09:00:00Z",
        "reviewedAt": "2026-04-17T15:00:00Z",
        "totalAmount": 5000000,
        "resolution": "Approved",
        "rejectionReason": null,
        "notes": null,
        "reviewedByUserId": 2,
        "reviewerName": "Chủ hệ thống",
        "approvedByUserId": 2,
        "approvedAt": "2026-04-17T15:00:00Z"
      }
    ],
    "page": 1,
    "limit": 20,
    "total": 45
  },
  "message": "Thành công"
}
```

### 6.1 Quy tắc map field (nguồn sự thật)

| JSON | Nguồn DB |
| :--- | :-------- |
| `resolution` | `StockReceipts.status` |
| `reviewedAt` | `StockReceipts.reviewed_at` (**bắt buộc NOT NULL** cho bản ghi trong tập kết quả; bản ghi `reviewed_at IS NULL` loại khỏi history — xem §8.3) |
| `rejectionReason` | `StockReceipts.rejection_reason` |
| `reviewedByUserId` / `reviewerName` | `StockReceipts.reviewed_by` → `Users` |
| `approvedByUserId` / `approvedAt` | `approved_by` / `approved_at` (thường chỉ khác null khi `Approved`) |
| `date` | `created_at` (ngày tạo phiếu; hiển thị như mock) |

---

## 7. Logic DB

### 7.1 Điều kiện lọc `type` (v1)

```text
IF :type IN ('Outbound', 'Return', 'Debt') THEN return empty page (WHERE false shortcut).
ELSE IF :type = 'Inbound' OR :type = 'all' THEN apply SQL below (stock_receipt only).
```

### 7.2 Danh sách + đếm `total`

Chỉ lấy bản ghi đã có mốc quyết định:

```sql
SELECT
  'stock_receipt' AS entity_type,
  sr.id AS entity_id,
  sr.receipt_code,
  'Inbound' AS type_label,
  u_creator.full_name AS creator_name,
  sr.created_at AS created_at,
  sr.reviewed_at,
  sr.total_amount,
  sr.status AS resolution,
  sr.rejection_reason,
  sr.notes,
  sr.approved_by,
  sr.approved_at,
  sr.reviewed_by,
  u_rev.full_name AS reviewer_name
FROM stock_receipts sr
JOIN users u_creator ON u_creator.id = sr.staff_id
LEFT JOIN users u_rev ON u_rev.id = sr.reviewed_by
WHERE sr.status IN ('Approved', 'Rejected')
  AND sr.reviewed_at IS NOT NULL
  AND ( :resolution = 'all' OR sr.status = :resolution )
  AND ( :search IS NULL OR sr.receipt_code ILIKE '%' || :search || '%'
        OR u_creator.full_name ILIKE '%' || :search || '%'
        OR u_rev.full_name ILIKE '%' || :search || '%' )
  AND ( :from_date IS NULL OR sr.reviewed_at::date >= :from_date::date )
  AND ( :to_date IS NULL OR sr.reviewed_at::date <= :to_date::date )
ORDER BY sr.reviewed_at DESC
LIMIT :limit OFFSET (:page - 1) * :limit;
```

`COUNT(*)` cùng `FROM`/`WHERE` (không `ORDER`/`LIMIT`) cho `data.total`.

### 7.3 Dữ liệu cũ chưa backfill

Bản ghi `Approved`/`Rejected` mà **`reviewed_at IS NULL`** **không** xuất hiện trong API cho đến khi chạy backfill (§2). Tránh dùng `updated_at` làm mốc thời gian phê duyệt.

---

## 8. Lỗi

### 8.1 400 Bad Request — khoảng ngày sai

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "fromDate không được lớn hơn toDate"
}
```

### 8.2 403 Forbidden

```json
{
  "success": false,
  "error": "FORBIDDEN",
  "message": "Bạn không có quyền xem lịch sử phê duyệt"
}
```

### 8.3 401 / 500

Theo chuẩn dự án.

---

## 9. Acceptance criteria (UAT)

1. Chỉ `Owner`/`Admin` gọi được; user vai `Staff` nhận **403**.  
2. Phiếu `Rejected` luôn có `rejectionReason` khác null/rỗng trong response (sau khi Task020 ghi đúng cột).  
3. Lọc `fromDate`/`toDate` áp trên **`reviewed_at`**, không phải `updated_at`.  
4. `type=Outbound` (và Return, Debt) trả **0** bản ghi, **không** lỗi.  
5. `fromDate > toDate` → **400**.  
6. Sắp xếp mặc định: **`reviewed_at` giảm dần**.

---

## 10. Zod (query — FE)

```typescript
import { z } from "zod";

export const ApprovalsHistoryQuerySchema = z
  .object({
    resolution: z.enum(["all", "Approved", "Rejected"]).optional().default("all"),
    search: z.string().optional(),
    type: z.enum(["all", "Inbound", "Outbound", "Return", "Debt"]).optional().default("all"),
    fromDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
    toDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
    page: z.coerce.number().int().min(1).optional().default(1),
    limit: z.coerce.number().int().min(1).max(100).optional().default(20),
  })
  .refine(
    (q) =>
      !q.fromDate ||
      !q.toDate ||
      q.fromDate <= q.toDate,
    { message: "fromDate không được lớn hơn toDate", path: ["toDate"] }
  );
```

---

## 11. Ghi chú FE

- Cột “Ngày xử lý” dùng **`reviewedAt`** (thay `processedDate` mock).  
- Map `resolution` → `status` cho `OrderTable`.  
- `reviewerName` hiển thị cho cả **Đã phê duyệt** và **Đã từ chối**.
