# Auth API Contracts

Base path: `/api/v1/auth`

> Response envelope: `{ success: boolean, data: T, message: string }`

---

## POST /api/v1/auth/login

**Mô tả:** Đăng nhập bằng email và mật khẩu.

**Auth:** Public

**Request body:**
```json
{
  "email": "string (email, required) — Email người dùng",
  "password": "string (min 6, required) — Mật khẩu"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "accessToken": "string — JWT access token",
    "refreshToken": "string — Refresh token",
    "user": {
      "id": "int",
      "username": "string",
      "fullName": "string",
      "email": "string",
      "role": "string — Tên role"
    }
  },
  "message": "Đăng nhập thành công"
}
```

**Errors:** 400 (validation), 401 (sai email/mật khẩu)

---

## POST /api/v1/auth/refresh

**Mô tả:** Làm mới access token bằng refresh token.

**Auth:** Public

**Request body:**
```json
{
  "refreshToken": "string (required) — Refresh token"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "accessToken": "string — JWT access token mới",
    "refreshToken": "string — Refresh token mới"
  },
  "message": "Token đã được làm mới"
}
```

**Errors:** 400 (validation), 401 (token hết hạn/không hợp lệ)

---

## POST /api/v1/auth/logout

**Mô tả:** Đăng xuất, hủy session và refresh token.

**Auth:** JWT (Bearer token trong `Authorization` header)

**Headers:**
- `Authorization: Bearer <accessToken>`
- `X-Client-Session-Id` (optional)

**Request body:**
```json
{
  "refreshToken": "string (required) — Refresh token cần hủy"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {},
  "message": "Đăng xuất thành công và đã hủy các phiên làm việc"
}
```

**Errors:** 401 (token không hợp lệ)

---

## POST /api/v1/auth/password-reset-requests

**Mô tả:** Gửi yêu cầu đặt lại mật khẩu (public).

**Auth:** Public

**Request body:**
```json
{
  "username": "string (max 100, required) — Tên đăng nhập",
  "message": "string (max 500, optional) — Ghi chú"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {},
  "message": "Yêu cầu đã được gửi đến quản trị viên"
}
```

**Errors:** 400 (validation)

---

## GET /api/v1/roles

**Mô tả:** Danh sách roles.

**Auth:** JWT + `can_manage_staff`

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "id": "int",
      "name": "string — Tên role",
      "permissions": "object — JSONB permissions map"
    }
  ],
  "message": "Thao tác thành công"
}
```

**Errors:** 403 (thiếu quyền)
