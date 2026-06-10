# SRS - Tùy biến thanh điều hướng và hiển thị menu hệ thống trong Trình thiết kế dữ liệu

> File: `docs/backend/srs/004_srs_system-menu-visibility-in-custom-builder.md`  
> Agent: SRS_WRITER  
> Ngày cập nhật: 03/06/2026  
> Trạng thái: DRAFT_FOR_PO_REVIEW  
> Phạm vi: Backend (migration, API, cô lập store) + Frontend (dynamic sidebar, builder UI)

---

## 1. Input và Traceability

| Nguồn | Nội dung sử dụng |
| :--- | :--- |
| `docs/frontend/srs/010_custom-builder-menu-interface-design.md` | SRS gốc: giao diện builder folder/file, quản lý dynamic menu |
| `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx` | Chuyển đổi static menu `navConfig` thành cấu hình động từ DB |
| `frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx` | Cho phép tùy biến nhãn, icon, thứ tự, roles của menu hệ thống |
| `frontend/mini-erp/src/features/custom-builder/runtime/customMenuRuntime.ts` | Trả về cấu hình menu chạy động hoàn toàn từ API |
| `backend/smart-erp/src/main/java/.../custominterface/service/CustomInterfaceService.java` | Lọc menu và phân quyền theo vai trò kết hợp với cô lập `owner_id` (store) |
| `backend/smart-erp/src/main/java/.../users/entity/User.java` | Bổ sung cột `owner_id` để xác định ngữ cảnh cửa hàng cho Staff |

---

## 2. Executive Summary / Tóm tắt

- **Vấn đề:** 
  1. Trình thiết kế dữ liệu trước đây chỉ quản lý các custom menu mới tạo. Các menu tĩnh nguyên bản (Kho hàng, Sản phẩm, Đơn hàng...) bị hardcode trong `Sidebar.tsx` làm cho Owner/Admin không thể sửa đổi, sắp xếp thứ tự hoặc ẩn bớt đi theo nhu cầu riêng của cửa hàng.
  2. Các tài khoản Staff chưa được liên kết với Owner sở hữu cửa hàng trong cơ sở dữ liệu. Khi Staff đăng nhập, hệ thống tự động sinh một store profile riêng cho họ, dẫn đến giao diện menu hiển thị bị sai lệch và thiếu đồng bộ với thiết lập của Owner.
- **Mục tiêu:** 
  1. Loại bỏ hoàn toàn menu tĩnh hardcode ở frontend. Đưa toàn bộ cấu trúc thư mục và trang hệ thống vào database dưới dạng cấu hình có thể tùy biến (chỉ khóa cứng ID khóa cấu trúc và route đường dẫn tĩnh để tránh lỗi định tuyến).
  2. Bổ sung liên kết `owner_id` cho tài khoản người dùng để cô lập ngữ cảnh cấu hình menu theo từng store. Tài khoản Staff của một store sẽ hiển thị thanh sidebar y hệt như cấu hình của Admin/Owner của store đó.

---

## 3. Capability Breakdown / Bóc tách nghiệp vụ

| # | Capability | Kích hoạt bởi | Kết quả mong đợi |
| :---: | :--- | :--- | :--- |
| C1 | Xem và tùy biến toàn bộ menu hệ thống trong builder | Owner/Admin mở `/settings/custom-builder` | Tree explorer hiển thị cả menu hệ thống và custom menu. Menu hệ thống cho phép chỉnh sửa nhãn, icon, phân quyền hiển thị, thứ tự sắp xếp và trạng thái ẩn/hiện. |
| C2 | Khóa an toàn thuộc tính cấu trúc | Hệ thống trả flag `isSystem=true` | Trình thiết kế khóa cứng (read-only) trường `key` và `routePath` của các mục hệ thống, ngăn ngừa việc thay đổi khóa định tuyến làm hỏng tính năng gốc. |
| C3 | Render Sidebar động hoàn toàn | Sidebar load khi user đăng nhập | Sidebar loại bỏ `navConfig` tĩnh và render hoàn toàn từ API `runtime-menu`. Các icon được ánh xạ từ chuỗi động trong database sang Lucide React components. |
| C4 | Cô lập cấu hình menu theo store | API trả thông tin menu | API lọc cấu hình menu dựa vào `owner_id` lấy từ claim của JWT token hiện tại, đảm bảo Staff và Owner cùng store chia sẻ chung một giao diện tùy chỉnh. |
| C5 | Copy cấu hình mẫu cho Store mới | Tạo StoreProfile mới | Hệ thống tự động sao chép cây cấu hình menu mẫu mặc định (`owner_id IS NULL`) sang cho `ownerId` của store mới tạo. |

---

## 4. Phạm vi

### 4.1 In Scope

- **Database:** Thêm cột `owner_id` vào bảng `users` để thiết lập mối quan hệ Staff - Owner.
- **Database:** Thêm cột `owner_id` và `is_system` vào các bảng `custom_menu_folders`, `custom_menu_pages` và các bảng lịch sử phiên bản (`versions`).
- **Backend:** Cập nhật JWT Access Token để nhúng thêm claim `owner_id`.
- **Backend:** Áp dụng bộ lọc theo `owner_id` (trích xuất từ JWT) tại `CustomInterfaceService` và các repository.
- **Frontend:** Xóa bỏ `navConfig` tĩnh khỏi `Sidebar.tsx`. Render thanh điều hướng động hoàn toàn bằng cách ánh xạ chuỗi icon trong DB với Lucide Icons.
- **Frontend:** Cập nhật `CustomBuilderPage` để cho phép tùy biến thuộc tính hiển thị (nhãn, icon, vai trò, thứ tự, ẩn hiện) của menu hệ thống có cờ `isSystem=true`.

### 4.2 Out Of Scope

- Không thay đổi các component định tuyến (React Router) trong `App.tsx` (các trang tĩnh như `/dashboard`, `/inventory/stock` vẫn trỏ về component cũ).
- Không cho phép thay đổi trường định danh khóa (`key`, `folderKey`) và đường dẫn liên kết (`routePath`) đối với các menu hệ thống.
- Không hỗ trợ tạo menu custom trỏ đến các route tĩnh của hệ thống ngoài các route được định cấu hình sẵn.

---

## 5. Open Questions (Câu hỏi mở)

| ID | Câu hỏi | Ảnh hưởng nếu không trả lời | Trạng thái đề xuất |
| :--- | :--- | :--- | :---: |
| OQ-1 | Xử lý tài khoản hiện tại khi chạy migration? | Gây ra tình trạng không xác định được store của các Staff đang có | Cập nhật `owner_id = id` cho toàn bộ tài khoản Owner hiện tại. Admin/Staff sẽ cần cập nhật `owner_id` trỏ tới ID của Owner quản lý họ. |
| OQ-2 | Icon custom do người dùng tự nhập sẽ thế nào? | Nếu nhập sai tên icon sẽ hiển thị icon mặc định | Có bảng ánh xạ cứng các Lucide icons được hỗ trợ ở frontend. Nếu không khớp sẽ tự động dùng icon `FolderTree` hoặc `File` làm fallback. |

---

## 6. Evidence Scope / Phân tích scope tệp

### 6.1 Tài liệu đã đối chiếu

- `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx` (navConfig static menu)
- `frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx` (builder page)
- `backend/smart-erp/src/main/java/.../custominterface/service/CustomInterfaceService.java` (service)
- `backend/smart-erp/src/main/java/.../custominterface/repository/CustomInterfaceJdbcRepository.java` (repository)
- `backend/smart-erp/src/main/java/.../settings/storeprofile/StoreProfileService.java` (lấy profile theo ownerId)

### 6.2 Mã dự kiến thay đổi

- **Migration mới:** `V57__custom_sidebar_store_isolation.sql` (Schema + Seed dữ liệu mẫu hệ thống)
- **Backend:** `User.java` (Thêm thuộc tính `ownerId`), `JwtTokenService.java` (Claim `owner_id`)
- **Backend:** `StoreProfileService.java` (Lấy store profile theo `owner_id` claim)
- **Backend:** `CustomInterfaceJdbcRepository.java` & `CustomInterfaceService.java` (Truy vấn theo `ownerId`)
- **Frontend:** `Sidebar.tsx` (Xóa `navConfig`, mapping icon, render 100% động)
- **Frontend:** `CustomBuilderPage.tsx` (Mở khóa tùy biến thông tin hiển thị cho system items)

---

## 7. Persona & RBAC

| Vai trò | Quyền trên builder | Quyền trên runtime menu |
| :--- | :--- | :--- |
| Owner/Admin | `can_manage_custom_builder` → Xem và cấu hình toàn bộ menu (gồm hệ thống + custom) | Xem theo cấu hình menu đã published |
| Staff / Warehouse | Không có quyền quản trị thiết kế | Xem theo phân quyền vai trò được chỉ định trong cấu hình menu của store |

---

## 8. Actor & Luồng nghiệp vụ

### 8.1 Luồng tùy biến Sidebar (Owner/Admin)

1. Owner/Admin mở Trình thiết kế dữ liệu `/settings/custom-builder`.
2. Frontend gọi API `GET /api/v1/custom/menu-tree` kèm JWT có chứa `owner_id`.
3. Backend lấy `ownerId` từ JWT, truy vấn các menu của cửa hàng đó (nếu chưa có, sao chép cấu hình mẫu hệ thống).
4. Hệ thống trả về cây menu bao gồm các mục hệ thống có cờ `isSystem=true`.
5. Owner đổi nhãn "Kho hàng" thành "Kho tổng" và đổi icon, chọn Lưu nháp và Publish.
6. Cấu hình được đẩy vào bảng version tương ứng với `owner_id`.

### 8.2 Luồng hiển thị Sidebar (User bất kỳ đăng nhập)

1. Người dùng (Owner, Admin, Staff...) đăng nhập thành công.
2. Frontend gọi API `GET /api/v1/custom/runtime-menu`.
3. Backend trích xuất `ownerId` từ claim tùy chỉnh trong JWT, lấy danh sách menu đã publish của store.
4. Lọc bỏ các trang/thư mục không được phân quyền cho vai trò của người dùng đó (ví dụ: Staff không thấy "Sổ cái tài chính").
5. Trả về cấu trúc JSON của menu.
6. Sidebar ở frontend duyệt qua danh sách, ánh xạ chuỗi icon sang React component và hiển thị lên màn hình.

---

## 9. Quy tắc nghiệp vụ

| Mã | Điều kiện | Hành động / kết quả |
| :--- | :--- | :--- |
| BR-SYS-01 | Cấu hình menu hệ thống (`is_system = true`) | Chỉ cho phép cập nhật: `label`, `icon`, `sort_order`, `visibility_roles`, `status`. Khóa cứng: `page_key`, `parent_folder_key`, `route_path`, `entity_key`. |
| BR-SYS-02 | Sidebar runtime | Không hiển thị bất kỳ menu cứng nào từ frontend code. Hiển thị 100% dữ liệu động từ API `runtime-menu`. |
| BR-SYS-03 | Cô lập dữ liệu cửa hàng | Tất cả API tùy biến giao diện bắt buộc phải lọc theo `owner_id` của tài khoản hiện tại thông qua claim trên JWT. |
| BR-SYS-04 | Khởi tạo cấu hình cho store mới | Khi kích hoạt store profile mới, sao chép toàn bộ cấu hình mẫu (`owner_id IS NULL`) làm cấu hình khởi tạo cho store đó. |

---

## 10. Dữ liệu & SQL thay đổi

### 10.1 Schema thay đổi

```sql
-- Liên kết người dùng con với Owner của store
ALTER TABLE users ADD COLUMN owner_id INT REFERENCES users(id) ON DELETE SET NULL;

-- Thêm cột is_system và owner_id cho menu folders
ALTER TABLE custom_menu_folders 
  ADD COLUMN is_system BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN owner_id INT REFERENCES users(id) ON DELETE CASCADE;

-- Thêm cột is_system và owner_id cho menu pages
ALTER TABLE custom_menu_pages 
  ADD COLUMN is_system BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN owner_id INT REFERENCES users(id) ON DELETE CASCADE;

-- Thêm cột owner_id cho các bảng lịch sử phiên bản
ALTER TABLE custom_menu_folder_versions ADD COLUMN owner_id INT;
ALTER TABLE custom_menu_page_versions ADD COLUMN owner_id INT;
```

---

## 11. Hợp đồng API ví dụ

### GET /api/v1/custom/runtime-menu (Staff thuộc Store của Owner có ID = 1)
API tự động phân tích `owner_id` từ JWT token để trả về cấu hình menu của Store 1:

```json
{
  "treeEtag": "runtime-store1-v2",
  "folders": [
    {
      "nodeType": "folder",
      "id": "101",
      "key": "sys_inventory",
      "label": "Kho tổng hợp",
      "icon": "Package",
      "status": "Published",
      "sortOrder": 1,
      "roles": ["Owner", "Admin", "Staff"],
      "isSystem": true,
      "children": [
        {
          "nodeType": "page",
          "id": "201",
          "key": "sys_stock",
          "label": "Tồn kho thực tế",
          "icon": "File",
          "routePath": "/inventory/stock",
          "entityKey": "stock_item",
          "pageType": "record_list",
          "status": "Published",
          "sortOrder": 0,
          "isSystem": true
        }
      ]
    }
  ]
}
```

---

## 12. Kế hoạch kiểm thử

| Nhóm | Kiểm thử | Kết quả mong đợi |
| :--- | :--- | :--- |
| SQL | Chạy migration schema mới | Cột `owner_id` được bổ sung thành công, dữ liệu mẫu của hệ thống được import với `owner_id = NULL`. |
| Auth | Đăng nhập tài khoản Staff | JWT token trả về chứa đúng claim `owner_id` bằng ID của Owner quản lý Staff đó. |
| API | `GET /api/v1/custom/runtime-menu` | Trả về danh sách menu đã qua bộ lọc quyền vai trò và lọc theo `owner_id` tương ứng. |
| Frontend | Mở Sidebar | Hiển thị đầy đủ menu đã tùy biến. Nhãn của menu hệ thống khớp với cấu hình tùy biến lưu trong database. |
| Isolation | Thay đổi menu tại Store A | Store B đăng nhập hoàn toàn không bị ảnh hưởng giao diện menu. |
