# 📄 API SPEC: `GET /api/v1/categories/{id}` — Chi tiết danh mục - Task031

> **Trạng thái**: Draft  
> **Feature**: UC8 — `CategoryDetailDialog`, điều hướng sâu (nếu có)  
> **Tags**: RESTful, Categories, Read

---

## 1. Mục tiêu Task

- Trả về **một** danh mục theo `id`, kèm **đường dẫn cha** (breadcrumb) và **`productCount`** — **đồng bộ Task029**: đếm sản phẩm gán **trực tiếp** `category_id = id` (không cộng dồn theo cây con).

---

## 2. Endpoint

**`GET /api/v1/categories/{id}`**

---

## 3. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Endpoint** | `/api/v1/categories/{id}` |
| **Method** | `GET` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner, Staff, Admin — đọc UC8 |
| **Use Case Ref** | UC8 |

---

## 4. Path parameters

| Tham số | Kiểu | Mô tả |
| :------ | :--- | :---- |
| `id` | int > 0 | `Categories.id` |

---

## 5. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "id": 2,
    "categoryCode": "CAT001-01",
    "name": "Đồ khô",
    "description": null,
    "parentId": 1,
    "parentName": "Thực phẩm",
    "sortOrder": 1,
    "status": "Active",
    "productCount": 5,
    "createdAt": "2026-01-11T09:00:00Z",
    "updatedAt": "2026-04-20T10:00:00Z",
    "breadcrumb": [
      { "id": 1, "name": "Thực phẩm", "categoryCode": "CAT001" },
      { "id": 2, "name": "Đồ khô", "categoryCode": "CAT001-01" }
    ]
  },
  "message": "Thành công"
}
```

`breadcrumb` có thể tính bằng recursive CTE từ node lên gốc rồi đảo mảng.

---

## 6. Logic DB

1. **JWT** → **401** / **403**.
2. **`SELECT * FROM Categories WHERE id = ?`** — không có → **404**.
3. **LEFT JOIN** parent để lấy `parent_name`.
4. **COUNT** `Products WHERE category_id = ?`.
5. **Breadcrumb**: lặp `parent_id` hoặc CTE.

```sql
WITH RECURSIVE anc AS (
  SELECT id, parent_id, name, category_code, 1 AS lvl FROM Categories WHERE id = $1
  UNION ALL
  SELECT c.id, c.parent_id, c.name, c.category_code, anc.lvl + 1
  FROM Categories c
  JOIN anc ON c.id = anc.parent_id
)
SELECT * FROM anc ORDER BY lvl DESC;
```

---

## 7. Lỗi

- **404**: không tìm thấy.
- **401** / **403** / **500**.

---

## 8. Zod (params — FE)

```typescript
import { z } from "zod";

export const CategoryIdParamsSchema = z.object({
  id: z.coerce.number().int().positive(),
});
```
