# 📄 API SPEC: `GET /api/v1/pos/products` — Tìm hàng cho POS (bán lẻ) - Task059

> **Trạng thái**: Draft  
> **Feature**: UC9 — màn **Bán lẻ (POS)** (`RetailPage`, `POSProductSelector`)  
> **Tags**: RESTful, POS, Products, Read

---

## 1. Mục tiêu Task

- Endpoint **đọc** tối ưu cho lưới sản phẩm POS: tìm theo tên / SKU / **barcode**, lọc danh mục; trả **giá bán** (đơn vị chọn), **tên đơn vị**, có thể **tồn khả dụng** tổng hợp (read-model) để cảnh báo hết hàng.

---

## 2. Endpoint

**`GET /api/v1/pos/products`**

_Không ghi nhận giỏ hàng — giỏ nằm client (`useOrderStore`) cho đến Task060._

---

## 3. Tham chiếu

Thay `mockInventory` trong `POSProductSelector` — join [`Database_Specification.md`](../UC/Database_Specification.md) **§7** `Products`, **§8** `ProductUnits`, **§9** `ProductPriceHistory`, **§16** `Inventory` (tùy policy hiển thị tồn).

---

## 4. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Endpoint** | `/api/v1/pos/products` |
| **Method** | `GET` |
| **Authentication** | `Bearer` |
| **RBAC** | Staff có quyền POS / UC9 |
| **Use Case Ref** | UC9 |

---

## 5. Query parameters

| Tham số | Kiểu | Mô tả |
| :------ | :--- | :---- |
| `search` | string | ILIKE `name`, `sku_code`, **exact hoặc prefix `barcode`** (policy quét mã vạch). |
| `categoryId` | int | Lọc `Products.category_id`. |
| `locationId` | int | Nếu có: tính tồn theo vị trí; không có → tồn **toàn kho** hoặc kho mặc định của user. |
| `limit` | int | Mặc định `40`, max `100`. |

---

## 6. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "productId": 12,
        "productName": "Nước suối 500ml",
        "skuCode": "SP0001",
        "barcode": "8934563123456",
        "unitId": 101,
        "unitName": "Chai",
        "unitPrice": 6000,
        "availableQty": 240,
        "imageUrl": null
      }
    ]
  },
  "message": "Thành công"
}
```

- **`unitPrice`**: `sale_price` hiện hành của `unit_id` (giống tinh thần Task034).
- **`availableQty`**: tùy PM — `SUM(quantity)` `Inventory` theo `product_id` (đơn vị cơ sở) chia cho `conversion_rate` hoặc chỉ hiển thị cờ `inStock: boolean`.

---

## 7. Logic DB

Read-only; index trên `sku_code`, `barcode`, `name`; LATERAL giá mới nhất per `unit_id` (thường đơn vị cơ sở hoặc đơn vị bán lẻ mặc định).

---

## 8. Lỗi

**400** / **401** / **403** / **500**.

---

## 9. Zod (query — FE)

```typescript
import { z } from "zod";

export const PosProductsQuerySchema = z.object({
  search: z.string().optional(),
  categoryId: z.coerce.number().int().positive().optional(),
  locationId: z.coerce.number().int().positive().optional(),
  limit: z.coerce.number().int().min(1).max(100).optional().default(40),
});
```
