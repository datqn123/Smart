# 📄 API SPEC: `POST /api/v1/products/{id}/images` — Thêm ảnh sản phẩm - Task039

> **Trạng thái**: Draft  
> **Feature**: UC8 — gallery / ảnh đại diện (mở rộng sau `Products.image_url`)  
> **Tags**: RESTful, Products, Media, Multipart

---

## 1. Mục tiêu Task

- Upload hoặc ghi nhận **URL ảnh** cho sản phẩm; hỗ trợ cờ **`isPrimary`** (đồng bộ `Products.image_url` khi primary).

---

## 2. Lưu ý schema

`Database_Specification.md` mục lục nhắc **`ProductImages`** nhưng **chưa** có mục chi tiết cột — backend cần **migration** trước khi triển khai.

### DDL đề xuất (PostgreSQL)

```sql
CREATE TABLE product_images (
  id BIGSERIAL PRIMARY KEY,
  product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  url VARCHAR(500) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX uq_product_images_one_primary
  ON product_images (product_id)
  WHERE is_primary = TRUE;
```

---

## 3. Endpoint

**`POST /api/v1/products/{id}/images`**

**Content-Type**: `multipart/form-data` **hoặc** `application/json` nếu chỉ lưu URL đã upload sẵn (CDN / Cloudinary URL từ nguồn khác).

---

## 3.1 Cấu hình Cloudinary (multipart)

Backend tải file lên Cloudinary khi gọi **multipart** và `app.cloudinary.enabled=true`.

| Biến / property | Ý nghĩa |
| :--- | :--- |
| `app.cloudinary.enabled` | `true` để bật bean Cloudinary (mặc định `false`; có thể set qua `CLOUDINARY_ENABLED`) |
| `CLOUDINARY_CLOUD_NAME` / `app.cloudinary.cloud-name` | Cloud name dashboard |
| `CLOUDINARY_API_KEY` / `app.cloudinary.api-key` | API Key |
| `CLOUDINARY_API_SECRET` / `app.cloudinary.api-secret` | API Secret (không commit) |
| `CLOUDINARY_FOLDER` / `app.cloudinary.folder` | Tiền tố folder trên Cloudinary (mặc định `smart-erp/products`; BE thêm `/{productId}`) |
| `CLOUDINARY_MAX_BYTES` / `app.cloudinary.max-file-size-bytes` | Kích thước tối đa một file (mặc định 5242880) |

Giới hạn Spring multipart: `spring.servlet.multipart.max-file-size` / `max-request-size` = **5MB** mỗi part (root `application.properties`) — phải ≥ giới hạn nghiệp vụ ảnh.

---

## 4. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.9** |
| **Endpoint** | `/api/v1/products/{id}/images` |
| **Method** | `POST` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner, Staff |
| **Use Case Ref** | UC8 |

---

## 5. JSON body (khi không multipart)

```json
{
  "url": "https://cdn.example/p/12/b.jpg",
  "sortOrder": 1,
  "isPrimary": false
}
```

- Nếu `isPrimary: true`: **`UPDATE Products SET image_url = :url`** và **`UPDATE productimages SET is_primary = false`** các ảnh khác của cùng `product_id`, rồi insert row mới `is_primary = true`.

---

## 5.1 Multipart (`multipart/form-data`)

| Part / field | Bắt buộc | Kiểu | Ghi chú |
| :--- | :---: | :--- | :--- |
| `file` | Có | file | Ảnh JPEG, PNG hoặc WebP; kích thước ≤ `app.cloudinary.max-file-size-bytes` khi upload lên Cloudinary |
| `sortOrder` | Không | int | Mặc định `0`; phải ≥ 0 |
| `isPrimary` | Không | boolean | Mặc định `false` |

Luồng: BE nhận `file` → upload Cloudinary → lấy `secure_url` → **cùng transaction** lưu DB như JSON (cột `productimages.image_url`, đồng bộ `products.image_url` nếu primary). Response **201** cùng shape §6 (`data.url` = URL HTTPS Cloudinary).

Nếu Cloudinary **chưa bật** hoặc thiếu credential: **400** với message hướng dẫn cấu hình.

---

## 6. Thành công — `201 Created`

```json
{
  "success": true,
  "data": {
    "id": 9,
    "productId": 12,
    "url": "https://cdn.example/p/12/b.jpg",
    "sortOrder": 1,
    "isPrimary": false
  },
  "message": "Đã thêm ảnh"
}
```

---

## 7. Logic DB (transaction)

1. Xác nhận `products.id` tồn tại → **404**.
2. Nếu `isPrimary`: bỏ primary cũ (`productimages`); cập nhật `products.image_url`.
3. **`INSERT INTO productimages`** (`image_url`, `sort_order`, `is_primary`, tùy chọn `file_size_bytes`, `mime_type`).

Ràng buộc DB: Flyway **`V15__productimages_one_primary_unique.sql`** — unique partial một dòng `is_primary = true` theo `product_id` (bổ sung cho transaction ứng dụng).

---

## 8. Lỗi

- **400**: file quá lớn / MIME không cho phép / URL không hợp lệ / thiếu part `file` (multipart) / Cloudinary chưa cấu hình khi multipart.
- **404**: sản phẩm không tồn tại.
- **401** / **403** / **500** (lỗi tải lên Cloudinary hoặc hệ thống).

---

## 9. Zod (JSON body)

```typescript
import { z } from "zod";

export const ProductImageCreateBodySchema = z.object({
  url: z.string().url().max(500),
  sortOrder: z.number().int().min(0).optional().default(0),
  isPrimary: z.boolean().optional().default(false),
});
```
