# Finance API Contracts

Base path: `/api/v1`

> Response envelope: `{ success: boolean, data: T, message: string }`

---

## GET /api/v1/finance-ledger

**Mô tả:** Danh sách sổ cái tài chính (ledger entries).

**Auth:** JWT + Admin

**Query parameters:**
| Tên | Kiểu | Bắt buộc | Mô tả |
|-----|------|----------|-------|
| dateFrom | string | Không | Lọc từ ngày (yyyy-MM-dd) |
| dateTo | string | Không | Lọc đến ngày (yyyy-MM-dd) |
| transactionType | string | Không | Loại giao dịch |
| referenceType | string | Không | Loại tham chiếu |
| search | string | Không | Từ khóa tìm kiếm |
| page | string | Không | Số trang (bắt đầu từ 1) |
| limit | string | Không | Số bản ghi mỗi trang |

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "long",
        "date": "string — Ngày hạch toán",
        "transactionCode": "string — Mã giao dịch",
        "description": "string — Diễn giải",
        "transactionType": "string — Loại giao dịch",
        "referenceType": "string — Loại tham chiếu",
        "referenceId": "int — ID tham chiếu",
        "amount": "BigDecimal — Số tiền",
        "debit": "BigDecimal — Nợ",
        "credit": "BigDecimal — Có",
        "balance": "BigDecimal — Số dư"
      }
    ],
    "page": "int",
    "limit": "int",
    "total": "long"
  },
  "message": "Thành công"
}
```

**Errors:** 401 (thiếu JWT), 403 (không phải Admin)

---

## GET /api/v1/cash-transactions

**Mô tả:** Danh sách giao dịch thu chi.

**Auth:** JWT (người dùng có quyền xem tài chính)

**Query parameters:**
| Tên | Kiểu | Bắt buộc | Mô tả |
|-----|------|----------|-------|
| type | string | Không | Loại (IN/OUT) |
| status | string | Không | Trạng thái |
| dateFrom | string | Không | Từ ngày (yyyy-MM-dd) |
| dateTo | string | Không | Đến ngày (yyyy-MM-dd) |
| fundId | string | Không | ID quỹ |
| search | string | Không | Từ khóa tìm kiếm |
| page | string | Không | Số trang |
| limit | string | Không | Số bản ghi mỗi trang |

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "long",
        "transactionCode": "string — Mã giao dịch",
        "direction": "string — IN (thu) / OUT (chi)",
        "amount": "BigDecimal — Số tiền",
        "category": "string — Danh mục",
        "description": "string — Mô tả",
        "paymentMethod": "string — Phương thức thanh toán",
        "status": "string — Trạng thái",
        "transactionDate": "string — Ngày giao dịch",
        "financeLedgerId": "long — ID sổ cái (nếu đã ghi sổ)",
        "createdBy": "int — ID người tạo",
        "createdByName": "string — Tên người tạo",
        "performedBy": "int — ID người thực hiện",
        "performedByName": "string — Tên người thực hiện",
        "createdAt": "string — Thời điểm tạo",
        "updatedAt": "string — Thời điểm cập nhật",
        "fundId": "int — ID quỹ",
        "fundCode": "string — Mã quỹ"
      }
    ],
    "page": "int",
    "limit": "int",
    "total": "long"
  },
  "message": "Thành công"
}
```

**Errors:** 401 (thiếu JWT), 403 (thiếu quyền)

---

## POST /api/v1/cash-transactions

**Mô tả:** Tạo giao dịch thu chi mới.

**Auth:** JWT (người dùng có quyền xem tài chính)

**Request body:**
```json
{
  "direction": "string (required) — IN (thu) / OUT (chi)",
  "amount": "BigDecimal (required, > 0) — Số tiền",
  "category": "string (max 500, required) — Danh mục",
  "description": "string (max 2000) — Mô tả",
  "paymentMethod": "string (max 30) — Phương thức thanh toán",
  "transactionDate": "string (date, required) — Ngày giao dịch (yyyy-MM-dd)",
  "fundId": "int (required) — ID quỹ",
  "status": "string — Trạng thái (mặc định theo BR-12)"
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "transactionCode": "string",
    "direction": "string",
    "amount": "BigDecimal",
    "category": "string",
    "description": "string",
    "paymentMethod": "string",
    "status": "string",
    "transactionDate": "string",
    "financeLedgerId": "long",
    "createdBy": "int",
    "createdByName": "string",
    "performedBy": "int",
    "performedByName": "string",
    "createdAt": "string",
    "updatedAt": "string",
    "fundId": "int",
    "fundCode": "string"
  },
  "message": "Đã tạo giao dịch"
}
```

**Errors:** 400 (validation), 401 (thiếu JWT), 403 (thiếu quyền)

---

## GET /api/v1/cash-transactions/{id}

**Mô tả:** Chi tiết một giao dịch thu chi.

**Auth:** JWT (người dùng có quyền xem tài chính)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "transactionCode": "string",
    "direction": "string",
    "amount": "BigDecimal",
    "category": "string",
    "description": "string",
    "paymentMethod": "string",
    "status": "string",
    "transactionDate": "string",
    "financeLedgerId": "long",
    "createdBy": "int",
    "createdByName": "string",
    "performedBy": "int",
    "performedByName": "string",
    "createdAt": "string",
    "updatedAt": "string",
    "fundId": "int",
    "fundCode": "string"
  },
  "message": "Thành công"
}
```

**Errors:** 401 (thiếu JWT), 403 (thiếu quyền), 404 (không tìm thấy)

---

## PATCH /api/v1/cash-transactions/{id}

**Mô tả:** Cập nhật một phần giao dịch thu chi.

**Auth:** JWT (người dùng có quyền xem tài chính)

**Request body:** (JSON object, chỉ gửi các field cần cập nhật)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "transactionCode": "string",
    "direction": "string",
    "amount": "BigDecimal",
    "category": "string",
    "description": "string",
    "paymentMethod": "string",
    "status": "string",
    "transactionDate": "string",
    "financeLedgerId": "long",
    "createdBy": "int",
    "createdByName": "string",
    "performedBy": "int",
    "performedByName": "string",
    "createdAt": "string",
    "updatedAt": "string",
    "fundId": "int",
    "fundCode": "string"
  },
  "message": "Thành công"
}
```

**Errors:** 400 (validation), 401 (thiếu JWT), 403 (thiếu quyền), 404 (không tìm thấy)

---

## DELETE /api/v1/cash-transactions/{id}

**Mô tả:** Xóa một giao dịch thu chi.

**Auth:** JWT (người dùng có quyền xem tài chính)

**Response 200:**
```json
{
  "success": true,
  "data": {},
  "message": "Đã xóa giao dịch"
}
```

**Errors:** 401 (thiếu JWT), 403 (thiếu quyền), 404 (không tìm thấy)

---

## GET /api/v1/cashflow/movements

**Mô tả:** Danh sách dòng tiền thống nhất (Admin-only).

**Auth:** JWT + Admin

**Query parameters:**
| Tên | Kiểu | Bắt buộc | Mô tả |
|-----|------|----------|-------|
| dateFrom | string | Không | Từ ngày (yyyy-MM-dd) |
| dateTo | string | Không | Đến ngày (yyyy-MM-dd) |
| fundId | string | Không | ID quỹ |
| search | string | Không | Từ khóa tìm kiếm |
| page | string | Không | Số trang |
| limit | string | Không | Số bản ghi mỗi trang |

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "string — ID unique",
        "sourceKind": "string — Loại nguồn (ledger/pending/cancelled)",
        "transactionDate": "string — Ngày giao dịch",
        "amount": "BigDecimal — Số tiền",
        "direction": "string — IN / OUT",
        "description": "string — Diễn giải",
        "referenceType": "string — Loại tham chiếu",
        "referenceId": "int — ID tham chiếu",
        "fundId": "int — ID quỹ",
        "fundCode": "string — Mã quỹ",
        "cashTransactionId": "long — ID giao dịch thu chi",
        "status": "string — Trạng thái",
        "category": "string — Danh mục"
      }
    ],
    "page": "int",
    "limit": "int",
    "total": "long",
    "summary": {
      "totalIncome": "BigDecimal — Tổng thu",
      "totalExpense": "BigDecimal — Tổng chi",
      "net": "BigDecimal — Chênh lệch"
    }
  },
  "message": "Thao tác thành công"
}
```

**Errors:** 401 (thiếu JWT), 403 (không phải Admin)

---

## GET /api/v1/cash-funds

**Mô tả:** Danh sách quỹ tiền đang hoạt động.

**Auth:** JWT (người dùng có quyền xem tài chính)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "int",
        "code": "string — Mã quỹ",
        "name": "string — Tên quỹ",
        "isDefault": "boolean — Quỹ mặc định",
        "isActive": "boolean — Đang hoạt động"
      }
    ]
  },
  "message": "Thao tác thành công"
}
```

**Errors:** 401 (thiếu JWT), 403 (thiếu quyền)

---

## POST /api/v1/cash-funds

**Mô tả:** Tạo quỹ tiền mới.

**Auth:** JWT + Admin

**Request body:**
```json
{
  "code": "string (max 30, required) — Mã quỹ",
  "name": "string (max 255, required) — Tên quỹ",
  "isDefault": "boolean — Đặt làm mặc định"
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "code": "string",
    "name": "string",
    "isDefault": "boolean",
    "isActive": "boolean"
  },
  "message": "Đã tạo quỹ"
}
```

**Errors:** 400 (validation), 401 (thiếu JWT), 403 (không phải Admin)

---

## PATCH /api/v1/cash-funds/{id}

**Mô tả:** Cập nhật quỹ tiền (vô hiệu hóa / đặt mặc định).

**Auth:** JWT + Admin

**Request body:**
```json
{
  "isActive": "boolean — Kích hoạt / vô hiệu hóa",
  "isDefault": "boolean — Đặt làm mặc định"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "code": "string",
    "name": "string",
    "isDefault": "boolean",
    "isActive": "boolean"
  },
  "message": "Thành công"
}
```

**Errors:** 400 (validation), 401 (thiếu JWT), 403 (không phải Admin), 404 (không tìm thấy)

---

## GET /api/v1/debts

**Mô tả:** Danh sách sổ nợ đối tác.

**Auth:** JWT (người dùng có quyền xem tài chính)

**Query parameters:**
| Tên | Kiểu | Bắt buộc | Mô tả |
|-----|------|----------|-------|
| partnerType | string | Không | Loại đối tác (CUSTOMER/SUPPLIER) |
| status | string | Không | Trạng thái nợ |
| dueDateFrom | string | Không | Từ ngày đến hạn (yyyy-MM-dd) |
| dueDateTo | string | Không | Đến ngày đến hạn (yyyy-MM-dd) |
| search | string | Không | Từ khóa tìm kiếm |
| page | string | Không | Số trang |
| limit | string | Không | Số bản ghi mỗi trang |

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "long",
        "debtCode": "string — Mã khoản nợ",
        "partnerType": "string — CUSTOMER / SUPPLIER",
        "customerId": "long — ID khách hàng",
        "supplierId": "long — ID nhà cung cấp",
        "partnerName": "string — Tên đối tác",
        "totalAmount": "BigDecimal — Tổng số nợ",
        "paidAmount": "BigDecimal — Đã trả",
        "remainingAmount": "BigDecimal — Còn lại",
        "dueDate": "string — Ngày đến hạn",
        "status": "string — Trạng thái",
        "notes": "string — Ghi chú",
        "createdAt": "string — Thời điểm tạo",
        "updatedAt": "string — Thời điểm cập nhật"
      }
    ],
    "page": "int",
    "limit": "int",
    "total": "long"
  },
  "message": "Thành công"
}
```

**Errors:** 401 (thiếu JWT), 403 (thiếu quyền)

---

## POST /api/v1/debts

**Mô tả:** Tạo khoản nợ đối tác mới.

**Auth:** JWT (người dùng có quyền xem tài chính)

**Request body:**
```json
{
  "partnerType": "string (required) — CUSTOMER (khách nợ) / SUPPLIER (nợ NCC)",
  "customerId": "int — ID khách hàng (nếu partnerType=CUSTOMER)",
  "supplierId": "int — ID nhà cung cấp (nếu partnerType=SUPPLIER)",
  "totalAmount": "BigDecimal (required, >= 0) — Tổng số nợ",
  "paidAmount": "BigDecimal (>= 0) — Đã trả",
  "dueDate": "string (date) — Ngày đến hạn (yyyy-MM-dd)",
  "notes": "string — Ghi chú"
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "debtCode": "string",
    "partnerType": "string",
    "customerId": "long",
    "supplierId": "long",
    "partnerName": "string",
    "totalAmount": "BigDecimal",
    "paidAmount": "BigDecimal",
    "remainingAmount": "BigDecimal",
    "dueDate": "string",
    "status": "string",
    "notes": "string",
    "createdAt": "string",
    "updatedAt": "string"
  },
  "message": "Đã tạo khoản nợ"
}
```

**Errors:** 400 (validation), 401 (thiếu JWT), 403 (thiếu quyền)

---

## GET /api/v1/debts/{id}

**Mô tả:** Chi tiết một khoản nợ đối tác.

**Auth:** JWT (người dùng có quyền xem tài chính)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "debtCode": "string",
    "partnerType": "string",
    "customerId": "long",
    "supplierId": "long",
    "partnerName": "string",
    "totalAmount": "BigDecimal",
    "paidAmount": "BigDecimal",
    "remainingAmount": "BigDecimal",
    "dueDate": "string",
    "status": "string",
    "notes": "string",
    "createdAt": "string",
    "updatedAt": "string"
  },
  "message": "Thành công"
}
```

**Errors:** 401 (thiếu JWT), 403 (thiếu quyền), 404 (không tìm thấy)

---

## PATCH /api/v1/debts/{id}

**Mô tả:** Cập nhật một phần khoản nợ đối tác.

**Auth:** JWT (người dùng có quyền xem tài chính)

**Request body:** (JSON object, chỉ gửi các field cần cập nhật)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "debtCode": "string",
    "partnerType": "string",
    "customerId": "long",
    "supplierId": "long",
    "partnerName": "string",
    "totalAmount": "BigDecimal",
    "paidAmount": "BigDecimal",
    "remainingAmount": "BigDecimal",
    "dueDate": "string",
    "status": "string",
    "notes": "string",
    "createdAt": "string",
    "updatedAt": "string"
  },
  "message": "Đã cập nhật khoản nợ"
}
```

**Errors:** 400 (validation), 401 (thiếu JWT), 403 (thiếu quyền), 404 (không tìm thấy)
