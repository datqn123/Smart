# Codebase Analyst — Brief Task002 (brownfield)

**Mục đích:** Ghi nhận hiện trạng mã trước/sau Task002 để Doc Sync đối chiếu.

## Cần khảo sát (khi Dev mở PR)

- `AuthController` / `AuthService` — có endpoint logout chưa.  
- `RefreshToken` entity + `RefreshTokenRepository`.  
- `LoginSessionRegistry` (ConcurrentHashMap) — API remove theo user id.  
- Flyway version hiện tại sau `V3__task001_refresh_tokens.sql`.

## Output mong đợi (sau merge)

- Cập nhật mục “Auth / Session” trong báo cáo brownfield chung (nếu team dùng template `backend/AGENTS/briefs/`) — liên kết PR Task002.
