# 📄 API SPEC: `POST /api/v1/suppliers/bulk-delete` — Xóa nhiều nhà cung cấp - Task047

> **Trạng thái**: Draft  
> **Feature**: UC8 — `SuppliersPage` xóa hàng loạt  
> **Tags**: RESTful, Suppliers, Bulk, Delete

---

## 1. Mục tiêu Task

- Xóa nhiều NCC trong **một request**; áp dụng **cùng ràng buộc** như [`API_Task046_suppliers_delete.md`](API_Task046_suppliers_delete.md) (phiếu nhập + **PartnerDebts**).
- **Policy (đồng bộ SRS Task042-047 — OQ-2):** **all-or-nothing** — một `id` không đủ điều kiện → **409**, **không** xóa bản ghi nào.

---

## 2. Endpoint

**`POST /api/v1/suppliers/bulk-delete`**

**Content-Type**: `application/json`

---

## 3. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) §4.14 |
| **Endpoint** | `/api/v1/suppliers/bulk-delete` |
| **Method** | `POST` |
| **Authentication** | `Bearer` |
| **RBAC** | Khuyến nghị **Owner** cho xóa — đồng bộ [`SRS_Task042-047_suppliers-management.md`](../../../backend/docs/srs/SRS_Task042-047_suppliers-management.md) **OQ-1** (Staff chỉ đọc/ghi NCC nếu PO chọn (a)). |
| **Use Case Ref** | UC8 |

---

## 4. Request body

```json
{
  "ids": [3, 4, 5]
}
```

| Trường | Kiểu | Bắt buộc | Mô tả |
| :----- | :--- | :------- | :---- |
| `ids` | number[] | Có | `Suppliers.id` > 0; tối đa **50**; không rỗng; **không** trùng lặp (trùng → **400** — **OQ-6** trong SRS). |

---

## 5. Thành công — `200 OK` (all-or-nothing)

Khi **tất cả** `id` đều tồn tại và không vi phạm ràng buộc Task046:

```json
{
  "success": true,
  "data": {
    "deletedIds": [3, 4, 5],
    "deletedCount": 3
  },
  "message": "Đã xóa các nhà cung cấp"
}
```

---

## 6. Logic DB

1. Validate `ids` (rỗng, trùng, vượt 50, không phải số nguyên dương) → **400**.
2. Trong **một transaction**: validate **tất cả** `id` trước khi `DELETE`; một lỗi → **ROLLBACK** + **409** kèm `details.failedId` + `details.reason` (SRS §8.7):
   - thiếu bất kỳ `suppliers.id` nào → **409**, `reason`: `NOT_FOUND` hoặc `INVALID_ID`.
   - tồn tại `stockreceipts` / `partnerdebts` cho bất kỳ id nào → **409** (`HAS_RECEIPTS` / `HAS_PARTNER_DEBTS`) giống Task046.
3. Nếu tất cả hợp lệ → **`DELETE FROM suppliers WHERE id = ANY(:ids)`** (một lệnh hoặc từng dòng trong cùng transaction).

---

## 7. Lỗi

**400** — `ids` không hợp lệ (rỗng, trùng, vượt limit).

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Danh sách id không hợp lệ",
  "details": { "ids": "Tối đa 50 id, không được trùng" }
}
```

**409** — (all-or-nothing) ít nhất một id không đủ điều kiện xóa; **không** xóa bản ghi nào.

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Không thể xóa toàn bộ: ít nhất một nhà cung cấp không đủ điều kiện",
  "details": { "failedId": 5, "reason": "HAS_RECEIPTS" }
}
```

**401** / **403** / **500** — envelope chuẩn dự án.

---

## 8. Zod (body)

```typescript
import { z } from "zod";

export const SuppliersBulkDeleteBodySchema = z.object({
  ids: z.array(z.number().int().positive()).min(1).max(50),
});
```

*(Có thể bổ sung `.refine((a) => new Set(a).size === a.length, { message: "Không được trùng id" })` trên FE.)*
