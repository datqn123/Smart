# 📄 API SPEC: `POST /api/v1/customers/bulk-delete` — Xóa nhiều khách hàng - Task053

> **Trạng thái**: Draft  
> **Feature**: UC9 — `CustomersPage` xóa hàng loạt  
> **Tags**: RESTful, Customers, Bulk, Delete

---

## 1. Mục tiêu Task

- Xóa nhiều khách hàng; ràng buộc **giống** [`API_Task052_customers_delete.md`](API_Task052_customers_delete.md) cho từng `id`.

---

## 2. Endpoint

**`POST /api/v1/customers/bulk-delete`**

---

## 3. Request body

```json
{
  "ids": [10, 11, 12]
}
```

`ids`: tối đa **50** (gợi ý).

---

## 4. Thành công

Theo policy **all-or-nothing** hoặc **partial** — cùng hợp đồng với [`API_Task041_products_bulk_delete.md`](API_Task041_products_bulk_delete.md).

---

## 5. Logic DB

Kiểm tra `SalesOrders` cho từng `customer_id` trước khi `DELETE`; transaction all-or-nothing khuyến nghị để tránh xóa lệch một phần khi không dùng partial.

---

## 6. Zod (body)

```typescript
import { z } from "zod";
export const CustomersBulkDeleteBodySchema = z.object({
  ids: z.array(z.number().int().positive()).min(1).max(50),
});
```
