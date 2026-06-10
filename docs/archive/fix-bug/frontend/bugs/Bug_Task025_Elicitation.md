# BUG ELICITATION - Task025: Màn hình trắng xóa (WSOD) tại Inbound Page

**Status: Open**
**Severity: Critical (Blocker)**
**Reported At: 16/04/2026**

## 1. Mô tả lỗi
Người dùng gặp màn hình trắng hoàn toàn khi truy cập đường dẫn `/inventory/inbound` sau khi thực hiện refactor sang Table Layout.

## 2. Các file nghi ngờ (Suspects)
- `mini-erp/src/features/inventory/pages/InboundPage.tsx`
- `mini-erp/src/features/inventory/components/ReceiptTable.tsx`
- `mini-erp/src/features/inventory/components/ReceiptDetailPanel.tsx`

## 3. Phân tích nguyên nhân (Giả thuyết)
- **Null Pointer**: Có thể `selectedReceipt` đang truyền vào `ReceiptDetailPanel` khi giá trị là `null` mà component chưa xử lý check null tốt.
- **Hook mismatch**: Lỗi trong logic `inboundLogic.ts` hoặc việc tái sử dụng hook gây crash.
- **Component Error**: Lỗi import hoặc thư viện (Shadcn UI) chưa được cài đặt đúng/đầy đủ.

## 4. Requirement để sửa (Fix Requirements)
- Khắc phục lỗi màn hình trắng, hiển thị lại được danh sách phiếu nhập.
- Đảm bảo Error Boundary hoạt động để không crash toàn trang (nếu có thể).
- Viết Unit Test để tái hiện lỗi (Regression Test).

---
**Agent BA done.** Chuyển thông tin cho Agent PM để điều phối.
