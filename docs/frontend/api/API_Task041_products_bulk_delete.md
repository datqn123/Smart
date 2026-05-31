# 📄 API SPEC: `POST /api/v1/products/bulk-delete` — Xóa nhiều sản phẩm - Task041

> **Trạng thái**: Draft  
> **Feature**: UC8 — `ProductsPage` (toolbar xóa hàng loạt, `ConfirmDialog`)  
> **Tags**: RESTful, Products, Bulk, Delete

---

## 1. Mục tiêu Task

- Cho phép xóa **nhiều** sản phẩm trong **một request** (transaction tùy policy), thay vì gọi lặp [`API_Task038_products_delete.md`](API_Task038_products_delete.md).

---

## 2. Endpoint

**`POST /api/v1/products/bulk-delete`**

**Content-Type**: `application/json`

---

## 3. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | Bổ sung cho [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.9** (UC8) |
| **Endpoint** | `/api/v1/products/bulk-delete` |
| **Method** | `POST` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner (khuyến nghị); Staff nếu policy cho phép |
| **Use Case Ref** | UC8 |

---

## 4. Request body

```json
{
  "ids": [12, 15, 18]
}
```

| Trường | Kiểu | Bắt buộc | Mô tả |
| :----- | :--- | :------- | :---- |
| `ids` | number[] | Có | Mỗi phần tử là `Products.id` > 0; tối đa **100** (cấu hình backend). |

---

## 5. Thành công — `200 OK` (all-or-nothing hoặc partial)

### 5.1 All-or-nothing (khuyến nghị khi đơn giản)

Nếu **bất kỳ** `id` nào vi phạm ràng buộc như Task038 → **409** toàn bộ, không xóa bản ghi nào.

### 5.2 Partial success (tùy chọn)

```json
{
  "success": true,
  "data": {
    "deletedIds": [12, 15],
    "failed": [{ "id": 18, "error": "CONFLICT", "message": "Còn tồn kho hoặc đã có trên đơn hàng" }]
  },
  "message": "Đã xóa 2 sản phẩm, 1 không thể xóa"
}
```

Ghi rõ policy dự án: **chỉ chọn một** trong hai (all-or-nothing **hoặc** partial).

---

## 6. Logic DB

1. Validate `ids` → **400** (rỗng, trùng, vượt limit).
2. Với từng `id` (hoặc batch `WHERE id = ANY`): áp dụng **cùng kiểm tra** như Task038 (phiếu nhập, đơn hàng, tồn > 0 nếu policy).
3. **`DELETE FROM Products WHERE id = ANY(:ids)`** trong transaction nếu all-or-nothing.

---

## 7. Lỗi

- **400**: `ids` không hợp lệ.
- **409**: (all-or-nothing) ít nhất một id không đủ điều kiện xóa.
- **401** / **403** / **500**.

---

## 8. Zod (body — FE)

```typescript
import { z } from "zod";

export const ProductsBulkDeleteBodySchema = z.object({
  ids: z.array(z.number().int().positive()).min(1).max(100),
});
```
