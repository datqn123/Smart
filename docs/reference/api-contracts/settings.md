# Settings API Contracts

Base path: `/api/v1`

> Response envelope: `{ success: boolean, data: T, message: string }`

---

## Store Profile

### GET /api/v1/store-profile

**Mô tả:** Lấy thông tin hồ sơ cửa hàng.

**Auth:** JWT

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "name": "string — Tên cửa hàng",
    "businessCategory": "string — Ngành nghề kinh doanh",
    "address": "string — Địa chỉ",
    "phone": "string — Số điện thoại",
    "email": "string — Email",
    "website": "string — Website",
    "taxCode": "string — Mã số thuế",
    "footerNote": "string — Ghi chú cuối hóa đơn",
    "logoUrl": "string — URL logo",
    "facebookUrl": "string — URL Facebook",
    "instagramHandle": "string — Instagram handle",
    "defaultRetailLocationId": "int — ID vị trí bán lẻ mặc định",
    "updatedAt": "string (ISO instant) — Thời gian cập nhật"
  },
  "message": "Thành công"
}
```

**Errors:** 401 (thiếu JWT)

---

### PATCH /api/v1/store-profile

**Mô tả:** Cập nhật thông tin hồ sơ cửa hàng.

**Auth:** JWT + Admin

**Request body:** (các trường không bắt buộc, chỉ gửi những trường cần thay đổi)
```json
{
  "name": "string — Tên cửa hàng",
  "businessCategory": "string — Ngành nghề kinh doanh",
  "address": "string — Địa chỉ",
  "phone": "string — Số điện thoại",
  "email": "string — Email",
  "website": "string — Website",
  "taxCode": "string — Mã số thuế",
  "footerNote": "string — Ghi chú cuối hóa đơn",
  "facebookUrl": "string — URL Facebook",
  "instagramHandle": "string — Instagram handle",
  "defaultRetailLocationId": "int — ID vị trí bán lẻ mặc định"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "name": "string",
    "businessCategory": "string",
    "address": "string",
    "phone": "string",
    "email": "string",
    "website": "string",
    "taxCode": "string",
    "footerNote": "string",
    "logoUrl": "string",
    "facebookUrl": "string",
    "instagramHandle": "string",
    "defaultRetailLocationId": "int",
    "updatedAt": "string (ISO instant)"
  },
  "message": "Đã cập nhật thông tin cửa hàng"
}
```

**Errors:** 400 (dữ liệu không hợp lệ), 401 (thiếu JWT), 403 (thiếu quyền)

---

### POST /api/v1/store-profile/logo

**Mô tả:** Tải lên logo cửa hàng (multipart).

**Auth:** JWT

**Headers:**
- `Content-Type: multipart/form-data`

**Request body:**
```
file: MultipartFile (required) — File ảnh logo
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "logoUrl": "string — URL logo sau khi upload",
    "updatedAt": "string (ISO instant) — Thời gian cập nhật"
  },
  "message": "Đã cập nhật logo"
}
```

**Errors:** 400 (file không hợp lệ), 401 (thiếu JWT)

---

## System Logs

### GET /api/v1/system-logs

**Mô tả:** Danh sách nhật ký hệ thống (phân trang).

**Auth:** JWT + Admin

**Query parameters:**
- `search` (string, optional) — Từ khóa tìm kiếm
- `module` (string, optional) — Lọc theo module
- `logLevel` (string, optional) — Lọc theo cấp độ log
- `dateFrom` (string, optional) — Từ ngày (ISO date)
- `dateTo` (string, optional) — Đến ngày (ISO date)
- `page` (int, optional) — Số trang (mặc định 1)
- `limit` (int, optional) — Số bản ghi mỗi trang (mặc định 10)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "long",
        "timestamp": "string — Thời gian",
        "user": "string — Người thực hiện",
        "action": "string — Hành động",
        "module": "string — Module",
        "description": "string — Mô tả",
        "severity": "string — Mức độ",
        "ipAddress": "string — Địa chỉ IP"
      }
    ],
    "page": "int — Trang hiện tại",
    "limit": "int — Số bản ghi mỗi trang",
    "total": "long — Tổng số bản ghi"
  },
  "message": "Thành công"
}
```

**Errors:** 401 (thiếu JWT), 403 (thiếu quyền)

---

### GET /api/v1/system-logs/{id}

**Mô tả:** Chi tiết nhật ký hệ thống.

**Auth:** JWT + Admin

**Path parameters:**
- `id` (long, required) — ID nhật ký

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "timestamp": "string — Thời gian",
    "user": "string — Người thực hiện",
    "action": "string — Hành động",
    "module": "string — Module",
    "description": "string — Mô tả chi tiết",
    "severity": "string — Mức độ",
    "ipAddress": "string — Địa chỉ IP",
    "stackTrace": "string — Stack trace (nếu có)",
    "contextData": "object — Dữ liệu ngữ cảnh (JSON)"
  },
  "message": "Thành công"
}
```

**Errors:** 401 (thiếu JWT), 403 (thiếu quyền), 404 (không tìm thấy)

---

### DELETE /api/v1/system-logs/{id}

**Mô tả:** Xóa nhật ký hệ thống.

**Auth:** JWT + Admin

**Path parameters:**
- `id` (long, required) — ID nhật ký

**Response 204:** No Content

**Errors:** 401 (thiếu JWT), 403 (thiếu quyền), 404 (không tìm thấy)

---

### POST /api/v1/system-logs/bulk-delete

**Mô tả:** Xóa hàng loạt nhật ký hệ thống.

**Auth:** JWT + Admin

**Request body:**
```json
{
  "ids": "long[] (tối đa 100 phần tử, required) — Danh sách ID nhật ký cần xóa"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "deletedCount": "int — Số bản ghi đã xóa"
  },
  "message": "Thành công"
}
```

**Errors:** 400 (dữ liệu không hợp lệ, ids tối đa 100 phần tử), 401 (thiếu JWT), 403 (thiếu quyền)

---

## Alert Settings

### GET /api/v1/alert-settings

**Mô tả:** Danh sách cấu hình cảnh báo.

**Auth:** JWT + Admin

**Query parameters:**
- `ownerId` (int, optional) — Lọc theo chủ sở hữu
- `alertType` (string, optional) — Lọc theo loại cảnh báo
- `isEnabled` (boolean, optional) — Lọc theo trạng thái bật/tắt

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "long",
        "alertType": "string — Loại cảnh báo (LowStock, ExpiryDate, HighValueTransaction, PendingApproval, OverStock, SalesOrderCreated, PartnerDebtDueSoon, SystemHealth)",
        "thresholdValue": "decimal — Ngưỡng cảnh báo",
        "channel": "string — Kênh gửi (App, Email, SMS, Zalo)",
        "frequency": "string — Tần suất (Realtime, Daily, Weekly)",
        "isEnabled": "boolean — Bật/tắt",
        "recipients": "string[] — Danh sách người nhận",
        "updatedAt": "string (ISO instant) — Thời gian cập nhật"
      }
    ]
  },
  "message": "Thành công"
}
```

**Errors:** 401 (thiếu JWT), 403 (thiếu quyền)

---

### POST /api/v1/alert-settings

**Mô tả:** Tạo mới cấu hình cảnh báo.

**Auth:** JWT + Admin

**Request body:**
```json
{
  "alertType": "string (required) — Loại cảnh báo (LowStock, ExpiryDate, HighValueTransaction, PendingApproval, OverStock, SalesOrderCreated, PartnerDebtDueSoon, SystemHealth)",
  "channel": "string (required) — Kênh gửi (App, Email, SMS, Zalo)",
  "frequency": "string (optional) — Tần suất (Realtime, Daily, Weekly)",
  "thresholdValue": "decimal (optional) — Ngưỡng cảnh báo",
  "isEnabled": "boolean (optional) — Bật/tắt",
  "recipients": "string[] (optional) — Danh sách người nhận"
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "alertType": "string",
    "thresholdValue": "decimal",
    "channel": "string",
    "frequency": "string",
    "isEnabled": "boolean",
    "recipients": "string[]",
    "updatedAt": "string (ISO instant)"
  },
  "message": "Thao tác thành công"
}
```

**Errors:** 400 (validation), 401 (thiếu JWT), 403 (thiếu quyền)

---

### PATCH /api/v1/alert-settings/{id}

**Mô tả:** Cập nhật cấu hình cảnh báo.

**Auth:** JWT + Admin

**Path parameters:**
- `id` (long, required) — ID cấu hình cảnh báo

**Request body:** (các trường không bắt buộc, chỉ gửi những trường cần thay đổi)
```json
{
  "alertType": "string — Loại cảnh báo",
  "channel": "string — Kênh gửi",
  "frequency": "string — Tần suất",
  "thresholdValue": "decimal — Ngưỡng cảnh báo",
  "isEnabled": "boolean — Bật/tắt",
  "recipients": "string[] — Danh sách người nhận"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "long",
    "alertType": "string",
    "thresholdValue": "decimal",
    "channel": "string",
    "frequency": "string",
    "isEnabled": "boolean",
    "recipients": "string[]",
    "updatedAt": "string (ISO instant)"
  },
  "message": "Thao tác thành công"
}
```

**Errors:** 400 (dữ liệu không hợp lệ), 401 (thiếu JWT), 403 (thiếu quyền), 404 (không tìm thấy)

---

### DELETE /api/v1/alert-settings/{id}

**Mô tả:** Vô hiệu hóa cấu hình cảnh báo (soft disable).

**Auth:** JWT + Admin

**Path parameters:**
- `id` (long, required) — ID cấu hình cảnh báo

**Response 204:** No Content

**Errors:** 401 (thiếu JWT), 403 (thiếu quyền), 404 (không tìm thấy)

---

## Interface Settings — Table Columns

### GET /api/v1/interface-settings/table-columns

**Mô tả:** Lấy cấu hình cột hiển thị theo scope.

**Auth:** JWT

**Query parameters:**
- `scope` (string, optional, mặc định `inventory`) — Loại bảng (ví dụ: `inventory`, `products`, `customers`)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "tableKey": "string — Mã bảng",
        "tableLabel": "string — Nhãn bảng",
        "columns": [
          {
            "key": "string — Mã cột",
            "label": "string — Nhãn cột",
            "required": "boolean — Cột bắt buộc (luôn hiển thị)",
            "visible": "boolean — Trạng thái hiển thị",
            "order": "int — Thứ tự hiển thị"
          }
        ],
        "updatedAt": "string (ISO instant) — Thời gian cập nhật",
        "updatedByName": "string — Người cập nhật"
      }
    ]
  },
  "message": "Thành công"
}
```

**Errors:** 401 (thiếu JWT)

---

### PUT /api/v1/interface-settings/table-columns

**Mô tả:** Lưu cấu hình cột hiển thị.

**Auth:** JWT

**Request body:**
```json
{
  "scope": "string (required) — Loại bảng",
  "items": [
    {
      "tableKey": "string (required) — Mã bảng",
      "hiddenColumns": "string[] (optional) — Danh sách cột ẩn",
      "columnOrder": "string[] (optional) — Thứ tự cột"
    }
  ]
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "tableKey": "string",
        "tableLabel": "string",
        "columns": [
          {
            "key": "string",
            "label": "string",
            "required": "boolean",
            "visible": "boolean",
            "order": "int"
          }
        ],
        "updatedAt": "string (ISO instant)",
        "updatedByName": "string"
      }
    ]
  },
  "message": "Đã cập nhật cấu hình cột"
}
```

**Errors:** 400 (dữ liệu không hợp lệ), 401 (thiếu JWT)
