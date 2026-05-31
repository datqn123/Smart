# 📄 API SPEC: `GET /api/v1/sales-orders` — Danh sách đơn bán / trả - Task054

> **Trạng thái**: Draft  
> **Feature**: UC9 — màn **Đơn bán sỉ** (`WholesalePage`), **Đơn trả hàng** (`ReturnsPage`); có thể dùng cho lịch sử POS  
> **Tags**: RESTful, SalesOrders, Pagination, Read

---

## 1. Mục tiêu Task

- Cung cấp **danh sách phân trang** `SalesOrders` kèm read-model (`customerName`, `itemsCount`, …) phục vụ `OrderTable`, `OrderToolbar`, lọc `search` / `status` / **`orderChannel`**.

---

## 2. Khoảng trống schema (bắt buộc đọc trước khi code)

[`Database_Specification.md`](../UC/Database_Specification.md) **§19** `SalesOrders` **chưa** có:

- **`order_channel`**: phân biệt **Bán lẻ / Bán sỉ / Trả hàng** (khớp FE `Order.type`: `Retail` \| `Wholesale` \| `Return`).
- **`payment_status`**: khớp FE `Paid` \| `Unpaid` \| `Partial`.

**DDL đề xuất (PostgreSQL):**

```sql
ALTER TABLE sales_orders
  ADD COLUMN order_channel VARCHAR(20) NOT NULL DEFAULT 'Wholesale'
    CHECK (order_channel IN ('Retail', 'Wholesale', 'Return'));

ALTER TABLE sales_orders
  ADD COLUMN payment_status VARCHAR(20) NOT NULL DEFAULT 'Unpaid'
    CHECK (payment_status IN ('Paid', 'Unpaid', 'Partial'));

-- Phiếu trả tham chiếu đơn bán gốc (tuỳ nghiệp vụ)
ALTER TABLE sales_orders
  ADD COLUMN ref_sales_order_id INT NULL REFERENCES sales_orders(id);
```

**Trạng thái đơn (FE vs DB):** FE dùng thêm `Completed`; API/DB theo §19: `Pending`, `Processing`, `Partial`, `Shipped`, `Delivered`, `Cancelled`. Mapping khuyến nghị: **`Completed` (UI) ↔ `Delivered` (API)** — response dùng `Delivered`, FE đổi nhãn nếu cần.

---

## 3. Endpoint

**`GET /api/v1/sales-orders`**

---

## 4. Tham chiếu

[`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.10** — `SalesOrders`, `Customers`, `OrderDetails`.

---

## 5. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Endpoint** | `/api/v1/sales-orders` |
| **Method** | `GET` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner, Staff — đọc đơn trong phạm vi quyền |
| **Use Case Ref** | UC9 |

---

## 6. Query parameters

| Tham số | Kiểu | Mặc định | Mô tả |
| :------ | :--- | :------- | :---- |
| `orderChannel` | string | — | `Retail` \| `Wholesale` \| `Return` — **khuyến nghị** gửi từ màn một loại (WholesalePage → `Wholesale`, ReturnsPage → `Return`). Bỏ qua → tất cả kênh (chỉ nên bật cho Admin / báo cáo). |
| `search` | string | — | ILIKE `order_code`, tên KH (`Customers.name`). |
| `status` | string | `all` | `all` hoặc một trong các giá trị CHECK §19 (chuỗi PascalCase giống DB). |
| `paymentStatus` | string | `all` | `all` \| `Paid` \| `Unpaid` \| `Partial` (sau migration). |
| `page` | int ≥ 1 | `1` | |
| `limit` | int 1–100 | `20` | |
| `sort` | string | `createdAt:desc` | Whitelist |

---

## 7. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "orderCode": "SO-2026-0001",
        "customerId": 12,
        "customerName": "Công ty TNHH Tuấn Phát",
        "totalAmount": 45000000,
        "discountAmount": 0,
        "finalAmount": 45000000,
        "status": "Delivered",
        "orderChannel": "Wholesale",
        "paymentStatus": "Paid",
        "itemsCount": 5,
        "notes": null,
        "createdAt": "2026-03-01T10:00:00Z",
        "updatedAt": "2026-03-02T08:00:00Z"
      }
    ],
    "page": 1,
    "limit": 20,
    "total": 120
  },
  "message": "Thành công"
}
```

**`itemsCount`**: `COUNT(*)` từ `OrderDetails` theo `order_id`.

---

## 8. Logic DB

1. JWT → **401** / **403**.
2. Validate query → **400**.
3. `FROM SalesOrders so JOIN Customers c ON c.id = so.customer_id` + `LEFT JOIN` aggregate lines count.
4. `WHERE` theo `order_channel`, `search`, `status`, `payment_status`, RBAC.
5. `ORDER BY` + `LIMIT`/`OFFSET`; query `COUNT(*)` cho `total`.

```sql
SELECT so.id, so.order_code, so.customer_id, c.name AS customer_name,
       so.total_amount, so.discount_amount, so.final_amount,
       so.status, so.order_channel, so.payment_status,
       so.notes, so.created_at, so.updated_at,
       (SELECT COUNT(*)::int FROM order_details od WHERE od.order_id = so.id) AS items_count
FROM sales_orders so
JOIN customers c ON c.id = so.customer_id
WHERE so.order_channel = :channel /* + filters */;
```

---

## 9. Lỗi

**400** / **401** / **403** / **500**.

---

## 10. Zod (query — FE)

```typescript
import { z } from "zod";

export const SalesOrdersListQuerySchema = z.object({
  orderChannel: z.enum(["Retail", "Wholesale", "Return"]).optional(),
  search: z.string().optional(),
  status: z.string().optional(),
  paymentStatus: z.enum(["all", "Paid", "Unpaid", "Partial"]).optional().default("all"),
  page: z.coerce.number().int().min(1).optional().default(1),
  limit: z.coerce.number().int().min(1).max(100).optional().default(20),
  sort: z.string().optional(),
});
```

---

## 11. Ánh xạ UI

| Màn | `orderChannel` / ghi chú |
| :-- | :-------------- |
| `/orders/wholesale` | **Không còn dùng Task054 cho màn này** — màn **Lịch sử hóa đơn bán lẻ** dùng [`API_Task102_sales_orders_retail_history_get_list.md`](API_Task102_sales_orders_retail_history_get_list.md) (`GET /sales-orders/retail/history`). |
| `/orders/returns` | `Return` |
