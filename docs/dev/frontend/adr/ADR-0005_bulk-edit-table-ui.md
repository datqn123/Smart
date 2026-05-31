# ADR-0005: Quy chuẩn giao diện bảng sửa hàng loạt (Bulk Edit Table UI)

## 1. Trạng thái
- **Trạng thái**: Proposed
- **Task**: Task049
- **Ngày**: 2026-04-19

## 2. Bối cảnh
Người dùng cần một giao diện sửa hàng loạt thông tin tồn kho với mật độ thông tin cao (8 cột). Các thiết kế trước đó gặp vấn đề về căn chỉnh (alignment) và bị ép khung (squished) do giới hạn mặc định của Dialog.

## 3. Quyết định (Decision)
- **Cấu trúc bảng**: Sử dụng `Table` chuẩn của Shadcn nhưng ép thuộc tính `table-fixed` để kiểm soát % chiều rộng từng cột.
- **Tách cột**: Tách biệt hoàn toàn `Mã SP`, `Tên SP`, `Định mức`, `Đơn vị`, `Số lô`, `Hạn SD` thành các cột độc lập để dễ căn chỉnh (`center` vs `left`).
- **Styling**: 
    - Loại bỏ hoàn toàn `ring` của Input; thay bằng `border-black` khi focus.
    - Chiều cao dòng cố định bằng padding (`py-3`) thay vì `h-24` để giao diện phẳng và gọn.
- **Hợp đồng dữ liệu**: `unitName` sẽ trở thành trường có thể sửa đổi (editable) thay vì chỉ đọc.

## 4. Non-Functional Requirements (NFR)

### 4.1 Performance Impact
- **Mô tả**: Khi sửa đổi nhanh trên bảng lớn (nhiều sản phẩm), việc re-render state mảng lớn có thể gây lag.
- **Biện pháp**: Sử dụng React local state tối ưu; tránh gắn logic tính toán nặng vào sự kiện `onChange`.

### 4.2 Scalability
- **Mô tả**: Khả năng hiển thị khi số lượng cột tăng thêm.
- **Biện pháp**: Sử dụng `max-w-[1700px]` và `95vw` đảm bảo bảng vẫn hoạt động tốt trên các màn hình Ultrawide 2K/4K.

### 4.3 Security
- **Mô tả**: XSS thông qua các ô nhập liệu (Unit Name, Batch Number).
- **Biện pháp**: Dữ liệu được quản lý bởi React (Controlled Components), đảm bảo escape tự động các ký tự đặc biệt khi render.

### 4.4 Reliability
- **Mô tả**: Đảm bảo đóng tất cả thẻ HTML/JSX đầy đủ.
- **Biện pháp**: Thực hiện linting và build check trước khi hoàn thành task.

### 4.5 Observability
- **Mô tả**: Theo dõi các lỗi nhập liệu.
- **Biện pháp**: Sử dụng Console Error nếu có xung đột kiểu dữ liệu (data type mismatch) trong logic `handleChange`.

## 5. Hệ quả (Consequences)
- **Ưu điểm**: Giao diện chuyên nghiệp, giống bảng tính Excel, đáp ứng đúng yêu cầu thẩm mỹ của Owner.
- **Nhược điểm**: Đòi hỏi DEV phải căn chỉnh CSS rất chi tiết cho từng cột (thông qua class `w-[%]`).
