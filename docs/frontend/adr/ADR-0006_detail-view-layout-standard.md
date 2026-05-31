# ADR-0006: Detail View Layout Standard (Chuẩn hóa Layout Chi tiết)

## 1. Context
Dự án Mini-ERP cần một chuẩn hiển thị chi tiết (Quick View) cho các thực thể (Sản phẩm, Đơn hàng, Khách hàng). Hiện tại các chi tiết đang được hiển thị trong Dialog nhỏ, gây hạn chế cho việc mở rộng thông tin trong tương lai.

## 2. Decision
Chúng tôi quyết định chuẩn hóa giao diện Detail Dialog theo mô hình "Overview-First Data-Second".

**Chi tiết cấu trúc**:
1.  **Dialog Content**: Sử dụng `max-w-4xl` cho Desktop để tối ưu không gian.
2.  **Top Section (Overview)**:
    - Sử dụng CSS Grid responsive: `grid-cols-1 md:grid-cols-2 lg:grid-cols-4`.
    - Mỗi ô grid chứa một cặp `Label` (Slate 500, text-xs) và `Value` (Slate 900, text-sm, font-medium).
3.  **Data Section (Tables)**:
    - Sử dụng Shadcn Table.
    - Border-radius: `rounded-md`.
    - Background header: `bg-slate-50`.
4.  **Separation**: Sử dụng `<Separator />` giữa Header, Overview và Data Table để tạo sự phân cấp rõ ràng.

## 3. Rationale
- **Tính mở rộng**: Grid layout cho phép thêm bớt thông tin mà không làm vỡ giao diện.
- **Trải nghiệm người dùng (UX)**: Người dùng có thể quét nhanh các chỉ số quan trọng (Giá, Tồn kho) trước khi xem chi tiết bảng lưu bên dưới.
- **Tính nhất quán**: Đồng bộ với logic Monochrome và Premium của `RULES.md`.

## 4. Consequences
- Phải cập nhật lại các Dialog cũ nếu muốn đồng bộ 100%.
- Cần chú ý responsive logic để grid không bị quá dài trên mobile.
