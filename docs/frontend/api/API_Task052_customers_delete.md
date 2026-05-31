# 📄 API SPEC: `DELETE /api/v1/customers/{id}` — Xóa mềm khách hàng (Admin) — Task052

> **Trạng thái**: Đồng bộ SRS [`SRS_PRD_customers-admin-soft-delete-single.md`](../../../backend/docs/srs/SRS_PRD_customers-admin-soft-delete-single.md) — **Approved** 02/05/2026; amendment [`SRS_Task048-053_customers-management.md`](../../../backend/docs/srs/SRS_Task048-053_customers-management.md) §0.2  
> **Feature**: UC9 — `CustomersPage` / `ConfirmDialog`  
> **Tags**: RESTful, Customers, Delete, Soft delete

---

## 1. Mục tiêu Task

- **Xóa mềm** khách hàng: set `deleted_at` trên bản ghi `customers` (**không** `DELETE` cứng).
- Chỉ user có JWT **`role` = `Admin`** được gọi thành công.
- Chặn khi còn **đơn bán chưa hoàn tất** (trạng thái **không** thuộc `Delivered`, `Cancelled`) hoặc còn **công nợ đối tác** (`partnerdebts`).
- Bản ghi đã xóa mềm **không** xuất hiện trong `GET` list / `GET` by id (404 khi tra cứu theo id).

---

## 2. Endpoint

**`DELETE /api/v1/customers/{id}`**

---

## 3. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Endpoint** | `/api/v1/customers/{id}` |
| **Method** | `DELETE` |
| **Authentication** | `Bearer` |
| **RBAC** | **Chỉ Admin** (`role` = `Admin`) |
| **Use Case Ref** | UC9 |

---

## 4. Thành công — `200 OK`

```json
{
  "success": true,
  "data": { "id": 10, "deleted": true },
  "message": "Đã xóa khách hàng"
}
```

---

## 5. Logic (tóm tắt)

1. Nếu JWT không phải **Admin** → **403**.
2. `SELECT id FROM customers WHERE id = ? AND deleted_at IS NULL FOR UPDATE` — không có → **404**.
3. EXISTS `salesorders` với `customer_id` = id và `status` **không** (không phân biệt hoa thường) thuộc `delivered`, `cancelled` → **409**, `details.reason` = **`HAS_OPEN_SALES_ORDERS`**.
4. EXISTS `partnerdebts` với `customer_id` = id → **409**, `details.reason` = **`HAS_PARTNER_DEBTS`**.
5. `UPDATE customers SET deleted_at = CURRENT_TIMESTAMP WHERE id = ? AND deleted_at IS NULL`.

---

## 6. Lỗi — ví dụ envelope

### 403 — không phải Admin

```json
{
  "success": false,
  "error": "FORBIDDEN",
  "message": "Bạn không có quyền thực hiện thao tác này.",
  "details": {}
}
```

### 404 — không có khách đang hoạt động

```json
{
  "success": false,
  "error": "NOT_FOUND",
  "message": "Không tìm thấy khách hàng",
  "details": {}
}
```

### 409 — còn đơn chưa hoàn tất

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Không thể xóa khách hàng vì còn đơn hàng chưa hoàn tất.",
  "details": { "reason": "HAS_OPEN_SALES_ORDERS" }
}
```

### 409 — còn công nợ

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Không thể xóa khách hàng đang có công nợ.",
  "details": { "reason": "HAS_PARTNER_DEBTS" }
}
```

**401** / **500** — theo [`API_RESPONSE_ENVELOPE.md`](API_RESPONSE_ENVELOPE.md).

---

## 7. Zod (params)

```typescript
import { z } from "zod";
export const CustomerIdParamsSchema = z.object({
  id: z.coerce.number().int().positive(),
});
```
