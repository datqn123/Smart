# 📄 API SPEC: `DELETE /api/v1/products/{id}/images/{imageId}` — Xóa ảnh sản phẩm - Task040

> **Trạng thái**: Draft  
> **Feature**: UC8 — xóa một ảnh trong gallery  
> **Tags**: RESTful, Products, Media, Delete

---

## 1. Mục tiêu Task

- Xóa một bản ghi **`product_images`**; nếu xóa ảnh **primary**, cập nhật `Products.image_url` sang ảnh còn lại (ưu tiên `sort_order` nhỏ nhất) hoặc `NULL`.

---

## 2. Endpoint

**`DELETE /api/v1/products/{id}/images/{imageId}`**

---

## 3. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.9** |
| **Endpoint** | `/api/v1/products/{id}/images/{imageId}` |
| **Method** | `DELETE` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner, Staff |
| **Use Case Ref** | UC8 |

**Phụ thuộc**: bảng `product_images` — xem **Task039** (DDL đề xuất).

---

## 4. Path parameters

| Tham số | Mô tả |
| :------ | :---- |
| `id` | `Products.id` |
| `imageId` | `product_images.id` |

---

## 5. Thành công — `200 OK`

```json
{
  "success": true,
  "data": { "imageId": 9, "deleted": true },
  "message": "Đã xóa ảnh"
}
```

---

## 6. Logic DB (transaction)

1. **`SELECT * FROM product_images WHERE id = ? AND product_id = ?`** — không có → **404**.
2. Ghi nhận `was_primary`.
3. **`DELETE FROM product_images WHERE id = ?`**.
4. Nếu `was_primary`: chọn ảnh mới primary hoặc set `Products.image_url = NULL`.

---

## 7. Lỗi

- **404**: ảnh không thuộc sản phẩm hoặc không tồn tại.
- **401** / **403** / **500**.

---

## 8. Zod (params)

```typescript
import { z } from "zod";

export const ProductImageDeleteParamsSchema = z.object({
  id: z.coerce.number().int().positive(),
  imageId: z.coerce.number().int().positive(),
});
```
