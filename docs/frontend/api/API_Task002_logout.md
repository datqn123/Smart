# 📄 API SPEC: Đăng xuất hệ thống - Task002

> **Trạng thái**: Approved  
> **Feature**: Authentication  
> **Tags**: RESTful, Auth, Logout, Revoke

**Khung thiết kế dự án**: [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) §2–§3, §4.1 (`POST /auth/logout`).

## 0. Bộ file mẫu (JSON) — API_BRIDGE / Doc Sync

| Mục | Đường dẫn |
| :--- | :--- |
| Index endpoint | [`endpoints/Task002.md`](endpoints/Task002.md) |
| Request + response envelope | [`samples/Task002/`](samples/Task002/) |
| Postman (3 file) | `backend/smart-erp/docs/postman/Task002_logout.*.body.json` |

---

## 1. Thông tin chung (Overview)

| Thuộc tính           | Giá trị                                      |
| :------------------- | :------------------------------------------- |
| **API Design Ref**   | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.1** |
| **Endpoint**         | `/api/v1/auth/logout`                        |
| **Method**           | `POST`                                       |
| **Authentication**   | `Bearer Token` (bắt buộc)                    |
| **RBAC Roles**       | `Owner`, `Staff`, `Admin` (mọi vai đã đăng nhập) |
| **Use Case Ref**     | Kết thúc phiên (đồng bộ với Task001 / refresh)   |

---

## 2. Đặc tả Request (Request Specification)

### 2.1 Headers

```http
Authorization: Bearer <your_access_token>
Content-Type: application/json
```

### 2.2 Query Parameters

_Không có_

### 2.3 Request Body

```json
{
  "refreshToken": "def72b38..."
}
```

_(Gửi kèm refreshToken để thu hồi hoàn toàn phiên đăng nhập)_

---

## 3. Cấu trúc phản hồi (Response Specification)

### 3.1 Thành công (Successful Response)

**Code**: `200 OK`

```json
{
  "success": true,
  "data": {},
  "message": "Đăng xuất thành công và đã hủy các phiên làm việc"
}
```

### 3.2 Lỗi (Error Responses)

#### 400 Bad Request (Thiếu hoặc sai định dạng refresh token)

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Dữ liệu không hợp lệ",
  "details": {
    "refreshToken": "Refresh token là bắt buộc để đăng xuất an toàn"
  }
}
```

#### 401 Unauthorized (Token không hợp lệ)

```json
{
  "success": false,
  "error": "UNAUTHORIZED",
  "message": "Phiên đăng nhập không hợp lệ hoặc đã hết hạn"
}
```

#### 403 Forbidden (Refresh token không thuộc phiên hiện tại)

```json
{
  "success": false,
  "error": "FORBIDDEN",
  "message": "Refresh token không khớp với phiên đăng nhập hiện tại"
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

### 4.1 Quy trình thực thi (Step-by-Step)

1.  **Xác thực Phiên**:
    - Hệ thống kiểm tra `accessToken` từ Header để xác định `user_id`.
    - Nếu Token không hợp lệ hoặc đã hết hạn, trả về lỗi 401.
2.  **Kiểm tra & Thu hồi Refresh Token**:
    - Nhận `refreshToken` từ request body.
    - Truy vấn trong Database hoặc Redis để xác nhận sự tồn tại của Refresh Token này gắn với `user_id`.
    - Nếu tồn tại, thực hiện **xóa/vô hiệu hóa** Refresh Token này để ngăn chặn việc cấp mới Access Token.
3.  **Giải phóng Session (Single Session Management)**:
    - Truy cập **State Management (Redis/HashMap)**.
    - Thực hiện xóa Key: `DEL current_session:user:{id}`.
    - **Ý nghĩa**: Việc xóa này cho phép tài khoản có thể đăng nhập lại từ thiết bị khác (tuân thủ quy tắc chặn đăng nhập song song).
4.  **Ghi nhật ký (Audit Log)**:
    - Ghi Log: `INSERT INTO SystemLogs (log_level, module, action, user_id, message) VALUES ('INFO', 'AUTH', 'LOGOUT', ?, 'Người dùng đã đăng xuất');`
5.  **Phản hồi**: Trả về thông báo thành công cho Frontend để xóa Token khỏi LocalStorage/Cookie.

### 4.2 Các ràng buộc (Constraints)

- API này bắt buộc phải đi qua middleware xác thực JWT.
- Khi Logout thành công, mọi request sử dụng `accessToken` cũ hoặc `refreshToken` cũ đều phải bị từ chối 401.

---

## 5. Zod Schema (Dành cho Frontend)

```typescript
import { z } from "zod";

const LogoutSchema = z.object({
  refreshToken: z
    .string()
    .min(1, "Refresh Token là bắt buộc để đăng xuất an toàn"),
});
```
