# 📄 API SPEC: `POST /api/v1/suppliers` — Tạo nhà cung cấp - Task043

> **Trạng thái**: Draft  
> **Feature**: UC8 — `SupplierForm` (thêm mới)  
> **Tags**: RESTful, Suppliers, Create

---

## 1. Mục tiêu Task

- Tạo bản ghi **`Suppliers`** khớp form: `supplierCode`, `name`, `contactPerson`, `phone`, `email`, `address`, `taxCode`, `status`.

---

## 2. Endpoint

**`POST /api/v1/suppliers`**

---

## 3. Tham chiếu

[`Database_Specification.md`](../UC/Database_Specification.md) **§3** `Suppliers`.

---

## 4. Request body

```json
{
  "supplierCode": "NCC0002",
  "name": "Công ty XYZ",
  "contactPerson": "Trần B",
  "phone": "0911222333",
  "email": "b@xyz.com",
  "address": "TP.HCM",
  "taxCode": null,
  "status": "Active"
}
```

| Trường | Bắt buộc | Ghi chú |
| :----- | :------- | :------ |
| `supplierCode` | Có | UNIQUE; format gợi ý NCC + digits |
| `name` | Có | |
| `contactPerson` | Có | (UI bắt buộc; DB cho phép NULL — có thể nới backend) |
| `phone` | Có | |
| `email` | Không | Chuẩn hoá chuỗi rỗng → `NULL` |
| `address` | Không | |
| `taxCode` | Không | |
| `status` | Không | Mặc định `Active` |

---

## 5. Thành công — `201 Created`

Trả object đầy đủ (giống một phần tử `items` Task042, `receiptCount: 0`).

---

## 6. Logic DB

```sql
INSERT INTO Suppliers (supplier_code, name, contact_person, phone, email, address, tax_code, status)
VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
RETURNING id, supplier_code, name, contact_person, phone, email, address, tax_code, status, created_at, updated_at;
```

Trùng `supplier_code` → **409**.

---

## 7. Lỗi

**400** / **409** / **401** / **403** / **500**.

---

## 8. Zod (body — FE)

```typescript
import { z } from "zod";

export const SupplierCreateBodySchema = z.object({
  supplierCode: z.string().min(1).max(50),
  name: z.string().min(1).max(255),
  contactPerson: z.string().min(1).max(255),
  phone: z.string().min(1).max(20),
  email: z.union([z.string().email(), z.literal("")]).optional(),
  address: z.string().optional(),
  taxCode: z.string().max(50).nullable().optional(),
  status: z.enum(["Active", "Inactive"]).optional().default("Active"),
});
```
