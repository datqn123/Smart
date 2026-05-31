# 📄 API SPEC: `PATCH /api/v1/customers/{id}` — Cập nhật khách hàng - Task051

> **Trạng thái**: Draft  
> **Feature**: UC9 — `CustomerForm` (sửa)  
> **Tags**: RESTful, Customers, Update

---

## 1. Mục tiêu Task

- **`PATCH`** thông tin hồ sơ KH; **`loyaltyPoints`** chỉ chỉnh khi có quyền đặc biệt (Admin/Owner) — mặc định **không** cho Staff đổi tay điểm.

---

## 2. Endpoint

**`PATCH /api/v1/customers/{id}`**

---

## 3. Request body (partial)

```json
{
  "name": "Lê Văn C (VIP)",
  "phone": "0988111222",
  "email": "new@mail.com",
  "address": "Huế",
  "status": "Inactive",
  "loyaltyPoints": 200
}
```

| Trường | Ghi chú |
| :----- | :------ |
| `customerCode` | Cho phép đổi nếu policy; trùng → **409** |
| `loyaltyPoints` | **403** nếu role không đủ |

---

## 4. Thành công — `200 OK`

Trả object như Task050.

---

## 5. Logic DB

```sql
UPDATE Customers
SET name = COALESCE($2, name),
    customer_code = COALESCE($3, customer_code),
    phone = COALESCE($4, phone),
    email = COALESCE($5, email),
    address = COALESCE($6, address),
    loyalty_points = COALESCE($7, loyalty_points),
    status = COALESCE($8, status),
    updated_at = CURRENT_TIMESTAMP
WHERE id = $1;
```

---

## 6. Lỗi

**400** / **403** (điểm) / **404** / **409** / **401** / **500**.

---

## 7. Zod (body — FE)

```typescript
import { z } from "zod";

export const CustomerPatchBodySchema = z
  .object({
    customerCode: z.string().min(1).max(50).optional(),
    name: z.string().min(1).max(255).optional(),
    phone: z.string().min(1).max(20).optional(),
    email: z.union([z.string().email(), z.literal("")]).nullable().optional(),
    address: z.string().nullable().optional(),
    status: z.enum(["Active", "Inactive"]).optional(),
    loyaltyPoints: z.number().int().min(0).optional(),
  })
  .refine((o) => Object.keys(o).length > 0, { message: "Cần ít nhất một trường" });
```
