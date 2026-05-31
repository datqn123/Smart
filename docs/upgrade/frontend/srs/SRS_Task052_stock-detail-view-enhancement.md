# SRS_Task052 — Stock Detail View Enhancement (Nâng cấp Chi tiết Tồn kho)

## 1. Thông tin chung

- **Dự án**: Mini-ERP (Phân hệ Tồn kho)
- **Task ID**: Task052
- **Trạng thái**: Approved
- **Người thực hiện**: Agent BA
- **Ngày tạo**: 2026-04-19

## 2. Bối cảnh & Mục tiêu

Hiện tại, form chi tiết sản phẩm tồn kho (`StockBatchDetailsDialog`) còn quá nhỏ và chỉ hiển thị thông tin lô hàng cơ bản. Người dùng cần cái nhìn tổng quan và sâu sắc hơn về từng mặt hàng (giá trị, định mức, ảnh sản phẩm) ngay trong màn hình chi tiết mà không cần điều hướng sang trang khác.

**Mục tiêu**:

- Mở rộng kích thước Dialog để chứa nhiều thông tin hơn.
- Phân tách thông tin thành các khối: Thông tin chung, Giá trị & Định mức, Danh sách lô hàng chi tiết.
- Đảm bảo tính thẩm mỹ "Premium" theo `RULES.md`.

## 3. Đặc tả yêu cầu giao diện (UI/UX)

### 3.1. Kích thước & Layout

- **Kích thước**: `max-w-4xl` (khoảng 900px) hoặc `max-w-5xl`.
- **Cấu trúc**:
  - **Header**: Tên sản phẩm (To, đậm), SKU, Trạng thái (Badge).
  - **Top Section (Overview)**: Chia làm 4 cột bằng Grid:
    - Cột 1: Thông tin mã hóa (SKU, Barcode, Đơn vị).
    - Cột 2: Kho & Vị trí (Kho chính, Kệ mặc định).
    - Cột 3: Giá trị & Tài chính (Giá vốn, Tổng giá trị tồn).
    - Cột 4: Cảnh báo & Định mức (Số lượng thực tế vs Định mức tối thiểu).
  - **Bottom Section (Batches)**: Bảng chi tiết lô hàng (căn chỉnh theo chuẩn Master Table).

### 3.2. Thành phần dữ liệu mới

- **Barcode**: Hiển thị text font Mono kèm nhãn.
- **Giá vốn (Cost Price)**: Hiển thị định dạng tiền tệ (VND).
- **Tổng giá trị (Total Value)**: = Số lượng \* Giá vốn.
- **Mức tồn kho**: Hiển thị badge màu sắc (An toàn/Sắp hết/Hết hàng) dựa trên định mức.

### 3.3. Hiệu ứng thẩm mỹ (Style Guardrails)

- Palette: Slate 50 - 900.
- Typography: Inter Font.
- Border: `border-slate-200` mỏng, tinh tế.

## 4. Ràng buộc kỹ thuật

- Responsive: Tối ưu cho Desktop và Tablet.
- Component: Sử dụng `Dialog`, `Table`, `Badge`, `Separator` của Shadcn.

## 5. Tiêu chí nghiệm thu (Acceptance Criteria)

- [x] Dialog mở rộng tối thiểu `max-w-4xl`.
- [x] Thông tin giá vốn và tổng giá trị phải chính xác.
- [x] UI đồng bộ với phong cách cao cấp của toàn hệ thống.
