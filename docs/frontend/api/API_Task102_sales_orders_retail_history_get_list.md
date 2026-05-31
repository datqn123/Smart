# API SPEC: `GET /api/v1/sales-orders/retail/history` — Lịch sử hóa đơn bán lẻ (read-only list) — Task102

> **Trạng thái:** Draft — đồng bộ SRS [`SRS_Task102_retail-invoice-history.md`](../../../backend/docs/srs/SRS_Task102_retail-invoice-history.md) (**Approved** 02/05/2026)  
> **Feature:** UC9 — màn **Lịch sử hóa đơn bán lẻ** (`/orders/wholesale`, thay nội dung cũ Đơn bán sỉ)  
> **Tags:** RESTful, SalesOrders, Pagination, Read-only

---

## 1. Mục tiêu

- Danh sách **chỉ** đơn `orderChannel = Retail`, gồm trạng thái **`Delivered`** và **`Cancelled`** (theo PO Task102 §4).
- Hỗ trợ **`dateFrom` / `dateTo`** (v1), `search`, phân trang, `sort` whitelist.
- **Không** nhận `orderChannel`, `status`, `paymentStatus` từ client.

---

## 2. Endpoint

**`GET /api/v1/sales-orders/retail/history`**

---

## 3. Tham chiếu

| Tài liệu | Đường dẫn |
| :--- | :--- |
| SRS | [`SRS_Task102_retail-invoice-history.md`](../../../backend/docs/srs/SRS_Task102_retail-invoice-history.md) |
| Envelope | [`API_RESPONSE_ENVELOPE.md`](API_RESPONSE_ENVELOPE.md) |
| Catalog | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) §4.10 |
| DB | `Database_Specification.md` §19 `SalesOrders` |

---

## 4. Overview

| Thuộc tính | Giá trị |
| :--- | :--- |
| **Authentication** | `Bearer` |
| **RBAC** | Mọi user đã đăng nhập được gọi (theo SRS §6); chặn theo Task101 menu nếu role không có quyền vào module Đơn hàng. |

---

## 5. Query parameters

| Tham số | Kiểu | Mặc định | Mô tả |
| :--- | :--- | :--- | :--- |
| `search` | string | — | Trim, tối đa **100** ký tự. ILIKE `order_code`, `customers.name`. |
| `dateFrom` | string (`yyyy-MM-dd`) | — | Lọc `created_at` **≥** đầu ngày. **Múi giờ:** Dev chốt một chuẩn (khuyến nghị **Asia/Ho_Chi_Minh** cho biên `dateFrom`/`dateTo`) và ghi vào release notes / comment handler. |
| `dateTo` | string (`yyyy-MM-dd`) | — | Lọc `created_at` **≤** cuối ngày `dateTo` (cùng múi giờ với `dateFrom`). |
| `page` | int ≥ 1 | `1` | |
| `limit` | int 1–100 | `20` | |
| `sort` | string | `createdAt:desc` | Whitelist: `createdAt:asc`, `createdAt:desc`, `finalAmount:asc`, `finalAmount:desc`. |

**Validation:**

- Nếu cả `dateFrom` và `dateTo` có mặt: bắt buộc `dateFrom` ≤ `dateTo` → nếu vi phạm **400**.
- Định dạng ngày sai → **400** (`details` theo field).

**Filter server-side (không là query param):**

- `order_channel = 'Retail'`
- `status IN ('Delivered', 'Cancelled')`

### 5.1 Múi giờ (`dateFrom` / `dateTo`)

- Dev **chốt và ghi tại đây** khi triển khai: biên ngày áp dụng theo **`Asia/Ho_Chi_Minh`** hoặc **UTC** nhất quán với cột `sales_orders.created_at`.
- SRS Task102 §12 — *Giả định* trỏ về mục này.

---

## 6. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 501,
        "orderCode": "SO-2026-0501",
        "customerName": "Khách lẻ",
        "finalAmount": 185000,
        "itemsCount": 3,
        "createdAt": "2026-05-02T08:15:00Z"
      }
    ],
    "page": 1,
    "limit": 20,
    "total": 1
  },
  "message": "Thao tác thành công"
}
```

---

## 7. Lỗi

| HTTP | `error` | Khi nào |
| :---: | :--- | :--- |
| 400 | `BAD_REQUEST` | Query không hợp lệ (`page`, `limit`, `sort`, `dateFrom`/`dateTo`). |
| 401 | `UNAUTHORIZED` | JWT thiếu / hết hạn. |
| 403 | `FORBIDDEN` | Policy toàn cục (vd. không vào được module). |
| 500 | `INTERNAL_SERVER_ERROR` | Lỗi không lường trước. |

**400 — ví dụ (`dateFrom` > `dateTo`):**

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Dữ liệu không hợp lệ",
  "details": {
    "dateTo": "Ngày kết thúc phải sau hoặc bằng ngày bắt đầu"
  }
}
```

---

## 8. Ghi chú triển khai

- **Chi tiết đơn:** `GET /api/v1/sales-orders/{id}` — [`API_Task055_sales_orders_get_by_id.md`](API_Task055_sales_orders_get_by_id.md). Màn Task102 chỉ mở `id` từ list retail; không thay đổi contract Task055 toàn cục (màn Trả hàng / khác vẫn dùng).
- **Index:** xem SRS Task102 §10.3.

---

## 9. Zod (query — FE)

```typescript
import { z } from "zod";

export const RetailSalesHistoryQuerySchema = z
  .object({
    search: z.string().trim().max(100).optional(),
    dateFrom: z
      .string()
      .regex(/^\d{4}-\d{2}-\d{2}$/)
      .optional(),
    dateTo: z
      .string()
      .regex(/^\d{4}-\d{2}-\d{2}$/)
      .optional(),
    page: z.coerce.number().int().min(1).optional().default(1),
    limit: z.coerce.number().int().min(1).max(100).optional().default(20),
    sort: z
      .enum([
        "createdAt:asc",
        "createdAt:desc",
        "finalAmount:asc",
        "finalAmount:desc",
      ])
      .optional()
      .default("createdAt:desc"),
  })
  .superRefine((val, ctx) => {
    if (val.dateFrom && val.dateTo && val.dateFrom > val.dateTo) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "dateTo phải >= dateFrom",
        path: ["dateTo"],
      });
    }
  });
```
