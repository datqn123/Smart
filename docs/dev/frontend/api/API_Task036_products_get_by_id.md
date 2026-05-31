# 📄 API SPEC: `GET /api/v1/products/{id}` — Chi tiết sản phẩm - Task036

> **Trạng thái**: Draft  
> **Feature**: UC8 — `ProductDetailDialog`, chỉnh sửa sâu  
> **Tags**: RESTful, Products, ProductUnits, Read

---

## 1. Mục tiêu Task

- Trả **chi tiết** `Products` + danh sách **`ProductUnits`** + **giá hiện hành** theo từng đơn vị (hoặc chỉ base + lịch sử tóm tắt) + **`imageUrl`** + **ảnh phụ** (nếu đã có bảng `ProductImages` sau migration Task039).

---

## 2. Endpoint

**`GET /api/v1/products/{id}`**

---

## 3. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.9** |
| **Endpoint** | `/api/v1/products/{id}` |
| **Method** | `GET` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner, Staff, Admin |
| **Use Case Ref** | UC8 |

---

## 4. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "id": 12,
    "skuCode": "SP0001",
    "barcode": "8934563123456",
    "name": "Nước suối 500ml",
    "categoryId": 2,
    "categoryName": "Đồ khô",
    "description": null,
    "weight": 500,
    "status": "Active",
    "imageUrl": "https://cdn.example/p/12.jpg",
    "createdAt": "2026-02-01T08:00:00Z",
    "updatedAt": "2026-04-22T09:00:00Z",
    "units": [
      {
        "id": 101,
        "unitName": "Chai",
        "conversionRate": 1,
        "isBaseUnit": true,
        "currentCostPrice": 4000,
        "currentSalePrice": 6000
      }
    ],
    "images": [
      { "id": 1, "url": "https://cdn.example/p/12.jpg", "sortOrder": 0, "isPrimary": true }
    ]
  },
  "message": "Thành công"
}
```

- `images`: rỗng nếu chưa triển khai `ProductImages`; khi đã có migration Task039, join `ProductImages` theo `product_id`.
- Giá “current” per unit: `LATERAL` giống Task034 nhưng lặp theo từng `unit_id`.

---

## 5. Logic DB

1. **`SELECT`** `Products` + join `Categories`.
2. **`SELECT`** `ProductUnits WHERE product_id = ?`.
3. Với mỗi unit (hoặc batch query): latest `ProductPriceHistory`.
4. **`SELECT`** từ `ProductImages` (nếu bảng tồn tại) `ORDER BY sort_order, id`.

---

## 6. Lỗi

- **404**: không có sản phẩm.
- **401** / **403** / **500**.

---

## 7. Zod (params)

```typescript
import { z } from "zod";
export const ProductIdParamsSchema = z.object({
  id: z.coerce.number().int().positive(),
});
```
