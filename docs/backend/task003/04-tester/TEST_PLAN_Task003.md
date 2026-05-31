# Tester — Kế hoạch kiểm thử Task003 (`POST /api/v1/auth/refresh`)

> **Phiên bản:** 1.2  
> **Loại:** Kiểm thử **thủ công** (manual “unit” theo từng request) + **3 file Postman envelope** + contract CI.

---

## 0. Bộ 3 file Postman (envelope Task001)

| # | File | Case manual chính |
| :---: | :--- | :--- |
| 1 | [`Task003_refresh.valid.body.json`](../../../smart-erp/docs/postman/Task003_refresh.valid.body.json) | U-01, U-07 (sửa `body.refreshToken`) |
| 2 | [`Task003_refresh.invalid.missing-refresh.body.json`](../../../smart-erp/docs/postman/Task003_refresh.invalid.missing-refresh.body.json) | U-02 |
| 3 | [`Task003_refresh.invalid.empty-refresh.body.json`](../../../smart-erp/docs/postman/Task003_refresh.invalid.empty-refresh.body.json) | U-03 |

**Schema & quy tắc:** [`../../../AGENTS/TESTER_AGENT_INSTRUCTIONS.md`](../../../AGENTS/TESTER_AGENT_INSTRUCTIONS.md) §2.1 — mẫu [`Task001_login.valid.body.json`](../../../smart-erp/docs/postman/Task001_login.valid.body.json).

---

## 1. Mục tiêu kiểm thử

1. Xác nhận hành vi **`POST /api/v1/auth/refresh`** khớp **SRS Task003** (§4–§5) và **API Task003** (request/response/error).  
2. Xác nhận **không rotation** refresh: `data.refreshToken` **trùng** input khi thành công.  
3. Xác nhận **throttle** 5 phút / user (429) và **clear** sau login / logout theo code hiện tại.  
4. Xác nhận **đồng bộ Task002**: sau logout, refresh cùng token → **401**.  
5. Ghi nhận **bằng chứng** (status + JSON + môi trường) đủ để Dev tái hiện.

---

## 2. Tài liệu tham chiếu (traceability)

| Loại | Đường dẫn |
| :--- | :--- |
| SRS (Approved) | [`../../srs/SRS_Task003_auth_refresh.md`](../../srs/SRS_Task003_auth_refresh.md) |
| API (Approved) | [`../../../../frontend/docs/api/API_Task003_auth_refresh.md`](../../../../frontend/docs/api/API_Task003_auth_refresh.md) |
| Envelope | [`../../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md`](../../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md) |
| Manual chi tiết | [`MANUAL_UNIT_TEST_Task003.md`](MANUAL_UNIT_TEST_Task003.md) |
| Postman JSON | [`../../../smart-erp/docs/postman/`](../../../smart-erp/docs/postman/) — **§0** (3 file `Task003_refresh.*`); thêm `Task001_login.*`, `Task002_logout.*` cho chuỗi |
| Task phụ thuộc | Task001 (login), Task002 (logout revoke) |

---

## 3. Phạm vi & ngoài phạm vi

| Trong phạm vi | Ngoài phạm vi (ghi ticket khác) |
| :--- | :--- |
| Mã HTTP 200 / 400 / 401 / 429 (+ 500 optional) | Load/stress; soak 24h |
| Body JSON + message lỗi chính | UI Mini-ERP (frontend agent) |
| Một user / một DB dev điển hình | Multi-pod throttle (in-memory không share) |
| Luồng login → refresh → logout | Rotation refresh (đã tắt SRS §7.1) |
| So sánh access JWT trước/sau (tay) | Giải mã claim đầy đủ (có thể dùng jwt.io — **không** dán secret) |

---

## 4. Chiến lược & cấp độ test

| Cấp độ | Mô tả | Công cụ | Trách nhiệm |
| :--- | :--- | :--- | :--- |
| **L1 — Manual unit** | Từng request độc lập U-01… | Postman / Bruno / curl | Tester — file [`MANUAL_UNIT_TEST_Task003.md`](MANUAL_UNIT_TEST_Task003.md) |
| **L2 — Automation** | Controller/service (mock) + **envelope Postman** | JUnit | `AuthControllerWebMvcTest`, `AuthServiceRefreshTest`, `Task003RefreshPostmanBodyContractTest` |
| **L3 — E2E (tùy sprint)** | Full stack + DB thật | Theo `Task003_e2e.md` | Tester + môi trường staging |

**Lệnh automation tham chiếu (Dev/CI):**

```text
cd backend/smart-erp
.\mvnw.cmd -q "-Dtest=AuthControllerWebMvcTest,AuthServiceRefreshTest,Task003RefreshPostmanBodyContractTest" test
```

---

## 5. Ma trận traceability (SRS / API / Auto)

| ID manual | Mô tả ngắn | HTTP | SRS § | API § | Ưu tiên | Gợi ý automation liên quan |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- |
| U-01 | Refresh thành công, refresh echo | 200 | §5.1 | §3.1 | P0 | `AuthControllerWebMvcTest#refresh_success_returns200RegistersSessionAndEchoesRefresh` + Postman **valid** envelope |
| U-02 | Thiếu `refreshToken` | 400 | §5.2 | §3.2 | P0 | Postman **invalid.missing** + `Task003RefreshPostmanBodyContractTest#invalidMissingRefresh_bodyHasNoRefreshTokenKey` |
| U-03 | `refreshToken` rỗng | 400 | §5.2 | §3.2 | P0 | `AuthControllerWebMvcTest#refresh_returns400WhenRefreshTokenBlank` + Postman **invalid.empty** + `Task003RefreshPostmanBodyContractTest#invalidEmptyRefresh_parsesBlankToken` |
| U-04 | Token không hợp lệ | 401 | §5.3 | §3.2 | P0 | `AuthServiceRefreshTest#refresh_throws401WhenNoValidRow`; WebMvc `refresh_returns401WhenServiceUnauthorized` |
| U-05 | Sau logout | 401 | §4 (sync Task002) | §3.2 | P0 | Manual / E2E (cần DB + logout) |
| U-06 | Throttle 5 phút | 429 | §7.2 | — | P0 | `AuthServiceRefreshTest#refresh_secondCallWithinWindow_is429`; WebMvc `refresh_returns429WhenThrottled` |
| U-07 | Bearer rác + body đúng | 200 | §4 | §2.1 | P1 | Manual (WebMvc hiện mock service; vẫn nên chạy tay tích hợp) |
| U-08 | Sau login clear throttle | 200 | §7.2 + code | — | P0 | Manual hoặc E2E (cần chuỗi login→429→login→refresh) |
| U-09 | 500 | 500 | — | §3.x / envelope | P2 | Manual / fault inject |

---

## 6. Dữ liệu kiểm thử (test data)

| Mã | Mô tả | Cách tạo |
| :--- | :--- | :--- |
| TD-01 | User Active + login OK | Tài khoản dev trong `AuthTask001Fixtures` / seed Flyway (theo môi trường). |
| TD-02 | Cặp `accessToken` / `refreshToken` hợp lệ | `POST /api/v1/auth/login` 200. |
| TD-03 | Refresh đã revoke | Thực hiện logout Task002 với TD-02. |
| TD-04 | Chuỗi refresh không tồn tại | Chuỗi 32 hex cố định không có trong DB. |

**Lưu ý JWT access:** TTL access trong code có thể rất ngắn (vd. 1 phút) — khi test logout/refresh, hoàn thành chuỗi **trước khi** access hết hạn nếu logout bắt buộc Bearer hợp lệ.

---

## 7. Thứ tự chạy khuyến nghị (tránh nhiễu throttle)

1. **U-02, U-03, U-04** — không phụ thuộc login (U-04 không tạo throttle thành công).  
2. **U-01** — cần login; ghi nhận thời điểm nếu sau đó chạy U-06.  
3. **U-06** — chỉ chạy khi đã hiểu trạng thái throttle (xem manual §2 E-5).  
4. **U-05** — tiêu tố refresh; cần **login lại** trước các case cần refresh hợp lệ.  
5. **U-07, U-08, U-09** — theo điều kiện trong manual.

---

## 8. Tiêu chí vào / ra (gate Tester)

**Vào (entry):** SRS + API Task003 **Approved**; build có endpoint refresh; DB migration refresh tồn tại.

**Ra (exit) cho “đạt” manual sprint:**

- Tất cả case **P0** (U-01, U-02, U-03, U-04, U-05, U-06, U-08) = **Pass** trên ít nhất một môi trường chuẩn (local hoặc staging).  
- Mọi **Fail** có ticket defect kèm bằng chứng theo manual §8.

---

## 9. Rủi ro & mitigation

| Rủi ro | Ảnh hưởng | Mitigation |
| :--- | :--- | :--- |
| Throttle in-memory / instance | U-06 khác nhau giữa local vs cluster | Ghi rõ “1 replica”; staging 1 pod hoặc chấp nhận gap. |
| Access TTL ngắn | Logout fail 401 trước khi test refresh chain | Login lại; làm nhanh; hoặc tăng TTL chỉ trên env test (ADR). |
| API doc còn `INTERNAL_ERROR` / SystemLogs | Lệch tài liệu | Doc Sync ticket; manual ưu tiên SRS + code. |

---

## 10. Deliverable Tester

| Artifact | Trạng thái |
| :--- | :--- |
| [`MANUAL_UNIT_TEST_Task003.md`](MANUAL_UNIT_TEST_Task003.md) | Pass/Fail điền đầy đủ + bằng chứng |
| Ticket / báo cáo sprint | Link commit, môi trường, người chạy, ngày |
