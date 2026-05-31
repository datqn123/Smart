# BRIDGE — Task003 refresh

**Task:** Task003 | **Path:** `POST /api/v1/auth/refresh` | **Mode:** wire-fe | **Date:** 2026-04-24

*Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y)*

| Hạng mục | API doc (mục) | Backend (file) | Frontend | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Path + body (no Bearer) | `API_Task003_auth_refresh.md` mục 1–2 | `AuthController` `@PostMapping("/refresh")` | `authApi.ts` → `postRefresh` (gọi tay khi cần) | Y | — |
| Tự refresh khi access hết hạn | mục 1 (duy trì phiên) | — | `lib/api/refreshAccessToken.ts` + `http.ts` retry **một lần** sau **401** nếu `auth: true` | Y | Đã nối wire-fe |
| Tránh lặp | — | — | Không retry trên `/api/v1/auth/login` và `/api/v1/auth/refresh`; cờ `_didRefresh` | Y | — |

**Kết luận:** Mọi `apiJson(..., { auth: true })` nhận **401** sẽ thử `POST /auth/refresh` với `refreshToken` trong storage, cập nhật token rồi **gọi lại** request tối đa một lần. Gọi trực tiếp `postRefresh` vẫn dùng được cho luồng tùy chỉnh.
