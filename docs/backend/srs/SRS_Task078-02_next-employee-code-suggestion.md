# SRS — Task078_02 — Gợi ý mã nhân viên tiếp theo (next employee code)

> **File:** `backend/docs/srs/SRS_Task078-02_next-employee-code-suggestion.md`  
> **Người viết:** Agent BA + SQL (Draft, cập nhật theo trả lời PO)  
> **Ngày:** 24/04/2026  
> **Trạng thái:** Approved

**Traceability:** UC3 / Task078 [`SRS_Task078_users-post.md`](./SRS_Task078_users-post.md) · Task078_01 [`SRS_Task078-01_validate-create-user-inputs.md`](./SRS_Task078-01_validate-create-user-inputs.md) · Task077 read-model [`../../../frontend/docs/api/API_Task077_users_get_list.md`](../../../frontend/docs/api/API_Task077_users_get_list.md) · **API Task078_02** [`../../../frontend/docs/api/API_Task078_02_next_staff_code.md`](../../../frontend/docs/api/API_Task078_02_next_staff_code.md) · Flyway [`../../smart-erp/src/main/resources/db/migration/V5__task078_users_staff_code.sql`](../../smart-erp/src/main/resources/db/migration/V5__task078_users_staff_code.sql) · Envelope [`../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md`](../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md)

---

## 1. Tóm tắt & vấn đề

- Form tạo nhân viên cần **`staff_code`** (hiển thị như `employeeCode`). PO yêu cầu **endpoint đọc** trả về **mã tiếp theo** theo thứ tự đã lưu (vd. `NV-MAN-002` → gợi ý `NV-MAN-003`).
- **Nguồn dữ liệu:** `users.staff_code` (`VARCHAR(50)`, nullable, unique khi not null) — V5.

---

## 2. Phạm vi

### 2.1 In-scope

- `GET /api/v1/users/next-staff-code` (chi tiết [`API_Task078_02_next_staff_code.md`](../../../frontend/docs/api/API_Task078_02_next_staff_code.md)).
- Đọc `users.staff_code`, tính suffix số tối đa theo **prefix** suy ra từ **`roleId`** (form chọn vai trò).
- RBAC + JWT như mục 3.

### 2.2 Out-of-scope

- Giữ chỗ / lock mã; thay đổi DDL (ngoài index gợi ý tùy chọn).

---

## 3. Persona & RBAC — **Quyết định PO (đã chốt)**

| Quyết định | Nội dung |
| :--- | :--- |
| Xác thực | **Bearer JWT bắt buộc**, cùng cơ chế Resource Server như `POST /api/v1/users`. |
| Quyền | Chỉ khi actor có quyền **tạo / quản lý nhân viên** (tương đương `can_manage_staff` / policy Task078); không đủ → **403**. |

---

## 4. Đầu vào & suy ra prefix — **Quyết định PO (đã chốt)**

| Quyết định | Nội dung |
| :--- | :--- |
| Tham số chính | Query **`roleId`** (số nguyên > 0) — khớp vai trò đang chọn trên form. |
| Prefix | **Không** do người dùng nhập tự do: do **BE suy ra** từ `roleId` qua **ánh xạ cấu hình** (vd. role quản lý → `NV-MAN`, role kho → `NV-WH`). |
| Ghi chú PO | “Không phụ thuộc vào prefix tự nhập mà phụ thuộc **vai trò / quyền hiển thị ở form** → prefix khác nhau.” |

**[CẦN CHỐT] triển khai (Dev/PO):** Bảng `Roles` hiện **chưa** có cột prefix trong Flyway — v1 triển khai dùng **constants trong application** (map `roleId` → chuỗi prefix). Nếu sau này đưa prefix vào DB → migration + đọc từ `Roles`.

---

## 5. Quy tắc sinh mã & edge — **Quyết định / mặc định đồ án**

1. Gọi SQL (hoặc JPQL/native tương đương) với `:prefix` đã suy ra từ `roleId`.
2. Chỉ tính các `staff_code` khớp mẫu **`^<prefix>-[0-9]+$`** (một cụm số ở cuối).
3. `next_numeric = COALESCE(MAX(suffix), 0) + 1`.
4. **Không có** mã khớp → mã đầu tiên **`<prefix>-001`** (đệm **3 chữ số** — mặc định đồ án; PO có thể đổi qua CR).
5. **Dòng không parse được** (không khớp regex): **bỏ qua** khi tính `MAX` (không sửa DB). Nếu mọi dòng đều không khớp → coi như không có mã hợp lệ → trả `<prefix>-001`.
6. **Concurrency:** hai GET đồng thời có thể cùng `nextCode`; xung đột khi POST vẫn xử lý bởi unique `staff_code` (**409**) — chấp nhận theo Task078.

---

## 6. Acceptance Criteria (Given / When / Then)

```text
Given JWT hợp lệ và actor có quyền quản lý nhân viên
When GET …/next-staff-code?roleId=<id> và roleId ánh xạ tới prefix NV-MAN, DB có NV-MAN-001 và NV-MAN-002
Then HTTP 200 và data.nextCode = NV-MAN-003 (đệm 3 số)
```

```text
Given điều kiện trên nhưng không có staff_code nào khớp pattern prefix đó
When GET với cùng roleId
Then HTTP 200 và data.nextCode = <prefix>-001
```

```text
Given không có JWT hoặc không đủ quyền
When GET endpoint
Then HTTP 401 hoặc 403 theo policy dự án
```

```text
Given roleId thiếu hoặc ≤ 0 hoặc không có trong ánh xạ prefix
When GET
Then HTTP 400 và envelope lỗi (details nếu áp dụng style Task078_01)
```

---

## 7. Dữ liệu & SQL tham chiếu (Agent SQL — PostgreSQL)

### 7.1 Bảng / cột (Flyway, không bịa)

| Đối tượng | Mô tả |
| :--- | :--- |
| `users` | JPA `@Table(name = "users")` |
| `users.staff_code` | `VARCHAR(50)` nullable; partial unique `uq_users_staff_code` (V5) |

### 7.2 Transaction & cô lập

- **Một** `SELECT` thuần đọc → `READ COMMITTED`, **`@Transactional(readOnly = true)`** (Spring); **không** `SELECT … FOR UPDATE`.
- **Hậu quả concurrent:** như mục 5.6 — không lost update trên GET; trùng khi INSERT user.

### 7.3 Câu lệnh SQL — bước 1: max suffix hợp lệ

**Tham số:** `:prefix` — chuỗi an toàn do app tạo (chỉ ký tự cho phép trong quy ước đặt mã, **không** chứa ký tự đặc biệt regex; vd. `NV-MAN`).  
**Ý nghĩa:** mọi `staff_code` khớp `^prefix-[0-9]+$`.

```sql
SELECT COALESCE(MAX(x.suffix), 0) AS max_suffix
FROM (
  SELECT (regexp_match(u.staff_code, '^' || :prefix || '-([0-9]+)$'))[1]::int AS suffix
  FROM users u
  WHERE u.staff_code IS NOT NULL
) AS x
WHERE x.suffix IS NOT NULL;
```

- `regexp_match` trả `NULL` nếu không khớp → hàng bị loại bởi `WHERE x.suffix IS NOT NULL` → đúng policy **bỏ qua** mã hỏng format.
- `COALESCE(MAX(...), 0)` khi không còn hàng nào sau lọc → `0` → mã tiếp theo logic app là `1`.

### 7.4 Ghép `nextCode` (khuyến nghị tầng app)

Tránh nhồi format chuỗi phức tạp trong SQL (dễ test):

```text
next_suffix := kết quả max_suffix + 1
nextCode    := prefix || '-' || lpad(next_suffix::text, 3, '0')
```

Độ dài tổng phải **≤ 50**; nếu `next_suffix` vượt ngưỡng → **400** hoặc overflow policy **[CẦN CHỐT]** (hiếu khi VARCHAR(50)).

### 7.5 Ràng buộc prefix trong regex

Ký tự `-` trong `prefix` literal (vd. `NV-MAN`) nằm **bên trong** nhóm tĩnh trước `-([0-9]+)$` — mẫu `'^' || :prefix || '-([0-9]+)$'` là đúng nếu `prefix` không chứa metacharacter regex. **App phải validate** `prefix` (vd. chỉ `[A-Za-z0-9]+` hoặc whitelist).

### 7.6 Index gợi ý (tùy chọn — khi bảng lớn / EXPLAIN chậm)

 btree trên cột giúp một phần truy vấn lọc; với pattern prefix, PostgreSQL có thể dùng btree + điều kiện bổ sung:

```sql
CREATE INDEX IF NOT EXISTS idx_users_staff_code_not_null
  ON users (staff_code)
  WHERE staff_code IS NOT NULL;
```

**Ghi chú SQL Agent:** với volume nhỏ (đồ án), index có thể **chưa** cần; khi triển khai production, chạy `EXPLAIN (ANALYZE, BUFFERS)` trên query thật rồi quyết định thêm `V{n}__idx_users_staff_code.sql`.

### 7.7 Kiểm thử dữ liệu (tiêu chí cho Tester / Dev)

| Bước | Kỳ vọng |
| :--- | :--- |
| Seed `staff_code` = `NV-MAN-001`, `NV-MAN-002` | `max_suffix` = 2 |
| Xóa hết mã khớp `NV-MAN-*` | `max_suffix` = 0 → next `001` |
| Thêm `NV-MAN-bad` | Bị bỏ qua, không làm hỏng MAX |

---

## 8. Open Questions (còn lại sau trả lời PO)

1. **Bảng ánh xạ `roleId` → prefix`:** nội dung cụ thể từng role (seed hiện có Owner/Staff/Admin + UI có thể mở rộng) — Dev/PO liệt kê constants hoặc CR thêm cột `Roles.staff_code_prefix`.
2. **Tham số `prefix` override** trên API có bật không (mục 3 file API) — mặc định tắt.
3. **Số chữ số đệm** khác 3 — chỉ đổi bằng CR đã duyệt.

---

## 9. GAP / rủi ro

| GAP | Ghi chú |
| :--- | :--- |
| `Roles` chưa có prefix trong DB | Map tạm trong code; drift FE (4 nhãn) vs DB (3 role seed) cần thống nhất. |
| `regexp_match` cần prefix an toàn | Validate đầu vào ở tầng app trước khi nối chuỗi vào SQL. |

---

## 10. Không làm trong SRS này

- Không viết mã production Java/TypeScript trong file này.
- Không chốt thay PO các mục **[CẦN CHỐT]** ở mục 8.
