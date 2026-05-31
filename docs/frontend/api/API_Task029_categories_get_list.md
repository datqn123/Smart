# 📄 API SPEC: `GET /api/v1/categories` — Danh sách / cây danh mục - Task029

> **Trạng thái**: Draft  
> **Feature**: UC8 — màn **Danh mục sản phẩm** (`CategoriesPage`, `CategoryTable`, `CategoryToolbar`)  
> **Tags**: RESTful, Categories, Tree, Read

---

## 1. Mục tiêu Task

- **Nghiệp vụ**: Cung cấp **toàn bộ danh mục** dạng **cây** (theo `parent_id`) phục vụ bảng phân cấp, ô tìm kiếm, lọc trạng thái, chọn cha trong form, và hiển thị **số sản phẩm** gán trực tiếp vào từng danh mục.
- **Ai được lợi**: Owner / Staff có quyền UC8; thay `mockCategories`.
- **Phạm vi**: **một** endpoint `GET /categories`.
- **Out of scope**: tạo / sửa / xóa → Task030–033; danh sách sản phẩm → Task034.

---

## 2. Mục đích Endpoint

**`GET /api/v1/categories`** trả về danh mục đã **sắp xếp** (theo `sort_order`, `name`) và — mặc định — **lồng `children`** cho đúng UI cây.

**Khi nào gọi**: mở `/products/categories`; refresh sau Task030–033; mở `CategoryForm` (danh sách cha).

**Sau khi thành công**: client nhận `items` (cây gốc) hoặc `items` phẳng nếu chọn `format=flat`.

**Endpoint này KHÔNG**: ghi DB; không thay thế endpoint chi tiết một danh mục (Task031) nếu cần payload đầy đủ hơn cho popup.

---

## 3. Tham chiếu

**Khung thiết kế**: [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.9**.  
**DB**: [`Database_Specification.md`](../UC/Database_Specification.md) **§2** `Categories`; đếm SP: **§7** `Products`.

---

## 4. Thông tin chung (Overview)

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.9** |
| **Endpoint** | `/api/v1/categories` |
| **Method** | `GET` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner, Staff, Admin — đọc UC8 |
| **Use Case Ref** | UC8 |

---

## 5. Đặc tả Request

### 5.1 Headers

```http
Authorization: Bearer <your_access_token>
```

### 5.2 Query parameters

| Tham số | Kiểu | Bắt buộc | Mặc định | Mô tả |
| :------ | :--- | :------- | :------- | :---- |
| `format` | string | Không | `tree` | `tree` \| `flat` — `flat` trả mảng một cấp, mỗi phần tử có `parentId` (nullable). |
| `search` | string | Không | — | Lọc theo `name` hoặc `category_code` (ILIKE). Áp dụng trên **mọi** node; với `tree`, backend **giữ nhánh** nếu khớp node hoặc khớp **bất kỳ con cháu** (policy gợi ý). |
| `status` | string | Không | `all` | `all` \| `Active` \| `Inactive` — lọc theo `Categories.status`. |

### 5.3 Request body

_Không có_

---

## 6. Ánh xạ UI → endpoint

| Khu vực UI | Query / field |
| :----------- | :-------------- |
| Bảng cây danh mục | `format=tree`, `data.items` |
| Ô tìm kiếm | `search` |
| Lọc trạng thái | `status` |
| Cột số SP | `productCount` (đếm `Products` có `category_id =` id **trực tiếp**, không cộng dồn con) |

---

## 7. Thành công — `200 OK`

### 7.1 `format=tree` (mặc định)

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "categoryCode": "CAT001",
        "name": "Thực phẩm",
        "description": null,
        "parentId": null,
        "sortOrder": 1,
        "status": "Active",
        "productCount": 12,
        "createdAt": "2026-01-10T08:00:00Z",
        "updatedAt": "2026-04-20T10:00:00Z",
        "children": [
          {
            "id": 2,
            "categoryCode": "CAT001-01",
            "name": "Đồ khô",
            "parentId": 1,
            "sortOrder": 1,
            "status": "Active",
            "productCount": 5,
            "createdAt": "2026-01-11T09:00:00Z",
            "updatedAt": "2026-04-20T10:00:00Z",
            "children": []
          }
        ]
      }
    ]
  },
  "message": "Thành công"
}
```

### 7.2 `format=flat`

`data.items` là mảng phẳng các node (không có `children`); `parentId` có thể `null`.

---

## 8. Logic nghiệp vụ & Database

### 8.1 Quy trình (Step-by-Step)

1. **JWT** → **401** / **403**.
2. **Validate query** (`format`, `status`) → **400** nếu sai.
3. **`SELECT`** từ `Categories` (tenant nếu có multi-tenant sau này).
4. **LEFT JOIN** subquery đếm SP:

```sql
SELECT c.id, c.category_code, c.name, c.description, c.parent_id,
       c.sort_order, c.status, c.created_at, c.updated_at,
       COALESCE(pc.cnt, 0) AS product_count
FROM Categories c
LEFT JOIN (
  SELECT category_id, COUNT(*)::int AS cnt
  FROM Products
  WHERE category_id IS NOT NULL
  GROUP BY category_id
) pc ON pc.category_id = c.id
WHERE /* status filter, search filter */;
```

5. **Build tree** trong app layer (map `parent_id` → `children`, sort), hoặc dùng **recursive CTE** nếu muốn SQL-only.
6. **Map** sang JSON camelCase.

### 8.2 Ràng buộc

- `category_code` UNIQUE; không leak dữ liệu ngoài UC8.
- **Read-only**; không lock.

---

## 9. Lỗi (Error Responses)

#### 400 Bad Request

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Tham số truy vấn không hợp lệ",
  "details": { "format": "Chỉ chấp nhận tree hoặc flat" }
}
```

#### 401 / 403 / 500

Theo chuẩn dự án (message tiếng Việt).

---

## 10. Zod (query — FE)

```typescript
import { z } from "zod";

export const CategoriesListQuerySchema = z.object({
  format: z.enum(["tree", "flat"]).optional().default("tree"),
  search: z.string().optional(),
  status: z.enum(["all", "Active", "Inactive"]).optional().default("all"),
});
```

---

## 11. Ghi chú FE

Thay `mockCategories` bằng response; lọc `search`/`status` có thể **client-side** tạm thời nhưng nên chuyển dần sang query để đồng bộ dữ liệu lớn.
