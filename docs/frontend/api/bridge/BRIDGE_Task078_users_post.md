# BRIDGE — Task078 users POST

**Task:** Task078 | **Path:** `POST /api/v1/users` | **Mode:** wire-fe | **Date:** 2026-04-24

*Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y)*

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Path + method + Bearer | `API_Task078_users_post.md` mục 1–2 | `UsersController` `@PostMapping("/users")` | `settings/api/usersApi.ts` → `postCreateUser` (`auth: true`) | Y | — |
| Body camelCase | mục 3 + Zod mục 7 | `UserCreateRequest` | `buildUserCreateBody` từ form tạo mới | Y | — |
| Response 201 / `data` | mục 5 | `UserResponseData` | `userResponseToEmployee` → state `EmployeesPage` | Y | Map `role` BE (Owner/Staff/Admin) → `Employee.role` UI |
| Form client | mục 7 | — | `EmployeeForm.tsx` — schema tạo: username, password ≥8, … | Y | Tách schema create vs edit |
| `roleId` | mục 3 | `Roles` seed (Owner/Staff/Admin) | `roleUiToRoleId` — Manager/Warehouse map tạm sang Admin/Staff | P | Chờ API roles hoặc migration đủ vai trò |
| 400/409/401/403 | mục 6 | `BusinessException` / envelope | `EmployeesPage` `toast.error` từ `ApiRequestError` | P | Chưa map `details` → từng field form |

**Kết luận:** Đã nối `postCreateUser` qua `apiJson`; luồng **Thêm mới** trên `/settings/employees` gọi BE, **Sửa** vẫn mock local. Không dùng `fetch` ngoài `apiJson`. Cần JWT + quyền `can_manage_staff` khi BE bật `jwt-api`.
