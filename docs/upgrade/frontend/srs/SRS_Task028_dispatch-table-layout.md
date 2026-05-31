# SRS_Task028: Refactor Xuất kho (Dispatch) sang Table Layout

**ID**: Task028
**Module**: Inventory (Xuất kho & Điều phối)
**Status**: Approved (BA)

## 1. Mục tiêu (Objective)
Hiện đại hóa giao diện "Xuất kho & Điều phối" từ dạng danh sách thẻ (Card list) sang dạng bảng dữ liệu chuyên nghiệp (Table Layout), tương tự như giao diện Phiếu nhập kho đã thực hiện. Áp dụng cơ chế **Standalone Header** để tránh lỗi sticky trôi và cải thiện UX khi cuộn danh sách lớn.

## 2. Business Logic & Requirements
- **Danh sách phiếu**: Hiển thị tất cả phiếu xuất kho, phiếu điều chuyển.
- **Dữ liệu cột (Columns)**:
  - Mã phiếu: Font mono, in đậm.
  - Mã đơn hàng: Liên kết kèm theo.
  - Khách hàng: Tên đầy đủ.
  - Ngày xuất: Định dạng dd/mm/yyyy.
  - Người thực hiện: Tên nhân viên.
  - Số lượng SP: Tổng số SKU trong phiếu.
  - Trạng thái: StatusBadge (Pending, Full, Partial, Cancelled).
  - Thao tác: Nút "Xem chi tiết" (Icon Eye).
- **Thành phần giao diện (UI Components)**:
  - `DispatchTable.tsx`: Chứa Standalone Header và Table Body.
  - `DispatchDetailPanel.tsx`: Dạng Sheet (Drawer) hiển thị chi tiết phiếu, bao gồm:
    - Thông tin chung (Mã phiếu, ngày, trạng thái).
    - **Picking List**: Danh sách hàng hóa cần lấy, vị trí lưu kho (vùng-ô).
    - Thao tác: In phiếu xuất, Phê duyệt xuất hàng.
- **Infinite Scroll**: Kế thừa cơ chế IntersectionObserver để load dữ liệu mượt mà.

## 3. Quy tắc Thiết kế (Design Rules)
- Sử dụng mô hình **Standalone Header** (Pattern [BF-008]).
- Padding Sheet Content chuẩn `p-6` (Pattern [BF-007]).
- Không được để xảy ra nested scroll giữa MainLayout và Page container.

## 4. Acceptance Criteria
1. Header bảng luôn dính cố định khi cuộn dữ liệu bên dưới.
2. Các cột Header và Body thẳng hàng tuyệt đối.
3. Khi click "Xem chi tiết", Sheet hiện ra từ bên phải với đầy đủ thông tin và Picking List.
4. Chức năng Search và Filter Status hoạt động đúng với Table mới.

---
**Agent BA done.** Chuyển thông tin cho Agent PM lập Task.
