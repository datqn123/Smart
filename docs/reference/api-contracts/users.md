# Users API Contracts

Base path: `/api/v1/users`

> Response envelope: `{ success: boolean, data: T, message: string }`

---

## GET /api/v1/users/next-staff-code

**Mô tả:** Gợi ý mã nhân viên tiếp theo dựa trên roleId và staffFamily.

**Auth:** JWT + `can_manage_staff`

**Query params:**
- `roleId` (int, required) — ID vai trò
- `staffFamily` (string, optional) — Nhóm nhân viên

**Response 200:**
```json
{
  "success": true,
  "data": {
    "nextCode": "string — Mã nhân viên gợi ý",
    "prefix": "string — Tiền tố mã",
    "roleId": "int — ID vai trò",
    "staffFamily": "string — Nhóm nhân viên"
  },
  "message": "Thành công"
}
```

**Errors:** 400 (thiếu tham số), 401 (JWT không hợp lệ), 403 (thiếu quyền)

---

## POST /api/v1/users

**Mô tả:** Tạo nhân viên mới.

**Auth:** JWT + `can_manage_staff`

**Request body:**
```json
{
  "username": "string (min 3, max 100, required) — Tên đăng nhập",
  "password": "string (min 8, max 128, required) — Mật khẩu",
  "fullName": "string (min 1, max 255, required) — Họ tên",
  "email": "string (email, required) — Email",
  "phone": "string (max 20, optional) — Số điện thoại",
  "staffCode": "string (max 50, optional) — Mã nhân viên",
  "roleId": "int (positive, required) — ID vai trò",
  "status": "string (Active|Inactive, optional) — Trạng thái"
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "employeeCode": "string — Mã nhân viên",
    "fullName": "string — Họ tên",
    "email": "string — Email",
    "phone": "string — Số điện thoại",
    "roleId": "int — ID vai trò",
    "role": "string — Tên vai trò",
    "status": "string — Trạng thái",
    "joinedDate": "string — Ngày tham gia",
    "avatar": "string — Ảnh đại diện"
  },
  "message": "Tạo nhân viên thành công"
}
```

**Errors:** 400 (validation), 401 (JWT không hợp lệ), 403 (thiếu quyền)

---

## GET /api/v1/users

**Mô tả:** Danh sách nhân viên (phân trang).

**Auth:** JWT + `can_manage_staff`

**Query params:**
- `search` (string, optional) — Từ khóa tìm kiếm
- `status` (string, optional, default: "all") — Lọc theo trạng thái
- `roleId` (int, optional) — Lọc theo vai trò
- `page` (int, optional, default: 1, min: 1) — Số trang
- `limit` (int, optional, default: 20, min: 1, max: 100) — Số lượng mỗi trang

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "int",
        "employeeCode": "string — Mã nhân viên",
        "fullName": "string — Họ tên",
        "email": "string — Email",
        "phone": "string — Số điện thoại",
        "roleId": "int — ID vai trò",
        "role": "string — Tên vai trò",
        "status": "string — Trạng thái",
        "joinedDate": "string — Ngày tham gia",
        "avatar": "string — Ảnh đại diện"
      }
    ],
    "page": "int — Trang hiện tại",
    "limit": "int — Số lượng mỗi trang",
    "total": "long — Tổng số nhân viên"
  },
  "message": "Thành công"
}
```

**Errors:** 400 (param không hợp lệ), 401 (JWT không hợp lệ), 403 (thiếu quyền)

---

## GET /api/v1/users/{userId}

**Mô tả:** Chi tiết nhân viên.

**Auth:** JWT + `can_manage_staff`

**Path params:**
- `userId` (int, required, positive) — ID nhân viên

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "employeeCode": "string — Mã nhân viên",
    "fullName": "string — Họ tên",
    "email": "string — Email",
    "phone": "string — Số điện thoại",
    "roleId": "int — ID vai trò",
    "role": "string — Tên vai trò",
    "status": "string — Trạng thái",
    "joinedDate": "string — Ngày tham gia",
    "avatar": "string — Ảnh đại diện",
    "username": "string — Tên đăng nhập",
    "lastLogin": "string — Lần đăng nhập cuối"
  },
  "message": "Thành công"
}
```

**Errors:** 400 (userId không hợp lệ), 401 (JWT không hợp lệ), 403 (thiếu quyền), 404 (không tìm thấy)

---

## PATCH /api/v1/users/{userId}

**Mô tả:** Cập nhật thông tin nhân viên (partial).

**Auth:** JWT + `can_manage_staff`

**Path params:**
- `userId` (int, required, positive) — ID nhân viên

**Request body:**
```json
{
  "fullName": "string (min 1, max 255, optional) — Họ tên",
  "email": "string (email, optional) — Email",
  "phone": "string (max 20, optional) — Số điện thoại",
  "staffCode": "string (max 50, optional) — Mã nhân viên",
  "roleId": "int (positive, optional) — ID vai trò",
  "status": "string (Active|Inactive, optional) — Trạng thái",
  "password": "string (min 8, max 128, optional) — Mật khẩu mới"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "int",
    "employeeCode": "string — Mã nhân viên",
    "fullName": "string — Họ tên",
    "email": "string — Email",
    "phone": "string — Số điện thoại",
    "roleId": "int — ID vai trò",
    "role": "string — Tên vai trò",
    "status": "string — Trạng thái",
    "joinedDate": "string — Ngày tham gia",
    "avatar": "string — Ảnh đại diện",
    "username": "string — Tên đăng nhập",
    "lastLogin": "string — Lần đăng nhập cuối"
  },
  "message": "Đã cập nhật nhân viên"
}
```

**Errors:** 400 (validation/body rỗng), 401 (JWT không hợp lệ), 403 (thiếu quyền), 404 (không tìm thấy)

---

## DELETE /api/v1/users/{userId}

**Mô tả:** Xóa mềm nhân viên.

**Auth:** JWT + `can_manage_staff`

**Path params:**
- `userId` (int, required, positive) — ID nhân viên

**Response 204:** No Content

**Errors:** 401 (JWT không hợp lệ), 403 (thiếu quyền), 404 (không tìm thấy)
