# BUG ELICITATION - Bug025_01: Sticky Header & Layout Padding

**Status: Open**
**Severity: Medium**
**Reported At: 16/04/2026**

## 1. Mô tả lỗi
Sau khi refactor sang Table Layout, giao diện gặp 2 vấn đề về UI/UX:
1. **Sticky Header không hoạt động**: Khi cuộn danh sách phiếu nhập, thanh tiêu đề bảng (Mã phiếu, NCC...) bị cuộn mất tích thay vì cố định ở trên đầu.
2. **Padding Detail Panel**: Nội dung trong Panel chi tiết (Sheet) nằm sát mép trái, thiếu khoảng trống đệm (padding) gây cảm giác chật chội và không thẩm mỹ.

## 2. Các file liên quan (Affected Files)
- `mini-erp/src/features/inventory/components/ReceiptTable.tsx` (Vấn đề Sticky)
- `mini-erp/src/features/inventory/components/ReceiptDetailPanel.tsx` (Vấn đề Padding)
- `mini-erp/src/features/inventory/pages/InboundPage.tsx` (Có thể do lỗi container cuộn)

## 3. Phân tích nguyên nhân
- **Vấn đề 1 (Sticky)**: `TableHeader` có `sticky top-0` nhưng có thể bị ghi đè hoặc do `overflow-hidden` ở container cha không đúng chỗ. Quy tắc `[BF-003]` trong `RULES_BUG_FIX.md` có đề cập đến việc container phải có `overflow-y-auto` và chiều cao xác định.
- **Vấn đề 2 (Padding)**: `SheetContent` hoặc các phần tử bên trong (`DetailItem`) thiếu class padding (`px-4`, `pl-6`...).

## 4. Fix Requirements
- Đảm bảo thanh tiêu đề bảng cố định khi cuộn.
- Thêm padding hợp lý cho `ReceiptDetailPanel` (ít nhất `px-6`).
- Đảm bảo tính thẩm mỹ đồng bộ với hệ thống.

---
**Agent BA done.** Chuyển thông tin cho Agent PM.
