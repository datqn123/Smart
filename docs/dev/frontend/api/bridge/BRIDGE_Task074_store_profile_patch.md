Task: **Task074**  
Path: **PATCH `/api/v1/store-profile`**  
Mode: **verify**  
Date: **2026-04-30**

- Đã đọc `FE_API_CONNECTION_GUIDE.md`: **Y**

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| RBAC `can_view_store_profile` | `API_Task074` §2 | `StoreProfileController.java` `@PreAuthorize("hasAuthority('can_view_store_profile')")`; Flyway `V28...` | Chưa gọi API trong `mini-erp` | Y (BE↔Doc) | Khi `wire-fe`: handle 403 theo guide |
| Patch body partial + “ít nhất 1 field” | `API_Task074` §3, §7 | `StoreProfileService.patch()` kiểm tra body rỗng → 400 + details `{ body: "Cần ít nhất một trường" }` | `StoreInfoPage.tsx` hiện mock state | Y (BE↔Doc), N (FE) | `wire-fe`: build patch body theo field thay đổi và map details vào form |
| Validate `defaultRetailLocationId` | `API_Task074` §3 | `StoreProfileJdbcRepository.existsWarehouseLocation()` + check trong `StoreProfileService.patch()` → 400 details | — | Y | OK |
| Response 200 trả object đầy đủ | `API_Task074` §5 | `StoreProfileData.java` return | — | Y | OK |

| Wire FE (PATCH) | `API_Task074` §1–§7 | `StoreProfileController.java` | `features/settings/api/storeProfileApi.ts` (`patchStoreProfile`), `features/settings/pages/StoreInfoPage.tsx` (`useMutation`) | Y | Đã nối PATCH; refetch GET Task073 sau success |

Kết luận:
- BE khớp spec Task074.
- FE đã nối `PATCH /api/v1/store-profile` vào nút “Lưu thay đổi” của `StoreInfoPage`.

