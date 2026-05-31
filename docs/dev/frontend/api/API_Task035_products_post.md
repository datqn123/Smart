# 📄 API SPEC: `POST /api/v1/products` — Tạo sản phẩm - Task035

> **Trạng thái**: Draft  
> **Feature**: UC8 — `ProductForm` (thêm mới)  
> **Tags**: RESTful, Products, ProductUnits, ProductPriceHistory, Create

---

## 1. Mục tiêu Task

- Tạo **`Products`** + **đúng một** `ProductUnits` (đơn vị cơ sở, ví dụ `"Cái"`, `conversion_rate = 1`, `is_base_unit = true`) + **một** dòng **`ProductPriceHistory`** (giá vốn / giá bán khởi tạo) trong **một transaction**.

---

## 2. Endpoint

**`POST /api/v1/products`**

---

## 3. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.9** |
| **Endpoint** | `/api/v1/products` |
| **Method** | `POST` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner, Staff (UC8 ghi) |
| **Use Case Ref** | UC8 |

---

## 4. Request body

```json
{
  "skuCode": "SP0001",
  "barcode": "8934563123456",
  "name": "Nước suối 500ml",
  "categoryId": 2,
  "description": null,
  "weight": 500,
  "status": "Active",
  "imageUrl": null,
  "baseUnitName": "Chai",
  "costPrice": 4000,
  "salePrice": 6000,
  "priceEffectiveDate": "2026-04-23"
}
```

| Trường | Bắt buộc | Mô tả |
| :----- | :------- | :---- |
| `skuCode` | Có | UNIQUE |
| `name` | Có | |
| `barcode` | Không | |
| `categoryId` | Không | FK `Categories`; `null` = chưa phân loại |
| `description` | Không | |
| `weight` | Không | Gram (theo DB §7) |
| `status` | Không | Mặc định `Active` |
| `imageUrl` | Không | Ảnh đại diện; gallery → Task039 |
| `baseUnitName` | Có | Tạo `ProductUnits` cơ sở |
| `costPrice` | Có | ≥ 0 |
| `salePrice` | Có | ≥ 0 — khớp `currentPrice` form |
| `priceEffectiveDate` | Không | Mặc định `CURRENT_DATE` |

---

## 5. Thành công — `201 Created`

Trả object sản phẩm (có thể gọn như Task034 item + `unitId` của đơn vị cơ sở).

---

## 6. Logic DB (transaction)

1. Validate → **400**.
2. `sku_code` trùng → **409**.
3. `category_id` không tồn tại → **404** hoặc **400**.
4. **`INSERT INTO Products`** … `RETURNING id`.
5. **`INSERT INTO ProductUnits`** (`product_id`, `unit_name`, `conversion_rate`, `is_base_unit`) VALUES (`id`, `baseUnitName`, `1`, `TRUE`) `RETURNING id` → `unit_id`.
6. **`INSERT INTO ProductPriceHistory`** (`product_id`, `unit_id`, `cost_price`, `sale_price`, `effective_date`).
7. Commit; (tuỳ chọn) SystemLogs.

```sql
BEGIN;
INSERT INTO Products (category_id, sku_code, barcode, name, image_url, description, weight, status)
VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id;
INSERT INTO ProductUnits (product_id, unit_name, conversion_rate, is_base_unit)
VALUES ($pid, $uname, 1, TRUE) RETURNING id;
INSERT INTO ProductPriceHistory (product_id, unit_id, cost_price, sale_price, effective_date)
VALUES ($pid, $uid, $cost, $sale, $eff);
COMMIT;
```

---

## 6b. `multipart/form-data` — tạo kèm nhiều ảnh (SRS §14)

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Content-Type** | `multipart/form-data` |
| **Part `metadata`** | Chuỗi JSON — **cùng schema** mục §4 (Task035 `ProductCreateRequest`) |
| **Part `file`** | Lặp lại nhiều lần (tối đa **10** tệp); MIME jpeg/png/webp; upload **song song** phía server (Cloudinary bắt buộc bật) |
| **Param `primaryImageIndex`** | Tùy chọn, số nguyên **0-based** — ảnh chính trong danh sách `file`; mặc định `0` |

- **201** — cùng shape JSON `201` ở trên (sản phẩm + `unitId`).
- **All-or-nothing:** lỗi bất kỳ bước upload / lưu → rollback tạo sản phẩm (không dữ liệu nửa vời) — SRS §14.4.
- **Khi không gửi `file`:** tương đương tạo JSON (chỉ `metadata`).

**Client (mini-erp):** `postProductCreateMultipart` trong `features/product-management/api/productsApi.ts` — gọi khi bấm **Lưu** và có `File[]` đã chọn ở form (BR-10).

---

## 7. Lỗi

- **400**, **404** (category), **409** (SKU), **401**, **403**, **500**.

---

## 8. Zod (body — FE)

```typescript
import { z } from "zod";

export const ProductCreateBodySchema = z.object({
  skuCode: z.string().min(1).max(50),
  barcode: z.string().max(100).optional().nullable(),
  name: z.string().min(1).max(255),
  categoryId: z.number().int().positive().nullable().optional(),
  description: z.string().nullable().optional(),
  weight: z.number().nonnegative().nullable().optional(),
  status: z.enum(["Active", "Inactive"]).optional().default("Active"),
  imageUrl: z.string().url().max(500).nullable().optional(),
  baseUnitName: z.string().min(1).max(50),
  costPrice: z.number().nonnegative(),
  salePrice: z.number().nonnegative(),
  priceEffectiveDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
});
```
