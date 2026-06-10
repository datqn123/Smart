# Inventory API Contracts

Base path: `/api/v1`

> Response envelope: `{ success: boolean, data: T, message: string }`

---

## InventoryController — `/api/v1/inventory`

### GET /api/v1/inventory/summary

**Mô tả:** KPI tồn kho (tổng số SKU, tổng giá trị, số lượng sắp hết hạn, số lượng tồn thấp) theo bộ lọc.

**Auth:** JWT + `can_manage_inventory`

**Query params:**
- `search` (string, optional)
- `stockLevel` (string, optional)
- `locationId` (string, optional)
- `categoryId` (string, optional)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "totalSkus": "long — Tổng số SKU",
    "totalValue": "BigDecimal — Tổng giá trị tồn",
    "lowStockCount": "long — Số lượng tồn thấp",
    "expiringSoonCount": "long — Số lượng sắp hết hạn"
  },
  "message": "Thành công"
}
```

**Errors:** 401 (thiếu JWT), 403 (thiếu quyền)

---

### GET /api/v1/inventory

**Mô tả:** Danh sách tồn kho phân trang kèm summary KPI.

**Auth:** JWT + `can_manage_inventory`

**Query params:**
- `search` (string, optional)
- `stockLevel` (string, optional)
- `locationId` (string, optional)
- `categoryId` (string, optional)
- `productId` (string, optional)
- `page` (string, optional)
- `limit` (string, optional)
- `sort` (string, optional)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "totalSkus": "long",
      "totalValue": "BigDecimal",
      "lowStockCount": "long",
      "expiringSoonCount": "long"
    },
    "items": [
      {
        "id": "long",
        "productId": "long",
        "productName": "string",
        "skuCode": "string",
        "barcode": "string",
        "locationId": "int",
        "warehouseCode": "string",
        "shelfCode": "string",
        "batchNumber": "string",
        "expiryDate": "LocalDate (yyyy-MM-dd)",
        "quantity": "int",
        "minQuantity": "int",
        "unitId": "int",
        "unitName": "string",
        "costPrice": "BigDecimal",
        "updatedAt": "Instant",
        "isLowStock": "boolean",
        "isExpiringSoon": "boolean",
        "totalValue": "BigDecimal"
      }
    ],
    "page": "int",
    "limit": "int",
    "total": "long"
  },
  "message": "Thành công"
}
```

**Errors:** 401, 403

---

### GET /api/v1/inventory/{id}

**Mô tả:** Chi tiết một dòng tồn kho, tùy chọn bao gồm danh sách lô liên quan.

**Auth:** JWT + `can_manage_inventory`

**Path params:**
- `id` (long, required) — ID dòng tồn

**Query params:**
- `include` (string, optional) — Giá trị: `relatedLines`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "productId": "long",
    "productName": "string",
    "skuCode": "string",
    "barcode": "string",
    "locationId": "int",
    "warehouseCode": "string",
    "shelfCode": "string",
    "batchNumber": "string",
    "expiryDate": "LocalDate",
    "quantity": "int",
    "minQuantity": "int",
    "unitId": "int",
    "unitName": "string",
    "costPrice": "BigDecimal",
    "updatedAt": "Instant",
    "isLowStock": "boolean",
    "isExpiringSoon": "boolean",
    "totalValue": "BigDecimal",
    "relatedLines": [
      {
        "id": "long",
        "batchNumber": "string",
        "quantity": "int",
        "expiryDate": "LocalDate",
        "warehouseCode": "string",
        "shelfCode": "string"
      }
    ]
  },
  "message": "Thành công"
}
```

**Errors:** 400 (id không hợp lệ), 401, 403

---

### PATCH /api/v1/inventory/{id}

**Mô tả:** Cập nhật meta thông tin một dòng tồn kho (partial JSON).

**Auth:** JWT + `can_manage_inventory`

**Path params:**
- `id` (long, required)

**Request body:** `JsonNode` — Các field cần cập nhật (vd: `costPrice`, `minQuantity`, `batchNumber`,...)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "productId": "long",
    "productName": "string",
    "skuCode": "string",
    "barcode": "string",
    "locationId": "int",
    "warehouseCode": "string",
    "shelfCode": "string",
    "batchNumber": "string",
    "expiryDate": "LocalDate",
    "quantity": "int",
    "minQuantity": "int",
    "unitId": "int",
    "unitName": "string",
    "costPrice": "BigDecimal",
    "updatedAt": "Instant",
    "isLowStock": "boolean",
    "isExpiringSoon": "boolean",
    "totalValue": "BigDecimal"
  },
  "message": "Đã cập nhật thông tin tồn kho"
}
```

**Errors:** 400, 401, 403

---

### PATCH /api/v1/inventory/bulk

**Mô tả:** Cập nhật meta nhiều dòng tồn kho (all-or-nothing, tối đa 100 phần tử).

**Auth:** JWT + `can_manage_inventory`

**Request body:** `JsonNode` — Mảng các item cần cập nhật

**Response 200:**
```json
{
  "success": true,
  "data": {
    "updated": [
      { "...InventoryListItemData" }
    ],
    "failed": []
  },
  "message": "Đã cập nhật thông tin tồn kho (hàng loạt)"
}
```

**Errors:** 400, 401, 403

---

## StockReceiptsController — `/api/v1/stock-receipts`

### GET /api/v1/stock-receipts

**Mô tả:** Danh sách phiếu nhập kho phân trang.

**Auth:** JWT + `can_manage_inventory`

**Query params:**
- `search` (string, optional)
- `status` (string, optional)
- `dateFrom` (string, optional)
- `dateTo` (string, optional)
- `supplierId` (string, optional)
- `mine` (string, optional) — Lọc theo người tạo (`true`/`1`/`yes`)
- `page` (string, optional)
- `limit` (string, optional)
- `sort` (string, optional)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "long",
        "receiptCode": "string",
        "supplierId": "long",
        "supplierName": "string",
        "staffId": "int",
        "staffName": "string",
        "receiptDate": "LocalDate",
        "status": "string",
        "invoiceNumber": "string",
        "totalAmount": "BigDecimal",
        "lineCount": "int",
        "notes": "string",
        "approvedBy": "Integer",
        "approvedByName": "string",
        "approvedAt": "Instant",
        "reviewedBy": "Integer",
        "reviewedByName": "string",
        "reviewedAt": "Instant",
        "rejectionReason": "string",
        "createdAt": "Instant",
        "updatedAt": "Instant"
      }
    ],
    "page": "int",
    "limit": "int",
    "total": "long"
  },
  "message": "Thành công"
}
```

**Errors:** 401, 403

---

### POST /api/v1/stock-receipts

**Mô tả:** Tạo phiếu nhập kho mới.

**Auth:** JWT + `can_manage_inventory`

**Request body:**
```json
{
  "supplierId": "int (required) — ID nhà cung cấp",
  "receiptDate": "string (required, pattern: yyyy-MM-dd) — Ngày nhập",
  "invoiceNumber": "string (max 100, optional) — Số hóa đơn",
  "notes": "string (optional) — Ghi chú",
  "saveMode": "string (required) — draft | pending",
  "details": [
    {
      "productId": "int (required)",
      "unitId": "int (required)",
      "quantity": "int (required)",
      "costPrice": "BigDecimal (required, >= 0)",
      "batchNumber": "string (optional)",
      "expiryDate": "string (optional, pattern: yyyy-MM-dd)"
    }
  ]
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "receiptCode": "string",
    "supplierId": "long",
    "supplierName": "string",
    "staffId": "int",
    "staffName": "string",
    "receiptDate": "LocalDate",
    "status": "string",
    "invoiceNumber": "string",
    "totalAmount": "BigDecimal",
    "notes": "string",
    "approvedBy": "Integer",
    "approvedByName": "string",
    "approvedAt": "Instant",
    "reviewedBy": "Integer",
    "reviewedByName": "string",
    "reviewedAt": "Instant",
    "rejectionReason": "string",
    "createdAt": "Instant",
    "updatedAt": "Instant",
    "details": [
      {
        "id": "long",
        "receiptId": "long",
        "productId": "int",
        "productName": "string",
        "skuCode": "string",
        "unitId": "int",
        "unitName": "string",
        "quantity": "int",
        "costPrice": "BigDecimal",
        "batchNumber": "string",
        "expiryDate": "LocalDate",
        "lineTotal": "BigDecimal"
      }
    ]
  },
  "message": "Đã tạo phiếu nhập kho"
}
```

**Errors:** 400 (validation), 401, 403

---

### GET /api/v1/stock-receipts/{id}

**Mô tả:** Chi tiết phiếu nhập kho.

**Auth:** JWT + `can_manage_inventory`

**Path params:**
- `id` (long, required)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "receiptCode": "string",
    "supplierId": "long",
    "supplierName": "string",
    "staffId": "int",
    "staffName": "string",
    "receiptDate": "LocalDate",
    "status": "string",
    "invoiceNumber": "string",
    "totalAmount": "BigDecimal",
    "notes": "string",
    "approvedBy": "Integer",
    "approvedByName": "string",
    "approvedAt": "Instant",
    "reviewedBy": "Integer",
    "reviewedByName": "string",
    "reviewedAt": "Instant",
    "rejectionReason": "string",
    "createdAt": "Instant",
    "updatedAt": "Instant",
    "details": [
      {
        "id": "long",
        "receiptId": "long",
        "productId": "int",
        "productName": "string",
        "skuCode": "string",
        "unitId": "int",
        "unitName": "string",
        "quantity": "int",
        "costPrice": "BigDecimal",
        "batchNumber": "string",
        "expiryDate": "LocalDate",
        "lineTotal": "BigDecimal"
      }
    ]
  },
  "message": "Thành công"
}
```

**Errors:** 400, 401, 403

---

### PATCH /api/v1/stock-receipts/{id}

**Mô tả:** Cập nhật phiếu nhập kho (partial).

**Auth:** JWT + `can_manage_inventory`

**Path params:**
- `id` (long, required)

**Request body:**
```json
{
  "supplierId": "int (optional)",
  "receiptDate": "string (optional, yyyy-MM-dd)",
  "invoiceNumber": "string (optional)",
  "notes": "string (optional)",
  "details": [
    {
      "productId": "int (required)",
      "unitId": "int (required)",
      "quantity": "int (required)",
      "costPrice": "BigDecimal (required, >= 0)",
      "batchNumber": "string (optional)",
      "expiryDate": "string (optional, yyyy-MM-dd)"
    }
  ]
}
```

**Response 200:**
```json
{
  "success": true,
  "data": { "...StockReceiptViewData" },
  "message": "Đã cập nhật phiếu nhập kho"
}
```

**Errors:** 400, 401, 403

---

### DELETE /api/v1/stock-receipts/{id}

**Mô tả:** Xóa phiếu nhập kho.

**Auth:** JWT + `can_manage_inventory`

**Path params:**
- `id` (long, required)

**Response 200:**
```json
{
  "success": true,
  "data": null,
  "message": "Đã xóa phiếu nhập kho"
}
```

**Errors:** 400, 401, 403

---

### POST /api/v1/stock-receipts/{id}/submit

**Mô tả:** Gửi yêu cầu duyệt phiếu nhập kho.

**Auth:** JWT + `can_manage_inventory`

**Path params:**
- `id` (long, required)

**Response 200:**
```json
{
  "success": true,
  "data": { "...StockReceiptViewData" },
  "message": "Đã gửi yêu cầu duyệt"
}
```

**Errors:** 400, 401, 403

---

### POST /api/v1/stock-receipts/{id}/approve

**Mô tả:** Phê duyệt phiếu nhập kho.

**Auth:** JWT + `can_approve`

**Path params:**
- `id` (long, required)

**Request body:**
```json
{
  "inboundLocationId": "int (required) — ID vị trí nhập"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": { "...StockReceiptViewData" },
  "message": "Đã phê duyệt phiếu nhập kho"
}
```

**Errors:** 400, 401, 403

---

### POST /api/v1/stock-receipts/{id}/reject

**Mô tả:** Từ chối phiếu nhập kho.

**Auth:** JWT + `can_approve`

**Path params:**
- `id` (long, required)

**Request body:**
```json
{
  "reason": "string (required, min 15, max 2000) — Lý do từ chối"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": { "...StockReceiptViewData" },
  "message": "Đã từ chối phiếu nhập kho"
}
```

**Errors:** 400, 401, 403

---

## StockDispatchesController — `/api/v1/stock-dispatches`

### GET /api/v1/stock-dispatches

**Mô tả:** Danh sách phiếu xuất kho phân trang.

**Auth:** JWT + `can_manage_inventory`

**Query params:**
- `search` (string, optional)
- `status` (string, optional)
- `dateFrom` (string, optional)
- `dateTo` (string, optional)
- `mine` (boolean, default: false) — Lọc theo người tạo
- `page` (int, default: 1)
- `limit` (int, default: 20)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "long",
        "dispatchCode": "string",
        "orderCode": "string",
        "customerName": "string",
        "dispatchDate": "LocalDate",
        "userName": "string",
        "itemCount": "int",
        "status": "string",
        "createdByUserId": "int",
        "manualDispatch": "boolean",
        "hasStockDispatchLines": "boolean",
        "shortageWarning": "boolean",
        "canEdit": "boolean",
        "canDelete": "boolean"
      }
    ],
    "page": "int",
    "limit": "int",
    "total": "long"
  },
  "message": "Thành công"
}
```

**Errors:** 401, 403

---

### GET /api/v1/stock-dispatches/{id}

**Mô tả:** Chi tiết phiếu xuất kho.

**Auth:** JWT + `can_manage_inventory`

**Path params:**
- `id` (long, required)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "dispatchCode": "string",
    "orderCode": "string",
    "customerName": "string",
    "dispatchDate": "LocalDate",
    "userId": "int",
    "userName": "string",
    "status": "string",
    "notes": "string",
    "referenceLabel": "string",
    "manualDispatch": "boolean",
    "stockLinesFulfillment": "boolean",
    "shortageWarning": "boolean",
    "lines": [
      {
        "lineId": "long",
        "inventoryId": "long",
        "productId": "long",
        "quantity": "int",
        "availableQuantity": "int",
        "shortageLine": "boolean",
        "productName": "string",
        "skuCode": "string",
        "warehouseCode": "string",
        "shelfCode": "string",
        "unitPriceSnapshot": "BigDecimal"
      }
    ],
    "canEdit": "boolean",
    "canDelete": "boolean",
    "deletedAt": "Instant",
    "deletedByUserId": "Integer",
    "deletedByUserName": "string",
    "deleteReason": "string"
  },
  "message": "Thành công"
}
```

**Errors:** 400, 401, 403

---

### POST /api/v1/stock-dispatches

**Mô tả:** Tạo phiếu xuất kho thủ công từ dòng tồn.

**Auth:** JWT + `can_manage_inventory`

**Request body:**
```json
{
  "dispatchDate": "LocalDate (required) — Ngày xuất",
  "referenceLabel": "string (max 255, optional)",
  "notes": "string (max 2000, optional)",
  "lines": [
    {
      "inventoryId": "long (required, > 0)",
      "quantity": "int (required, > 0)",
      "unitPriceSnapshot": "BigDecimal (optional)"
    }
  ]
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "dispatchCode": "string",
    "dispatchDate": "LocalDate",
    "status": "string",
    "referenceLabel": "string"
  },
  "message": "Đã tạo phiếu xuất kho"
}
```

**Errors:** 400, 401, 403

---

### POST /api/v1/stock-dispatches/from-order

**Mô tả:** Tạo phiếu xuất kho gắn với đơn hàng.

**Auth:** JWT + `can_manage_inventory`

**Request body:**
```json
{
  "orderId": "int (required, > 0) — ID đơn hàng",
  "dispatchDate": "LocalDate (required)",
  "notes": "string (max 2000, optional)",
  "lines": [
    {
      "inventoryId": "long (required, > 0)",
      "quantity": "int (required, > 0)",
      "unitPriceSnapshot": "BigDecimal (required)"
    }
  ]
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "dispatchCode": "string",
    "dispatchDate": "LocalDate",
    "status": "string",
    "referenceLabel": "string"
  },
  "message": "Đã tạo phiếu xuất kho gắn đơn"
}
```

**Errors:** 400, 401, 403

---

### POST /api/v1/stock-dispatches/{id}/approve

**Mô tả:** Duyệt phiếu xuất kho (chuyển sang chờ xuất).

**Auth:** JWT + `can_manage_inventory`

**Path params:**
- `id` (long, required)

**Response 200:**
```json
{
  "success": true,
  "data": { "...StockDispatchDetailData" },
  "message": "Đã duyệt phiếu — chuyển sang chờ xuất"
}
```

**Errors:** 400, 401, 403

---

### PATCH /api/v1/stock-dispatches/{id}

**Mô tả:** Cập nhật phiếu xuất kho thủ công.

**Auth:** JWT + `can_manage_inventory`

**Path params:**
- `id` (long, required)

**Request body:**
```json
{
  "dispatchDate": "LocalDate (optional)",
  "notes": "string (max 2000, optional)",
  "referenceLabel": "string (max 255, optional)",
  "status": "string (optional)",
  "lines": [
    {
      "inventoryId": "long (> 0)",
      "quantity": "int (> 0)",
      "unitPriceSnapshot": "BigDecimal (optional)"
    }
  ]
}
```

**Response 200:**
```json
{
  "success": true,
  "data": { "...StockDispatchDetailData" },
  "message": "Đã cập nhật phiếu xuất kho"
}
```

**Errors:** 400, 401, 403

---

### POST /api/v1/stock-dispatches/{id}/soft-delete

**Mô tả:** Xóa mềm phiếu xuất kho kèm lý do.

**Auth:** JWT + `can_manage_inventory`

**Path params:**
- `id` (long, required)

**Request body:**
```json
{
  "reason": "string (required, min 3, max 2000) — Lý do xóa"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {},
  "message": "Đã xóa mềm phiếu xuất kho"
}
```

**Errors:** 400, 401, 403

---

## AuditSessionsController — `/api/v1/inventory/audit-sessions`

### GET /api/v1/inventory/audit-sessions

**Mô tả:** Danh sách đợt kiểm kê phân trang.

**Auth:** JWT + `can_manage_inventory`

**Query params:**
- `search` (string, optional)
- `status` (string, optional)
- `dateFrom` (string, optional)
- `dateTo` (string, optional)
- `page` (string, optional)
- `limit` (string, optional)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "long",
        "auditCode": "string",
        "title": "string",
        "auditDate": "LocalDate",
        "status": "string",
        "locationFilter": "string",
        "categoryFilter": "string",
        "createdBy": "int",
        "createdByName": "string",
        "completedAt": "Instant",
        "completedByName": "string",
        "createdAt": "Instant",
        "updatedAt": "Instant",
        "totalLines": "int",
        "countedLines": "int",
        "varianceLines": "int"
      }
    ],
    "page": "int",
    "limit": "int",
    "total": "long"
  },
  "message": "Thành công"
}
```

**Errors:** 401, 403

---

### POST /api/v1/inventory/audit-sessions

**Mô tả:** Tạo đợt kiểm kê mới.

**Auth:** JWT + `can_manage_inventory`

**Request body:**
```json
{
  "title": "string (required, max 255) — Tiêu đề",
  "auditDate": "string (required, pattern: yyyy-MM-dd)",
  "notes": "string (max 2000, optional)",
  "scope": {
    "mode": "string (required) — Phạm vi (vd: all, location, category, custom)",
    "locationIds": "int[] (optional)",
    "categoryId": "int (optional)",
    "inventoryIds": "int[] (optional)"
  }
}
```

**Response 201:**
```json
{
  "success": true,
  "data": { "...AuditSessionDetailData" },
  "message": "Đã tạo đợt kiểm kê"
}
```

**Errors:** 400, 401, 403

---

### GET /api/v1/inventory/audit-sessions/{id}

**Mô tả:** Chi tiết đợt kiểm kê kèm danh sách dòng kiểm kê và sự kiện.

**Auth:** JWT + `can_manage_inventory`

**Path params:**
- `id` (long, required)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "auditCode": "string",
    "title": "string",
    "auditDate": "LocalDate",
    "status": "string",
    "locationFilter": "string",
    "categoryFilter": "string",
    "notes": "string",
    "createdBy": "int",
    "createdByName": "string",
    "completedAt": "Instant",
    "completedByName": "string",
    "cancelReason": "string",
    "createdAt": "Instant",
    "updatedAt": "Instant",
    "ownerNotes": "string",
    "events": [
      {
        "id": "long",
        "eventType": "string",
        "payload": "string (JSON)",
        "createdBy": "int",
        "createdAt": "Instant"
      }
    ],
    "items": [
      {
        "id": "long",
        "auditSessionId": "long",
        "inventoryId": "long",
        "productId": "int",
        "productName": "string",
        "skuCode": "string",
        "unitName": "string",
        "locationId": "int",
        "warehouseCode": "string",
        "shelfCode": "string",
        "batchNumber": "string",
        "systemQuantity": "BigDecimal",
        "actualQuantity": "BigDecimal",
        "variance": "BigDecimal",
        "variancePercent": "BigDecimal",
        "isCounted": "boolean",
        "notes": "string"
      }
    ]
  },
  "message": "Thành công"
}
```

**Errors:** 400, 401, 403

---

### PATCH /api/v1/inventory/audit-sessions/{id}

**Mô tả:** Cập nhật thông tin đợt kiểm kê.

**Auth:** JWT + `can_manage_inventory`

**Path params:**
- `id` (long, required)

**Request body:**
```json
{
  "title": "string (min 1, max 255, optional)",
  "notes": "string (max 2000, optional)",
  "ownerNotes": "string (max 2000, optional)",
  "status": "string (optional)"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": { "...AuditSessionDetailData" },
  "message": "Đã cập nhật đợt kiểm kê"
}
```

**Errors:** 400, 401, 403

---

### PATCH /api/v1/inventory/audit-sessions/{id}/lines

**Mô tả:** Cập nhật số lượng kiểm đếm thực tế cho các dòng kiểm kê.

**Auth:** JWT + `can_manage_inventory`

**Path params:**
- `id` (long, required)

**Request body:**
```json
{
  "lines": [
    {
      "lineId": "long (required, > 0) — ID dòng kiểm kê",
      "actualQuantity": "BigDecimal (required, >= 0) — Số lượng thực tế",
      "notes": "string (max 500, optional)"
    }
  ]
}
```

**Response 200:**
```json
{
  "success": true,
  "data": { "...AuditSessionDetailData" },
  "message": "Đã cập nhật dòng kiểm kê"
}
```

**Errors:** 400, 401, 403

---

### POST /api/v1/inventory/audit-sessions/{id}/complete

**Mô tả:** Hoàn tất kiểm kê, gửi chờ Owner duyệt.

**Auth:** JWT + `can_manage_inventory`

**Path params:**
- `id` (long, required)

**Request body:**
```json
{
  "requireAllCounted": "boolean (optional, default: true)"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": { "...AuditSessionDetailData" },
  "message": "Đã gửi đợt kiểm kê chờ Owner duyệt"
}
```

**Errors:** 400, 401, 403

---

### POST /api/v1/inventory/audit-sessions/{id}/approve

**Mô tả:** Owner duyệt hoàn thành đợt kiểm kê.

**Auth:** JWT + `can_manage_inventory`

**Path params:**
- `id` (long, required)

**Request body:**
```json
{
  "notes": "string (max 500, optional)"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": { "...AuditSessionDetailData" },
  "message": "Owner đã duyệt hoàn thành"
}
```

**Errors:** 400, 401, 403

---

### POST /api/v1/inventory/audit-sessions/{id}/reject

**Mô tả:** Owner từ chối — trả về In Progress.

**Auth:** JWT + `can_manage_inventory`

**Path params:**
- `id` (long, required)

**Request body:**
```json
{
  "notes": "string (max 500, optional)"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": { "...AuditSessionDetailData" },
  "message": "Owner đã từ chối — trả về In Progress"
}
```

**Errors:** 400, 401, 403

---

### DELETE /api/v1/inventory/audit-sessions/{id}

**Mô tả:** Xóa mềm đợt kiểm kê.

**Auth:** JWT + `can_manage_inventory`

**Path params:**
- `id` (long, required)

**Response 200:**
```json
{
  "success": true,
  "data": null,
  "message": "Đã xóa mềm đợt kiểm kê"
}
```

**Errors:** 400, 401, 403

---

### POST /api/v1/inventory/audit-sessions/{id}/cancel

**Mô tả:** Hủy đợt kiểm kê kèm lý do.

**Auth:** JWT + `can_manage_inventory`

**Path params:**
- `id` (long, required)

**Request body:**
```json
{
  "cancelReason": "string (required, max 1000) — Lý do hủy"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": { "...AuditSessionDetailData" },
  "message": "Đã hủy đợt kiểm kê"
}
```

**Errors:** 400, 401, 403

---

### POST /api/v1/inventory/audit-sessions/{id}/apply-variance

**Mô tả:** Áp chênh lệch kiểm kê lên tồn kho.

**Auth:** JWT + `can_manage_inventory`

**Path params:**
- `id` (long, required)

**Request body:**
```json
{
  "reason": "string (required, max 500) — Lý do áp chênh lệch",
  "mode": "string (optional, pattern: delta|set_actual, default: delta)"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "sessionId": "long",
    "appliedLines": [
      {
        "lineId": "long",
        "inventoryId": "long",
        "deltaQty": "int — Chênh lệch số lượng",
        "quantityAfter": "int — Số lượng sau khi áp"
      }
    ]
  },
  "message": "Đã áp chênh lệch kiểm kê lên tồn kho"
}
```

**Errors:** 400, 401, 403

---

## ApprovalsController — `/api/v1/approvals`

### GET /api/v1/approvals/pending

**Mô tả:** Danh sách yêu cầu chờ phê duyệt (Owner/Admin).

**Auth:** JWT + Owner/Admin

**Query params:**
- `search` (string, optional)
- `type` (string, optional)
- `fromDate` (string, optional)
- `toDate` (string, optional)
- `page` (string, optional)
- `limit` (string, optional)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "totalPending": "long — Tổng số chờ duyệt",
      "byType": "object — Map<type, count>"
    },
    "items": [
      {
        "entityType": "string — Loại (receipt, dispatch, audit...)",
        "entityId": "long",
        "transactionCode": "string — Mã giao dịch",
        "type": "string",
        "creatorName": "string — Người tạo",
        "date": "Instant",
        "totalAmount": "BigDecimal",
        "status": "string",
        "notes": "string"
      }
    ],
    "page": "int",
    "limit": "int",
    "total": "long"
  },
  "message": "Thành công"
}
```

**Errors:** 401, 403

---

### GET /api/v1/approvals/history

**Mô tả:** Lịch sử phê duyệt (Owner/Admin).

**Auth:** JWT + Owner/Admin

**Query params:**
- `resolution` (string, optional) — Lọc theo kết quả (approved/rejected)
- `search` (string, optional)
- `type` (string, optional)
- `fromDate` (string, optional)
- `toDate` (string, optional)
- `page` (string, optional)
- `limit` (string, optional)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "entityType": "string",
        "entityId": "long",
        "transactionCode": "string",
        "type": "string",
        "creatorName": "string",
        "date": "Instant",
        "reviewedAt": "Instant",
        "totalAmount": "BigDecimal",
        "resolution": "string — approved | rejected",
        "rejectionReason": "string",
        "notes": "string",
        "reviewedByUserId": "Integer",
        "reviewerName": "string",
        "approvedByUserId": "Integer",
        "approvedAt": "Instant"
      }
    ],
    "page": "int",
    "limit": "int",
    "total": "long"
  },
  "message": "Thành công"
}
```

**Errors:** 401, 403
