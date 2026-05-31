# BRIDGE — Task001 login

**Task:** Task001 | **Path:** `POST /api/v1/auth/login` | **Mode:** wire-fe | **Date:** 2026-04-24

*Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y)*

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Path + method | `API_Task001_login.md` mục 1 | `AuthController` `@PostMapping("/login")` | `authApi.ts` → `postLogin` | Y | — |
| Request / envelope | mục 2–3 | `LoginRequest`, `LoginResponseData` | `apiJson` + `postLogin` | Y | — |
| Client validate (Zod) | mục 5 | — | `LoginForm.tsx` — `loginSchema` đồng bộ message / refine mật khẩu | Y | Đã chỉnh wire-fe |
| 400 `details` → field | mục 3.2 | Bean Validation → `GlobalExceptionHandler` | `LoginForm` `setError` email/password + `submitError` | Y | — |
| 401 / 403 / lỗi khác | mục 3.2 | — | `submitError` từ `ApiRequestError.body.message` | Y | — |
| Session + điều hướng | UC đăng nhập | — | `sessionStorage` + `navigate("/dashboard")` | Y | — |

**Kết luận:** Endpoint đã nối qua `features/auth/api/authApi.ts` và `LoginForm.tsx`. Phiên `wire-fe` căn **Zod** với spec (email bắt buộc, mật khẩu ≥6 ký tự và không chỉ khoảng trắng). Không thêm `fetch` ngoài `apiJson`.
