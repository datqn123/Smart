# 📄 API SPEC: `GET /api/v1/suppliers/{id}` — Chi tiết nhà cung cấp - Task044

> **Trạng thái**: Draft  
> **Feature**: UC8 — `SupplierDetailDialog`  
> **Tags**: RESTful, Suppliers, Read

---

## 1. Mục tiêu Task

- Trả **một** NCC đầy đủ cột + **`receiptCount`** + **`lastReceiptAt`** (đã chốt PO — [`SRS_Task042-047_suppliers-management.md`](../../../backend/docs/srs/SRS_Task042-047_suppliers-management.md) **OQ-4(b)**).

---

## 2. Endpoint

**`GET /api/v1/suppliers/{id}`**

---

## 3. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Endpoint** | `/api/v1/suppliers/{id}` |
| **Method** | `GET` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner, Staff, Admin |
| **Use Case Ref** | UC7, UC8 |

---

## 4. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "id": 3,
    "supplierCode": "NCC0001",
    "name": "Công ty ABC",
    "contactPerson": "Nguyễn A",
    "phone": "0909123456",
    "email": "a@abc.com",
    "address": "Hà Nội",
    "taxCode": "0101234567",
    "status": "Active",
    "receiptCount": 8,
    "lastReceiptAt": "2026-03-15T14:30:00Z",
    "createdAt": "2026-01-05T08:00:00Z",
    "updatedAt": "2026-04-01T10:00:00Z"
  },
  "message": "Thành công"
}
```

**`lastReceiptAt`:** `MAX(stockreceipts.created_at)` theo `supplier_id`; không có phiếu → **`null`** (ISO-8601 trong JSON).

---

## 5. Logic DB

```sql
SELECT
  s.id,
  s.supplier_code,
  s.name,
  s.contact_person,
  s.phone,
  s.email,
  s.address,
  s.tax_code,
  s.status,
  s.created_at,
  s.updated_at,
  (SELECT COUNT(*)::int FROM stockreceipts sr WHERE sr.supplier_id = s.id) AS receipt_count,
  (SELECT MAX(sr2.created_at) FROM stockreceipts sr2 WHERE sr2.supplier_id = s.id) AS last_receipt_at
FROM suppliers s
WHERE s.id = $1;
```

---

## 6. Lỗi

**404** / **401** / **403** / **500**.

---

## 7. Zod (params)

```typescript
import { z } from "zod";
export const SupplierIdParamsSchema = z.object({
  id: z.coerce.number().int().positive(),
});
```
