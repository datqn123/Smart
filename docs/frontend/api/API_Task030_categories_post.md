# 📄 API SPEC: `POST /api/v1/categories` — Tạo danh mục - Task030

> **Trạng thái**: Draft  
> **Feature**: UC8 — `CategoryForm` (thêm mới / thêm con)  
> **Tags**: RESTful, Categories, Create

---

## 1. Mục tiêu Task

- **Nghiệp vụ**: Tạo **một** bản ghi `Categories` với mã duy nhất, tên, mô tả, cha, thứ tự, trạng thái — khớp form Zod trong `CategoryForm`.
- **Out of scope**: cập nhật → Task032; đọc cây → Task029.

---

## 2. Mục đích Endpoint

**`POST /api/v1/categories`** tạo danh mục mới; chặn **vòng tham chiếu** và `parent_id` không tồn tại.

---

## 3. Tham chiếu

[`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.9** — [`Database_Specification.md`](../UC/Database_Specification.md) **§2** `Categories`.

---

## 4. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Endpoint** | `/api/v1/categories` |
| **Method** | `POST` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner, Staff (UC8 ghi) |
| **Use Case Ref** | UC8 |

---

## 5. Request body (JSON, camelCase)

```json
{
  "categoryCode": "CAT010",
  "name": "Đồ uống",
  "description": "Các loại nước giải khát",
  "parentId": null,
  "sortOrder": 10,
  "status": "Active"
}
```

| Trường | Kiểu | Bắt buộc | Mô tả |
| :----- | :--- | :------- | :---- |
| `categoryCode` | string | Có | Trim; UNIQUE; max 50 |
| `name` | string | Có | Max 255 |
| `description` | string \| null | Không | |
| `parentId` | number \| null | Không | FK `Categories.id`; `null` = gốc |
| `sortOrder` | number | Không | Mặc định `0` |
| `status` | string | Không | `Active` \| `Inactive`, mặc định `Active` |

---

## 6. Thành công — `201 Created`

```json
{
  "success": true,
  "data": {
    "id": 15,
    "categoryCode": "CAT010",
    "name": "Đồ uống",
    "description": "Các loại nước giải khát",
    "parentId": null,
    "sortOrder": 10,
    "status": "Active",
    "createdAt": "2026-04-23T12:00:00Z",
    "updatedAt": "2026-04-23T12:00:00Z",
    "productCount": 0,
    "children": []
  },
  "message": "Đã tạo danh mục"
}
```

---

## 7. Logic DB (Step-by-Step)

1. **JWT** → **401** / **403**.
2. **Validate body** → **400** + `details`.
3. Nếu `parentId` có giá trị: **`SELECT id FROM categories WHERE id = ?`** → không có → **400** + `details.parentId` (cha không phải resource có URI riêng; đồng bộ Task032).
4. **`INSERT INTO Categories`** (`category_code`, `name`, `description`, `parent_id`, `sort_order`, `status`, `created_at`, `updated_at`).
5. (Tuỳ chọn) **`INSERT SystemLogs`**.
6. Trả bản ghi mới (có thể `JOIN` `product_count = 0`).

```sql
INSERT INTO categories (category_code, name, description, parent_id, sort_order, status)
VALUES ($1, $2, $3, $4, $5, $6)
RETURNING id, category_code, name, description, parent_id, sort_order, status, created_at, updated_at;
```

### Ràng buộc

- UNIQUE `category_code` trùng → **409** với message "Mã danh mục đã tồn tại".
- Không cho `parent_id` trỏ chính `id` sau insert (chỉ áp dụng PATCH); POST không gửi `id`.

---

## 8. Lỗi

- **400**: validation; `parentId` không tồn tại.
- **409**: trùng `category_code`.
- **401** / **403** / **500**.

---

## 9. Zod (body — FE)

```typescript
import { z } from "zod";

export const CategoryCreateBodySchema = z.object({
  categoryCode: z.string().min(1).max(50),
  name: z.string().min(1).max(255),
  description: z.string().nullable().optional(),
  parentId: z.union([z.number().int().positive(), z.null()]).optional(),
  sortOrder: z.number().int().optional().default(0),
  status: z.enum(["Active", "Inactive"]).optional().default("Active"),
});
```
