# BUG ELICITATION - Bug025_02: Sticky Header Persistence Fail

**Status: Open**
**Severity: Medium-High**
**Root Cause Hypothesis**: Shadcn UI `<Table />` component has an internal `div` wrapper (`data-slot="table-container"`) with `overflow-x-auto`. This intermediate wrapper breaks the `sticky top-0` behavior when the parent page container is the one scrolling vertically.

## 1. Triệu chứng
Khi cuộn trang `InboundPage`, thanh tiêu đề (`TableHeader`) không ở lại trên cùng mà bị đẩy lên phía trên cùng với toàn bộ bảng.

## 2. Giải pháp đề xuất (Tech Lead)
- Loại bỏ wrapper `div` trong `Table.tsx` của UI component (nguy hiểm vì ảnh hưởng toàn hệ thống).
- **Hoặc (Khuyến nghị)**: Đặt thuộc tính `sticky top-0` lên từng `TableHead` thay vì chỉ `TableHeader`. CSS `sticky` trên `th` có độ tin cậy cao hơn khi nằm trong các wrapper trung gian.
- Đảm bảo `z-index` đủ cao để không bị nội dung hàng đè lên.

## 3. Fix Requirement
- Header phải dính chặt dù cuộn ở bất kỳ tốc độ nào.
- Giữ nguyên horizontal scroll của bảng (không làm vỡ tính năng này).

---
**Agent BA done.** Chuyển PM thực hiện flow.
