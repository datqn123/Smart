# 📄 API SPEC: `GET /api/v1/suppliers` — Danh sách nhà cung cấp - Task042

> **Trạng thái**: Draft  
> **Feature**: UC7/UC8 — màn **Nhà cung cấp** (`SuppliersPage`, `SupplierTable`, `SupplierToolbar`)  
> **Tags**: RESTful, Suppliers, Pagination, Read

---

## 1. Mục tiêu Task

- Danh sách **phân trang** NCC với `search` (tên, mã, SĐT), `status`; read-model **`receiptCount`** (số phiếu nhập) phục vụ badge/CRM nhẹ (optional trên UI hiện tại).

---

## 2. Endpoint

**`GET /api/v1/suppliers`**

---

## 3. Tham chiếu

[`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.14** — [`Database_Specification.md`](../UC/Database_Specification.md) **§3** `Suppliers`, **§17** `StockReceipts` (đếm).

---

## 4. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Endpoint** | `/api/v1/suppliers` |
| **Method** | `GET` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner, Staff, Admin — đọc đối tác |
| **Use Case Ref** | UC7 (chọn NCC), UC8 (master data) |

---

## 5. Query parameters

| Tham số | Kiểu | Mặc định | Mô tả |
| :------ | :--- | :------- | :---- |
| `search` | string | — | ILIKE `name`, `supplier_code`, `phone` |
| `status` | string | `all` | `all` \| `Active` \| `Inactive` |
| `page` | int ≥ 1 | `1` | |
| `limit` | int 1–100 | `20` | |
| `sort` | string | `updatedAt:desc` | Whitelist — xem §5.1 |

### 5.1 Whitelist `sort` (đồng bộ `SRS_Task042-047_suppliers-management.md` §8.2)

Giá trị hợp lệ (một chuỗi `field:direction`); khác → **400** `BAD_REQUEST`.

| Giá trị |
| :--- |
| `name:asc`, `name:desc` |
| `supplierCode:asc`, `supplierCode:desc` |
| `updatedAt:asc`, `updatedAt:desc` |
| `createdAt:asc`, `createdAt:desc` |

---

## 6. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "items": [
      {
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
        "createdAt": "2026-01-05T08:00:00Z",
        "updatedAt": "2026-04-01T10:00:00Z"
      }
    ],
    "page": 1,
    "limit": 20,
    "total": 42
  },
  "message": "Thành công"
}
```

**`receiptCount`**: `COUNT(*)` từ `StockReceipts WHERE supplier_id = s.id`.

---

## 7. Logic DB

```sql
SELECT s.*, COALESCE(rc.cnt, 0) AS receipt_count
FROM Suppliers s
LEFT JOIN (
  SELECT supplier_id, COUNT(*)::int AS cnt
  FROM StockReceipts
  GROUP BY supplier_id
) rc ON rc.supplier_id = s.id
WHERE /* search, status */
ORDER BY /* whitelist */
LIMIT :limit OFFSET :offset;
```

Đếm `total` riêng cùng `WHERE`.

---

## 8. Lỗi

**400** / **401** / **403** / **500** — message tiếng Việt.

---

## 9. Zod (query — FE)

```typescript
import { z } from "zod";

export const SuppliersListQuerySchema = z.object({
  search: z.string().optional(),
  status: z.enum(["all", "Active", "Inactive"]).optional().default("all"),
  page: z.coerce.number().int().min(1).optional().default(1),
  limit: z.coerce.number().int().min(1).max(100).optional().default(20),
  sort: z.string().optional(),
});
```
