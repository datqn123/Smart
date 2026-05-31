# 📄 API SPEC: `DELETE /api/v1/categories/{id}` — Xóa danh mục - Task033

> **Trạng thái**: Draft  
> **Feature**: UC8 — xóa một dòng / xác nhận xóa (`CategoriesPage`, `ConfirmDialog`)  
> **Tags**: RESTful, Categories, Delete

---

## 1. Mục tiêu Task

- Xóa **một** danh mục khi **an toàn nghiệp vụ**: không còn **danh mục con** và không còn **sản phẩm** gán trực tiếp (policy nghiêm hơn so với ON DELETE SET NULL trong DB — tránh “mồ côi” dữ liệu không chủ đích).

---

## 2. Endpoint

**`DELETE /api/v1/categories/{id}`** — không body.

---

## 3. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.9** |
| **Endpoint** | `/api/v1/categories/{id}` |
| **Method** | `DELETE` |
| **Authentication** | `Bearer` |
| **RBAC** | `can_manage_products` trên controller; **xóa mềm:** chỉ **Owner** (`Jwt` claim `role`, `StockReceiptAccessPolicy.assertOwnerOnly`) — khớp [`SRS_Task029-033_categories-management.md`](../../../../backend/docs/srs/SRS_Task029-033_categories-management.md) §6 |
| **Use Case Ref** | UC8 |

---

## 4. Path parameters

| Tham số | Kiểu | Mô tả |
| :------ | :--- | :---- |
| `id` | int > 0 | `Categories.id` |

---

## 5. Thành công — `200 OK`

Chốt **`200 OK`** + envelope [`API_RESPONSE_ENVELOPE.md`](../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md) (không dùng `204 No Content` để tránh lệch `ApiSuccessResponse`).

```json
{
  "success": true,
  "data": { "id": 15, "deleted": true },
  "message": "Đã xóa danh mục"
}
```

---

## 6. Logic server & DB (Step-by-Step) — **soft-delete**

1. **JWT** → **401**; thiếu `can_manage_products` → **403**; không phải Owner khi thực hiện xóa mềm → **403** (message theo SRS §8.7).
2. **`SELECT … FROM categories WHERE id = ? AND deleted_at IS NULL FOR UPDATE`** — không có → **404**.
3. **`SELECT 1 FROM categories WHERE parent_id = ? AND deleted_at IS NULL LIMIT 1`** — có → **409** (còn con đang hiệu lực).
4. **`SELECT 1 FROM products WHERE category_id = ? LIMIT 1`** — có → **409** (còn SP gán trực tiếp).
5. **`UPDATE categories SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND deleted_at IS NULL`** — không xóa vật lý row.

```sql
UPDATE categories
SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
WHERE id = :id AND deleted_at IS NULL;
```

**Schema:** bảng vật lý PostgreSQL **`categories`**; cột **`deleted_at`** + partial unique mã — Flyway **`V14__categories_deleted_at.sql`** (tham chiếu SRS §10).

---

## 7. Lỗi

#### 404 Not Found

```json
{
  "success": false,
  "error": "NOT_FOUND",
  "message": "Không tìm thấy danh mục"
}
```

#### 403 Forbidden (không phải Owner)

```json
{
  "success": false,
  "error": "FORBIDDEN",
  "message": "Chỉ tài khoản Owner mới được xóa mềm danh mục",
  "details": {}
}
```

#### 409 Conflict

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Không thể đánh dấu xóa: còn danh mục con đang hiệu lực hoặc còn sản phẩm gán vào danh mục này",
  "details": {}
}
```

#### 401 / 403 / 500

Theo chuẩn dự án.

---

## 8. Ghi chú FE

Xóa nhiều ID (toolbar): có thể gọi lần lượt **DELETE** hoặc thêm Task sau **`POST /categories/bulk-delete`** nếu cần transaction một lần.
