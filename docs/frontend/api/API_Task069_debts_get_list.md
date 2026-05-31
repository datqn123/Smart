# 📄 API SPEC: `GET /api/v1/debts` — Danh sách sổ nợ — Task069

> **Trạng thái**: Approved  
> **Feature**: Cashflow — màn **Sổ nợ** (`DebtPage`, `/cashflow/debt`)  
> **Tags**: RESTful, Finance, Pagination

---

## 1. Mục tiêu Task

- **Nghiệp vụ**: Liệt kê bảng **`partnerdebts`** (Flyway `PartnerDebts`) kèm **tên đối tác** (join `customers` / `suppliers`), trả `remainingAmount` tính từ `totalAmount - paidAmount` — thay mock `Debt[]`.
- **Phạm vi**: **Chỉ** `GET /debts`.
- **Out of scope**: Tạo/sửa chi tiết → Task070–072.

---

## 2. Mục đích Endpoint

Hỗ trợ bảng sổ nợ: lọc theo loại đối tác, trạng thái, tìm theo tên/mã.

---

## 3. Tham chiếu

[`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) §4.14.  
[`Database_Specification.md`](../UC/Database_Specification.md) §12.2 `PartnerDebts`.  
**SRS (BE):** [`../../../backend/docs/srs/SRS_Task069-072_debts-api.md`](../../../backend/docs/srs/SRS_Task069-072_debts-api.md) — **Approved** 30/04/2026; RBAC **`mp.can_view_finance === true`**.

---

## 4. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Endpoint** | `/api/v1/debts` |
| **Method** | `GET` |
| **Authentication** | `Bearer` |
| **RBAC** | JWT **`mp.can_view_finance === true`** (Owner / Admin / Staff sau Flyway V25). Thiếu → **403**. |

---

## 5. Query parameters

| Tham số | Kiểu | Mô tả |
| :------ | :--- | :---- |
| `partnerType` | `Customer` \| `Supplier` | Map `partner_type` |
| `status` | `InDebt` \| `Cleared` | |
| `search` | string | `ILIKE` trên `debt_code`, tên KH/NCC |
| `dueDateFrom` | date | Lọc `due_date >=` |
| `dueDateTo` | date | Lọc `due_date <=` |
| `page` | int | Mặc định `1` |
| `limit` | int 1–100 | Mặc định `20` |

---

## 6. Ánh xạ UI

| FE `Debt` | API |
| :---------- | :-- |
| `partnerName` | `partnerName` (read-model join) |
| `remainingAmount` | `remainingAmount` (server tính) |
| `lastUpdate` | `updatedAt` |

---

## 7. `200 OK` — ví dụ

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 5,
        "debtCode": "NO-2026-0001",
        "partnerType": "Customer",
        "customerId": 12,
        "supplierId": null,
        "partnerName": "CT TNHH ABC",
        "totalAmount": 10000000,
        "paidAmount": 2000000,
        "remainingAmount": 8000000,
        "dueDate": "2026-05-01",
        "status": "InDebt",
        "notes": "Công nợ bán sỉ T4",
        "updatedAt": "2026-04-20T15:30:00Z"
      }
    ],
    "page": 1,
    "limit": 20,
    "total": 8
  },
  "message": "Thành công"
}
```

---

## 8. Database

```sql
SELECT d.*,
  COALESCE(c.name, s.name) AS partner_name
FROM partnerdebts d
LEFT JOIN customers c ON d.customer_id = c.id
LEFT JOIN suppliers s ON d.supplier_id = s.id
WHERE /* filters — xem SRS §10 */
ORDER BY d.updated_at DESC, d.id DESC;
```

`partnerName` = `COALESCE(c.name, s.name)` (cột `name` trên `customers` / `suppliers` — Flyway V1).

---

## 9. Lỗi

**400**, **401**, **403**, **500**.

---

## 10. Zod

```typescript
import { z } from "zod";

export const DebtsListQuerySchema = z.object({
  partnerType: z.enum(["Customer", "Supplier"]).optional(),
  status: z.enum(["InDebt", "Cleared"]).optional(),
  search: z.string().optional(),
  dueDateFrom: z.string().date().optional(),
  dueDateTo: z.string().date().optional(),
  page: z.coerce.number().int().min(1).optional().default(1),
  limit: z.coerce.number().int().min(1).max(100).optional().default(20),
});
```

---

## 11. Ghi chú FE

Đồng bộ filter `dueDate` trên UI với `dueDateFrom`/`dueDateTo` (một ngày = from=to).
