# 📄 API SPEC: Đăng nhập hệ thống - Task001

> **Trạng thái**: Approved  
> **Feature**: Authentication  
> **Tags**: RESTful, Auth, Login

**Khung thiết kế dự án**: [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) §2–§3 (envelope, mã lỗi), §4.1 (Auth — `POST /auth/login`).

## 0. Bộ file mẫu (JSON) — API_BRIDGE / Doc Sync

| Mục | Đường dẫn |
| :--- | :--- |
| Index endpoint (bảng link) | [`endpoints/Task001.md`](endpoints/Task001.md) |
| Request + response envelope (mẫu) | [`samples/Task001/`](samples/Task001/) |
| Postman (3 file, wrapper) | `backend/smart-erp/docs/postman/Task001_login.*.body.json` |

---

## 1. Thông tin chung (Overview)

| Thuộc tính           | Giá trị                                      |
| :------------------- | :------------------------------------------- |
| **API Design Ref**   | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.1** |
| **Endpoint**         | `/api/v1/auth/login`                         |
| **Method**           | `POST`                                       |
| **Authentication**   | `None` (public)                              |
| **RBAC Roles**       | `All Roles (Owner, Staff, Admin)`            |
| **Use Case Ref**     | Phiên đăng nhập hệ thống (tiền điều kiện UC1–UC13) |

---

## 2. Đặc tả Request (Request Specification)

### 2.1 Headers

```http
Content-Type: application/json
```

### 2.2 Query Parameters

_Không có_

### 2.3 Request Body

Đăng nhập bằng **email** (khớp cột `Users.email`, so khớng không phân biệt hoa thường do server chuẩn hóa).

```json
{
  "email": "admin@smartinventory.vn",
  "password": "your_password_here"
}
```

**Quy ước validate (400):** mỗi field lỗi có message riêng trong envelope field `details` (key = tên field JSON `email` / `password`). Client hiển thị lỗi **đúng ô input** tương ứng.  
`message` tổng (tóm tắt) do backend envelope chung quy định (vd. *Dữ liệu không hợp lệ*) — không thay thế `details`.

- **Mật khẩu chỉ gồm khoảng trắng**: coi như **thiếu mật khẩu** (cùng nhóm lỗi với `@NotBlank` / Zod tương đương).

---

## 3. Cấu trúc phản hồi (Response Specification)

### 3.1 Thành công (Successful Response)

**Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5...",
    "refreshToken": "def72b38...",
    "user": {
      "id": 1,
      "username": "admin",
      "fullName": "System Administrator",
      "email": "admin@smartinventory.vn",
      "role": "Owner"
    }
  },
  "message": "Đăng nhập thành công"
}
```

`user.username` vẫn là **tên đăng nhập nội bộ** hiển thị; định danh đăng nhập API là **email**.

### 3.2 Lỗi (Error Responses)

#### 400 Bad Request (Validation theo từng field)

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Dữ liệu không hợp lệ",
  "details": {
    "email": "Email là bắt buộc",
    "password": "Mật khẩu phải có ít nhất 6 ký tự"
  }
}
```

- Chỉ gửi các key trong `details` cho field **thực sự lỗi** (ví dụ chỉ `password` nếu chỉ mật khẩu sai độ dài).
- Message từng field do **constraint trên DTO** (Bean Validation / Zod) định nghĩa — không map lại bằng handler riêng trùng nội dung.

#### 401 Unauthorized (Sai email/mật khẩu, không Active, hoặc đã Locked)

```json
{
  "success": false,
  "error": "UNAUTHORIZED",
  "message": "Email hoặc mật khẩu không chính xác hoặc tài khoản bị khóa"
}
```

_(Sau **5** lần đăng nhập sai mật khẩu cho cùng một tài khoản Active, hệ thống chuyển `Users.status` → `Locked` — lần sau trả cùng 401 chung.)_

#### 403 Forbidden (Đã đăng nhập nơi khác — chặn, không “đá phiên”)

```json
{
  "success": false,
  "error": "FORBIDDEN",
  "message": "Tài khoản đang được đăng nhập ở một thiết bị khác. Vui lòng đăng xuất ở thiết bị đó hoặc liên hệ Admin."
}
```

**Thứ tự nghiệp vụ:** sau khi **Count** user Active theo email **= 1**, kiểm tra session đồng thời; nếu đã có phiên hoạt động → **403** (không tiếp tục verify mật khẩu).  
**Giai đoạn hiện tại (chưa Redis):** dùng **`ConcurrentHashMap`** trong JVM (`userId` → access token hoặc session id). Khi có Redis: **chỉ lưu access token** (hoặc jti) theo user để kiểm tra; refresh token **chỉ lưu DB** (bảng refresh).

_(Mã nội bộ log có thể dùng `ALREADY_LOGGED_IN`.)_

#### 500 Internal Server Error

Dùng chung envelope dự án ([`API_RESPONSE_ENVELOPE.md`](API_RESPONSE_ENVELOPE.md)):

```json
{
  "success": false,
  "error": "INTERNAL_SERVER_ERROR",
  "message": "Đã xảy ra lỗi hệ thống, vui lòng thử lại sau."
}
```

---

## 4. Logic nghiệp vụ & Database (Business Logic)

### 4.1 Quy trình thực thi (Step-by-Step)

1. **Nhận & Kiểm tra input**  
   - Nhận `email`, `password` từ body.  
   - Bean Validation / LoginSchema: lỗi → **400** + `details` theo field (mục 3.2).

2. **Count user Active theo email**  
   - JPQL/HQL hoặc query tối ưu tương đương: đếm `User` với `lower(email) = lower(?)` và `status = 'Active'`.  
   - Nếu **0** → **401** (message mục 3.2).

3. **Phiên đồng thời (403 ngay sau khi biết có đúng 1 user Active)**  
   - Nếu count **≥ 1** (thực tế unique email → 1): tra **HashMap** (sau này Redis) `current_session:user:{id}`.  
   - Nếu đã tồn tại → **403** (chặn, không ghi đè phiên).  
   - Nếu không có → tiếp tục.

4. **Lấy dữ liệu xác thực**  
   - Load entity/`User` cần thiết (password hash, role, …) — có thể dùng **HQL/JPQL theo entity**, không bắt buộc SQL thô trùng tên bảng vật lý nếu đã ánh xạ `@Entity`/`@Table`.

5. **Kiểm tra mật khẩu**  
   - **bcrypt** so `password` với `password_hash`.  
   - Sai: tăng bộ đếm sai cho `user_id`; đạt **5** → `UPDATE` set `status = 'Locked'` → **401**.  
   - Đúng: reset bộ đếm sai cho user đó.

6. **Cấp phát token**  
   - **Access JWT**: `sub` = `user_id`, `name` = username (hiển thị), `role` = role name, **`exp` = 5 phút**.  
   - Tuỳ cấu hình: thêm claim **`iss` (issuer)** và **`aud` (audience)** khi bật — giải thích:  
     - **`iss`**: định danh **ai phát hành** token (vd. URL dịch vụ auth `https://api.example.com`), client/resource server có thể chỉ chấp nhận token từ issuer đó.  
     - **`aud`**: **đối tượng được cấp token** (vd. `smart-erp-api`), tránh token dùng nhầm cho dịch vụ khác.  
   - **Refresh**: UUID (plain), TTL **30 ngày**, **lưu DB** (revoke/rotation task sau).

7. **Ghi nhật ký & cập nhật**  
   - `UPDATE` user `last_login`.  
   - `INSERT` nhật ký hệ thống (bảng theo Flyway; tên vật lý PostgreSQL thường chữ thường).  
   - Ghi session: **HashMap** (sau này Redis) lưu **access token** (hoặc jti) theo `user_id`.

8. **Phản hồi** 200 + envelope thành công.

### 4.2 Tối ưu

- Ưu tiên **ít round-trip DB** và index trên `email` / `status` khi triển khai; có thể gộp bước 2–4 bằng ADR nếu đo được lợi hơn hai query tách count + fetch.

### 4.3 Ràng buộc

- Không trả `password_hash`.  
- Chỉ `status = 'Active'` được đăng nhập; `Locked` sau brute-force.  
- `JWT_SECRET` từ biến môi trường production.

---

## 5. Zod Schema (Dành cho Frontend)

```typescript
import { z } from "zod";

const LoginSchema = z.object({
  email: z.string().min(1, "Email là bắt buộc").email("Email không hợp lệ"),
  password: z
    .string()
    .min(6, "Mật khẩu phải có ít nhất 6 ký tự")
    .refine((s) => s.trim().length > 0, { message: "Mật khẩu là bắt buộc" }),
});
```

_(Chuỗi mật khẩu chỉ khoảng trắng: `trim().length === 0` → lỗi thiếu; khớp server `@NotBlank`.)_
