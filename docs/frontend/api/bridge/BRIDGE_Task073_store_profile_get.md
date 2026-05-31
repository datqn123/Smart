Task: **Task073**  
Path: **GET `/api/v1/store-profile`**  
Mode: **verify**  
Date: **2026-04-30**

- Đã đọc `FE_API_CONNECTION_GUIDE.md`: **Y**

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| RBAC `can_view_store_profile` | `API_Task073` §4 | `StoreProfileController.java` `@PreAuthorize("hasAuthority('can_view_store_profile')")`; Flyway `V28__task073_075_can_view_store_profile_permission.sql`; `MenuPermissionClaims.java` | Chưa gọi API trong `mini-erp` | Y (BE↔Doc) | Khi `wire-fe`: đảm bảo UI xử lý 401/403 theo guide |
| Response fields (incl. `defaultRetailLocationId`) | `API_Task073` §5 | `StoreProfileData.java`; `StoreProfileJdbcRepository.java` select `default_retail_location_id` | `StoreInfoPage.tsx` hiện mock (không có fetch) | Y (BE↔Doc), N (FE) | `wire-fe`: map field camelCase và thay mock bằng query |
| Auto-create row khi thiếu | `API_Task073` §1 | `StoreProfileService.getOrCreate()` gọi `repo.ensureExists()` | — | Y | OK |

| Wire FE (GET) | `API_Task073` §2, §5 | `StoreProfileController.java` | `features/settings/api/storeProfileApi.ts` (`getStoreProfile`), `features/settings/pages/StoreInfoPage.tsx` (`useQuery`) | Y | Đã nối GET; PATCH/Logo sẽ làm theo Task074/075 |

Kết luận:
- BE khớp spec Task073.
- FE đã nối `GET /api/v1/store-profile` vào `StoreInfoPage` (đọc theo guide FE).

