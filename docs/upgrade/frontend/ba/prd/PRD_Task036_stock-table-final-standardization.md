# 📝 PRODUCT REQUIREMENT DOCUMENT (PRD) - Task036

> **Mã PRD:** `PRD_Task036_stock-table-final-standardization`
> **Trạng thái:** 🟢 Draft
> **Tính năng:** Tinh chỉnh bảng Tồn kho (StockPage) đạt chuẩn 100% Master Table Pattern.

---

## 1. Tổng quan (Product Overview)
Dù đã có một đợt cập nhật ở Task033, trang **Tồn kho (StockPage)** vẫn còn một số điểm chưa khớp hoàn toàn với bộ quy tắc "Master Table Pattern" vừa được thiết lập chính thức trong `RULES_UI_TABLE.md`. Cần thực hiện đợt tinh chỉnh cuối cùng để đảm bảo sự đồng bộ tuyệt đối với trang Nhập kho.

## 2. Mục tiêu (Goals)
- Khắc phục sự sai lệch về alignment giữa Header và Body của `StockTable`.
- Loại bỏ các style thừa (Shadow ở Filter Bar) để tập trung thị giác vào vùng dữ liệu.
- Đảm bảo kỹ thuật bù trừ thanh cuộn (`pr-[10px]`) hoạt động chính xác để các cột không bị lệch khi danh sách dài.

## 3. Đặc tả thay đổi (Deep Cleaning)

| Thành phần | Hiện trạng | Yêu cầu chuẩn (RULES_UI_TABLE.md) |
| :--- | :--- | :--- |
| **Filter Bar (Toolbar)** | Có `shadow-sm`. | Không sử dụng shadow, chỉ có border. |
| **Table Header Widths** | Dùng `w-full`, các cột có thể bị giãn. | Cố định width cho từng cột, đảm bảo khớp 1:1 với Body cells. |
| **Bù trừ Scrollbar** | Đã có `pr-[10px]` nhưng cần kiểm tra tính hiệu quả. | Phải đảm bảo Cell cuối (Action) luôn thẳng hàng với Header cuối. |
| **Mobile Card Style** | Background `bg-slate-50/30`. | Sử dụng `bg-white` làm nền chính, các card có thể có `bg-slate-50` khi được chọn. |

## 4. Danh sách User Stories

| ID | Vai trò | Hành động | Mục tiêu |
| :--- | :--- | :--- | :--- |
| **US036.1** | Quản lý kho | Xem danh sách Tồn kho trên Desktop | Thấy các cột thẳng hàng tuyệt đối, Header cố định và không bị lệch dù có thanh cuộn hay không. |
| **US036.2** | Nhân viên kho | Xem danh sách Tồn kho trên Mobile | Trải nghiệm Card view sạch sẽ, đồng bộ với các module khác. |

## 5. Ràng buộc (Constraints)
- Phải kế thừa `StockTableHeader` và `StockTable` hiện có nhưng tách rõ ràng hơn.
- Không phá vỡ logic Checkbox selection và Pagination (Infinite Scroll).

---
**Người lập:** Agent BA
**Ngày:** 17/04/2026
