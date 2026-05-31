# Bug_Task021 — GET audit-sessions: 500 “Đã xảy ra lỗi hệ thống…”

## Metadata
- Task / SRS: Task021 — danh sách đợt kiểm kê (`GET /api/v1/inventory/audit-sessions`)
- Môi trường: BE `http://localhost:8080` (theo Owner)
- Ngày / phiên: BUG_INVESTIGATOR — 2026-04-26

## Ngân sách phiên (Agent BUG_INVESTIGATOR tự ghi — §4.1)
- File đã `read` (đường dẫn + ~số dòng mỗi file):
  - `backend/smart-erp/src/main/java/com/example/smart_erp/common/exception/GlobalExceptionHandler.java` — ~13 dòng (§ `handleGeneric`)
  - `backend/smart-erp/src/main/java/com/example/smart_erp/inventory/audit/repository/AuditSessionJdbcRepository.java` — ~35 + ~32 dòng (`countList`/`loadListPage` + `buildFilter`)
- Số lần `grep`: 1 / 3 — Context7: Không

## Triệu chứng
- Màn **Kiểm kê kho** không tải được danh sách.
- Response API: **500** / `INTERNAL_SERVER_ERROR`, message: **“Đã xảy ra lỗi hệ thống, vui lòng thử lại sau”**.

## Tái hiện (bước ngắn)
1. Đăng nhập bằng admin (có quyền gọi API).
2. Mở giao diện Kiểm kê kho → FE gọi `GET /api/v1/inventory/audit-sessions?page=1&limit=20` (hoặc tương đương).

## Bằng chứng (đã che secret)
- Network: **GET** `/api/v1/inventory/audit-sessions` → **500**, body envelope lỗi với message trên (chuẩn `GlobalExceptionHandler` xử lý mọi `Exception` chưa được map).

```90:93:backend/smart-erp/src/main/java/com/example/smart_erp/common/exception/GlobalExceptionHandler.java
	@ExceptionHandler(Exception.class)
	public ResponseEntity<ApiErrorResponse> handleGeneric(Exception ex) {
		return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(ApiErrorResponse.of(
				ApiErrorCode.INTERNAL_SERVER_ERROR, "Đã xảy ra lỗi hệ thống, vui lòng thử lại sau"));
```

- List đợt kiểm kê luôn đi qua SQL có điều kiện **`s.deleted_at IS NULL`**:

```452:454:backend/smart-erp/src/main/java/com/example/smart_erp/inventory/audit/repository/AuditSessionJdbcRepository.java
	private Filter buildFilter(AuditSessionListQuery q) {
		StringBuilder where = new StringBuilder(" WHERE s.deleted_at IS NULL");
		var src = new MapSqlParameterSource();
```

- Cột `deleted_at` được thêm bởi Flyway **V12** (soft-delete theo SRS Task021–028):

```6:7:backend/smart-erp/src/main/resources/db/migration/V12__inventory_audit_sessions_v2_status_softdelete_events.sql
ALTER TABLE inventoryauditsessions
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ NULL;
```

## Phân tích

### Giả thuyết chính (khả năng cao nhất)
**DB chưa khớp mã (Flyway chưa chạy tới V12 hoặc DB cũ thiếu cột `deleted_at`).**  
Khi Postgres thực thi `COUNT` / `SELECT` list, tham chiếu `s.deleted_at` → **lỗi SQL** → ném ngoại lệ → `handleGeneric` → đúng message 500 mà Owner thấy (log gốc *không* trả về cho client trong handler hiện tại).

### Giả thuyết phụ
- **Lỗi SQL khác** (bảng `inventoryauditsessions` / `inventoryauditlines` / `users` thiếu hoặc tên khác môi trường) — ít gặp nếu cùng một Postgres baseline repo; cần **1 đoạn stack JDBC** từ log BE để xác nhận trong vài phút.
- **Dữ liệu / constraint** gây lỗi runtime trong layer khác trước khi trả JSON — vẫn bị gói vào cùng message 500; stack trace là chốt.

## Ánh xạ mã (file tối thiểu)
| File | Vai trò | Ghi chú |
|------|---------|--------|
| `GlobalExceptionHandler.java` | Trả 500 + message chung | Mọi `Exception` không handler riêng |
| `AuditSessionJdbcRepository.java` | SQL list + `WHERE s.deleted_at IS NULL` | `countList` / `loadListPage` |
| `V12__inventory_audit_sessions_v2_status_softdelete_events.sql` | Thêm `deleted_at` | Khớp code list |

## Phương án xử lý (Owner chốt một dòng)

### A. Đồng bộ DB với Flyway (khuyến nghị)
- **Ưu:** Khớp SRS + mã hiện tại; không phá soft-delete.
- **Nhược:** Cần quyền chạy migration trên đúng DB dev.
- **Rủi ro:** Thấp (V12 dùng `IF NOT EXISTS` cho cột).
- **Effort:** S

### B. Xác minh rồi sửa đích danh
- Chạy / kiểm tra `flyway_schema_history` (hoặc log khởi động Spring) xem **V12 đã applied chưa**; nếu fail migration trước đó → repair + migrate.
- **Ưu:** Chắc chắn nguyên nhân trước khi đổi mã.
- **Effort:** S

### C. (Không khuyến nghị) Gỡ `deleted_at` khỏi query list
- **Nhược:** Lệch SRS (soft-delete), rủi ro bảo trì.
- **Effort:** S nhưng **technical debt**

## Khuyến nghị gợi ý
Chọn **A + B**: bật BE, xem log một request list — nếu thấy `column "deleted_at" does not exist` (hoặc tương tự) thì chạy migration tới ≥ V12 trên đúng datasource `localhost:8080` đang trỏ tới.

## Handoff Developer
- Sau khi chốt: `@backend/AGENTS/DEVELOPER_AGENT_INSTRUCTIONS.md` + phương án đã chọn + link `backend/docs/bugs/Bug_Task021.md`.
- **Verify:** `GET /api/v1/inventory/audit-sessions?page=1&limit=20` → **200** + envelope `success`; UI Kiểm kê kho hiển thị bảng (kể cả rỗng).

## Open questions
- Log console BE **đầy đủ** cho một request 500 (20–40 dòng quanh `PSQLException` / `BadSqlGrammarException`) — để khóa 100% nếu không phải thiếu cột.

---

## Kết quả Developer — phương án A + B (tham chiếu `DEVELOPER_AGENT_INSTRUCTIONS.md`)

**B — Xác minh Flyway (`flyway:info`, JDBC trùng `pom.xml`):** DB `jdbc:postgresql://localhost:5432/smart_erp` đang **schema version 14**; migration **V12** (*inventory audit sessions v2 status softdelete events*) trạng thái **Success** (cùng các bản V11, V13).

**A — Đồng bộ:** `flyway:migrate` → *Schema is up to date. No migration necessary.*

**Kết luận:** Trên cùng máy/DB với cấu hình Maven mặc định, lỗi 500 **không** do thiếu migration V12. Nếu môi trường Owner vẫn 500, kiểm tra nhanh:

1. BE có đang bật **`spring.profiles.active=postgres`** (mặc định trong `application.properties`) hay lỡ **`local`** (H2 + `flyway=false` → schema audit không đủ).
2. `spring.datasource.url` khi chạy app có **trùng** DB đã migrate (không trỏ DB khác rỗng/cũ).
3. Dán stack trace một request thất bại (server log) vào mục Open questions ở trên.

**Ghi chú repo:** Đã bổ sung cảnh báo trong `application-local.properties` về giới hạn profile `local` với API kiểm kê.

**RCA cuối (log `BadSqlGrammarException`):** Chuỗi SQL bị dính `IS NULLORDER` và `LIMIT20` — do **text block Java** (JEP 378) **strip khoảng trắng cuối dòng**; phần `LIMIT ` trước `"""` mất space → nối số trang thành `LIMIT20`. **Sửa mã:** `AuditSessionJdbcRepository.loadListPage` — đuôi `ORDER BY` / `LIMIT` / `OFFSET` nối bằng literal `" ORDER BY s.id ASC LIMIT " + q.limit() + " OFFSET " + offset` (không phụ thuộc space cuối dòng text block).
