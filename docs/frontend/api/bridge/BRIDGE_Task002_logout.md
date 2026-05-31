# BRIDGE — Task002 logout

**Task:** Task002 | **Path:** `POST /api/v1/auth/logout` | **Mode:** wire-fe | **Date:** 2026-04-24

*Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y)*

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Path + Bearer + body | `API_Task002_logout.md` mục 1–2 | `AuthController` `@PostMapping("/logout")` | `authApi.ts` → `postLogout` + `auth: true` | Y | — |
| Gọi API khi đăng xuất | mục 2–3 | — | `sessionAuth.ts` → `tryServerLogout` | Y | Đã nối wire-fe |
| UI | `FEATURES_UI_INDEX` / Sidebar | — | `components/shared/layout/Sidebar.tsx` nút «Đăng xuất» | Y | Gọi `logoutAndGoToLogin` |
| Xóa phiên FE | — | — | `clearSessionAuth` + `useAuthStore.logout` + `navigate("/login")` | Y | — |

**Kết luận:** Logout gọi BE khi còn `accessToken` + `refreshToken`; luôn xóa storage và Zustand rồi về `/login` (best-effort nếu API lỗi).
