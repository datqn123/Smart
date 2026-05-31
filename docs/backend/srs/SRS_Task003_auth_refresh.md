# SRS — Làm mới access token (Task003 / `POST /auth/refresh`)

> **File**: `backend/docs/srs/SRS_Task003_auth_refresh.md`  
> **API:** [`../../../frontend/docs/api/API_Task003_auth_refresh.md`](../../../frontend/docs/api/API_Task003_auth_refresh.md)  
> **Envelope:** [`../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md`](../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md)  
> **Liên quan:** Task001 (login + lưu refresh), Task002 (soft revoke `delete_ymd` + `clear` map), Task100 (map access stale)  
> **Ngày:** 24/04/2026  
> **Phiên bản:** 1.2  
> **Trạng thái:** **Approved** (24/04/2026 — §7 đã chốt trong file)

---

## 1. Tóm tắt

Client gọi **`POST /api/v1/auth/refresh`** **không** gửi `Authorization` Bearer; chỉ gửi **`refreshToken`** trong body. Server tra **`refresh_tokens`** (Postgres, `delete_ymd IS NULL`, chưa quá `expires_at`), tải user **Active** + role, phát **access JWT mới**, **`LoginSessionRegistry.register(userId, newAccess)`** để map phiên đơn khớp access hiện tại.

**Chốt Owner (bản 1.1):** **Không** ghi `SystemLogs` cho thao tác refresh — không bắt buộc audit DB cho endpoint này; **đủ** nghiệp vụ khi đã có access mới (+ cập nhật map). **Rotation** refresh (phát refresh mới, revoke cũ) là **tùy chọn** — xem §7.1.

---

## 2. Phạm vi

| In | Out |
| :--- | :--- |
| `POST /api/v1/auth/refresh`, body `refreshToken`, mã 200/400/401/500 theo API | Đăng nhập (Task001), đăng xuất (Task002), MFA |
| Access JWT mới + cập nhật `LoginSessionRegistry` | Ghi `SystemLogs` cho `REFRESH` (ngoài phạm vi tối thiểu) |
| (Tùy chọn) Rotation refresh + SQL mở rộng | Rate limit / device binding (ADR sau) |
| Đọc `users` + `roles` tối thiểu | `SELECT *` rộng |

---

## 3. Hợp đồng HTTP (rút gọn từ API)

| Hạng mục | Giá trị |
| :--- | :--- |
| Endpoint | `POST /api/v1/auth/refresh` |
| Auth header | **Không** dùng Bearer access (theo API §2.1) |
| Body | `{ "refreshToken": "<chuỗi>" }` |
| 200 `data` | `accessToken` (mới); `refreshToken` = **chuỗi mới** nếu bật rotation (§7.1), ngược lại **trùng** chuỗi client gửi lên (vẫn đủ field theo API) |
| 400 | `BAD_REQUEST` + `details.refreshToken` |
| 401 | `UNAUTHORIZED` — message API §3.2 |
| 500 | `INTERNAL_SERVER_ERROR` theo [`API_RESPONSE_ENVELOPE.md`](../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md) §3.3 (Doc Sync chỉnh mẫu API nếu còn `INTERNAL_ERROR`) |

---

## 4. Luồng server (bắt buộc — tối thiểu)

1. Bean Validation: `refreshToken` `@NotBlank` (message khớp API / Zod Task003 §5).  
2. Tra cứu bản ghi **`refresh_tokens`**: `token` = body, **`delete_ymd IS NULL`**, **`expires_at` > now()** (UTC). Không thấy → **401**.  
3. Lấy `user_id`; load **User** + **Role.name** (tối thiểu cho JWT claims); nếu `status` ≠ **`Active`** (CHECK DB, thường `'Active'`) → **401**.  
4. Tạo **access JWT** mới — TTL **cùng** `JwtTokenService` / Task001 (không tự đổi TTL trong SRS).  
5. **(Tùy chọn §7.1 — rotation):** nếu bật: soft-revoke hàng refresh hiện tại + `INSERT` refresh mới; response trả refresh mới. Nếu **tắt**: **không** `UPDATE delete_ymd`, **không** insert refresh mới — response `refreshToken` = input (client giữ nguyên chuỗi).  
6. **`LoginSessionRegistry.register(userId, newAccessToken)`** — sau khi transaction DB (nếu có) **commit**; đảm bảo map không còn JWT access cũ.  
7. Trả **200** + message API §3.1.

**Không** thực hiện `INSERT systemlogs` cho `REFRESH` theo chốt §1.

**Đồng bộ Task002:** refresh đã `delete_ymd` → bước (2) fail → **401**.

---

## 5. Acceptance Criteria (Given / When / Then)

### 5.1 Thành công — tối thiểu (không rotation, không log)

```text
Given refresh token hợp lệ trong DB (delete_ymd null, chưa quá expires_at) và user Active
When POST /api/v1/auth/refresh với body { "refreshToken": "<token>" }
Then HTTP 200, data.accessToken là JWT mới
  And data.refreshToken trùng chuỗi đã gửi (khi rotation tắt)
  And LoginSessionRegistry(user_id) chứa access mới
  And không bắt buộc có dòng SystemLogs REFRESH
```

### 5.1b Thành công — có rotation (khi PO bật §7.1)

```text
Then data.refreshToken khác token cũ; bản ghi cũ delete_ymd đã set; có bản ghi refresh mới
```

### 5.2 400 — thiếu refresh

```text
Given body thiếu hoặc refreshToken rỗng
When POST /api/v1/auth/refresh
Then 400 BAD_REQUEST và details.refreshToken
```

### 5.3 401 — không tồn tại / hết hạn / đã revoke

```text
Given refresh không khớp bản ghi hợp lệ hoặc expires_at đã qua hoặc delete_ymd khác null
When POST /api/v1/auth/refresh
Then 401 UNAUTHORIZED và message theo API §3.2
```

### 5.4 401 — user không Active

```text
Given refresh trỏ tới user không còn Active
When POST /api/v1/auth/refresh
Then 401 (message thống nhất API)
```

---

## 6. Dữ liệu & SQL tham chiếu (BA + SQL)

### 6.1 Bảng & điều kiện đọc

- **`refresh_tokens`:**  
  `WHERE token = :plain AND delete_ymd IS NULL AND expires_at > CURRENT_TIMESTAMP`  
- **`users`** (+ **`roles`**): tối thiểu cho JWT.

### 6.2 SQL — **chỉ khi bật rotation** (§7.1 = Có)

```sql
UPDATE refresh_tokens
SET delete_ymd = CURRENT_TIMESTAMP
WHERE id = :refreshRowId
  AND delete_ymd IS NULL
  AND token = :oldPlainToken;

INSERT INTO refresh_tokens (user_id, token, expires_at)
VALUES (:userId, :newPlainToken, :newExpiresAt);
```

**Khi rotation tắt:** không cần câu SQL ghi ở trên; chỉ **đọc** hợp lệ rồi phát access (logic ứng dụng).

**Hiệu năng:** lookup theo `token` (UNIQUE); có thể partial index nếu đo (ADR).

**Transaction:** nếu có rotation — `UPDATE` + `INSERT` refresh trong một `@Transactional`; sau commit → `register` map. Không log DB.

---

## 7. Open Questions — giải thích để PO / Tech chốt

> Mục đích: mỗi câu hỏi là **điểm rẽ nhánh** ảnh hưởng triển khai, bảo mật, và chi phí bảo trì. Bên cạnh là **vì sao phải hỏi** và **hệ quả** từng lựa chọn.

### 7.1 Rotation refresh — **bật** hay **tắt** tạm thời?

| | Nội dung |
| :--- | :--- |
| **Vì sao hỏi** | API Task003 **khuyến nghị** mỗi lần refresh trả **refresh mới** và vô hiệu cũ — giảm rủi ro token refresh bị lộ dùng lại. Nhưng rotation cần thêm **UPDATE + INSERT** (hoặc tương đương), xử lý race, và FE phải **lưu refresh mới**. |
| **Tắt (tối thiểu hiện tại)** | Chỉ phát **access mới**, `data.refreshToken` = input; **ít code / ít DB**; rủi ro: refresh bị đánh cắp dùng đến `expires_at` (30 ngày) trừ khi user logout (Task002). |
| **Bật** | An toàn hơn theo chuẩn OAuth thực hành; phức tạp hơn; phải đồng bộ Task002 “một refresh một phiên”. |
| **Gợi ý** | MVP có thể **tắt** rồi bật sau khi có test + ADR; hoặc **bật ngay** nếu ưu tiên bảo mật. |

**Trả lời / chốt (PO):**
Không cần thiết, dùng refresh token xuyên suốt nếu refreshtoken hết hạn thì mới tạo cái mới


---

### 7.2 Giới hạn tần suất refresh (rate limit)?

| | Nội dung |
| :--- | :--- |
| **Vì sao hỏi** | Client lỗi vòng lặp hoặc bị tấn công có thể gọi `/auth/refresh` rất nhiều lần/phút → tải DB + CPU ký JWT. |
| **Không giới hạn (Task003 tối thiểu)** | Triển khai nhanh; dựa vào hạ tầng / WAF sau. |
| **Có giới hạn** | Cần đếm theo `user_id` hoặc IP (Redis, bucket) — **ADR + Dev riêng**, không chặn SRS tối thiểu. |

**Trả lời / chốt (PO):**
Có, 5p mới tạo được 1 access token 1 lần


---

### 7.3 Có cập nhật `users.last_login` khi refresh không?

| | Nội dung |
| :--- | :--- |
| **Vì sao hỏi** | `last_login` thường diễn giải là “lần **đăng nhập** gần nhất”; refresh là “**duy trì** phiên”, không phải login lại. |
| **Không cập nhật (mặc định)** | Semantics rõ; ít ghi DB. |
| **Có cập nhật** | Dashboard “hoạt động gần đây” đếm cả refresh — cần PO định nghĩa lại ý nghĩa cột. |

**Trả lời / chốt (PO):**
Không cần


---

### 7.4 (Đã chốt — không mở) Ghi `SystemLogs` cho REFRESH?

**Chốt:** **Không** ghi log DB cho refresh; đủ với access mới + map (§1). Nếu sau này cần audit bảo mật → tách task + ADR (có thể dùng metric/log tập trung thay vì `INSERT` bảng nghiệp vụ).

---

## 8. Handoff

- **DEV:** endpoint + validate refresh; **không** `INSERT systemlogs` REFRESH; `JwtTokenService.createAccessToken`; `register` sau commit; rotation chỉ khi PO chọn §7.1 **Bật**; không `strip` mù `refreshToken`.  
- **TESTER:** manual / Postman; 401 sau logout; nếu rotation bật — kiểm tra refresh đổi chuỗi.  
- **Doc Sync:** nếu API mẫu §4 Task003 vẫn nói `SystemLogs` — đánh dấu **lệch SRS** hoặc sửa API cho khớp chốt “không log”.

---

## 9. Traceability

| Nguồn | Mục đích |
| :--- | :--- |
| [`API_Task003_auth_refresh.md`](../../../frontend/docs/api/API_Task003_auth_refresh.md) | Hợp đồng HTTP |
| `V3`, `V4` Flyway `refresh_tokens` | Schema |
| [`SRS_Task002_logout.md`](SRS_Task002_logout.md) | Soft revoke đồng bộ |
