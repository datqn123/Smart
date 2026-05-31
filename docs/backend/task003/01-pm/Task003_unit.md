# Task003 — Unit (contract + kiểm thử tự động tối thiểu)

> **ID:** `Task-003-U`  
> **Loại:** **Unit theo nghiệp vụ** = (A) test tự động contract/slice + (B) bộ **manual** U-xx do Tester chạy tay — **cả hai** cùng chứng minh “đơn vị” `/auth/refresh`.  
> **SRS:** [`../../srs/SRS_Task003_auth_refresh.md`](../../srs/SRS_Task003_auth_refresh.md)  
> **API:** [`../../../../frontend/docs/api/API_Task003_auth_refresh.md`](../../../../frontend/docs/api/API_Task003_auth_refresh.md)

---

## 1. Mục tiêu (đo được)

1. **HTTP + envelope** khớp API Task003 cho: **200**, **400** (validation), **401** (refresh không hợp lệ), **429** (throttle).  
2. **Payload thành công:** `data` chỉ gồm `accessToken`, `refreshToken` — **không** có `user` (khác login Task001).  
3. **Không rotation:** `data.refreshToken` **bằng** chuỗi client gửi (SRS §5.1 tối thiểu).  
4. **Phiên đơn:** sau refresh, controller gọi `loginSessionRegistry.register(userId, newAccess)` (SRS §4).  
5. **Không** yêu cầu / không assert `INSERT` `SystemLogs` REFRESH.

---

## 2. Hai lớp “unit” (cách hiểu cho PM / Tester / Dev)

| Lớp | Ai làm | Công cụ | File / vị trí |
| :--- | :--- | :--- | :--- |
| **Postman envelope (3 file)** | Tester (+ Dev giữ CI xanh) | JSON repo | [`../../../AGENTS/TESTER_AGENT_INSTRUCTIONS.md`](../../../AGENTS/TESTER_AGENT_INSTRUCTIONS.md) §2.1 — mẫu `Task001_login.valid.body.json`; Task003: `Task003_refresh.valid.body.json`, `...invalid.missing-refresh...`, `...invalid.empty-refresh...` |
| **U-auto** | Dev + CI | JUnit | `.../AuthControllerWebMvcTest`, `.../AuthServiceRefreshTest`, `.../api/Task003RefreshPostmanBodyContractTest` |
| **U-manual** | Tester | Postman / tương đương | [`../04-tester/MANUAL_UNIT_TEST_Task003.md`](../04-tester/MANUAL_UNIT_TEST_Task003.md) |

**Quy tắc:** Automation **không** thay thế U-05 (chuỗi DB logout), U-07 (header thật), U-08 (chuỗi login→throttle→login) — các case đó vẫn **bắt buộc** trong manual P0/P1. Ba file Postman phải giữ **schema envelope** (contract test sẽ fail nếu thiếu `request.path` / `headers` / `body`).

---

## 3. Inventory test tự động (cập nhật theo code hiện tại)

### 3.1 `AuthControllerWebMvcTest` (`com.example.smart_erp.auth.controller`)

| Phương thức | Ý nghĩa nghiệp vụ | Mapping manual gần đương |
| :--- | :--- | :--- |
| `refresh_success_returns200RegistersSessionAndEchoesRefresh` | 200, envelope, `register` được gọi | U-01 (phần HTTP + registry qua verify) |
| `refresh_returns400WhenRefreshTokenBlank` | 400 + `details.refreshToken` | U-03 |
| `refresh_returns401WhenServiceUnauthorized` | 401 `UNAUTHORIZED` khi service ném | U-04 (mô phỏng lớp service) |
| `refresh_returns429WhenThrottled` | 429 `TOO_MANY_REQUESTS` | U-06 (mô phỏng service) |

**Cấu hình slice:** `@WebMvcTest(AuthController)` + import `GlobalExceptionHandler`, `SecurityBeansConfiguration`, `PermitAllWebSecurityConfiguration` — **không** nổi full DB.

### 3.2 `Task003RefreshPostmanBodyContractTest` (`com.example.smart_erp.auth.api`)

| Phương thức | Ý nghĩa |
| :--- | :--- |
| `validBody_matchesEnvelopeShape_andEndpoint` | File **valid** — `POST` + path `/api/v1/auth/refresh` + `body.refreshToken` không rỗng |
| `invalidMissingRefresh_bodyHasNoRefreshTokenKey` | File **invalid.missing** — `body` không có key `refreshToken` |
| `invalidEmptyRefresh_parsesBlankToken` | File **invalid.empty** — `refreshToken` = `""` |

### 3.3 `AuthServiceRefreshTest` (`com.example.smart_erp.auth.service`)

| Phương thức | Ý nghĩa | Ghi chú |
| :--- | :--- | :--- |
| `refresh_returnsNewAccessAndSameRefreshPlain` | JWT mới + refresh echo + đúng `userId` | Mock repo + JWT service |
| `refresh_throws401WhenNoValidRow` | Không có hàng refresh hợp lệ | |
| `refresh_throws401WhenUserNotActive` | User không Active | |
| `refresh_secondCallWithinWindow_is429` | Throttle 5 phút — `RefreshAccessThrottle` thật | Phụ thuộc thời gian hệ thống; chạy tuần tự trong class |

---

## 4. Hợp đồng field (khi viết thêm test)

### 4.1 Request `POST /api/v1/auth/refresh`

| Field | Ràng buộc | 400 message (gợi ý) |
| :--- | :--- | :--- |
| `refreshToken` | `@NotBlank` | *Refresh token là bắt buộc* |

**Lưu ý:** không `strip()` refresh ở record (giống logout) — test chỉ dùng chuỗi “đúng như client gửi”.

### 4.2 Response 200 `data`

| Field | Kiểu | Ghi chú |
| :--- | :--- | :--- |
| `accessToken` | string (JWT) | Mới ký; khác access trước đó trong kịch bản điển hình |
| `refreshToken` | string | **Trùng** request (Task003 không rotation) |

### 4.3 Response lỗi

| HTTP | `error` | `message` (backend hiện tại) |
| :---: | :--- | :--- |
| 400 | `BAD_REQUEST` | `Dữ liệu không hợp lệ` + `details` |
| 401 | `UNAUTHORIZED` | `Refresh token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.` |
| 429 | `TOO_MANY_REQUESTS` | `Vui lòng đợi 5 phút trước khi làm mới access token.` |

---

## 5. Artifact & đường dẫn

| Artifact | Đường dẫn |
| :--- | :--- |
| Manual U-xx | [`../04-tester/MANUAL_UNIT_TEST_Task003.md`](../04-tester/MANUAL_UNIT_TEST_Task003.md) |
| Test plan | [`../04-tester/TEST_PLAN_Task003.md`](../04-tester/TEST_PLAN_Task003.md) |
| Postman (3 envelope) | `Task003_refresh.valid.body.json`, `Task003_refresh.invalid.missing-refresh.body.json`, `Task003_refresh.invalid.empty-refresh.body.json` — [`../../../smart-erp/docs/postman/`](../../../smart-erp/docs/postman/) |
| Mã nguồn | `AuthController`, `AuthService#refresh`, `RefreshAccessThrottle`, `RefreshRequest` |

---

## 6. Verify (Dev / CI)

```text
cd backend/smart-erp
.\mvnw.cmd -q "-Dtest=AuthControllerWebMvcTest,AuthServiceRefreshTest,Task003RefreshPostmanBodyContractTest" test
```

Chạy full module (khi cần):

```text
.\mvnw.cmd verify
```

---

## 7. Definition of Done (Task-003-U)

### 7.1 Tự động

- [ ] `Task003RefreshPostmanBodyContractTest` xanh — **3 file** Postman đúng schema Task001.  
- [ ] `AuthControllerWebMvcTest` cover **200 / 400 / 401 / 429** cho endpoint refresh.  
- [ ] `AuthServiceRefreshTest` cover **happy path**, **401** (không row / không Active user), **429** throttle.  
- [ ] `mvn verify` xanh trên nhánh feature.

### 7.2 Thủ công (Tester)

- [ ] Hoàn thành tất cả **P0** trong [`TEST_PLAN_Task003.md`](../04-tester/TEST_PLAN_Task003.md) / [`MANUAL_UNIT_TEST_Task003.md`](../04-tester/MANUAL_UNIT_TEST_Task003.md) kèm **bằng chứng**.  
- [ ] **Đủ 3 file** envelope dưới `docs/postman/` (valid + missing + empty) theo [`TESTER_AGENT_INSTRUCTIONS.md`](../../../AGENTS/TESTER_AGENT_INSTRUCTIONS.md) §2.1; object `body` trong từng file khớp DTO sau mọi thay đổi Dev.

### 7.3 Không làm (tránh scope creep)

- [ ] Không bắt buộc automation E2E full DB trong task Unit — chuyển sang `Task-003-E` nếu cần.
