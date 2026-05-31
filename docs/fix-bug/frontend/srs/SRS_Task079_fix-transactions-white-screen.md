# SRS - Khắc phục lỗi hiển thị trang Giao dịch thu chi

> **File**: `docs/srs/SRS_Task079_fix-transactions-white-screen.md`  
> **Người viết**: Agent BA  
> **Ngày cập nhật**: 20/04/2026  
> **Trạng thái**: Completed

## 1. Tóm tắt

- **Vấn đề**: Khi người dùng truy cập vào trang "Giao dịch thu chi", màn hình hiển thị trắng tinh (White screen of death).
- **Mục tiêu**: Khôi phục hoạt động của trang Giao dịch thu chi, đảm bảo hiển thị đầy đủ thông tin và biểu tượng.
- **Đối tượng**: Chủ cửa hàng (Owner), Nhân viên kế toán.

## 2. Phạm vi

### 2.1 In-scope

- Sửa lỗi `ReferenceError` do thiếu import biểu tượng `DollarSign` trong `TransactionsPage.tsx`.
- Rà soát các tệp tin vừa được tối ưu hóa (dọn dẹp biến thừa) để đảm bảo không còn lỗi runtime tương tự:
  - `SuppliersPage.tsx`
  - `DispatchPage.tsx`
  - `EmployeeDetailDialog.tsx`
  - `EmployeeForm.tsx`
  - `LogTable.tsx`
- Đảm bảo lệnh `npm run build` thành công mà không có lỗi TypeScript nghiêm trọng.

### 2.2 Out-of-scope

- Thêm tính năng mới cho trang Giao dịch thu chi.
- Thay đổi cấu trúc dữ liệu hoặc API.

## 3. Persona & Quyền (RBAC)

- **Vai trò liên quan**: Owner | Staff (Kế toán)
- **Quyền bắt buộc**:
  - Xem danh sách giao dịch → Role: Owner, Staff
- **Xử lý thiếu quyền**:
  - Không thay đổi (giữ nguyên cơ chế hiện tại).

## 4. User Stories

- **US1 (chính)**: Là một người quản lý, tôi muốn truy cập vào trang Giao dịch thu chi mà không gặp lỗi để có thể theo dõi dòng tiền của cửa hàng.

## 5. Luồng nghiệp vụ (Business Flow)

N/A (Đây là lỗi hiển thị, không thay đổi luồng nghiệp vụ).

## 6. Quy tắc nghiệp vụ (Business Rules)

- Không có quy tắc nghiệp vụ mới.
- Yêu cầu kỹ thuật: Mọi biểu tượng (icon) được sử dụng trong mã nguồn phải được import đầy đủ từ thư viện `lucide-react`.

## 7. UI/UX Spec (Mobile-first)

- Giữ nguyên thiết kế "Premium Minimalist" đã thống nhất.
- Đảm bảo các StatCard hiển thị đúng icon tương ứng (TrendingUp cho Thu, TrendingDown cho Chi, DollarSign cho Số dư).

## 8. Edge Cases

- **Lỗi build**: Nếu bỏ qua `tsc` check, ứng dụng có thể chạy nhưng tiềm ẩn lỗi runtime. Ưu tiên sửa lỗi kiểu (type) nếu ảnh hưởng trực tiếp đến hiển thị.

## 9. Technical Mapping (Frontend)

- **Feature folder**: `mini-erp/src/features/cashflow/`
  - **Pages**: `pages/TransactionsPage.tsx`
- **Dependency**: `lucide-react` (icon library).

## 10. Data & Database Mapping

N/A (Lỗi phía Frontend).

## 11. Acceptance Criteria (BDD/Gherkin)

### 11.1 Happy paths

```gherkin
Given Trang "Giao dịch thu chi" đang bị lỗi trắng trang
When Developer khôi phục import "DollarSign" và sửa các lỗi type liên quan
Then Trang "Giao dịch thu chi" hiển thị đầy đủ tiêu đề, StatCards và danh sách giao dịch
And Không có lỗi đỏ trong Console của trình duyệt
```

## 12. Open Questions

- N/A
