# 📄 API SPEC: `GET /api/v1/products` — Danh sách sản phẩm - Task034

> **Trạng thái**: Draft  
> **Feature**: UC8 — màn **Quản lý sản phẩm** (`ProductsPage`, `ProductTable`, `ProductToolbar`)  
> **Tags**: RESTful, Products, Pagination, Read

---

## 1. Mục tiêu Task

- **Nghiệp vụ**: Danh sách **phân trang** sản phẩm với lọc `search`, `categoryId`, `status`, đọc **tên danh mục**, **tồn tổng** (đơn vị cơ sở), **giá bán hiện hành** (đơn vị cơ sở) từ read-model.
- **Out of scope**: chi tiết đầy đủ + đơn vị + ảnh gallery → Task036; CRUD khác → Task035–038.

---

## 2. Mục đích Endpoint

**`GET /api/v1/products`** phục vụ bảng danh sách và bộ lọc; thống nhất với [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.9**.

---

## 3. Tham chiếu

**DB**: [`Database_Specification.md`](../UC/Database_Specification.md) **§7** `Products`, **§2** `Categories`, **§8** `ProductUnits`, **§9** `ProductPriceHistory`, **§16** `Inventory` (tổng tồn).

---

## 4. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Endpoint** | `/api/v1/products` |
| **Method** | `GET` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner, Staff, Admin — đọc UC8 |
| **Use Case Ref** | UC8 |

---

## 5. Query parameters

| Tham số | Kiểu | Mặc định | Mô tả |
| :------ | :--- | :------- | :---- |
| `search` | string | — | `ILIKE` trên `Products.name`, `sku_code`, `barcode` |
| `categoryId` | int > 0 | — | Lọc `Products.category_id` |
| `status` | string | `all` | `all` \| `Active` \| `Inactive` |
| `page` | int ≥ 1 | `1` | |
| `limit` | int 1–100 | `20` | |
| `sort` | string | `updatedAt:desc` | Whitelist backend |

---

## 6. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 12,
        "skuCode": "SP0001",
        "barcode": "8934563123456",
        "name": "Nước suối 500ml",
        "categoryId": 2,
        "categoryName": "Đồ khô",
        "imageUrl": "https://cdn.example/p/12.jpg",
        "status": "Active",
        "currentStock": 240,
        "currentPrice": 6000,
        "createdAt": "2026-02-01T08:00:00Z",
        "updatedAt": "2026-04-22T09:00:00Z"
      }
    ],
    "page": 1,
    "limit": 20,
    "total": 156
  },
  "message": "Thành công"
}
```

- **`currentStock`**: `SUM(Inventory.quantity)` theo `product_id` (đơn vị cơ sở — khớp quy tắc tồn).
- **`currentPrice`**: `sale_price` mới nhất của **đơn vị cơ sở** (`ProductUnits.is_base_unit = TRUE`) từ `ProductPriceHistory` (`effective_date` ≤ `CURRENT_DATE`, order `effective_date DESC, id DESC`).

---

## 7. Logic DB

### 7.1 Đếm `total` + trang `items`

```sql
SELECT
  p.id,
  p.sku_code,
  p.barcode,
  p.name,
  p.category_id,
  c.name AS category_name,
  p.image_url,
  p.status,
  COALESCE(inv.qty, 0) AS current_stock,
  latest_pph.sale_price AS current_price,
  p.created_at,
  p.updated_at
FROM Products p
LEFT JOIN Categories c ON c.id = p.category_id
JOIN ProductUnits pu ON pu.product_id = p.id AND pu.is_base_unit = TRUE
LEFT JOIN (
  SELECT product_id, SUM(quantity) AS qty
  FROM Inventory
  GROUP BY product_id
) inv ON inv.product_id = p.id
LEFT JOIN LATERAL (
  SELECT pph.sale_price
  FROM ProductPriceHistory pph
  WHERE pph.product_id = p.id AND pph.unit_id = pu.id
    AND pph.effective_date <= CURRENT_DATE
  ORDER BY pph.effective_date DESC, pph.id DESC
  LIMIT 1
) latest_pph ON true
WHERE /* search, categoryId, status */
ORDER BY /* whitelist */
LIMIT :limit OFFSET :offset;
```

Nếu chưa có dòng `ProductPriceHistory`, `currentPrice` có thể `null` hoặc `0` — thống nhất một policy.

### 7.2 Ràng buộc

- Chỉ đọc; RBAC tenant nếu có.

---

## 8. Lỗi

- **400**: query không hợp lệ.
- **401** / **403** / **500**.

---

## 9. Zod (query — FE)

```typescript
import { z } from "zod";

export const ProductsListQuerySchema = z.object({
  search: z.string().optional(),
  categoryId: z.coerce.number().int().positive().optional(),
  status: z.enum(["all", "Active", "Inactive"]).optional().default("all"),
  page: z.coerce.number().int().min(1).optional().default(1),
  limit: z.coerce.number().int().min(1).max(100).optional().default(20),
  sort: z.string().optional(),
});
```

---

## 10. Ghi chú FE

Bộ lọc theo tên danh mục hiện dựng từ `products`: nên chuyển sang **`categoryId`** từ `GET /categories?format=flat` (Task029) + `categoryId` query.
