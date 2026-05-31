# 📝 PRODUCT REQUIREMENT DOCUMENT (PRD) - Task033

> **Mã PRD:** `PRD_Task033_standardize-inventory-tables`
> **Trạng thái:** 🟢 Draft
> **Tính năng:** Chuẩn hóa giao diện Bảng dữ liệu (Table Layout) theo Master Pattern.

---

## 1. Tổng quan (Product Overview)
Dựa trên phản hồi tích cực về thiết kế của trang **Phiếu nhập kho (InboundPage)**, hệ thống cần chuẩn hóa toàn bộ các bảng dữ liệu khác trong module Inventory để đảm bảo tính nhất quán (Consistency) về trải nghiệm người dùng (UX) và thẩm mỹ (UI).

## 2. Mục tiêu (Goals)
- Áp dụng **Master Table Pattern** (từ InboundPage) cho các trang **Xuất kho & Điều phối** (DispatchPage) và **Tồn kho** (StockPage).
- Đảm bảo tính nhất quán về: Spacing, Rounding, Shadow, và kỹ thuật Sticky Header.
- Tối ưu hóa trải nghiệm trên Mobile theo quy tắc Mobile-first.

## 3. Đối tượng tác động (Stakeholders)
- **Người dùng kho:** Nhân viên kho thực hiện thao tác nhập/xuất/kiểm kê.
- **Quản lý:** Theo dõi số liệu tồn kho.
- **Developer:** Sử dụng pattern chung để phát triển các module tiếp theo nhanh hơn.

## 4. Đặc tả thay đổi (Gap Analysis)

| Thành phần | Hiện trạng (Dispatch/Stock) | Đề xuất (Standard) |
| :--- | :--- | :--- |
| **Container Page** | Padding/Gap không đồng nhất. | `p-4 md:p-6 lg:p-8 gap-4 md:gap-5` |
| **Filter Bar** | `rounded-xl`, `shadow-sm`. | `rounded-lg`, `border border-slate-200`, `shadow-none` (theo Inbound). |
| **Table Wrapper** | `rounded-xl`. | `rounded-xl`, `border border-slate-200/60`, `shadow-md`. |
| **Sticky Header** | StockTable dùng `sticky top-0` nội bộ. | Standalone Header pattern (Tách Header component riêng). |
| **Typography** | Mã thực thể chưa đồng bộ font mono. | Luôn dùng `font-mono text-xs font-semibold`. |

## 5. Danh sách User Stories

| ID | Vai trò | Hành động | Mục tiêu |
| :--- | :--- | :--- | :--- |
| **US033.1** | Nhân viên kho | Xem danh sách Xuất kho | Thấy giao diện đồng nhất với trang Nhập kho, header luôn cố định khi cuộn. |
| **US033.2** | Quản lý kho | Xem danh sách Tồn kho | Trải nghiệm bảng dữ liệu chuyên nghiệp, dễ đọc mã SKU với font mono. |

## 6. Ràng buộc & Điều kiện (Constraints)
- Không thay đổi logic lọc/sắp xếp của các trang.
- Đảm bảo Touch Target >= 44px cho các nút thao tác trên Mobile.
- Giữ nguyên các chức năng đặc thù (Checkbox selection ở StockPage).

---
**Người lập:** Agent BA
**Ngày:** 17/04/2026
