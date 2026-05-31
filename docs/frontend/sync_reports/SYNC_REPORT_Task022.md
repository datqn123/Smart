# Báo cáo DOC_SYNC (Drift Report) - Task022

**Phạm vi**: Task022 - Cải thiện giao diện Phiếu nhập kho
**Ngày**: 15/04/2026

## 1. Docs impacted

- `FUNCTIONAL_SUMMARY.md`
- `docs/srs/SRS_Task022_inbound-receipt-ui-enhancement.md`
- `mini-erp/src/features/inventory/mockData.ts`
- `mini-erp/src/features/inventory/pages/InboundPage.tsx`

## 2. Drift Findings

### [Med] mockData.ts: Mảng 20 phiếu — Docs không tham chiếu đến dữ liệu đầy đủ
- **Mô tả**: SRS đề cập "tối thiểu 20 phiếu mock" nhưng không ghi chú số lượng hiện tại. File mock đã có 20 bản ghi đa dạng (5 NCC, 4 trạng thái, 2 tháng dữ liệu). Không cần sửa SRS nhưng nên ghi nhận.
- **Mức độ**: Low

### [Low] FUNCTIONAL_SUMMARY.md: Danh sách Tasks chưa bao gồm Task022-024
- **Mô tả**: Progress tracker trong `FUNCTIONAL_SUMMARY.md` vẫn dừng ở Task002, chưa phản ánh thực tế code đang ở Task023.
- **Cảnh báo**: Chưa phải BLOCKER nhưng sẽ gây nhầm lẫn cho agents hoạt động sau.
- **Đề xuất**: Cập nhật mục "Completed" và "In Progress" trong FUNCTIONAL_SUMMARY.md theo sprint.

## 3. Required Updates

- [ ] `FUNCTIONAL_SUMMARY.md` → Mục "Completed": Thêm Task022 (UNIT), Task023 (FEATURE). Mục "In Progress": Task024 (E2E).
- [ ] Không có drift nào ảnh hưởng đến logic nghiệp vụ hay contract API.

## 4. Warnings

- Không có BLOCKER nào. Drift ở mức thông báo (Low/Med).
- `IntersectionObserver` chạy tốt trên môi trường browser. Lưu ý: trong môi trường test (jsdom/vitest), `IntersectionObserver` không tồn tại — cần mock khi viết E2E cho Task024.
