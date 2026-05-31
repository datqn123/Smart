# Báo cáo DOC_SYNC (Drift Report) - Task017

**Phạm vi**: Cập nhật logic Tồn kho (Task016, Task017, Task019, Task020, Task021)
**Ngày**: 15/04/2026

## 1. Docs impacted
- `FUNCTIONAL_SUMMARY.md`
- `mini-erp/src/features/inventory/types.ts`
- Thư mục `TASKS/`

## 2. Drift Findings

### [High] Danh sách tiến độ Task bị lệch nghiêm trọng (Outdated Progress)
- **Mô tả**: Trong file `FUNCTIONAL_SUMMARY.md` ở mục "Progress", hệ thống báo mới chỉ hoàn thành Task001, Task002. Thực tế chúng ta đã hoàn tất tới **Task020** (Inventory Local Logic) và vừa render ra các tasks 019-021.
- **Tại sao xảy ra**: Các lần hoàn thành task trước (Task004-Task017) không trigger DOC_SYNC để cập nhật lại tóm tắt này.

### [Med] Model Contract thay đổi nhưng Schema Docs chưa đổi (Database/Type Drift)
- **Mô tả**: Field `status?: 'Draft' | 'Active'` vừa được bổ sung vào `InventoryItem` trong `types.ts` ở Frontend để phục vụ logic UI, nhưng field này có thể chưa xuất hiện trong Database schema (`docs/database/tables/Inventory.md`).
- **Lý do**: Đây là một thay đổi ở cấp độ Frontend (Mock) nhưng về lâu dài Schema DB cần phải mapping 1-1 với type.

## 3. Required Updates
Đề xuất các cập nhật sau:
1. **Cập nhật `FUNCTIONAL_SUMMARY.md`**: Làm mới danh sách Task để bao gồm các task từ 003 đến 021 (Ít nhất là gộp theo cụm Component/Feature đã xong).
2. **Review Database Schema**: Đảm bảo bảng `Inventory` thực sự có hỗ trợ field `status` thay vì chỉ dùng field khác (ví dụ: state lưu trên phiếu nhập `StockReceipt`).

## 4. Warnings (Cảnh báo blockers)
- Mức độ High (BLOCKER) do danh sách Tiến độ dự án bị sai lệch lớn khiến Owner mất cái nhìn tổng quan. Vui lòng cho phép cập nhật `FUNCTIONAL_SUMMARY.md` ngay lập tức.
