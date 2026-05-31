# SRS — Phiên HashMap khi access JWT hết hạn & không refresh (Task100)

> **File**: `backend/docs/srs/SRS_Task100_auth-session-registry-stale-access.md`  
> **Loại:** Nghiệp vụ **backend-only** — **không** có file `API_Task100_*` (index **100** theo quy ước task không map endpoint).  
> **Liên quan:** [`SRS_Task001_login-authentication.md`](SRS_Task001_login-authentication.md) (dự kiến cùng thư mục `backend/docs/srs/` khi khởi tạo), [`SRS_Task002_logout.md`](../task002/00-ba/SRS_Task002_logout.md) (`clear` map), [`SRS_Task003_auth_refresh.md`](SRS_Task003_auth_refresh.md).  
> **Envelope:** [`../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md`](../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md)  
> **Ngày:** 24/04/2026  
> **Phiên bản:** 1.1  
> **Trạng thái:** **Approved**

---

## 1. Tóm tắt

User đã đăng nhập nhưng **đóng tab / không gọi refresh** → access JWT **hết hạn** (5 phút) trong khi `refresh_tokens` vẫn có thể còn hiệu lực. **Nghiệp vụ mong muốn:** trong trạng thái đó coi như user **không còn “đang dùng” ứng dụng** — không được để `ConcurrentHashMap` (`LoginSessionRegistry`) giữ entry **đã chết** làm **chặn vĩnh viễn** đăng nhập lại (403 “thiết bị khác” oan).

---

## 2. Phạm vi

| In | Out |
| :--- | :--- |
| Định nghĩa “phiên map còn hiệu lực” vs **stale** (access đã hết hạn) | Task003 chi tiết refresh / rotation |
| Hành vi trước `assertNoConcurrentSession` + sau login thành công `register` | Đổi policy “đá phiên” (vẫn **chặn** khi access còn hạn) |
| Redis thay HashMap | ADR triển khai sau |

---

## 3. Vấn đề hiện trạng (GAP so Task001)

Task001 §3 quy tắc **4**: có key trong map → **403** (trước bcrypt).  
Map lưu **chuỗi access JWT**; **không** có TTL riêng trên entry. Khi JWT **exp** đã qua mà entry chưa bị `logout` / `clear` xóa → user **không** mở web nhưng server vẫn nghĩ còn phiên → **403** khi đăng nhập lại từ bất kỳ đâu.

---

## 4. Quy tắc nghiệp vụ đề xuất (chốt PO → §7)

1. **Định nghĩa “đang đăng nhập” (server):** tồn tại entry `userId → accessJwt` trong map **và** access JWT đó **chưa hết hạn** (`exp` > `now()`, có clock skew xem §7).  
2. **Hết hạn + không refresh:** coi như **không còn phiên tác động** — entry đó là **stale**; **không** dùng để chặn login mới.  
3. **Chặn phiên thứ hai** chỉ áp dụng khi entry **còn hiệu lực** theo (1).  
4. **Logout (Task002)** và mọi luồng revoke refresh sau này: vẫn **`clear(userId)`** như hiện tại.

---

## 5. Luồng xử lý đề xuất (HashMap — không SQL)

**Trước khi ném 403 concurrent** (`assertNoConcurrentSession` hoặc tương đương):

1. Nếu **không** có `userId` trong map → cho qua.  
2. Nếu có: lấy `accessJwt` đã lưu.  
3. **Nếu JWT đã hết hạn hoặc không parse được** (chuỗi hỏng) → **`remove(userId)`** (hoặc remove có điều kiện CAS) và **cho qua** (coi như không còn phiên).  
4. Nếu JWT **còn hạn** → giữ hành vi Task001: **403** (chặn đăng nhập thứ hai).

**Sau login thành công:** vẫn `register(userId, newAccessJwt)` như Task001.

**Sau logout:** `clear(userId)` như Task002.

**Không** cần thêm bảng DB cho map in-memory (SRS Task100 phạm vi HashMap).

---

## 6. Dữ liệu & SQL tham chiếu (Agent SQL)

| Chủ đề | Nội dung |
| :--- | :--- |
| **SQL runtime** | **Không** — `LoginSessionRegistry` chỉ bộ nhớ JVM. |
| **DB `refresh_tokens`** | Không đổi schema cho Task100; refresh còn hạn không đồng nghĩa “đang mở tab”. Đồng bộ nghĩa là **map theo access exp**, không theo `expires_at` refresh. |
| **Sau này (Redis / bảng session)** | Nếu chuyển lưu phiên: khuyến nghị **TTL = access TTL** hoặc cột `access_expires_at` + job quét — ghi ADR khi chuyển. |

---

## 7. Chốt kỹ thuật (PO / triển khai Task100)

| # | Chủ đề | Quyết định |
| :---: | :--- | :--- |
| 7.1 | Clock skew | **Không** margin bổ sung — `exp` theo server; có thể mở lại trong ADR nếu cần. |
| 7.2 | Audit auto-prune | **Không** log riêng khi gỡ stale (tránh nhiễu). |
| 7.3 | Profile bảo mật | Prune **cùng một** logic trên `permit-all` và `jwt-api` (chỉ đọc map + JWT). |

---

## 8. Acceptance Criteria (Given / When / Then)

```text
Given user đã login và map có entry với access JWT đã quá exp (user không refresh / không logout)
When gọi POST /api/v1/auth/login hợp lệ từ cùng hoặc thiết bị khác
Then không bị 403 chỉ vì entry stale; login thành công (200) và map được ghi access mới
```

```text
Given map có entry và access JWT trong map vẫn còn hạn
When gọi POST /api/v1/auth/login hợp lệ (phiên thứ hai)
Then 403 theo Task001 (chặn song song)
```

---

## 9. Handoff

- **DEV:** triển khai bước (3)–(4) mục §5 trong `LoginSessionRegistry` (hoặc lớp tiện ích JWT dùng chung) — parse `exp` bằng cùng secret/issuer/audience với phát token.  
- **TESTER:** bổ sung manual case vào kế hoạch Task001/Task100 (login sau khi chờ > TTL access, không gọi refresh).  
- **DOC_SYNC:** cập nhật `API_PROJECT_DESIGN` / trace Task100; Task001 SRS có thể thêm một dòng “map prune stale — xem Task100” sau khi PO Approved.

---

## 10. Traceability

| Nguồn | Ghi chú |
| :--- | :--- |
| `LoginSessionRegistry` | `ConcurrentHashMap<Integer, String>` |
| `JwtTokenService` | TTL access 5 phút (Task001) |
| Catalog dự án | [`API_PROJECT_DESIGN.md`](../../../frontend/docs/api/API_PROJECT_DESIGN.md) — mục Task100 / SRS |
