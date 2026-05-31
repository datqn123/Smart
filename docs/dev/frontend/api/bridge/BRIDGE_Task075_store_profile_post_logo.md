Task: **Task075**  
Path: **POST `/api/v1/store-profile/logo`**  
Mode: **verify**  
Date: **2026-04-30**

- Đã đọc `FE_API_CONNECTION_GUIDE.md`: **Y**

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| RBAC `can_view_store_profile` | `API_Task075` §3 | `StoreProfileController.java` `@PreAuthorize("hasAuthority('can_view_store_profile')")`; Flyway `V28...` | Chưa có call | Y (BE↔Doc) | `wire-fe`: handle 401/403 |
| Multipart field `file` | `API_Task075` §2 | `StoreProfileController.uploadLogo(@RequestPart("file"))` | `StoreInfoPage.tsx` chỉ preview local (FileReader) | Y (BE↔Doc), N (FE) | `wire-fe`: gọi multipart upload, nhận `logoUrl` |
| Validate type/size + upload Cloudinary | `API_Task075` §4 | `CloudinaryMediaService.validateFile()` (jpeg/png/webp, max bytes); `uploadStoreProfileLogo()` folder `smart-erp/store-profiles/{ownerId}` | — | Y | Nếu Cloudinary disabled sẽ trả 400 (message hiện tại) |
| Response 200 `{ logoUrl, updatedAt }` | `API_Task075` §5 | `StoreLogoUploadData.java` | — | Y | OK |

| Wire FE (POST logo) | `API_Task075` §1–§7 | `StoreProfileController.java` | `features/settings/api/storeProfileApi.ts` (`uploadStoreLogo`), `features/settings/pages/StoreInfoPage.tsx` (`useMutation`) | Y | Đã nối upload; refetch GET Task073 sau success |

Kết luận:
- BE khớp spec Task075.
- FE đã nối upload logo vào `StoreInfoPage` (chọn file → upload multipart → cập nhật `logoUrl`).

