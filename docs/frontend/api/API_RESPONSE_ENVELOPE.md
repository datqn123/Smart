# Chuẩn envelope JSON — phản hồi API (`smart-erp`)

> **Mục đích**: Một nguồn chân lý cho **shape JSON** mà backend Spring và frontend cùng tuân theo. Bổ sung cho [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) §3 và khớp ví dụ trong [`../../AGENTS/docs/templates/api/RESTFUL_API_TEMPLATE.md`](../../AGENTS/docs/templates/api/RESTFUL_API_TEMPLATE.md).  
> **Triển khai Java (tham chiếu)**: `com.example.smart_erp.common.api.*`, `GlobalExceptionHandler` trong `backend/smart-erp`.

---

## 1. Quy ước chung

| Hạng mục | Quy định |
| :--- | :--- |
| `Content-Type` | `application/json; charset=UTF-8` |
| Key JSON | **camelCase** |
| `message` | Tiếng Việt, ngắn gọn, hiển thị được cho người dùng cuối (tránh stack trace). |
| HTTP status | Luôn dùng mã HTTP đúng nghĩa RFC; **không** trả `200` kèm `success: false`. |

**Nội dung `message` / giá trị trong `details` hiển thị cho người dùng cuối:** **không** tiết lộ cơ chế nội bộ phía server (vd. *multipart*, *servlet*, *JDBC*, *Cloudinary bật/tắt*, tên class, stack trace, tên biến cấu hình). Chỉ mô tả **điều không hợp lệ** (nghiệp vụ) và **gợi ý hành động** (giảm dung lượng, đổi định dạng, thử lại…). Chi tiết kỹ thuật ghi trong SRS, `API_Task*` (dev) hoặc log server — không đưa vào envelope trả về client.

---

## 2. Thành công (`2xx`)

### 2.1 Envelope (bắt buộc khi có body JSON)

| Field | Kiểu | Bắt buộc | Mô tả |
| :--- | :--- | :---: | :--- |
| `success` | boolean | Có | Luôn `true`. |
| `data` | object \| array \| null | Có | Payload nghiệp vụ; kiểu từng endpoint xem `API_TaskXXX`. |
| `message` | string | Có | Ví dụ: `Thao tác thành công`, `Đăng nhập thành công`. |

```json
{
  "success": true,
  "data": {},
  "message": "Thao tác thành công"
}
```

### 2.2 Trường hợp không có body

- **`204 No Content`**: không gửi body (thường dùng `DELETE` idempotent hoặc thao tác không cần trả payload). Ghi rõ trong spec từng API.
- **`201 Created`**: có thể dùng cùng envelope như `200`; nếu có header `Location`, ghi trong spec.

### 2.3 Phân trang (danh sách) — khuyến nghị

Đặt meta phân trang **bên trong** `data` để `success` / `message` giữ nguyên hình dạng:

| Field trong `data` | Kiểu | Mô tả |
| :--- | :--- | :--- |
| `items` | array | Danh sách bản ghi. |
| `page` | integer | Trang hiện tại (bắt đầu 1). |
| `limit` | integer | Kích thước trang. |
| `total` | integer | Tổng bản ghi (hoặc null nếu không đếm). |

```json
{
  "success": true,
  "data": {
    "items": [],
    "page": 1,
    "limit": 20,
    "total": 0
  },
  "message": "Thao tác thành công"
}
```

Tên field con (`items`, `page`, …) có thể thay bằng tên domain nếu spec Task ghi rõ — miễn **một** pattern cho toàn hệ thống trong phạm vi một nhóm endpoint.

---

## 3. Lỗi (`4xx` / `5xx`)

### 3.1 Envelope (bắt buộc)

| Field | Kiểu | Bắt buộc | Mô tả |
| :--- | :--- | :---: | :--- |
| `success` | boolean | Có | Luôn `false`. |
| `error` | string | Có | Mã máy đọc, **UPPER_SNAKE**; bảng §3.3. |
| `message` | string | Có | Tiếng Việt — lý do tổng quát; tuân **§1** (không lộ cơ chế server). |
| `details` | object | Không | Map `tên_field` → `thông báo` (validation); chỉ gửi khi có; **giá trị** từng key cũng tránh lộ cơ chế nội bộ nếu chuỗi đó hiển thị cho end-user. |

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Dữ liệu không hợp lệ",
  "details": {
    "username": "Không được để trống"
  }
}
```

### 3.2 `details` — quy tắc

- **400** từ Bean Validation: mỗi field một chuỗi; key là tên property request (camelCase).
- **409** / nghiệp vụ: có thể dùng `details` cho mã lý do phụ (tuỳ spec Task) hoặc bỏ qua nếu `message` đủ rõ.
- **500**: **không** trả `details` chứa stack trace hoặc SQL; chỉ message an toàn cho client.

### 3.3 Bảng mã `error` (chuẩn tối thiểu)

| `error` | HTTP | Khi nào dùng |
| :--- | :---: | :--- |
| `BAD_REQUEST` | 400 | Sai định dạng JSON, thiếu field, validation. |
| `UNAUTHORIZED` | 401 | Thiếu / sai / hết hạn JWT. |
| `FORBIDDEN` | 403 | Đã xác thực nhưng không đủ quyền RBAC hoặc không sở hữu dữ liệu. |
| `NOT_FOUND` | 404 | Không tìm thấy tài nguyên theo id/slug. |
| `CONFLICT` | 409 | Xung đột trạng thái nghiệp vụ, trùng unique, … |
| `UNPROCESSABLE_ENTITY` | 422 | Chỉ khi spec dự án chọn mã này (nếu không dùng — bỏ khỏi handler mặc định). |
| `TOO_MANY_REQUESTS` | 429 | Rate limit (nếu bật). |
| `INTERNAL_SERVER_ERROR` | 500 | Lỗi không lường trước phía server. |

Mở rộng mã `error` mới (ví dụ `STOCK_INSUFFICIENT`) **phải** được ghi trong `API_TaskXXX` tương ứng và (nếu dùng chung) cập nhật bảng này.

---

## 4. Spring Boot — mapping gợi ý

| Nguồn lỗi | HTTP | `error` |
| :--- | :---: | :--- |
| `@Valid` / `MethodArgumentNotValidException` | 400 | `BAD_REQUEST` |
| `HttpMessageNotReadableException` | 400 | `BAD_REQUEST` |
| `ConstraintViolationException` | 400 | `BAD_REQUEST` |
| `AuthenticationException` (filter/controller) | 401 | `UNAUTHORIZED` |
| `AccessDeniedException` | 403 | `FORBIDDEN` |
| Tài nguyên không tồn tại (domain) | 404 | `NOT_FOUND` |
| `BusinessException` / xung đột nghiệp vụ | 409 | `CONFLICT` hoặc mã tùy chỉnh |
| `DataIntegrityViolationException` (tuỳ cách xử lý) | 409 hoặc 400 | `CONFLICT` / `BAD_REQUEST` |
| Exception chưa phân loại | 500 | `INTERNAL_SERVER_ERROR` |

**Lưu ý**: Lỗi 401 từ **Spring Security filter** (chưa vào controller) có thể trả body mặc định của framework; khi chuẩn hóa toàn cổng, cấu hình `authenticationEntryPoint` trả cùng envelope §3.1 (việc của Security Agent / Dev).

---

## 5. Checklist khi viết spec `API_TaskXXX`

- [ ] Một block JSON mẫu **thành công** đúng §2.
- [ ] Liệt kê đủ mã HTTP lỗi áp dụng; mỗi mã có ví dụ JSON **đủ field** theo §3.
- [ ] Nếu có phân trang: mô tả cấu trúc `data` theo §2.3.
