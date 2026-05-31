# BUG ELICITATION - Bug025_04: Chuẩn hóa UI Table toàn hệ thống

**Status: Open**
**User Requirement**: "Giao diện ở 2 table Phiếu nhập kho và Xuất kho & điều phối rất khác nhau. Hãy tạo lại table ở Xuất kho... update Rules quy tắc".

## 1. Phân tích sự khác biệt
- **Font & Style**: Inbound dùng `font-mono text-xs font-semibold` cho mã phiếu, Dispatch dùng `font-mono font-medium`.
- **Iconography**: Inbound dùng icon `Package` cho số lượng SKU, Dispatch chỉ dùng text.
- **Avatar**: Dispatch dùng Avatar circle cho người thực hiện, Inbound chỉ dùng text.
- **Width Management**: Dispatch dùng `w-[px]` trên từng Cell, Inbound chỉ dùng trên Header.

## 2. Giải pháp chuẩn hóa (The "Master Table" Pattern)
Tất cả các bảng dữ liệu chính phải tuân theo bộ quy tắc:
1. **Container**: Unified border wrapper (rounded-xl, shadow-sm).
2. **Header**: Standalone `ReceiptTableHeader` style (bg-slate-50, border-b).
3. **Mã code**: Font mono, `text-xs font-semibold text-slate-900`.
4. **Cột Staff**: Sử dụng Avatar Circle nhỏ + Name.
5. **Cột Số lượng**: Dùng Badge hoặc Icon + Qty để trực quan.
6. **Thao tác**: Luôn là `Eye` icon với `sticky right-0`.

## 3. Cập nhật Rules
Thiết lập file `RULES_UI_TABLE.md` để Agent DEV luôn tuân thủ khi tạo table mới.

---
**Agent BA done.** Chuyển PM điều phối flow Sửa đổi.
