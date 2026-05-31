# 📄 API SPEC: `PATCH /api/v1/sales-orders/{id}` — Cập nhật đơn - Task057

> **Trạng thái**: Draft  
> **Feature**: UC9 — `OrderFormDialog` / `ReturnFormDialog` (sửa meta: trạng thái, thanh toán, ghi chú, địa chỉ giao)  
> **Tags**: RESTful, SalesOrders, Update

---

## 1. Mục tiêu Task

- **`PATCH`** một phần header đơn; **không** thay thế toàn bộ `OrderDetails` trong Task này (sửa dòng → Task backlog `PATCH .../lines` hoặc xóa tạo lại theo policy).

---

## 2. Endpoint

**`PATCH /api/v1/sales-orders/{id}`**

---

## 3. Ràng buộc nghiệp vụ

- DB §19: **`status = Cancelled`** → không cho sửa (→ **409**), trừ flow đặc biệt do Owner bật.
- Đổi `discount_amount` phải vẫn thỏa `chk_discount` và `total_amount` hiện tại (hoặc cho phép đồng thời PATCH `total_amount` — thường **không**; giảm giá đủ dùng `discount_amount`).

---

## 4. Request body (partial)

```json
{
  "status": "Processing",
  "paymentStatus": "Partial",
  "shippingAddress": "Địa chỉ mới",
  "notes": "Giao buổi sáng",
  "discountAmount": 300000
}
```

| Trường | Mô tả |
| :----- | :---- |
| `status` | Whitelist theo DB **trừ** `Cancelled` — hủy đơn dùng [`API_Task058_sales_orders_cancel.md`](API_Task058_sales_orders_cancel.md). |
| `paymentStatus` | Sau migration cột `payment_status` |
| `shippingAddress` | string \| null |
| `notes` | string \| null |
| `discountAmount` | number ≥ 0 |

---

## 5. Thành công — `200 OK`

Trả object như Task055.

---

## 6. Logic DB

1. **`SELECT … FROM sales_orders WHERE id = ? FOR UPDATE`** → **404**.
2. Kiểm tra trạng thái cho phép sửa → **409** nếu `Cancelled`.
3. **`UPDATE sales_orders SET …, updated_at = NOW()`**.

---

## 7. Lỗi

**400** / **404** / **409** / **401** / **403** / **500**.

---

## 8. Zod (body)

```typescript
import { z } from "zod";

export const SalesOrderPatchBodySchema = z
  .object({
    status: z.enum(["Pending", "Processing", "Partial", "Shipped", "Delivered"]).optional(),
    paymentStatus: z.enum(["Paid", "Unpaid", "Partial"]).optional(),
    shippingAddress: z.string().nullable().optional(),
    notes: z.string().nullable().optional(),
    discountAmount: z.number().nonnegative().optional(),
  })
  .refine((o) => Object.keys(o).length > 0, { message: "Cần ít nhất một trường" });
```
