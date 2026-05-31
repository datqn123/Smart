# 📄 API SPEC: `GET /api/v1/customers/{id}` — Chi tiết khách hàng - Task050

> **Trạng thái**: Draft  
> **Feature**: UC9 — `CustomerDetailDialog`  
> **Tags**: RESTful, Customers, Read

---

## 1. Mục tiêu Task

- Trả **một** khách hàng + **`totalSpent`**, **`orderCount`** (aggregate) giống Task048.

---

## 2. Endpoint

**`GET /api/v1/customers/{id}`**

---

## 3. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "id": 10,
    "customerCode": "KH00001",
    "name": "Lê Văn C",
    "phone": "0988111222",
    "email": "c@mail.com",
    "address": "Đà Nẵng",
    "loyaltyPoints": 120,
    "totalSpent": 15000000,
    "orderCount": 6,
    "status": "Active",
    "createdAt": "2026-02-01T08:00:00Z",
    "updatedAt": "2026-04-10T09:00:00Z"
  },
  "message": "Thành công"
}
```

---

## 4. Logic DB

```sql
SELECT c.*,
  COALESCE(SUM(so.total_amount) FILTER (WHERE so.status IS DISTINCT FROM 'Cancelled'), 0) AS total_spent,
  COUNT(so.id) FILTER (WHERE so.status IS DISTINCT FROM 'Cancelled') AS order_count
FROM Customers c
LEFT JOIN SalesOrders so ON so.customer_id = c.id
WHERE c.id = $1
GROUP BY c.id;
```

---

## 5. Lỗi

**404** / **401** / **403** / **500**.

---

## 6. Zod (params)

```typescript
import { z } from "zod";
export const CustomerIdParamsSchema = z.object({
  id: z.coerce.number().int().positive(),
});
```
