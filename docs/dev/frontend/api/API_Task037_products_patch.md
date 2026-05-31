# 📄 API SPEC: `PATCH /api/v1/products/{id}` — Cập nhật sản phẩm - Task037

> **Trạng thái**: Draft  
> **Feature**: UC8 — `ProductForm` (cập nhật)  
> **Tags**: RESTful, Products, ProductPriceHistory, Update

---

## 1. Mục tiêu Task

- **`PATCH`** meta `Products` (tên, SKU nếu policy cho phép, barcode, category, weight, status, `imageUrl`).
- Khi đổi **`salePrice`** (và/hoặc `costPrice`) cho **đơn vị cơ sở**: ghi **thêm** một dòng **`ProductPriceHistory`** mới (`effective_date` = ngày áp dụng trong body hoặc hôm nay) — không sửa dòng lịch sử cũ.

---

## 2. Endpoint

**`PATCH /api/v1/products/{id}`**

---

## 3. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.9** |
| **Endpoint** | `/api/v1/products/{id}` |
| **Method** | `PATCH` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner, Staff |
| **Use Case Ref** | UC8 |

---

## 4. Request body (partial)

```json
{
  "name": "Nước suối 500ml (new)",
  "skuCode": "SP0001",
  "barcode": "8934563123456",
  "categoryId": 3,
  "description": "Mô tả",
  "weight": 520,
  "status": "Active",
  "imageUrl": "https://cdn.example/p/12.jpg",
  "salePrice": 6500,
  "costPrice": 4200,
  "priceEffectiveDate": "2026-05-01"
}
```

- Ít nhất một trường.
- Nếu có **`salePrice`** hoặc **`costPrice`**: backend **bắt buộc** có cả hai giá trị mới cho snapshot lịch sử **hoặc** lấy giá còn lại từ dòng hiện hành — policy: **gửi đủ cặp** khi đổi giá để đơn giản validation.

---

## 5. Thành công — `200 OK`

Trả object như Task036 (gọn) hoặc như Task034 item.

---

## 6. Logic DB (transaction)

1. **`SELECT … FROM Products WHERE id = ? FOR UPDATE`** → **404**.
2. Validate; `sku_code` trùng bản ghi khác → **409**.
3. **`UPDATE Products SET`** các cột nullable / COALESCE patch.
4. Nếu có thay đổi giá: resolve `unit_id` của `ProductUnits` với `is_base_unit = TRUE` cho `product_id`.
5. **`INSERT INTO ProductPriceHistory`** (`product_id`, `unit_id`, `cost_price`, `sale_price`, `effective_date`).
6. Commit; SystemLogs tuỳ chọn.

```sql
UPDATE Products SET name = COALESCE($2, name), /* ... */ updated_at = CURRENT_TIMESTAMP
WHERE id = $1;

INSERT INTO ProductPriceHistory (product_id, unit_id, cost_price, sale_price, effective_date)
SELECT $1, pu.id, $cost, $sale, $eff::date
FROM ProductUnits pu
WHERE pu.product_id = $1 AND pu.is_base_unit = TRUE;
```

_Chỉ `INSERT` khi giá thực sự khác dòng mới nhất (optional optimization)._

---

## 7. Lỗi

- **400**, **404**, **409** (SKU), **401**, **403**, **500**.

---

## 8. Zod (body — FE)

```typescript
import { z } from "zod";

export const ProductPatchBodySchema = z
  .object({
    name: z.string().min(1).max(255).optional(),
    skuCode: z.string().min(1).max(50).optional(),
    barcode: z.string().max(100).nullable().optional(),
    categoryId: z.number().int().positive().nullable().optional(),
    description: z.string().nullable().optional(),
    weight: z.number().nonnegative().nullable().optional(),
    status: z.enum(["Active", "Inactive"]).optional(),
    imageUrl: z.string().url().max(500).nullable().optional(),
    salePrice: z.number().nonnegative().optional(),
    costPrice: z.number().nonnegative().optional(),
    priceEffectiveDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  })
  .refine((o) => Object.keys(o).length > 0, { message: "Cần ít nhất một trường" })
  .refine(
    (o) =>
      (o.salePrice === undefined && o.costPrice === undefined) ||
      (o.salePrice !== undefined && o.costPrice !== undefined),
    { message: "Khi đổi giá, cần gửi cả salePrice và costPrice" }
  );
```
