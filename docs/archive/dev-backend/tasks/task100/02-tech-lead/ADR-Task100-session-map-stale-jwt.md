# ADR — Task100: Prune `LoginSessionRegistry` khi access JWT hết hạn

> **Trạng thái:** Accepted (kèm SRS Task100)  
> **SRS:** [`../../srs/SRS_Task100_auth-session-registry-stale-access.md`](../../srs/SRS_Task100_auth-session-registry-stale-access.md)

## Quyết định

- Trước 403 concurrent, nếu entry map có JWT **đã hết hạn** hoặc **không verify được** (ký/iss/aud/exp) → **remove** entry, **không** 403.
- JWT còn hạn (theo `exp` server, **không** margin skew — PO có thể bổ sung sau) → giữ 403 Task001.

## NFR (rút gọn)

| Tiêu chí | Cách đo |
| :--- | :--- |
| Performance | Parse JWT O(1) mỗi login; không query DB thêm. |
| Scalability | Một JVM; khi Redis — TTL key = access TTL (ADR sau). |
| Security | Chỉ chấp nhận JWT ký đúng secret + iss/aud đã cấu hình. |
| Reliability | `remove(userId, token)` CAS tránh xóa nhầm token mới. |
| Observability | Chưa bắt buộc log auto-prune (SRS §7.2 mặc định tắt). |
