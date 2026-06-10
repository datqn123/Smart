# Notifications API Contracts

Base path: `/api/v1/notifications`

> Response envelope: `{ success: boolean, data: T, message: string }`

---

## GET /api/v1/notifications

**Mô tả:** Danh sách thông báo của người dùng (phân trang).

**Auth:** JWT

**Query parameters:**
- `unreadOnly` (boolean, optional) — Chỉ lấy thông báo chưa đọc
- `page` (int, optional, default `1`, min `1`) — Số trang
- `limit` (int, optional, default `20`, min `1`, max `100`) — Số bản ghi mỗi trang

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "long",
        "notificationType": "string — Loại thông báo",
        "title": "string — Tiêu đề",
        "message": "string — Nội dung",
        "read": "boolean — Đã đọc chưa",
        "referenceType": "string — Loại đối tượng tham chiếu",
        "referenceId": "int — ID đối tượng tham chiếu",
        "createdAt": "Instant — Ngày tạo"
      }
    ],
    "page": "int — Trang hiện tại",
    "limit": "int — Số bản ghi mỗi trang",
    "total": "long — Tổng số thông báo",
    "unreadTotal": "long — Tổng số chưa đọc"
  },
  "message": "Thành công"
}
```

**Errors:** 401 (JWT hết hạn)

---

## PATCH /api/v1/notifications/{id}

**Mô tả:** Đánh dấu một thông báo là đã đọc.

**Auth:** JWT

**Path parameters:**
- `id` (long, required) — ID thông báo

**Response 200:**
```json
{
  "success": true,
  "data": {},
  "message": "Đã đánh dấu đã đọc"
}
```

**Errors:** 401 (JWT hết hạn), 404 (không tìm thấy thông báo)

---

## POST /api/v1/notifications/mark-all-read

**Mô tả:** Đánh dấu tất cả thông báo của người dùng là đã đọc.

**Auth:** JWT

**Response 200:**
```json
{
  "success": true,
  "data": {},
  "message": "Đã đọc hết"
}
```

**Errors:** 401 (JWT hết hạn)
