# 📄 API SPEC: `POST /api/v1/sales-orders` — Tạo đơn (bán sỉ / trả hàng) - Task056

> **Trạng thái**: Draft  
> **Feature**: UC9 — `OrderFormDialog` (WholesalePage), `ReturnFormDialog` (ReturnsPage) — **không** gồm checkout POS (→ Task060)  
> **Tags**: RESTful, SalesOrders, OrderDetails, Create

---

## 1. Mục tiêu Task

- Tạo **`SalesOrders`** + **`OrderDetails`** trong **một transaction**; sinh **`order_code`** theo policy (VD: `SO-YYYY-NNNN`); set **`order_channel`** = `Wholesale` hoặc `Return`.

---

## 2. Endpoint

**`POST /api/v1/sales-orders`**

---

## 3. Tham chiếu

[`Database_Specification.md`](../UC/Database_Specification.md) §19–20; DDL bổ sung — [`API_Task054_sales_orders_get_list.md`](API_Task054_sales_orders_get_list.md).

---

## 4. Request body

### 4.1 Bán sỉ (`orderChannel: "Wholesale"`)

```json
{
  "orderChannel": "Wholesale",
  "customerId": 12,
  "discountAmount": 500000,
  "shippingAddress": "KCN VSIP Bình Dương",
  "notes": null,
  "paymentStatus": "Unpaid",
  "status": "Pending",
  "lines": [
    {
      "productId": 5,
      "unitId": 12,
      "quantity": 5,
      "unitPrice": 1250000
    }
  ]
}
```

| Trường | Bắt buộc | Mô tả |
| :----- | :------- | :---- |
| `orderChannel` | Có | `Wholesale` \| `Return` |
| `customerId` | Có | FK `Customers` |
| `discountAmount` | Không | Mặc định `0`; `<= total_amount` sau tính dòng |
| `lines` | Có | Ít nhất 1 phần tử |
| `lines[].productId` | Có | |
| `lines[].unitId` | Có | Thuộc `product_id` |
| `lines[].quantity` | Có | > 0 |
| `lines[].unitPrice` | Có | ≥ 0 — snapshot giá |
| `paymentStatus` | Không | Mặc định `Unpaid` |
| `status` | Không | Mặc định `Pending` |
| `shippingAddress` / `notes` | Không | |

**`total_amount`**: server tính `SUM(quantity * unitPrice)`; **`final_amount`** generated column nếu DB đã có.

### 4.2 Trả hàng (`orderChannel: "Return"`)

Thêm (khuyến nghị):

```json
{
  "orderChannel": "Return",
  "customerId": 10,
  "refSalesOrderId": 42,
  "notes": "Trả hàng do lỗi sản xuất",
  "paymentStatus": "Paid",
  "lines": [
    { "productId": 5, "unitId": 12, "quantity": 1, "unitPrice": 1250000 }
  ]
}
```

| Trường | Mô tả |
| :----- | :---- |
| `refSalesOrderId` | FK đơn bán gốc (sau migration); **409** nếu không cùng `customer_id` hoặc không tồn tại. |

**Nhập kho hoàn trả**: không nằm trong Task này — có thể gọi pipeline phiếu nhập / điều chỉnh tồn trong Task khác hoặc trigger sau `status` chuyển `Delivered`.

---

## 5. Thành công — `201 Created`

Trả object đầy đủ giống [`API_Task055_sales_orders_get_by_id.md`](API_Task055_sales_orders_get_by_id.md) (có `lines`).

---

## 6. Logic DB (transaction)

1. Validate → **400** (`lines` rỗng, FK, `discount_amount`).
2. Kiểm tra `ProductUnits` khớp `product_id` từng dòng → **400**.
3. **`INSERT INTO sales_orders`** (sinh `order_code`, set `order_channel`, `payment_status`, …).
4. **`INSERT INTO order_details`** từng dòng (`price_at_time` = `unitPrice`).
5. Commit; (tuỳ chọn) `SystemLogs`.

```sql
INSERT INTO sales_orders (order_code, customer_id, user_id, total_amount, discount_amount, status, order_channel, payment_status, shipping_address, notes, ref_sales_order_id)
VALUES (/* seq */, $cust, $uid, $total, $disc, $st, $ch, $pay, $ship, $notes, $ref)
RETURNING id;

INSERT INTO order_details (order_id, product_id, unit_id, quantity, price_at_time)
VALUES ($oid, ...);
```

---

## 7. Lỗi

- **400**: validation; đơn vị không thuộc SP.
- **404**: `customerId` / `refSalesOrderId` không tồn tại.
- **409**: nghiệp vụ Return không hợp lệ.
- **401** / **403** / **500**.

---

## 8. Zod (body — FE)

```typescript
import { z } from "zod";

const LineSchema = z.object({
  productId: z.number().int().positive(),
  unitId: z.number().int().positive(),
  quantity: z.number().positive(),
  unitPrice: z.number().nonnegative(),
});

export const SalesOrderCreateBodySchema = z.discriminatedUnion("orderChannel", [
  z.object({
    orderChannel: z.literal("Wholesale"),
    customerId: z.number().int().positive(),
    discountAmount: z.number().nonnegative().optional(),
    shippingAddress: z.string().optional().nullable(),
    notes: z.string().optional().nullable(),
    paymentStatus: z.enum(["Paid", "Unpaid", "Partial"]).optional(),
    status: z.enum(["Pending", "Processing", "Partial", "Shipped", "Delivered"]).optional(),
    lines: z.array(LineSchema).min(1),
  }),
  z.object({
    orderChannel: z.literal("Return"),
    customerId: z.number().int().positive(),
    refSalesOrderId: z.number().int().positive().optional(),
    notes: z.string().optional().nullable(),
    paymentStatus: z.enum(["Paid", "Unpaid", "Partial"]).optional(),
    lines: z.array(LineSchema).min(1),
  }),
]);
```
