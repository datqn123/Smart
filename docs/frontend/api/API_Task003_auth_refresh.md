# 📄 API SPEC: Làm mới Access Token (Refresh) - Task003

> **Trạng thái**: Approved  
> **Feature**: Authentication  
> **Tags**: RESTful, Auth, JWT, Refresh

**Khung thiết kế dự án**: [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) §2–§3, §4.1 (`POST /auth/refresh` — **tách riêng** khỏi login để contract rõ ràng cho Spring Boot / FE).

**Lý do tách API**: `POST /auth/login` chỉ cấp phiên; việc gia hạn phiên lặp lại theo chu kỳ ngắn là hành vi độc lập — endpoint riêng giúp middleware, rate limit, rotation refresh token và audit tách biệt.

## 0. Bộ file mẫu (JSON) — API_BRIDGE / Doc Sync

| Mục | Đường dẫn |
| :--- | :--- |
| Index endpoint | [`endpoints/Task003.md`](endpoints/Task003.md) |
| Request + response envelope | [`samples/Task003/`](samples/Task003/) |
| Postman (3 file) | `backend/smart-erp/docs/postman/Task003_refresh.*.body.json` |

---

## 1. Thông tin chung (Overview)

| Thuộc tính           | Giá trị                                      |
| :------------------- | :------------------------------------------- |
| **API Design Ref**   | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.1** |
| **Endpoint**         | `/api/v1/auth/refresh`                         |
| **Method**           | `POST`                                       |
| **Authentication**   | `None` (xác thực bằng `refreshToken` trong body) |
| **RBAC Roles**       | Không áp dụng theo role; token phải hợp lệ và chưa thu hồi |
| **Use Case Ref**     | Duy trì phiên cho UC1–UC13 (sau khi đã đăng nhập Task001) |

---

## 2. Đặc tả Request (Request Specification)

### 2.1 Headers

```http
Content-Type: application/json
```

_(Không dùng `Authorization: Bearer` cho access token cũ — tránh nhầm với luồng API thông thường; chỉ dùng refresh trong body.)_

### 2.2 Query Parameters

_Không có_

### 2.3 Request Body

```json
{
  "refreshToken": "def72b38-...."
}
```

---

## 3. Cấu trúc phản hồi (Response Specification)

### 3.1 Thành công (Successful Response)

**Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5...",
    "refreshToken": "a1b2c3d4-...."
  },
  "message": "Token đã được làm mới"
}
```

**Rotation (khuyến nghị)**: Mỗi lần refresh thành công, phát hành **refreshToken mới** và vô hiệu hóa token cũ (giảm rủi ro token bị lộ lặp dùng). Nếu tạm thời không rotation, vẫn trả lại cùng `refreshToken` — phải ghi rõ trong triển khai backend.

### 3.2 Lỗi (Error Responses)

#### 400 Bad Request

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Dữ liệu không hợp lệ",
  "details": {
    "refreshToken": "Refresh token là bắt buộc"
  }
}
```

#### 401 Unauthorized (Token không hợp lệ / hết hạn / đã revoke)

```json
{
  "success": false,
  "error": "UNAUTHORIZED",
  "message": "Refresh token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại."
}
```

#### 500 Internal Server Error

```json
{
  "success": false,
  "error": "INTERNAL_ERROR",
  "message": "Hệ thống đang gặp sự cố. Vui lòng thử lại sau."
}
```

---

## 4. Logic nghiệp vụ & Database (Business Logic)

### 4.1 Quy trình

1. Validate body (`RefreshSchema`).
2. Tra cứu refresh token trong kho lưu trữ (Redis / bảng phụ — đồng bộ với nơi **Task001** ghi khi login).
3. Nếu không tồn tại, hết hạn, hoặc đã revoke → **401**.
4. Lấy `user_id` gắn với token; tải `Users` + `Roles.name` (cột tối thiểu, không `SELECT *`).
5. Nếu `Users.status <> 'Active'` → **401** (không cấp token cho tài khoản khóa).
6. Phát hành **accessToken** mới (JWT, TTL ngắn, ví dụ 15 phút — cùng policy Task001).
7. **(Khuyến nghị)** Phát hành **refreshToken** mới, xóa/ghi đè bản ghi cũ.
8. Ghi `SystemLogs`: module `AUTH`, action `REFRESH`, `user_id`.

### 4.2 Ràng buộc

- Refresh token phải khớp **đúng** phiên đang lưu (đồng bộ với Task002 logout revoke).

---

## 5. Zod Schema (Dành cho Frontend)

```typescript
import { z } from "zod";

const RefreshTokenSchema = z.object({
  refreshToken: z.string().min(1, "Refresh token là bắt buộc"),
});
```
