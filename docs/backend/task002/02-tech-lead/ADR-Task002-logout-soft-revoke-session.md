# ADR — Task002: Logout soft revoke (`delete_ymd`) + phiên đơn (HashMap)

> **Trạng thái:** Proposed (Tech Lead — chờ PR / Owner)  
> **SRS:** [`../../srs/SRS_Task002_logout.md`](../../srs/SRS_Task002_logout.md)  
> **Ngày:** 24/04/2026

## 1. Bối cảnh

Logout thu hồi refresh bằng **`UPDATE delete_ymd`** thay vì `DELETE` để giảm chi phí ghi; phiên đơn dùng **ConcurrentHashMap** (Task001). DB commit và remove map **không** cùng atomic transaction.

## 2. Quyết định

1. Thu hồi refresh: **`UPDATE … SET delete_ymd = now()`** với `delete_ymd IS NULL` + điều kiện `user_id` + `token`.  
2. **403** nếu `UPDATE` cập nhật 0 dòng và JWT access vẫn hợp lệ.  
3. **Sau commit DB** mới remove entry session theo `user_id`.  
4. Lỗi 500: envelope **`INTERNAL_SERVER_ERROR`** ([`API_RESPONSE_ENVELOPE.md`](../../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md)).  
5. Archive/partition `refresh_tokens`: **ngoài** Task002 (tech debt).

## 3. Hệ quả

- Task001 / Task003 phải lọc **`delete_ymd IS NULL`** khi đọc refresh hợp lệ.  
- Cần migration Flyway thêm cột.  
- `API_Task002_logout.md` mẫu 500 nên dần thống nhất `INTERNAL_SERVER_ERROR` (Doc Sync).

---

## 4. NFR (bắt buộc)

### 4.1 Performance

| | Nội dung |
| :--- | :--- |
| **Hiện trạng** | Chưa có endpoint logout production. |
| **Mục tiêu** | p95 logout (DB + map) trong ngưỡng team (ví dụ &lt; 300 ms trên dev có DB local) khi không cold start. |
| **Cách đo** | Log thời gian service; hoặc JMH/Micrometer timer trên method logout sau triển khai. |

### 4.2 Scalability

| | Nội dung |
| :--- | :--- |
| **Hiện trạng** | In-memory map một instance JVM. |
| **Mục tiêu** | Khi scale horizontal → thay map bằng Redis (ADR follow-up); contract remove session giữ nguyên semantically. |
| **Cách đo** | Checklist deploy 2 instance + soak test session (sau khi có hạ tầng). |

### 4.3 Security

| | Nội dung |
| :--- | :--- |
| **Hiện trạng** | JWT resource server + refresh DB. |
| **Mục tiêu** | Không chấp nhận refresh đã `delete_ymd`; không lộ khác biệt user tồn tại hay không trong message 403 (theo API). |
| **Cách đo** | Review test 403/401; SAST dependency check trong CI. |

### 4.4 Reliability

| | Nội dung |
| :--- | :--- |
| **Hiện trạng** | DB commit và map có thể lệch tạm thời. |
| **Mục tiêu** | Nếu remove map fail: log WARNING + metric; không rollback DB; user vẫn không refresh được do `delete_ymd`. |
| **Cách đo** | Test inject failure sau commit; quan sát log + trạng thái refresh. |

### 4.5 Observability

| | Nội dung |
| :--- | :--- |
| **Hiện trạng** | SystemLogs cho LOGOUT. |
| **Mục tiêu** | Mỗi logout thành công có log audit; cảnh báo khi remove map lỗi (counter hoặc log level WARNING). |
| **Cách đo** | Assert log trong test hoặc kiểm tra staging log pipeline. |
