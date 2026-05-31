# BUG ELICITATION - Bug025_05: Visual Harmony & Mandatory Standalone Header

**Status: Open**
**User Requirement**: "Header Table đã tách ra riêng chưa... table ở Xuất kho... đẹp hơn nên hãy chỉnh sửa lại box shadow ở Phiếu nhập kho. Cập nhập lại rule...".

## 1. Phân tích Hiện trạng
- **Standalone Header**: Cả 2 trang (`InboundPage` và `DispatchPage`) đã áp dụng `...TableHeader` tách biệt. Kết quả cuộn mượt mà, header cố định.
- **Box Shadow**: Hiện tại đang dùng `shadow-sm`. Người dùng thấy Dispatch đẹp hơn (có thể do độ tương phản màu sắc vùng xung quanh). 

## 2. Giải pháp đề xuất
- **Shadow**: Nâng cấp toàn bộ Table Wrapper lên `shadow-md` để tạo độ nổi khối chuyên nghiệp hơn, đáp ứng yêu cầu "đẹp hơn" của người dùng.
- **Container**: Áp dụng `bg-white border-slate-200/60` (giảm nhẹ độ đậm của border) để shadow nổi bật hơn.
- **Rule**: Cập nhật `RULES_UI_TABLE.md` mục "Technical" nhấn mạnh tính **Bắt buộc (MANDATORY)** của Standalone Header.

---
**Agent BA done.** Chuyển PM điều phối sửa lỗi visual.
