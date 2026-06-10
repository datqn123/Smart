# Catalog API Contracts

Base path: `/api/v1`

> Response envelope: `{ success: boolean, data: T, message: string }`

---

## GET /api/v1/products

**Mô tả:** Danh sách sản phẩm phân trang, có thể lọc.

**Auth:** JWT + `can_manage_products`

**Request parameters:**
- `search` (string, optional) — Từ khóa tìm kiếm
- `categoryId` (int, optional) — Lọc theo danh mục
- `status` (string, optional, default: `"all"`) — Trạng thái
- `page` (int, optional, default: `1`) — Trang
- `limit` (int, optional, default: `20`) — Số lượng mỗi trang
- `sort` (string, optional) — Sắp xếp

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "int",
        "skuCode": "string",
        "barcode": "string",
        "name": "string",
        "categoryId": "int | null",
        "categoryName": "string",
        "imageUrl": "string",
        "status": "string",
        "currentStock": "long",
        "currentPrice": "BigDecimal",
        "createdAt": "datetime (ISO-8601)",
        "updatedAt": "datetime (ISO-8601)"
      }
    ],
    "page": "int",
    "limit": "int",
    "total": "long"
  },
  "message": "Thành công"
}
```

**Errors:** 400 (validation), 401 (unauthorized), 403 (thiếu quyền)

---

## POST /api/v1/products

**Mô tả:** Tạo sản phẩm mới (JSON body).

**Auth:** JWT + `can_manage_products`

**Request body:**
```json
{
  "skuCode": "string (max 50, required) — Mã SKU",
  "barcode": "string (max 100, optional) — Mã vạch",
  "name": "string (max 255, required) — Tên sản phẩm",
  "categoryId": "int (optional) — ID danh mục",
  "description": "string (optional) — Mô tả",
  "weight": "BigDecimal (>= 0, optional) — Khối lượng",
  "status": "string (max 20, optional) — Trạng thái",
  "imageUrl": "string (max 500, optional) — URL ảnh",
  "baseUnitName": "string (max 50, required) — Đơn vị cơ sở",
  "costPrice": "BigDecimal (>= 0, required) — Giá vốn",
  "salePrice": "BigDecimal (>= 0, required) — Giá bán",
  "priceEffectiveDate": "string (optional) — Ngày hiệu lực giá"
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "skuCode": "string",
    "barcode": "string",
    "name": "string",
    "categoryId": "int | null",
    "categoryName": "string",
    "imageUrl": "string",
    "status": "string",
    "currentStock": "long",
    "currentPrice": "BigDecimal",
    "createdAt": "datetime (ISO-8601)",
    "updatedAt": "datetime (ISO-8601)",
    "unitId": "int"
  },
  "message": "Đã tạo sản phẩm"
}
```

**Errors:** 400 (validation), 401 (unauthorized), 403 (thiếu quyền)

---

## POST /api/v1/products (multipart)

**Mô tả:** Tạo sản phẩm kèm file ảnh (multipart/form-data).

**Auth:** JWT + `can_manage_products`

**Request parts:**
- `metadata` (string, required) — JSON của `ProductCreateRequest`
- `file` (file, lặp lại, optional) — Các file ảnh
- `primaryImageIndex` (int, optional) — Chỉ số ảnh chính

**Response 201:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "skuCode": "string",
    "barcode": "string",
    "name": "string",
    "categoryId": "int | null",
    "categoryName": "string",
    "imageUrl": "string",
    "status": "string",
    "currentStock": "long",
    "currentPrice": "BigDecimal",
    "createdAt": "datetime (ISO-8601)",
    "updatedAt": "datetime (ISO-8601)",
    "unitId": "int"
  },
  "message": "Đã tạo sản phẩm"
}
```

**Errors:** 400 (validation, JSON lỗi), 401 (unauthorized), 403 (thiếu quyền)

---

## GET /api/v1/products/{id}

**Mô tả:** Chi tiết sản phẩm.

**Auth:** JWT + `can_manage_products`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "skuCode": "string",
    "barcode": "string",
    "name": "string",
    "categoryId": "int | null",
    "categoryName": "string",
    "description": "string",
    "weight": "BigDecimal",
    "status": "string",
    "imageUrl": "string",
    "createdAt": "datetime (ISO-8601)",
    "updatedAt": "datetime (ISO-8601)",
    "units": [
      {
        "id": "int",
        "unitName": "string",
        "conversionRate": "BigDecimal",
        "isBaseUnit": "boolean",
        "currentCostPrice": "BigDecimal",
        "currentSalePrice": "BigDecimal"
      }
    ],
    "images": [
      {
        "id": "int",
        "url": "string",
        "sortOrder": "int",
        "isPrimary": "boolean"
      }
    ]
  },
  "message": "Thành công"
}
```

**Errors:** 400 (id không hợp lệ), 401 (unauthorized), 403 (thiếu quyền), 404 (không tìm thấy)

---

## PATCH /api/v1/products/{id}

**Mô tả:** Cập nhật một phần sản phẩm.

**Auth:** JWT + `can_manage_products`

**Request body:** JSON hợp lệ với các field cần cập nhật.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "skuCode": "string",
    "barcode": "string",
    "name": "string",
    "categoryId": "int | null",
    "categoryName": "string",
    "description": "string",
    "weight": "BigDecimal",
    "status": "string",
    "imageUrl": "string",
    "createdAt": "datetime (ISO-8601)",
    "updatedAt": "datetime (ISO-8601)",
    "units": [
      {
        "id": "int",
        "unitName": "string",
        "conversionRate": "BigDecimal",
        "isBaseUnit": "boolean",
        "currentCostPrice": "BigDecimal",
        "currentSalePrice": "BigDecimal"
      }
    ],
    "images": [
      {
        "id": "int",
        "url": "string",
        "sortOrder": "int",
        "isPrimary": "boolean"
      }
    ]
  },
  "message": "Thành công"
}
```

**Errors:** 400 (validation), 401 (unauthorized), 403 (thiếu quyền), 404 (không tìm thấy)

---

## DELETE /api/v1/products/{id}

**Mô tả:** Xóa sản phẩm.

**Auth:** JWT + `can_manage_products`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "deleted": true
  },
  "message": "Đã xóa sản phẩm"
}
```

**Errors:** 400 (id không hợp lệ), 401 (unauthorized), 403 (thiếu quyền), 404 (không tìm thấy)

---

## POST /api/v1/products/bulk-delete

**Mô tả:** Xóa hàng loạt sản phẩm.

**Auth:** JWT + `can_manage_products`

**Request body:**
```json
{
  "ids": "int[] (min 1, max 100, required) — Danh sách ID sản phẩm"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "deletedIds": "int[]",
    "deletedCount": "int"
  },
  "message": "Đã xóa các sản phẩm"
}
```

**Errors:** 400 (validation), 401 (unauthorized), 403 (thiếu quyền)

---

## POST /api/v1/products/{id}/images (JSON)

**Mô tả:** Thêm ảnh cho sản phẩm bằng JSON.

**Auth:** JWT + `can_manage_products`

**Request body:**
```json
{
  "url": "string (URL, max 500, required) — URL ảnh",
  "sortOrder": "int (>= 0, optional, default: 0) — Thứ tự",
  "isPrimary": "boolean (optional, default: false) — Ảnh chính"
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "productId": "int",
    "url": "string",
    "sortOrder": "int",
    "isPrimary": "boolean"
  },
  "message": "Đã thêm ảnh"
}
```

**Errors:** 400 (validation), 401 (unauthorized), 403 (thiếu quyền), 404 (không tìm thấy sản phẩm)

---

## POST /api/v1/products/{id}/images (multipart)

**Mô tả:** Thêm ảnh cho sản phẩm bằng multipart/form-data.

**Auth:** JWT + `can_manage_products`

**Request parts:**
- `file` (file, required) — File ảnh
- `sortOrder` (int, optional, default: `0`) — Thứ tự
- `isPrimary` (boolean, optional, default: `false`) — Ảnh chính

**Response 201:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "productId": "int",
    "url": "string",
    "sortOrder": "int",
    "isPrimary": "boolean"
  },
  "message": "Đã thêm ảnh"
}
```

**Errors:** 400 (thiếu file, sortOrder âm), 401 (unauthorized), 403 (thiếu quyền), 404 (không tìm thấy sản phẩm)

---

## GET /api/v1/categories

**Mô tả:** Danh sách danh mục dạng cây hoặc phẳng.

**Auth:** JWT + `can_manage_products`

**Request parameters:**
- `format` (string, optional) — Định dạng trả về (`"tree"` hoặc `"flat"`)
- `search` (string, optional) — Từ khóa tìm kiếm
- `status` (string, optional) — Lọc theo trạng thái

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "long",
        "categoryCode": "string",
        "name": "string",
        "description": "string",
        "parentId": "long | null",
        "sortOrder": "int",
        "status": "string",
        "productCount": "long",
        "createdAt": "datetime (ISO-8601)",
        "updatedAt": "datetime (ISO-8601)",
        "children": "CategoryNodeResponse[] | null"
      }
    ]
  },
  "message": "Thành công"
}
```

**Errors:** 401 (unauthorized), 403 (thiếu quyền)

---

## GET /api/v1/categories/{id}

**Mô tả:** Chi tiết danh mục kèm breadcrumb.

**Auth:** JWT + `can_manage_products`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "categoryCode": "string",
    "name": "string",
    "description": "string",
    "parentId": "long | null",
    "parentName": "string",
    "sortOrder": "int",
    "status": "string",
    "productCount": "long",
    "createdAt": "datetime (ISO-8601)",
    "updatedAt": "datetime (ISO-8601)",
    "breadcrumb": [
      {
        "id": "long",
        "name": "string",
        "categoryCode": "string"
      }
    ]
  },
  "message": "Thành công"
}
```

**Errors:** 400 (id không hợp lệ), 401 (unauthorized), 403 (thiếu quyền), 404 (không tìm thấy)

---

## POST /api/v1/categories

**Mô tả:** Tạo danh mục mới.

**Auth:** JWT + `can_manage_products`

**Request body:**
```json
{
  "categoryCode": "string (max 50, required) — Mã danh mục",
  "name": "string (max 255, required) — Tên danh mục",
  "description": "string (optional) — Mô tả",
  "parentId": "long (optional) — ID danh mục cha",
  "sortOrder": "int (optional) — Thứ tự sắp xếp",
  "status": "string (optional) — Trạng thái"
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "categoryCode": "string",
    "name": "string",
    "description": "string",
    "parentId": "long | null",
    "sortOrder": "int",
    "status": "string",
    "productCount": "long",
    "createdAt": "datetime (ISO-8601)",
    "updatedAt": "datetime (ISO-8601)",
    "children": null
  },
  "message": "Đã tạo danh mục"
}
```

**Errors:** 400 (validation), 401 (unauthorized), 403 (thiếu quyền)

---

## PATCH /api/v1/categories/{id}

**Mô tả:** Cập nhật một phần danh mục.

**Auth:** JWT + `can_manage_products`

**Request body:** JSON hợp lệ với các field cần cập nhật.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "categoryCode": "string",
    "name": "string",
    "description": "string",
    "parentId": "long | null",
    "sortOrder": "int",
    "status": "string",
    "productCount": "long",
    "createdAt": "datetime (ISO-8601)",
    "updatedAt": "datetime (ISO-8601)",
    "children": "CategoryNodeResponse[] | null"
  },
  "message": "Đã cập nhật danh mục"
}
```

**Errors:** 400 (validation), 401 (unauthorized), 403 (thiếu quyền), 404 (không tìm thấy)

---

## DELETE /api/v1/categories/{id}

**Mô tả:** Xóa danh mục.

**Auth:** JWT + `can_manage_products`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "deleted": true
  },
  "message": "Đã xóa danh mục"
}
```

**Errors:** 400 (id không hợp lệ), 401 (unauthorized), 403 (thiếu quyền), 404 (không tìm thấy)

---

## GET /api/v1/customers

**Mô tả:** Danh sách khách hàng phân trang.

**Auth:** JWT + `can_manage_customers`

**Request parameters:**
- `search` (string, optional) — Từ khóa tìm kiếm
- `status` (string, optional, default: `"all"`) — Trạng thái
- `page` (int, optional, default: `1`) — Trang
- `limit` (int, optional, default: `20`) — Số lượng mỗi trang
- `sort` (string, optional) — Sắp xếp

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "int",
        "customerCode": "string",
        "name": "string",
        "phone": "string",
        "email": "string",
        "address": "string",
        "loyaltyPoints": "int",
        "totalSpent": "BigDecimal",
        "orderCount": "long",
        "status": "string",
        "createdAt": "datetime (ISO-8601)",
        "updatedAt": "datetime (ISO-8601)"
      }
    ],
    "page": "int",
    "limit": "int",
    "total": "long"
  },
  "message": "Thành công"
}
```

**Errors:** 401 (unauthorized), 403 (thiếu quyền)

---

## POST /api/v1/customers

**Mô tả:** Tạo khách hàng mới.

**Auth:** JWT + `can_manage_customers`

**Request body:**
```json
{
  "customerCode": "string (max 50, required) — Mã khách hàng",
  "name": "string (max 255, required) — Tên khách hàng",
  "phone": "string (max 20, required) — Số điện thoại",
  "email": "string (optional) — Email",
  "address": "string (optional) — Địa chỉ",
  "status": "string (optional) — Trạng thái"
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "customerCode": "string",
    "name": "string",
    "phone": "string",
    "email": "string",
    "address": "string",
    "loyaltyPoints": "int",
    "totalSpent": "BigDecimal",
    "orderCount": "long",
    "status": "string",
    "createdAt": "datetime (ISO-8601)",
    "updatedAt": "datetime (ISO-8601)"
  },
  "message": "Đã tạo khách hàng"
}
```

**Errors:** 400 (validation), 401 (unauthorized), 403 (thiếu quyền)

---

## GET /api/v1/customers/{id}

**Mô tả:** Chi tiết khách hàng.

**Auth:** JWT + `can_manage_customers`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "customerCode": "string",
    "name": "string",
    "phone": "string",
    "email": "string",
    "address": "string",
    "loyaltyPoints": "int",
    "totalSpent": "BigDecimal",
    "orderCount": "long",
    "status": "string",
    "createdAt": "datetime (ISO-8601)",
    "updatedAt": "datetime (ISO-8601)"
  },
  "message": "Thành công"
}
```

**Errors:** 400 (id không hợp lệ), 401 (unauthorized), 403 (thiếu quyền), 404 (không tìm thấy)

---

## PATCH /api/v1/customers/{id}

**Mô tả:** Cập nhật một phần khách hàng.

**Auth:** JWT + `can_manage_customers`

**Request body:** JSON hợp lệ với các field cần cập nhật.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "customerCode": "string",
    "name": "string",
    "phone": "string",
    "email": "string",
    "address": "string",
    "loyaltyPoints": "int",
    "totalSpent": "BigDecimal",
    "orderCount": "long",
    "status": "string",
    "createdAt": "datetime (ISO-8601)",
    "updatedAt": "datetime (ISO-8601)"
  },
  "message": "Đã cập nhật khách hàng"
}
```

**Errors:** 400 (validation), 401 (unauthorized), 403 (thiếu quyền), 404 (không tìm thấy)

---

## DELETE /api/v1/customers/{id}

**Mô tả:** Xóa khách hàng.

**Auth:** JWT + `can_manage_customers`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "deleted": true
  },
  "message": "Đã xóa khách hàng"
}
```

**Errors:** 400 (id không hợp lệ), 401 (unauthorized), 403 (thiếu quyền), 404 (không tìm thấy)

---

## POST /api/v1/customers/bulk-delete

**Mô tả:** Xóa hàng loạt khách hàng.

**Auth:** JWT + `can_manage_customers`

**Request body:**
```json
{
  "ids": "int[] (min 1, max 200, required) — Danh sách ID khách hàng"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "deletedIds": "int[]",
    "deletedCount": "int"
  },
  "message": "Đã xóa các khách hàng"
}
```

**Errors:** 400 (validation), 401 (unauthorized), 403 (thiếu quyền)

---

## GET /api/v1/suppliers

**Mô tả:** Danh sách nhà cung cấp phân trang.

**Auth:** JWT + `can_manage_products`

**Request parameters:**
- `search` (string, optional) — Từ khóa tìm kiếm
- `status` (string, optional, default: `"all"`) — Trạng thái
- `page` (int, optional, default: `1`) — Trang
- `limit` (int, optional, default: `20`) — Số lượng mỗi trang
- `sort` (string, optional) — Sắp xếp

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "int",
        "supplierCode": "string",
        "name": "string",
        "contactPerson": "string",
        "phone": "string",
        "email": "string",
        "address": "string",
        "taxCode": "string",
        "status": "string",
        "receiptCount": "long",
        "createdAt": "datetime (ISO-8601)",
        "updatedAt": "datetime (ISO-8601)"
      }
    ],
    "page": "int",
    "limit": "int",
    "total": "long"
  },
  "message": "Thành công"
}
```

**Errors:** 401 (unauthorized), 403 (thiếu quyền)

---

## POST /api/v1/suppliers

**Mô tả:** Tạo nhà cung cấp mới.

**Auth:** JWT + `can_manage_products`

**Request body:**
```json
{
  "supplierCode": "string (max 50, required) — Mã nhà cung cấp",
  "name": "string (max 255, required) — Tên nhà cung cấp",
  "contactPerson": "string (max 255, required) — Người liên hệ",
  "phone": "string (max 20, required) — Số điện thoại",
  "email": "string (optional) — Email",
  "address": "string (optional) — Địa chỉ",
  "taxCode": "string (optional) — Mã số thuế",
  "status": "string (optional) — Trạng thái"
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "supplierCode": "string",
    "name": "string",
    "contactPerson": "string",
    "phone": "string",
    "email": "string",
    "address": "string",
    "taxCode": "string",
    "status": "string",
    "receiptCount": "long",
    "lastReceiptAt": "datetime (ISO-8601) | null",
    "createdAt": "datetime (ISO-8601)",
    "updatedAt": "datetime (ISO-8601)"
  },
  "message": "Đã tạo nhà cung cấp"
}
```

**Errors:** 400 (validation), 401 (unauthorized), 403 (thiếu quyền)

---

## GET /api/v1/suppliers/{id}

**Mô tả:** Chi tiết nhà cung cấp.

**Auth:** JWT + `can_manage_products`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "supplierCode": "string",
    "name": "string",
    "contactPerson": "string",
    "phone": "string",
    "email": "string",
    "address": "string",
    "taxCode": "string",
    "status": "string",
    "receiptCount": "long",
    "lastReceiptAt": "datetime (ISO-8601) | null",
    "createdAt": "datetime (ISO-8601)",
    "updatedAt": "datetime (ISO-8601)"
  },
  "message": "Thành công"
}
```

**Errors:** 400 (id không hợp lệ), 401 (unauthorized), 403 (thiếu quyền), 404 (không tìm thấy)

---

## PATCH /api/v1/suppliers/{id}

**Mô tả:** Cập nhật một phần nhà cung cấp.

**Auth:** JWT + `can_manage_products`

**Request body:** JSON hợp lệ với các field cần cập nhật.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "supplierCode": "string",
    "name": "string",
    "contactPerson": "string",
    "phone": "string",
    "email": "string",
    "address": "string",
    "taxCode": "string",
    "status": "string",
    "receiptCount": "long",
    "lastReceiptAt": "datetime (ISO-8601) | null",
    "createdAt": "datetime (ISO-8601)",
    "updatedAt": "datetime (ISO-8601)"
  },
  "message": "Đã cập nhật nhà cung cấp"
}
```

**Errors:** 400 (validation), 401 (unauthorized), 403 (thiếu quyền), 404 (không tìm thấy)

---

## DELETE /api/v1/suppliers/{id}

**Mô tả:** Xóa nhà cung cấp.

**Auth:** JWT + `can_manage_products`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "deleted": true
  },
  "message": "Đã xóa nhà cung cấp"
}
```

**Errors:** 400 (id không hợp lệ), 401 (unauthorized), 403 (thiếu quyền), 404 (không tìm thấy)

---

## POST /api/v1/suppliers/bulk-delete

**Mô tả:** Xóa hàng loạt nhà cung cấp.

**Auth:** JWT + `can_manage_products`

**Request body:**
```json
{
  "ids": "int[] (min 1, max 50, required) — Danh sách ID nhà cung cấp"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "deletedIds": "int[]",
    "deletedCount": "int"
  },
  "message": "Đã xóa các nhà cung cấp"
}
```

**Errors:** 400 (validation), 401 (unauthorized), 403 (thiếu quyền)
