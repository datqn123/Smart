# Task003 — Bộ “Unit test” thủ công (Postman / REST client)

> **Vai trò:** Tester / QA — chạy **từng case độc lập**, ghi **Pass/Fail** + bằng chứng (HTTP status, đoạn JSON, screenshot nếu cần).  
> **Mục đích:** Bao phủ hợp đồng **`POST /api/v1/auth/refresh`** theo SRS §5 + API Task003 + triển khai thực tế (throttle 5 phút, không rotation, không `SystemLogs`).

| Thuộc tính | Giá trị |
| :--- | :--- |
| **Phiên bản tài liệu** | 1.2 |
| **SRS** | [`../../srs/SRS_Task003_auth_refresh.md`](../../srs/SRS_Task003_auth_refresh.md) |
| **API** | [`../../../../frontend/docs/api/API_Task003_auth_refresh.md`](../../../../frontend/docs/api/API_Task003_auth_refresh.md) |
| **Envelope phản hồi API** | [`../../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md`](../../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md) |
| **Hướng dẫn Tester (3 file Postman)** | [`../../../AGENTS/TESTER_AGENT_INSTRUCTIONS.md`](../../../AGENTS/TESTER_AGENT_INSTRUCTIONS.md) §2.1 |
| **Postman — bộ 3 file envelope Task003** | Xem **§0** bên dưới; thư mục [`../../../smart-erp/docs/postman/`](../../../smart-erp/docs/postman/) |
| **Postman bổ trợ** | `Task001_login.*.json`, `Task002_logout.*.json` (login / logout) |
| **Automation tham chiếu** | `Task003RefreshPostmanBodyContractTest`, `AuthControllerWebMvcTest`, `AuthServiceRefreshTest` |

---

## 0. Ba file Postman envelope (Task003) — mẫu Task001

Theo [`TESTER_AGENT_INSTRUCTIONS.md`](../../../AGENTS/TESTER_AGENT_INSTRUCTIONS.md) §**2.1**, Task003 có **đúng 3 file** JSON dưới `smart-erp/docs/postman/`, cùng **schema** với [`Task001_login.valid.body.json`](../../../smart-erp/docs/postman/Task001_login.valid.body.json): `_description`, `request` (`method`, `path`, `url`), `headers`, `body`.

| # | File | Dùng cho case manual |
| :---: | :--- | :--- |
| 1 | [`Task003_refresh.valid.body.json`](../../../smart-erp/docs/postman/Task003_refresh.valid.body.json) | **U-01** (và phần body **U-07** sau khi thay token); thay `body.refreshToken` bằng `{{refreshToken}}` sau login. |
| 2 | [`Task003_refresh.invalid.missing-refresh.body.json`](../../../smart-erp/docs/postman/Task003_refresh.invalid.missing-refresh.body.json) | **U-02** — `body` = `{}` (thiếu key `refreshToken`). |
| 3 | [`Task003_refresh.invalid.empty-refresh.body.json`](../../../smart-erp/docs/postman/Task003_refresh.invalid.empty-refresh.body.json) | **U-03** — `refreshToken` rỗng. |

**Cách dùng trong Postman**

1. Mở file JSON trong repo (hoặc import vào collection).  
2. Tạo request: **Method** = `request.method`; **URL** = `{{baseUrl}}` + `request.path` (vd. `{{baseUrl}}/api/v1/auth/refresh`) — `request.url` trong file chỉ là **ví dụ localhost**.  
3. Tab **Headers**: copy object `headers` (tối thiểu `Content-Type: application/json`).  
4. Tab **Body** → raw JSON: copy **chỉ** object `body` từ file (không gửi `_description` hay `request` lên server).

Các case **401 / 429 / chuỗi login–logout** không nằm trong 3 file tĩnh — thực hiện theo bảng **§6** (body inline hoặc sửa tạm `body.refreshToken`).

---

## 1. Thuật ngữ & phạm vi

| Thuật ngữ | Ý nghĩa |
| :--- | :--- |
| **Access JWT** | Token ngắn hạn trong `data.accessToken` (login Task001 hoặc sau refresh). |
| **Refresh plaintext** | Chuỗi lưu trong DB `refresh_tokens.token` — **không** rotation Task003: response trả lại **cùng** chuỗi request. |
| **Throttle** | Giới hạn **1 lần** cấp access mới qua `/auth/refresh` / **5 phút** / `user_id` — **in-memory** một JVM (SRS §7.2). |

**Trong phạm vi manual này:** envelope JSON, mã HTTP, message lỗi chính, luồng login → refresh → logout.  
**Ngoài phạm vi (ghi ticket riêng nếu cần):** load test, multi-instance throttle, rotation refresh (đã tắt theo SRS chốt).

---

## 2. Điều kiện môi trường trước khi chạy

| # | Kiểm tra | Ghi chú / Giá trị mong đợi |
| :---: | :--- | :--- |
| E-1 | Backend `smart-erp` đang chạy | Ví dụ port **8080** (đổi `{{baseUrl}}`). |
| E-2 | DB có user dev + migration refresh | Login Task001 thành công; bảng `refresh_tokens` có cột `delete_ymd`, `expires_at`. |
| E-3 | Profile & bảo mật | `app.security.api-protection=permit-all` **hoặc** `jwt-api` — refresh vẫn nằm dưới `/api/v1/auth/**` (public chain). |
| E-4 | Đồng hồ | Throttle dùng thời gian server; không cần chỉnh client clock trừ khi so sánh `exp` JWT. |
| E-5 | Postman Environment | Tạo env **Task003-Manual** với biến bảng §3. |

**Nếu test throttle (U-06) bị “lệch” do lần chạy trước:** đợi đủ **5 phút** từ lần refresh 200 cuối **cùng user**, hoặc **khởi động lại** tiến trình Spring (map throttle reset).

---

## 3. Biến Postman / REST client (khuyến nghị)

| Biến | Nguồn | Ví dụ |
| :--- | :--- | :--- |
| `baseUrl` | Cấu hình tay | `http://localhost:8080` |
| `accessToken` | `POST .../login` → `data.accessToken` | `eyJ...` |
| `refreshToken` | `POST .../login` → `data.refreshToken` | chuỗi 32 hex (theo code login) |
| `accessTokenBeforeRefresh` | Copy **trước** khi gọi U-01 | để so sánh JWT sau refresh |
| `accessTokenAfterRefresh` | Copy **sau** U-01 | phải **khác** `accessTokenBeforeRefresh` (thường đúng nếu TTL/access mới) |

**URL đầy đủ (không rút gọn sai path):**

- Login: `POST {{baseUrl}}/api/v1/auth/login`
- Refresh: `POST {{baseUrl}}/api/v1/auth/refresh`
- Logout: `POST {{baseUrl}}/api/v1/auth/logout`

Header mặc định mọi request JSON: `Content-Type: application/json`.

---

## 4. Khung envelope — cách đọc nhanh response

### 4.1 Thành công (2xx)

```json
{
  "success": true,
  "data": {
    "accessToken": "<JWT>",
    "refreshToken": "<chuỗi plaintext — Task003 = trùng request nếu không rotation>"
  },
  "message": "Token đã được làm mới"
}
```

**Kiểm tra tối thiểu:** `success === true`, `data` có đúng **2 key** trên, `message` đúng chuỗi chốt backend.

### 4.2 Lỗi validation (400)

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Dữ liệu không hợp lệ",
  "details": {
    "refreshToken": "<message từ Bean Validation>"
  }
}
```

### 4.3 Lỗi nghiệp vụ 401 / 429

- **401:** `error` = `UNAUTHORIZED`, `message` =  
  `Refresh token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.`  
- **429:** `error` = `TOO_MANY_REQUESTS`, `message` chứa ý **chờ 5 phút** (backend:  
  `Vui lòng đợi 5 phút trước khi làm mới access token.`).

---

## 5. Bảng mã lỗi & HTTP (tóm tắt tra cứu)

| HTTP | `error` (machine) | Khi nào |
| :---: | :--- | :--- |
| 200 | — (`success: true`) | Refresh hợp lệ, không throttle chặn. |
| 400 | `BAD_REQUEST` | Thiếu / rỗng `refreshToken`. |
| 401 | `UNAUTHORIZED` | Token không khớp DB hợp lệ, hết hạn, đã revoke, user không Active. |
| 429 | `TOO_MANY_REQUESTS` | Cùng user refresh lại trong < 5 phút kể từ lần 200 trước. |
| 500 | `INTERNAL_SERVER_ERROR` | Lỗi hệ thống (hiếm; U-09). |

---

## 6. Các case “unit” thủ công (U-xx)

> **Quy ước ghi kết quả:** mỗi case có khối **Bằng chứng** — dán **HTTP status**, **một đoạn JSON** (che bớt JWT nếu policy), hoặc đường dẫn file ảnh.

---

### U-01 — Refresh thành công (200) — **P0**

| Trường | Nội dung |
| :--- | :--- |
| **Mục tiêu** | Cấp access JWT mới; `refreshToken` response **trùng** request (SRS §5.1 tối thiểu, không rotation). |
| **SRS / API** | SRS §5.1; API §3.1 |
| **Given** | User **Active**; vừa `POST /api/v1/auth/login` 200; chưa logout; `refreshToken` còn hàng hợp lệ (`delete_ymd` null, `expires_at` > now). |

**Bước thực hiện**

1. `POST {{baseUrl}}/api/v1/auth/login` — body [`Task001_login.valid.body.json`](../../../smart-erp/docs/postman/Task001_login.valid.body.json) (điền email/mật khẩu dev đúng môi trường).  
2. Lưu `accessToken` → biến `accessTokenBeforeRefresh`; lưu `refreshToken`.  
3. `POST {{baseUrl}}/api/v1/auth/refresh`  
   - Copy **`headers`** + object **`body`** từ envelope **§0 (1)** — trong `body` đặt `refreshToken` = `{{refreshToken}}` sau bước 2 (copy nguyên chuỗi, **không** trim thêm nếu không chủ đích test khoảng trắng).  
   - Không bắt buộc header `Authorization` (Task003 chỉ tin `body`).

**Kỳ vọng (assert tay)**

| # | Kiểm tra | Mong đợi |
| :---: | :--- | :--- |
| A1 | HTTP status | `200` |
| A2 | `success` | `true` |
| A3 | `data.refreshToken` | **Byte-by-byte** (hoặc nhìn mắt) **giống** giá trị đã gửi trong body |
| A4 | `data.accessToken` | Chuỗi JWT 3 phần (header.payload.sig); **khác** `accessTokenBeforeRefresh` *trong hầu hết trường hợp* (iat/exp mới). Nếu trùng do trùng seed thời gian cực hiếm — ghi **ghi chú ngoại lệ**. |
| A5 | `message` | Đúng: `Token đã được làm mới` |
| A6 | `data` không có field thừa theo API | Không có `user` trong `data` (khác login). |

**Hậu kiểm (tùy chọn P1)**

- Gọi một API cần Bearer với `accessTokenAfterRefresh` (khi `jwt-api`): mong đợi **200** trên endpoint an toàn đã biết — chứng minh access mới dùng được.

**Kết quả:** Pass / Fail / Blocked **Tester:** __________ **Ngày:** __________  

**Bằng chứng (dán ngắn):**

```
HTTP:
Body (che JWT):
```

---

### U-02 — Thiếu field `refreshToken` (400) — **P0**

| Trường | Nội dung |
| :--- | :--- |
| **Mục tiêu** | Bean Validation khi body thiếu key. |
| **SRS / API** | SRS §5.2; API §3.2 |
| **Given** | Server đang sống. |

**Bước**

1. `POST {{baseUrl}}/api/v1/auth/refresh`  
2. Mở file envelope **§0 (2)** — tab Headers: copy `headers`; tab Body (raw JSON): copy **chỉ** object `body` (object rỗng `{}`, không có `refreshToken`).

**Kỳ vọng**

| # | Kiểm tra | Mong đợi |
| :---: | :--- | :--- |
| B1 | HTTP | `400` |
| B2 | `success` | `false` |
| B3 | `error` | `BAD_REQUEST` |
| B4 | `message` | Chứa ý *dữ liệu không hợp lệ* (theo `GlobalExceptionHandler`) |
| B5 | `details.refreshToken` | Tồn tại; message kiểu *Refresh token là bắt buộc* |

**Kết quả:** ______ **Bằng chứng:** ________________________

---

### U-03 — `refreshToken` rỗng / chỉ khoảng trắng (400) — **P0**

| Trường | Nội dung |
| :--- | :--- |
| **Mục tiêu** | `@NotBlank` trên `RefreshRequest`. |
| **SRS / API** | SRS §5.2; API §3.2 |

**Bước**

1. Headers / Body: từ file envelope **§0 (3)**.  
2. *(Tùy chọn thêm một request riêng)* body `{ "refreshToken": "   " }` — ghi rõ Spring/validation có coi là blank không.

**Kỳ vọng:** giống **U-02** (400 + `details.refreshToken`).

**Kết quả:** ______ **Bằng chứng:** ________________________

---

### U-04 — Refresh không tồn tại / chuỗi giả (401) — **P0**

| Trường | Nội dung |
| :--- | :--- |
| **Mục tiêu** | Không có hàng `refresh_tokens` thỏa `token` + `delete_ymd IS NULL` + `expires_at > now`. |
| **SRS / API** | SRS §5.3; API §3.2 |

**Bước**

1. Body ví dụ:  
   `{ "refreshToken": "00000000000000000000000000000000" }`  
   (hoặc UUID ngẫu nhiên **chưa** xuất hiện sau bất kỳ login nào trên DB hiện tại).

**Kỳ vọng**

| # | Mong đợi |
| :---: | :--- |
| C1 | HTTP `401` |
| C2 | `error` = `UNAUTHORIZED` |
| C3 | `message` **đúng chuỗi**: `Refresh token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.` |
| C4 | Không có `data` thành công (envelope lỗi theo `ApiErrorResponse`) |

**Kết quả:** ______ **Bằng chứng:** ________________________

---

### U-05 — Sau logout Task002, refresh cùng token (401) — **P0**

| Trường | Nội dung |
| :--- | :--- |
| **Mục tiêu** | Refresh đã bị soft-revoke → không cấp access (SRS đồng bộ Task002). |
| **SRS** | SRS §4 đoạn “Đồng bộ Task002”; §5.3 |

**Bước (chuỗi đầy đủ)**

1. Login 200 → lưu `accessToken`, `refreshToken`.  
2. `POST {{baseUrl}}/api/v1/auth/logout`  
   - Headers: `Authorization: Bearer {{accessToken}}`, `Content-Type: application/json`.  
   - Body: [`Task002_logout.valid.body.json`](../../../smart-erp/docs/postman/Task002_logout.valid.body.json) — điền `refreshToken` **đúng** phiên.  
   - Kỳ vọng logout: 200 + message Task002 (xem manual Task002 nếu cần).  
3. `POST {{baseUrl}}/api/v1/auth/refresh` với body `{ "refreshToken": "<cùng refresh đã logout>" }`.

**Kỳ vọng bước 3:** giống **U-04** (401 + message thống nhất).

**Kết quả:** ______ **Bằng chứng:** ________________________

---

### U-06 — Throttle: hai refresh liên tiếp < 5 phút (429) — **P0**

| Trường | Nội dung |
| :--- | :--- |
| **Mục tiêu** | SRS §7.2 — giới hạn tần suất refresh / user. |
| **Rủi ro môi trường** | Throttle **theo JVM** — nhiều instance / restart làm kết quả khác; ghi nhận môi trường khi Fail. |

**Bước**

1. **Làm sạch tình huống:** đợi ≥ **5 phút** sau lần refresh 200 gần nhất **cùng user**, **hoặc** restart app, **hoặc** login user khác (user khác có bucket throttle khác).  
2. Login (hoặc dùng session còn refresh hợp lệ).  
3. `POST .../refresh` **lần 1** → kỳ vọng **200**.  
4. **Không đợi**, `POST .../refresh` **lần 2** cùng body `refreshToken` hợp lệ.

**Kỳ vọng lần 2**

| # | Mong đợi |
| :---: | :--- |
| D1 | HTTP `429` |
| D2 | `error` = `TOO_MANY_REQUESTS` |
| D3 | `message` = `Vui lòng đợi 5 phút trước khi làm mới access token.` (đúng triển khai `RefreshAccessThrottle`) |

**Kết quả:** ______ **Môi trường (1 pod / local / …):** __________ **Bằng chứng:** __________

---

### U-07 — Gửi kèm Bearer sai + body refresh hợp lệ (200) — **P1**

| Trường | Nội dung |
| :--- | :--- |
| **Mục tiêu** | Endpoint **không** dựa Bearer; header rác không làm fail nếu body đúng. |
| **API** | API §2.1 |

**Bước**

1. Login → có `refreshToken` hợp lệ.  
2. `POST .../refresh` với:  
   - `Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.invalid` (hoặc access đã hết hạn).  
   - Body đúng `refreshToken`.

**Kỳ vọng:** **200** như U-01 (refresh theo body).

**Kết quả:** ______ **Bằng chứng:** ________________________

---

### U-08 — Sau login, lần refresh đầu không bị 429 (200) — **P0**

| Trường | Nội dung |
| :--- | :--- |
| **Mục tiêu** | Throttle được xóa khi login thành công — không “kẹt” 429 sau khi vừa đăng nhập. |
| **Triển khai** | `AuthService.login` gọi `refreshAccessThrottle.clear(userId)`. |

**Bước**

1. Thực hiện **U-06** đến bước **lần 2** đã 429 (hoặc giả lập user vừa bị throttle).  
2. **Login lại** cùng user (200).  
3. **Ngay lập tức** `POST .../refresh` với `refreshToken` **mới** từ login.

**Kỳ vọng:** Bước 3 → **200** (không 429 oan).

**Kết quả:** ______ **Bằng chứng:** ________________________

---

### U-09 — Lỗi hệ thống (500) — **P2 / optional**

| Trường | Nội dung |
| :--- | :--- |
| **Mục tiêu** | Envelope 500 đúng `INTERNAL_SERVER_ERROR`. |
| **Cảnh báo** | Chỉ môi trường dev; không tạo sự cố production. |

**Gợi ý:** tắt DB / cấu hình sai cố ý → gọi refresh.

**Kỳ vọng:** HTTP `500`, `error` = `INTERNAL_SERVER_ERROR`, message thân thiện theo `GlobalExceptionHandler`.

**Kết quả:** ______ **Bằng chứng:** ________________________

---

## 7. Checklist nhanh (copy vào ticket / Excel)

| ID | Case | P | Kết quả |
| :---: | :--- | :---: | :---: |
| U-01 | Refresh 200 | 0 | ☐ |
| U-02 | Thiếu refresh 400 | 0 | ☐ |
| U-03 | Refresh rỗng 400 | 0 | ☐ |
| U-04 | Sai token 401 | 0 | ☐ |
| U-05 | Sau logout 401 | 0 | ☐ |
| U-06 | Throttle 429 | 0 | ☐ |
| U-07 | Bearer rác + body đúng 200 | 1 | ☐ |
| U-08 | Sau login không kẹt 429 | 0 | ☐ |
| U-09 | 500 optional | 2 | ☐ |

**P:** 0 = bắt buộc release; 1 = nên có; 2 = tùy môi trường.

---

## 8. Ghi chú nghiệm thu / Defect

Khi **Fail**, ghi tối thiểu: **ID case**, **HTTP**, **body lỗi đầy đủ**, **log server** (trace id nếu có), **phiên bản build / commit**, **môi trường**.
