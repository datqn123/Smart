# DOC SYNC REPORT - Task025: Inbound Table Layout Refactor

**Status: Completed**
**Author:** Agent DOC_SYNC (acting via Antigravity)

## 1. Docs Impacted
- `FUNCTIONAL_SUMMARY.md`: Cập nhật trạng thái Task025-027 và UC7.
- `RULES_BUG_FIX.md`: Thêm quy tắc [BF-003] về Sticky Header.

## 2. Drift Findings
- **High Drift**: `FUNCTIONAL_SUMMARY.md` trước đó vẫn coi `/inventory/inbound` là dạng Card. Sau Task026 đã đổi hoàn toàn sang Table.
  - *Status*: Đã cập nhật `FUNCTIONAL_SUMMARY.md`.
- **Low Drift**: `RULES.md` chưa đề cập đến việc ưu tiên Table cho các danh sách lớn.
  - *Recommendation*: Cân nhắc bổ sung vào `RULES.md` trong tương lai.

## 3. Knowledge Harvesting
- **Bug Fixed/Prevented**: [BF-003] Sticky Header Context.
- **RCA**: Sticky header trong Shadcn/Tailwind v4 yêu cầu container cha có `overflow-y-auto` và chiều cao cố định. Việc thiếu `z-index` cũng có thể làm nội dung hàng đè lên header khi cuộn.
- **Rule added to `RULES_BUG_FIX.md`**: Yes.

## 4. Required Updates
- [x] Cập nhật `FUNCTIONAL_SUMMARY.md` (Lines 398-403).
- [x] Cập nhật `RULES_BUG_FIX.md` (Section 2).

---
**DOC_SYNC done.** Report: `docs/sync_reports/SYNC_REPORT_Task025.md`. Drift findings: 1. Rules harvested: 1.
