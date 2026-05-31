# SRS - Task082: Standardize Search Bar and Page Layout

> **Mã Task**: Task082  
> **Tính năng**: Chuẩn hóa UI Toolbar và Layout trang Product Management  
> **Người viết**: Agent BA  
> **Ngày tạo**: 20/04/2026  
> **Trạng thái**: Pending Approval

## 1. Tóm tắt yêu cầu
Chuẩn hóa giao diện thanh tìm kiếm (Toolbar) và bố cục (Layout) của các trang thuộc phân hệ Sản phẩm theo mẫu của trang "Kiểm kê kho" (AuditPage). Mục tiêu là tạo ra sự đồng nhất về bo góc (border-radius), viền (border), độ đổ bóng (shadow) và khoảng cách giữa các thành phần.

## 2. Các trang phạm vi (Scope)
1. **Danh mục sản phẩm**: `CategoriesPage.tsx` + `CategoryToolbar.tsx`
2. **Quản lý sản phẩm**: `ProductsPage.tsx` + `ProductToolbar.tsx`
3. **Nhà cung cấp**: `SuppliersPage.tsx` + `SupplierToolbar.tsx`
4. **Khách hàng**: `CustomersPage.tsx` + `CustomerToolbar.tsx`

## 3. Đặc tả giao diện chuẩn (Reference: AuditPage)
### 3.1. Cấu trúc Page Layout
- Container chính của trang: `h-full flex flex-col p-4 md:p-6 lg:p-8 gap-4 md:gap-5 overflow-hidden`.
- Header section: `shrink-0`.
- Toolbar section: Tách riêng thành một khối độc lập (không bọc chung với Table).
- Table section: Tách riêng thành một khối độc lập với `shadow-md`.

### 3.2. Toolbar (Thanh tìm kiếm & Lọc)
- Container: `bg-white border border-slate-200 rounded-lg p-4 shrink-0 space-y-3`.
- Input tìm kiếm: `h-11` (chiều cao chuẩn), `pl-9` (padding cho icon).
- Border-radius: Sử dụng `rounded-lg` cho toàn bộ khối Toolbar.

### 3.3. Khoảng cách (Spacing)
- Toolbar và Table phải có khoảng cách rõ ràng (được thiết lập bởi `gap-4 md:gap-5` của container cha).
- Table container: `flex-1 flex flex-col min-h-0 bg-white border border-slate-200/60 rounded-xl overflow-hidden shadow-md`.

## 4. Danh sách các thay đổi cần thực hiện
### 4.1. Điều chỉnh Page (`.tsx` của các trang)
- Thay đổi cấu trúc return: Tách Toolbar và Table ra khỏi `div` bọc chung hiện tại.
- Đảm bảo container ngoài cùng có `gap-4 md:gap-5` hoặc `space-y-4 md:space-y-6`. Vì AuditPage dùng `gap`, ta sẽ ưu tiên dùng `gap` kết hợp `flex flex-col`.

### 4.2. Điều chỉnh Toolbar Component (`.tsx` của các toolbar)
- Cập nhật class CSS của container chính trong Toolbar:
  - Xóa `md:rounded-t-md` và `border-b`.
  - Thêm `border border-slate-200 rounded-lg shadow-none`.
- Chuẩn hóa chiều cao các thành phần:
  - Input: `h-11`.
  - Select: `h-11`.
  - Button: `h-11`.

## 5. Tiêu chí nghiệm thu (Acceptance Criteria)
- [ ] Giao diện 4 trang đích có Toolbar là một khối bo tròn riêng biệt (giống AuditPage).
- [ ] Có khoảng cách (gap) rõ ràng giữa Toolbar và Table.
- [ ] Table có border-radius `rounded-xl` và `shadow-md`.
- [ ] Các Input/Select/Button trong Toolbar có chiều cao đồng nhất `h-11`.
- [ ] Không làm phá vỡ logic lọc/tìm kiếm hiện tại.

## 6. Rủi ro
- Thay đổi class CSS có thể ảnh hưởng đến responsive trên màn hình siêu nhỏ (Mobile) nếu không test kỹ. Cần kiểm tra `sm:flex-row` để đảm bảo không bị tràn.
