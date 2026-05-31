# Task002 — Bộ “Unit test” thủ công (Postman / tay)

> **Mục đích:** Tách từng **đơn vị nghiệp vụ** (một request + kỳ vọng rõ ràng) để bạn **chạy tay** từng case, không dùng JUnit/automation.  
> **SRS:** [`../../srs/SRS_Task002_logout.md`](../../srs/SRS_Task002_logout.md) §5  
> **API:** [`../../../../frontend/docs/api/API_Task002_logout.md`](../../../../frontend/docs/api/API_Task002_logout.md)  
> **Body mẫu (Postman):** [`../../../smart-erp/docs/postman/`](../../../smart-erp/docs/postman/) — file `Task002_logout.*.json`

---

## 0. Chuẩn bị chung

| Mục | Giá trị / ghi chú |
| :--- | :--- |
| Base URL | Ví dụ `http://localhost:8080` (đổi theo môi trường) |
| Endpoint logout | `POST {{baseUrl}}/api/v1/auth/logout` |
| Header mặc định | `Content-Type: application/json` |
| Bearer | `Authorization: Bearer <accessToken>` — lấy từ bước login Task001 |

**Lấy token (một lần mỗi phiên test):**

1. `POST /api/v1/auth/login` với body trong [`Task001_login.valid.body.json`](../../../smart-erp/docs/postman/Task001_login.valid.body.json) (field `body`).  
2. Lưu vào Postman: `accessToken` = `data.accessToken`, `refreshToken` = `data.refreshToken`.

---

## U-01 — Logout thành công (200)

| | |
| :--- | :--- |
| **Mục tiêu** | Thu hồi refresh hợp lệ, envelope thành công đúng API. |
| **Given** | Vừa login thành công; `accessToken` còn hạn; `refreshToken` đúng phiên; bản ghi refresh còn hiệu lực (`delete_ymd` null nếu đã triển khai soft revoke). |

**Bước**

1. Headers: `Authorization: Bearer {{accessToken}}`, `Content-Type: application/json`.  
2. Body: dùng [`Task002_logout.valid.body.json`](../../../smart-erp/docs/postman/Task002_logout.valid.body.json) — thay `refreshToken` trong file bằng biến `{{refreshToken}}` sau login (hoặc copy giá trị thật).

**Kỳ vọng**

- HTTP **200**  
- `success` = `true`  
- `data` = `{}` (object rỗng)  
- `message` = `Đăng xuất thành công và đã hủy các phiên làm việc` (đúng API Task002 §3.1)  
- (Nếu có quyền xem DB) bản ghi refresh tương ứng có **`delete_ymd`** (hoặc tương đưản) đã được gán thời điểm.

**Kết quả tay (Pass/Fail):** ______ **Ghi chú:** ________________________

---

## U-02 — Thiếu field `refreshToken` (400)

| | |
| :--- | :--- |
| **Mục tiêu** | Validation Bean — thiếu refresh. |

**Bước**

1. Headers: Bearer hợp lệ (có thể dùng token còn hạn từ login **khác** hoặc cùng user tùy bạn; 401 không phải mục tiêu case này).  
2. Body: `{}` hoặc file [`Task002_logout.invalid.missing-refresh.body.json`](../../../smart-erp/docs/postman/Task002_logout.invalid.missing-refresh.body.json).

**Kỳ vọng**

- HTTP **400**  
- `success` = `false`  
- `error` = `BAD_REQUEST`  
- `details.refreshToken` tồn tại, message kiểu *bắt buộc để đăng xuất an toàn* (theo API §3.2).

**Kết quả tay:** ______ **Ghi chú:** ________________________

---

## U-03 — `refreshToken` rỗng / chỉ khoảng trắng (400)

| | |
| :--- | :--- |
| **Mục tiêu** | `@NotBlank` / `@Size(min=1)` tương đương. |

**Bước**

1. Bearer hợp lệ.  
2. Body: [`Task002_logout.invalid.empty-refresh.body.json`](../../../smart-erp/docs/postman/Task002_logout.invalid.empty-refresh.body.json).

**Kỳ vọng**

- HTTP **400**, `BAD_REQUEST`, có `details.refreshToken`.

**Kết quả tay:** ______ **Ghi chú:** ________________________

---

## U-04 — Không gửi `Authorization` (401)

| | |
| :--- | :--- |
| **Mục tiêu** | Bảo vệ endpoint — thiếu Bearer. |

**Bước**

1. **Không** gửi header `Authorization` (hoặc để trống).  
2. Body: `refreshToken` hợp lệ (có thể bất kỳ chuỗi dài hợp lệ).

**Kỳ vọng**

- HTTP **401**  
- `error` = `UNAUTHORIZED`  
- `message` theo hợp đồng (vd. *Phiên đăng nhập không hợp lệ hoặc đã hết hạn* — khớp API Task002).

**Kết quả tay:** ______ **Ghi chú:** ________________________

---

## U-05 — Bearer sai / không phải JWT hệ thống (401)

| | |
| :--- | :--- |
| **Mục tiêu** | Access token không parse được / không đúng secret. |

**Bước**

1. `Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid` (hoặc chuỗi ngẫu nhiên).  
2. Body: `refreshToken` tùy ý.

**Kỳ vọng**

- HTTP **401**, `UNAUTHORIZED`.

**Kết quả tay:** ______ **Ghi chú:** ________________________

---

## U-06 — Bearer hợp lệ + `refreshToken` không thuộc user / sai token (403)

| | |
| :--- | :--- |
| **Mục tiêu** | `UPDATE` 0 dòng — nghiệp vụ từ chối (SRS §7.2). |

**Bước**

1. Login user A → lưu `accessToken` của A.  
2. Logout body gửi **`refreshToken` của user B** (login B trước đó) hoặc chuỗi **UUID giả** chưa từng lưu DB.

**Kỳ vọng**

- HTTP **403**  
- `error` = `FORBIDDEN`  
- `message` khớp API: *Refresh token không khớp với phiên đăng nhập hiện tại* (hoặc bản địa hóa team đã chốt).

**Kết quả tay:** ______ **Ghi chú:** ________________________

---

## U-07 — Logout lần hai với cùng refresh đã thu hồi (403)

| | |
| :--- | :--- |
| **Mục tiêu** | Idempotent revoke — soft delete đã set. |

**Bước**

1. Thực hiện **U-01** thành công.  
2. Gửi **lại** cùng request logout (cùng Bearer nếu còn hạn + cùng `refreshToken` đã revoke).

**Kỳ vọng**

- HTTP **403** (theo SRS; không coi là 200).

**Kết quả tay:** ______ **Ghi chú:** ________________________

---

## U-08 — Sau logout, access cũ vẫn gọi API được hay không (SRS §5.5)

| | |
| :--- | :--- |
| **Mục tiêu** | Xác minh client phải bỏ token; server từ chối khi policy đã bật. |

**Bước**

1. Sau **U-01**, gọi một endpoint **yêu cầu JWT** (khi `app.security.api-protection=jwt-api`), header `Authorization: Bearer {{accessToken}}` **cũ**.  
2. Hoặc thử lại `POST /auth/login` / refresh với `refreshToken` đã revoke (tùy endpoint đã có).

**Kỳ vọng** (điều chỉnh theo bảo mật đã bật)

- Theo SRS §5.5: request với token đã logout → **401** (hoặc 403 tùy gateway). Ghi rõ **thực tế đo được** để Doc Sync.

**Kết quả tay:** ______ **HTTP / body thực tế:** ________________________

---

## U-09 — 500 (tùy chọn, không bắt buộc MVP)

| | |
| :--- | :--- |
| **Mục tiêu** | Envelope lỗi hệ thống. |

**Gợi ý** (chỉ môi trường dev): tạm tắt DB / inject lỗi — **không** làm production.

**Kỳ vọng**

- HTTP **500**  
- `error` = `INTERNAL_SERVER_ERROR` (theo [`API_RESPONSE_ENVELOPE.md`](../../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md) — SRS đã chốt §7.3).

**Kết quả tay:** ______ **Ghi chú:** ________________________

---

## Checklist nhanh (copy vào ticket)

- [ ] U-01  
- [ ] U-02  
- [ ] U-03  
- [ ] U-04  
- [ ] U-05  
- [ ] U-06  
- [ ] U-07  
- [ ] U-08  
- [ ] U-09 (optional)
