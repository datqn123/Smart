# BRIDGE — Task078_02 next staff code

**Task:** Task078_02 | **Path:** `GET /api/v1/users/next-staff-code` | **Mode:** wire-fe | **Date:** 2026-04-24

*Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y)*

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Path + GET + Bearer | `API_Task078_02_next_staff_code.md` mục 1–2 | `UsersController` `@GetMapping("/users/next-staff-code")` | `usersApi.ts` → `getNextStaffCode` (`auth: true`) | Y | — |
| Query `roleId` + `staffFamily` | mục 3 | `NextStaffCodeService` + `StaffFamily` | `roleUiToRoleId` + `staffFamilyFromUiRole` | Y | — |
| Response `data` | mục 4 | `NextStaffCodeData` | `EmployeeForm` nút **Lấy mã từ server** → `setValue("employeeCode")` | Y | Chỉ chế độ tạo mới |
| RBAC | mục 2 | `canManageStaff` giống `UserCreationService` | Cùng Bearer như `postCreateUser` | Y | — |

**Kết luận:** Đã nối `getNextStaffCode` và nút lấy mã trên `EmployeeForm.tsx` (tạo mới). Không dùng `fetch` ngoài `apiJson`.
