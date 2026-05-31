# 📄 API SPEC: `POST /api/v1/customers` — Tạo khách hàng - Task049

> **Trạng thái**: Draft  
> **Feature**: UC9 — `CustomerForm` (thêm mới)  
> **Tags**: RESTful, Customers, Create

---

## 1. Mục tiêu Task

- Tạo **`Customers`**: `customerCode`, `name`, `phone` (NOT NULL trong DB), `email`, `address`, `status`; **`loyalty_points`** mặc định **0** (không cho FE tự set điểm khi tạo trừ policy đặc biệt).

---

## 2. Endpoint

**`POST /api/v1/customers`**

---

## 3. Request body

```json
{
  "customerCode": "KH00100",
  "name": "Phạm D",
  "phone": "0977888999",
  "email": "d@mail.com",
  "address": "Cần Thơ",
  "status": "Active"
}
```

| Trường | Bắt buộc |
| :----- | :------- |
| `customerCode` | Có — UNIQUE |
| `name` | Có |
| `phone` | Có |
| `email` | Không |
| `address` | Không |
| `status` | Không — mặc định `Active` |

---

## 4. Thành công — `201 Created`

Trả object khách hàng (có `loyaltyPoints: 0`, `totalSpent`/`orderCount` có thể 0 hoặc bỏ qua trong response tạo).

---

## 5. Logic DB

```sql
INSERT INTO Customers (customer_code, name, phone, email, address, loyalty_points, status)
VALUES ($1, $2, $3, NULLIF(TRIM($4),''), $5, 0, $6)
RETURNING id, customer_code, name, phone, email, address, loyalty_points, status, created_at, updated_at;
```

Trùng `customer_code` hoặc `phone` nếu sau này có UNIQUE → **409** (hiện DB: UNIQUE `customer_code`; `phone` có index nhưng không UNIQUE — chỉ **409** trùng mã).

---

## 6. Lỗi

**400** / **409** / **401** / **403** / **500**.

---

## 7. Zod (body — FE)

```typescript
import { z } from "zod";

export const CustomerCreateBodySchema = z.object({
  customerCode: z.string().min(1).max(50),
  name: z.string().min(1).max(255),
  phone: z.string().min(1).max(20),
  email: z.union([z.string().email(), z.literal("")]).optional(),
  address: z.string().optional(),
  status: z.enum(["Active", "Inactive"]).optional().default("Active"),
});
```
