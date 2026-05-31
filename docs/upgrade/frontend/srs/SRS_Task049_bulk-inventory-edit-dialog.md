# SRS_Task049 — Bulk Inventory Edit Dialog (Sửa hàng loạt tồn kho)

## 1. Thông tin chung

- **Dự án**: Mini-ERP (Tồn kho)
- **Task ID**: Task049
- **Trạng thái**: Completed
- **Người thực hiện**: Agent BA
- **Ngày tạo**: 2026-04-19

## 2. Mục tiêu và Phạm vi

Xây dựng một giao diện hộp thoại (Dialog) cho phép sửa đổi thông tin của nhiều sản phẩm tồn kho cùng lúc. Giao diện phải đạt độ chính xác cao về căn chỉnh, mật độ thông tin dày đặc nhưng dễ đọc, và hiệu suất mượt mà.

## 3. Đặc tả chức năng (Functional Requirements)

- **Kích hoạt**: Xuất hiện khi chọn ≥ 1 sản phẩm tại `StockPage` và nhấn nút "Sửa" trên toolbar.
- **Tải dữ liệu**: Hiển thị danh sách các sản phẩm đã chọn với dữ liệu hiện tại.
- **Chỉnh sửa**:
  - Cho phép sửa trực tiếp trong bảng: Vị trí (Kho/Kệ), Định mức (Min Quantity), Đơn vị (Unit), Giá vốn (Cost Price), Số lô (Batch), Hạn sử dụng (Expiry).
  - Tất cả các trường là Edit-in-place.
- **Tính toán**: Khi lưu, hệ thống phải tính toán lại `totalValue` và trạng thái `isLowStock` cho từng mặt hàng.
- **Đóng/Hủy**: Đóng modal mà không lưu dữ liệu.

## 4. Đặc tả giao diện (UI/UX Requirements)

- **Kích thước**: `95vw`, tối đa `1700px`. Chiều cao `90vh`.
- **Cấu trúc cột (Strictly One Line)**:
  1. **Mã SP**: Nhãn xanh dương nhỏ, font đậm. (w-8%)
  2. **Tên sản phẩm**: Văn bản lề trái, có hiệu ứng `truncate` nếu quá dài. (w-18%)
  3. **Vị trí (Kho - Kệ)**: 2 ô input nhỏ (w-14) cách nhau dấu gạch ngang. (w-12%)
  4. **Định mức**: Input số căn giữa. (w-10%)
  5. **Đơn vị**: Input chữ căn giữa, cho phép sửa đơn vị định danh. (w-8%)
  6. **Giá vốn (VNĐ)**: Input số căn giữa. (w-12%)
  7. **Số lô**: Input chữ căn giữa. (w-12%)
  8. **Hạn SD**: Input type date căn giữa, font size nhỏ (`text-[10px]`). (w-10%)
- **Mật độ**: Các hàng có đệm vừa phải (`py-3`), input nhỏ (`h-8`, `text-xs`).
- **Tương tác**:
  - **Focus**: Viền đen mỏng (`border-black`) khi focus vào ô nhập liệu.
  - **Selection**: Màu bôi đen văn bản mặc định (không được dùng màu đen đặc).
  - **No Scroll**: Không được xuất hiện thanh cuộn ngang; bảng phải tự fit 100% khung hình.

## 5. Danh sách Task dự kiến

1. [UNIT] Tạo component `StockEditDialog.tsx` với cấu trúc Table 8 cột.
2. [FEATURE] Tích hợp logic xử lý state và callback `onConfirm` tại `StockPage.tsx`.
3. [E2E] Kiểm tra luồng: Chọn SP -> Mở Dialog -> Sửa dữ liệu -> Lưu -> Kiểm tra bảng chính cập nhật đúng số liệu.

---

> [!IMPORTANT]
> **GATE G1**: Yêu cầu Owner (User) xem xét tài liệu SRS trên. Nếu đồng ý, hãy phản hồi **"Approve"** hoặc **"Tiếp tục"** để chuyển sang Agent PM lập kế hoạch.
