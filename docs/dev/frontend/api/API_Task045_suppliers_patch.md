# 📄 API SPEC: `PATCH /api/v1/suppliers/{id}` — Cập nhật nhà cung cấp - Task045

> **Trạng thái**: Draft  
> **Feature**: UC8 — `SupplierForm` (sửa)  
> **Tags**: RESTful, Suppliers, Update

---

## 1. Mục tiêu Task

- **`PATCH`** một phần hoặc toàn bộ trường hiển thị trên form NCC.

---

## 2. Endpoint

**`PATCH /api/v1/suppliers/{id}`**

---

## 3. Request body (partial)

Ít nhất một trường.

```json
{
  "name": "Công ty ABC (mới)",
  "phone": "0909999888",
  "status": "Inactive"
}
```

Các trường cho phép: `supplierCode`, `name`, `contactPerson`, `phone`, `email`, `address`, `taxCode`, `status` (kiểu giống Task043).

---

## 4. Thành công — `200 OK`

Trả object như Task044.

---

## 5. Logic DB

1. **`SELECT … FOR UPDATE`** — không có → **404**.
2. Đổi `supplier_code` trùng bản ghi khác → **409**.
3. **`UPDATE Suppliers SET …, updated_at = NOW()`**.

---

## 6. Lỗi

**400** / **404** / **409** / **401** / **403** / **500**.

---

## 7. Zod (body — FE)

```typescript
import { z } from "zod";

export const SupplierPatchBodySchema = z
  .object({
    supplierCode: z.string().min(1).max(50).optional(),
    name: z.string().min(1).max(255).optional(),
    contactPerson: z.string().min(1).max(255).optional(),
    phone: z.string().min(1).max(20).optional(),
    email: z.union([z.string().email(), z.literal("")]).nullable().optional(),
    address: z.string().nullable().optional(),
    taxCode: z.string().max(50).nullable().optional(),
    status: z.enum(["Active", "Inactive"]).optional(),
  })
  .refine((o) => Object.keys(o).length > 0, { message: "Cần ít nhất một trường" });
```
