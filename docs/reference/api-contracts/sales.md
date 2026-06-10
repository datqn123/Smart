# Sales API Contracts

Base path: `/api/v1/sales-orders`

> Response envelope: `{ success: boolean, data: T, message: string }`

---

## GET /api/v1/sales-orders/retail/history

**Mô tả:** Lịch sử hóa đơn bán lẻ (Retail, read-only list).

**Auth:** JWT + `can_manage_orders`

**Query params:**
- `search` (string, optional) — Tìm kiếm theo mã đơn/tên khách
- `dateFrom` (string, optional) — Lọc từ ngày (ISO date)
- `dateTo` (string, optional) — Lọc đến ngày (ISO date)
- `page` (int, default: 1) — Số trang
- `limit` (int, default: 20) — Số bản ghi mỗi trang
- `sort` (string, optional) — Sắp xếp (VD: `createdAt,desc`)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "int",
        "orderCode": "string — Mã đơn hàng",
        "customerId": "int",
        "customerName": "string",
        "totalAmount": "decimal — Tổng tiền hàng",
        "discountAmount": "decimal — Chiết khấu",
        "finalAmount": "decimal — Thành tiền",
        "status": "string — Trạng thái đơn",
        "orderChannel": "string — Kênh bán",
        "paymentStatus": "string — Trạng thái thanh toán",
        "itemsCount": "int — Số dòng sản phẩm",
        "notes": "string",
        "createdAt": "datetime (ISO instant)",
        "updatedAt": "datetime (ISO instant)"
      }
    ],
    "page": "int",
    "limit": "int",
    "total": "long — Tổng số bản ghi"
  },
  "message": "Thao tác thành công"
}
```

**Errors:** 401 (thiếu JWT), 403 (thiếu quyền)

---

## GET /api/v1/sales-orders

**Mô tả:** Danh sách đơn hàng (phân trang).

**Auth:** JWT + `can_manage_orders`

**Query params:**
- `orderChannel` (string, optional) — Lọc theo kênh bán
- `search` (string, optional) — Tìm kiếm
- `status` (string, default: `all`) — Lọc theo trạng thái
- `paymentStatus` (string, default: `all`) — Lọc theo trạng thái thanh toán
- `page` (int, default: 1) — Số trang
- `limit` (int, default: 20) — Số bản ghi mỗi trang
- `sort` (string, optional) — Sắp xếp

**Response 200:** Giống `SalesOrderListPageData` ở trên (items là `SalesOrderListItemData[]`).

**Errors:** 401, 403

---

## GET /api/v1/sales-orders/{id}

**Mô tả:** Chi tiết đơn hàng.

**Auth:** JWT + `can_manage_orders`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "orderCode": "string — Mã đơn hàng",
    "customerId": "int",
    "customerName": "string",
    "totalAmount": "decimal — Tổng tiền hàng",
    "discountAmount": "decimal — Chiết khấu",
    "finalAmount": "decimal — Thành tiền",
    "status": "string — Trạng thái đơn",
    "orderChannel": "string — Kênh bán",
    "paymentStatus": "string — Trạng thái thanh toán",
    "parentOrderId": "int | null — ID đơn cha",
    "refSalesOrderId": "int | null — ID đơn tham chiếu",
    "shippingAddress": "string | null — Địa chỉ giao hàng",
    "notes": "string | null",
    "posShiftRef": "string | null — Mã ca POS",
    "voucherId": "int | null — ID voucher áp dụng",
    "voucherCode": "string | null — Mã voucher",
    "cancelledAt": "datetime (ISO instant) | null",
    "cancelledBy": "int | null",
    "createdAt": "datetime (ISO instant)",
    "updatedAt": "datetime (ISO instant)",
    "lines": [
      {
        "id": "int",
        "productId": "int",
        "productName": "string",
        "skuCode": "string",
        "unitId": "int",
        "unitName": "string",
        "quantity": "int — Số lượng",
        "unitPrice": "decimal — Đơn giá",
        "lineTotal": "decimal — Thành tiền dòng",
        "dispatchedQty": "int — Số lượng đã xuất"
      }
    ]
  },
  "message": "Thành công"
}
```

**Errors:** 400 (id không hợp lệ), 401, 403, 404 (không tìm thấy)

---

## POST /api/v1/sales-orders

**Mô tả:** Tạo đơn hàng mới.

**Auth:** JWT + `can_manage_orders`

**Request body:**
```json
{
  "orderChannel": "string (required) — Kênh bán (VD: retail, online)",
  "customerId": "int (positive, required) — ID khách hàng",
  "discountAmount": "decimal (optional) — Chiết khấu",
  "shippingAddress": "string (optional) — Địa chỉ giao",
  "notes": "string (optional) — Ghi chú",
  "paymentStatus": "string (optional) — Trạng thái thanh toán",
  "status": "string (optional) — Trạng thái đơn",
  "refSalesOrderId": "int (optional) — ID đơn tham chiếu",
  "lines": [
    {
      "productId": "int (positive, required) — ID sản phẩm",
      "unitId": "int (positive, required) — ID đơn vị tính",
      "quantity": "int (positive, required) — Số lượng",
      "unitPrice": "decimal (required) — Đơn giá"
    }
  ]
}
```

**Response 201:** `SalesOrderDetailData` (giống GET /{id}).

```json
{
  "success": true,
  "data": { "...": "SalesOrderDetailData" },
  "message": "Tạo đơn thành công"
}
```

**Errors:** 400 (validation), 401, 403

---

## POST /api/v1/sales-orders/retail/checkout

**Mô tả:** Thanh toán bán lẻ tại POS.

**Auth:** JWT + `can_manage_orders`

**Request body:**
```json
{
  "customerId": "int (optional) — ID khách hàng (null nếu walk-in)",
  "walkIn": "boolean (optional) — Khách vãng lai",
  "lines": [
    {
      "productId": "int (positive, required)",
      "unitId": "int (positive, required)",
      "quantity": "int (positive, required)",
      "unitPrice": "decimal (required)"
    }
  ],
  "discountAmount": "decimal (optional) — Chiết khấu thủ công",
  "voucherCode": "string (max 50, optional) — Mã voucher",
  "paymentStatus": "string (optional) — Trạng thái TT",
  "notes": "string (max 1000, optional)",
  "shiftReference": "string (max 100, optional) — Mã ca"
}
```

**Response 201:** `SalesOrderDetailData`.

```json
{
  "success": true,
  "data": { "...": "SalesOrderDetailData" },
  "message": "Thanh toán thành công"
}
```

**Errors:** 400 (validation), 401, 403

---

## POST /api/v1/sales-orders/retail/voucher-preview

**Mô tả:** Xem trước chiết khấu voucher trước khi thanh toán.

**Auth:** JWT + `can_manage_orders`

**Request body:**
```json
{
  "voucherId": "int (optional) — ID voucher",
  "voucherCode": "string (max 50, optional) — Mã voucher",
  "lines": [
    {
      "productId": "int (positive, required)",
      "unitId": "int (positive, required)",
      "quantity": "int (positive, required)",
      "unitPrice": "decimal (required)"
    }
  ],
  "discountAmount": "decimal (optional) — Chiết khấu thủ công"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "applicable": "boolean — Có áp dụng được không",
    "message": "string — Thông báo",
    "voucherId": "int | null",
    "voucherCode": "string | null",
    "voucherName": "string | null — Tên voucher",
    "discountType": "string | null — percentage / fixed",
    "discountValue": "decimal | null — Giá trị chiết khấu",
    "subtotal": "decimal — Tạm tính",
    "manualDiscountAmount": "decimal — Chiết khấu thủ công",
    "voucherDiscountAmount": "decimal — Chiết khấu từ voucher",
    "totalDiscountAmount": "decimal — Tổng chiết khấu",
    "payableAmount": "decimal — Số tiền phải trả"
  },
  "message": "Thao tác thành công"
}
```

**Errors:** 400 (validation), 401, 403

---

## PATCH /api/v1/sales-orders/{id}

**Mô tả:** Cập nhật đơn hàng (partial update).

**Auth:** JWT + `can_manage_orders`

**Request body:** JSON object (partial) — các field cần cập nhật.

**Response 200:** `SalesOrderDetailData`.

```json
{
  "success": true,
  "data": { "...": "SalesOrderDetailData" },
  "message": "Đã cập nhật đơn hàng"
}
```

**Errors:** 400 (id không hợp lệ), 401, 403, 404

---

## POST /api/v1/sales-orders/{id}/cancel

**Mô tả:** Hủy đơn hàng.

**Auth:** JWT + `can_manage_orders`

**Request body:**
```json
{
  "reason": "string (max 500, optional) — Lý do hủy"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "status": "string — Trạng thái sau khi hủy",
    "cancelledAt": "datetime (ISO instant)",
    "cancelledBy": "int"
  },
  "message": "Đã hủy đơn hàng"
}
```

**Errors:** 400 (id không hợp lệ), 401, 403, 404

---

## GET /api/v1/pos/products

**Mô tả:** Tìm kiếm sản phẩm POS theo barcode/tên.

**Auth:** JWT + `can_manage_orders`

**Query params:**
- `search` (string, optional) — Từ khóa tìm kiếm (barcode / tên)
- `categoryId` (int, optional) — Lọc theo danh mục
- `locationId` (int, optional) — Lọc theo kho
- `limit` (int, default: 40) — Số kết quả tối đa

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "productId": "int",
        "productName": "string",
        "skuCode": "string",
        "barcode": "string",
        "unitId": "int",
        "unitName": "string",
        "unitPrice": "decimal — Giá bán",
        "availableQty": "long — Tồn khả dụng",
        "imageUrl": "string | null — URL ảnh"
      }
    ]
  },
  "message": "Thành công"
}
```

**Errors:** 401, 403

---

## GET /api/v1/vouchers

**Mô tả:** Danh sách voucher áp dụng cho bán lẻ (phân trang).

**Auth:** JWT + `can_manage_orders`

**Query params:**
- `page` (int, default: 1) — Số trang
- `limit` (int, optional) — Số bản ghi mỗi trang

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "int",
        "code": "string — Mã voucher",
        "name": "string — Tên voucher",
        "discountType": "string — percentage / fixed",
        "discountValue": "decimal — Giá trị giảm",
        "validFrom": "date (ISO date) — Ngày bắt đầu",
        "validTo": "date (ISO date) — Ngày kết thúc",
        "isActive": "boolean — Còn hiệu lực",
        "usedCount": "int — Số lần đã dùng",
        "maxUses": "int | null — Giới hạn lượt dùng",
        "createdAt": "datetime (ISO instant)"
      }
    ],
    "page": "int",
    "limit": "int",
    "total": "long — Tổng số voucher"
  },
  "message": "Thao tác thành công"
}
```

**Errors:** 401, 403

---

## GET /api/v1/vouchers/{id}

**Mô tả:** Chi tiết voucher.

**Auth:** JWT + `can_manage_orders`

**Response 200:** `VoucherListItemData` (giống item trong danh sách).

```json
{
  "success": true,
  "data": {
    "id": "int",
    "code": "string",
    "name": "string",
    "discountType": "string",
    "discountValue": "decimal",
    "validFrom": "date",
    "validTo": "date",
    "isActive": "boolean",
    "usedCount": "int",
    "maxUses": "int | null",
    "createdAt": "datetime"
  },
  "message": "Thao tác thành công"
}
```

**Errors:** 400 (id không hợp lệ), 401, 403, 404
