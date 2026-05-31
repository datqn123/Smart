# 📄 API SPEC: `GET /api/v1/store-profile` — Thông tin cửa hàng — Task073

> **Trạng thái**: Draft  
> **Feature**: mini-ERP — màn **Thông tin cửa hàng** (`StoreInfoPage`)  
> **Tags**: RESTful, Settings, Read-only

---

## 1. Mục tiêu

Trả về **một** bản ghi `storeprofiles` (StoreProfiles) gắn với **Owner** hiện tại (tenant đơn).

- DB đã có seed tạo hồ sơ tối thiểu cho Owner (Flyway **V22**), nhưng backend vẫn cần xử lý an toàn nếu thiếu.
- Chuẩn khuyến nghị: **200** với object (tạo tối thiểu nếu thiếu). Không dùng 404 cho “chưa cấu hình”.

---

## 2. Endpoint

**`GET /api/v1/store-profile`** (số ít — tài nguyên đơn)

---

## 3. Tham chiếu

[`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.16**.  
[`Database_Specification.md`](../UC/Database_Specification.md) **§6.1** `StoreProfiles`.

---

## 4. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Authentication** | `Bearer` |
| **RBAC** | Yêu cầu `hasAuthority('can_view_store_profile')`. |

---

## 5. Response `200 OK`

Ánh xạ cột DB → **camelCase** khớp state FE `StoreInfoPage`:

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Mini ERP Solution Center",
    "businessCategory": "Bán lẻ & Phân phối thiết bị",
    "address": "123 Đường ABC, Quận X, TP. Hồ Chí Minh",
    "phone": "028 1234 5678",
    "email": "contact@minierp.vn",
    "website": "https://minierp.vn",
    "taxCode": "0312345678",
    "footerNote": "Cảm ơn quý khách…",
    "logoUrl": "https://cdn.example.com/logo.png",
    "facebookUrl": "https://facebook.com/minierp_store",
    "instagramHandle": "@minierp.official",
    "defaultRetailLocationId": 1,
    "updatedAt": "2026-04-23T08:00:00Z"
  },
  "message": "Thành công"
}
```

---

## 6. Logic DB

> **Lưu ý tên bảng vật lý (PostgreSQL)**: Flyway tạo `CREATE TABLE StoreProfiles` (không quote) ⇒ tên thật là **`storeprofiles`**.

```sql
SELECT
  id,
  name,
  business_category,
  address,
  phone,
  email,
  website,
  tax_code,
  footer_note,
  logo_url,
  facebook_url,
  instagram_handle,
  default_retail_location_id,
  updated_at
FROM storeprofiles
WHERE owner_id = :ownerId
LIMIT 1;
```

(JWT chứa `user_id` / `sub` để xác định `ownerId` — tenant đơn.)

---

## 7. Lỗi

**401**, **403**, **500**.

---

## 8. Zod (response — FE)

```typescript
import { z } from "zod";

export const StoreProfileSchema = z.object({
  id: z.number().int().positive(),
  name: z.string(),
  businessCategory: z.string().nullable().optional(),
  address: z.string().nullable().optional(),
  phone: z.string().nullable().optional(),
  email: z.string().nullable().optional(),
  website: z.string().nullable().optional(),
  taxCode: z.string().nullable().optional(),
  footerNote: z.string().nullable().optional(),
  logoUrl: z.string().nullable().optional(),
  facebookUrl: z.string().nullable().optional(),
  instagramHandle: z.string().nullable().optional(),
  updatedAt: z.string(),
});
```
