# 📄 API SPEC: `GET /api/v1/approvals/pending` — Danh sách chờ phê duyệt - Task061

> **Trạng thái**: Draft  
> **Feature**: **UC4** — màn **Chờ phê duyệt** (`PendingApprovalsPage`, `/approvals/pending`)  
> **Tags**: RESTful, Approvals, Read, Polymorphic  
> **Hợp đồng BE (đã Approved):** [`SRS_Task061-062_approvals-pending-and-history.md`](../../../backend/docs/srs/SRS_Task061-062_approvals-pending-and-history.md) — lọc ngày pending theo **`receipt_date`**, trường **`date`** trong item = **`receipt_date`**, thứ tự **`created_at ASC`**, Staff **403**.

---

## 1. Mục tiêu Task

- Trả **danh sách giao dịch đang chờ Owner/Admin duyệt**, thống nhất nhiều loại chứng từ (Inbound / Outbound / Return / Debt — theo [`mini-erp/src/features/approvals/types.ts`](../../mini-erp/src/features/approvals/types.ts) `ApprovalType`).
- **Phiên bản tối thiểu (MVP triển khai)**: SQL đầy đủ cho **`StockReceipts`** (`status = 'Pending'`); các loại khác **UNION** hoặc read-model rỗng cho đến khi có Task endpoint nghiệp vụ tương ứng. Phiếu ở trạng thái chờ có **`reviewed_at` / `reviewed_by` / `rejection_reason` = NULL** cho đến khi Task019 hoặc Task020 chạy (cột mới — [`Database_Specification.md`](../UC/Database_Specification.md) §17).

---

## 2. Mục đích Endpoint

**`GET /api/v1/approvals/pending`** thay `useApprovalStore` mock; hỗ trợ lọc **mã**, **khoảng ngày trên phiếu** (`fromDate` / `toDate` so với **`receipt_date`** — đồng bộ SRS **OQ-2b**), tổng hợp **`summary`** cho badge “N giao dịch cần xử lý”. Thứ tự danh sách: **`created_at ASC`** (FIFO theo thời điểm vào hệ thống).

**Phê duyệt / Từ chối** từ UI: **không** dùng endpoint này — map `entityType` + `entityId` sang:

| `type` (UI) | `entityType` (API) | Duyệt | Từ chối |
| :---------- | :----------------- | :---- | :------ |
| Inbound | `stock_receipt` | [`API_Task019_stock_receipts_approve.md`](API_Task019_stock_receipts_approve.md) | [`API_Task020_stock_receipts_reject.md`](API_Task020_stock_receipts_reject.md) |
| Outbound | `stock_dispatch` | _(Task sau — `POST /stock-dispatches/{id}/approve` hoặc tương đương)_ | _(Task sau)_ |
| Return | `sales_order` / `return_request` | _(Task sau — luồng trả hàng UC9 + UC4)_ | _(Task sau)_ |
| Debt | `debt_request` / `finance_…` | _(Task sau)_ | _(Task sau)_ |

Request body Task019 (`inboundLocationId`) vẫn bắt buộc khi duyệt phiếu nhập.

---

## 3. Tham chiếu

[`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.5** — [`Database_Specification.md`](../UC/Database_Specification.md) **§17** `StockReceipts`, **§11** `SystemLogs`.

---

## 4. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Endpoint** | `/api/v1/approvals/pending` |
| **Method** | `GET` |
| **Authentication** | `Bearer` |
| **RBAC** | **Owner**, **Admin** (UC4); **Staff → 403** trên endpoint này (v1 — SRS **OQ-1a**) |
| **Use Case Ref** | UC4 |

---

## 5. Query parameters

| Tham số | Kiểu | Mặc định | Mô tả |
| :------ | :--- | :------- | :---- |
| `search` | string | — | ILIKE `receipt_code` / mã chứng từ tương đương; có thể mở rộng tên `Users` (người tạo). |
| `type` | string | `all` | `all` \| `Inbound` \| `Outbound` \| `Return` \| `Debt` — lọc theo loại hiển thị UI. |
| `fromDate` | date (YYYY-MM-DD) | — | So với **`receipt_date`** (ngày trên phiếu); inclusive. |
| `toDate` | date (YYYY-MM-DD) | — | So với **`receipt_date`**; **cuối ngày inclusive**. |
| `page` | int ≥ 1 | `1` | |
| `limit` | int 1–100 | `50` | Danh sách chờ thường ngắn. |

**Validation:** nếu có cả `fromDate` và `toDate` mà `fromDate > toDate` → **400** `BAD_REQUEST` (cùng quy tắc với `GET /approvals/history` — SRS §8.A.5).

---

## 6. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "summary": {
      "totalPending": 2,
      "byType": { "Inbound": 2, "Outbound": 0, "Return": 0, "Debt": 0 }
    },
    "items": [
      {
        "entityType": "stock_receipt",
        "entityId": 12,
        "transactionCode": "PN-2026-0012",
        "type": "Inbound",
        "creatorName": "Nguyễn Văn Kho",
        "date": "2026-04-19T00:00:00Z",
        "totalAmount": 12500000,
        "status": "Pending",
        "notes": "Nhập hàng sữa từ Vinamilk"
      }
    ],
    "page": 1,
    "limit": 50,
    "total": 2
  },
  "message": "Thành công"
}
```

**Khóa tổng hợp cho FE**: dùng cặp **`entityType` + `entityId`** khi gọi Task019/020 (không dùng chung `id` số across bảng).

**Trường `date` trong mỗi item:** map từ cột DB **`receipt_date`** (serialize ISO-8601, ví dụ nửa đêm UTC — quy ước chung với BE).

---

## 7. Logic DB (MVP — phiếu nhập)

> Tên bảng thực tế trên PostgreSQL/Flyway: **`stockreceipts`** (không gạch dưới). Ví dụ dưới dùng đúng tên đó.

### 7.1 Danh sách `items` (StockReceipts)

```sql
SELECT
  'stock_receipt' AS entity_type,
  sr.id AS entity_id,
  sr.receipt_code AS transaction_code,
  'Inbound' AS type_label,
  u.full_name AS creator_name,
  sr.receipt_date,
  sr.created_at,
  sr.total_amount,
  sr.status,
  sr.notes
FROM stockreceipts sr
JOIN users u ON u.id = sr.staff_id
WHERE sr.status = 'Pending'
  AND ( :search IS NULL OR sr.receipt_code ILIKE '%' || :search || '%' )
  AND ( :from_date IS NULL OR sr.receipt_date >= :from_date::date )
  AND ( :to_date IS NULL OR sr.receipt_date <= :to_date::date )
ORDER BY sr.created_at ASC;
```

- JSON **`date`**: từ **`receipt_date`** (không dùng `created_at` cho field này).

### 7.2 `summary`

- `totalPending`: `COUNT(*)` cùng `WHERE` (sau này cộng thêm các UNION).
- `byType`: đếm theo nhánh UNION (MVP: chỉ **Inbound** có thể > 0; Outbound / Return / Debt = **0** cho đến khi có UNION).

---

## 8. Lỗi

### 8.1 400 — khoảng ngày sai

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Ngày bắt đầu không được sau ngày kết thúc.",
  "details": { "fromDate": "fromDate phải nhỏ hơn hoặc bằng toDate" }
}
```

### 8.2 401 / 403 / 500

Theo [`API_RESPONSE_ENVELOPE.md`](API_RESPONSE_ENVELOPE.md) và SRS §8.A.5 (403 Staff: không có quyền xem danh sách chờ phê duyệt).

---

## 9. Zod (query — FE)

```typescript
import { z } from "zod";

export const ApprovalsPendingQuerySchema = z
  .object({
    search: z.string().optional(),
    type: z.enum(["all", "Inbound", "Outbound", "Return", "Debt"]).optional().default("all"),
    fromDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
    toDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
    page: z.coerce.number().int().min(1).optional().default(1),
    limit: z.coerce.number().int().min(1).max(100).optional().default(50),
  })
  .refine(
    (q) => !q.fromDate || !q.toDate || q.fromDate <= q.toDate,
    { message: "fromDate không được lớn hơn toDate", path: ["toDate"] }
  );
```

---

## 10. Ghi chú FE

- **`date`:** là **ngày trên phiếu** (`receipt_date`), không nhầm với thời điểm tạo bản ghi (`created_at` chỉ ảnh hưởng thứ tự sort phía BE).
- Thay `displayData` map sang `OrderTable`: map `transactionCode` → `orderCode`, `creatorName` → `customerName`, `type` giữ nguyên chuỗi hiển thị badge.
- Nút **Phê duyệt**: `POST /api/v1/stock-receipts/{entityId}/approve` khi `entityType === 'stock_receipt'`.
- Nút **Từ chối**: `POST .../reject` với `{ "reason": "..." }`.
