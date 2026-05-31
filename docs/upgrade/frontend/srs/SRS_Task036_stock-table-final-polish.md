# 📑 SOFTWARE REQUIREMENT SPECIFICATION (SRS) - Task036

**Mã SRS:** `SRS_Task036_stock-table-final-polish`
**Trạng thái:** ✅ Completed
**Tính năng:** Tinh chỉnh kỹ thuật Bảng Tồn kho theo Master Pattern.

---

## 1. Phạm vi (Scope)
- **File tác động:** 
  - `src/features/inventory/pages/StockPage.tsx`
  - `src/features/inventory/components/StockTable.tsx`
- **Nội dung:** Căn chỉnh CSS, Column Widths, và Layout Wrappers.

## 2. Đặc tả kỹ thuật chi tiết

### 2.1 Căn chỉnh Cột (Column Alignment)
Phải áp dụng độ rộng cố định cho cả `StockTableHeader` và `StockTableBody` để tránh hiện tượng giãn table khi container rộng:

| Cột | Width Class |
| :--- | :--- |
| **Checkbox** | `w-[48px]` |
| **Mã SP** | `w-[110px]` |
| **Tên sản phẩm** | `min-w-[200px]` (Cột giãn duy nhất) |
| **Vị trí** | `w-[120px]` |
| **Tồn kho** | `w-[110px]` |
| **Hạn SD** | `w-[140px]` |
| **Trạng thái** | `w-[130px]` |
| **Thao tác (Action)**| `w-[80px]` |

### 2.2 Sửa lỗi Layout trang (StockPage.tsx)
- Loại bỏ class `shadow-sm` tại Filter Bar (Dòng 142).
- Đảm bảo Table Wrapper có `shadow-md` và `rounded-xl`.

### 2.3 Cải thiện Table Component (StockTable.tsx)
- Loại bỏ `w-full` trên thẻ `Table` nếu nó gây giãn cột không mong muốn, hoặc sử dụng `table-fixed` kết hợp với các width trên.
- Đảm bảo `border-separate border-spacing-0` được sử dụng để các đường kẻ border không bị chồng lấp khi sticky.

## 3. Tiêu chí nghiệm thu (Acceptance Criteria)
- **AC1:** Header và Body của `StockTable` phải thẳng hàng 100% (kiểm tra bằng mắt thường và DevTools).
- **AC2:** Thanh cuộn dọc xuất hiện mà không làm lệch cột tiêu đề (nhờ `pr-[10px]` và alignment chuẩn).
- **AC3:** Filter bar không có shadow.
- **AC4:** Layout responsive mobile hiển thị dạng Card sạch sẽ trên nền trắng (`bg-white`).

---
**Người lập:** Agent BA
**Ngày:** 17/04/2026
