# 📄 API SPEC: `GET /api/v1/sales-orders/{id}` — Chi tiết đơn + dòng hàng - Task055

> **Trạng thái**: Draft  
> **Feature**: UC9 — `OrderDetailDialog` (bán sỉ / bán lẻ / trả — theo `orderChannel`)  
> **Tags**: RESTful, SalesOrders, OrderDetails, Read

---

## 1. Mục tiêu Task

- Trả **header** đơn + **`lines`** (`OrderDetails` join `Products`, `ProductUnits`) phục vụ popup chi tiết thay cho `mockOrderItems`.

---

## 2. Endpoint

**`GET /api/v1/sales-orders/{id}`**

---

## 3. Tham chiếu

[`Database_Specification.md`](../UC/Database_Specification.md) **§19** `SalesOrders`, **§20** `OrderDetails`.

**Schema mở rộng**: cột `order_channel`, `payment_status`, `ref_sales_order_id` — xem [`API_Task054_sales_orders_get_list.md`](API_Task054_sales_orders_get_list.md).

---

## 4. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Endpoint** | `/api/v1/sales-orders/{id}` |
| **Method** | `GET` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner, Staff |
| **Use Case Ref** | UC9 |

---

## 5. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "id": 1,
    "orderCode": "SO-2026-0001",
    "customerId": 12,
    "customerName": "Công ty TNHH Tuấn Phát",
    "totalAmount": 45000000,
    "discountAmount": 0,
    "finalAmount": 45000000,
    "status": "Processing",
    "orderChannel": "Wholesale",
    "paymentStatus": "Partial",
    "parentOrderId": null,
    "refSalesOrderId": null,
    "shippingAddress": null,
    "notes": null,
    "createdAt": "2026-03-01T10:00:00Z",
    "updatedAt": "2026-03-01T12:00:00Z",
    "lines": [
      {
        "id": 1001,
        "productId": 5,
        "productName": "Sơn Mykolor Grand",
        "skuCode": "MK-001",
        "unitId": 12,
        "unitName": "Thùng",
        "quantity": 5,
        "unitPrice": 1250000,
        "lineTotal": 6250000,
        "dispatchedQty": 0
      }
    ]
  },
  "message": "Thành công"
}
```

Với **`orderChannel = Return`**, `refSalesOrderId` (nếu có) trỏ đơn bán gốc.

---

## 6. Logic DB

```sql
SELECT so.*, c.name AS customer_name
FROM sales_orders so
JOIN customers c ON c.id = so.customer_id
WHERE so.id = $1;

SELECT od.id, od.product_id, p.name AS product_name, p.sku_code,
       od.unit_id, pu.unit_name, od.quantity, od.price_at_time,
       od.line_total, od.dispatched_qty
FROM order_details od
JOIN products p ON p.id = od.product_id
JOIN product_units pu ON pu.id = od.unit_id
WHERE od.order_id = $1
ORDER BY od.id;
```

Không tìm thấy → **404**.

---

## 7. Lỗi

**404** / **401** / **403** / **500**.

---

## 8. Zod (params)

```typescript
import { z } from "zod";
export const SalesOrderIdParamsSchema = z.object({
  id: z.coerce.number().int().positive(),
});
```
