# 📄 API SPEC: `GET /api/v1/customers` — Danh sách khách hàng - Task048

> **Trạng thái**: Draft  
> **Feature**: UC9 — màn **Khách hàng** (`CustomersPage`, `CustomerTable`, `CustomerToolbar`)  
> **Tags**: RESTful, Customers, Pagination, Read

---

## 1. Mục tiêu Task

- Danh sách **phân trang** khách hàng với `search` (tên, mã, SĐT, email), `status`; read-model **`loyaltyPoints`**, **`totalSpent`**, **`orderCount`** theo [`Database_Specification.md`](../UC/Database_Specification.md) **§4** (điểm lưu trên `Customers`; tổng chi / số đơn tính từ `SalesOrders`).

---

## 2. Endpoint

**`GET /api/v1/customers`**

---

## 3. Tham chiếu

[`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.10** — `Customers`, `SalesOrders`.

---

## 4. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Endpoint** | `/api/v1/customers` |
| **Method** | `GET` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner, Staff, Admin — đọc khách hàng |
| **Use Case Ref** | UC9 (master), UC8 (nếu gom module đối tác) |

---

## 5. Query parameters

| Tham số | Kiểu | Mặc định | Mô tả |
| :------ | :--- | :------- | :---- |
| `search` | string | — | ILIKE `name`, `customer_code`, `phone`, `email` |
| `status` | string | `all` | `all` \| `Active` \| `Inactive` |
| `page` | int ≥ 1 | `1` | |
| `limit` | int 1–100 | `20` | |
| `sort` | string | `updatedAt:desc` | Whitelist |

---

## 6. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "items": [
      {
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
      }
    ],
    "page": 1,
    "limit": 20,
    "total": 200
  },
  "message": "Thành công"
}
```

- **`totalSpent`**: `COALESCE(SUM(so.total_amount), 0)` với `SalesOrders` `status != 'Cancelled'` (theo query mẫu DB §4).
- **`orderCount`**: `COUNT(*)` cùng điều kiện (hoặc mọi trạng thái — ghi rõ policy).

---

## 7. Logic DB

```sql
SELECT
  c.id,
  c.customer_code,
  c.name,
  c.phone,
  c.email,
  c.address,
  c.loyalty_points,
  c.status,
  c.created_at,
  c.updated_at,
  COALESCE(SUM(so.total_amount) FILTER (WHERE so.status IS DISTINCT FROM 'Cancelled'), 0) AS total_spent,
  COUNT(so.id) FILTER (WHERE so.status IS DISTINCT FROM 'Cancelled') AS order_count
FROM Customers c
LEFT JOIN SalesOrders so ON so.customer_id = c.id
WHERE /* search, status */
GROUP BY c.id
ORDER BY /* whitelist */
LIMIT :limit OFFSET :offset;
```

Đếm `total`: subquery hoặc `COUNT(*) OVER` tùy hiệu năng.

---

## 8. Lỗi

**400** / **401** / **403** / **500**.

---

## 9. Zod (query — FE)

```typescript
import { z } from "zod";

export const CustomersListQuerySchema = z.object({
  search: z.string().optional(),
  status: z.enum(["all", "Active", "Inactive"]).optional().default("all"),
  page: z.coerce.number().int().min(1).optional().default(1),
  limit: z.coerce.number().int().min(1).max(100).optional().default(20),
  sort: z.string().optional(),
});
```
