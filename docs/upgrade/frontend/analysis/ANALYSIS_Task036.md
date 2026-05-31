# 📊 CODEBASE ANALYSIS - Task036

> **Task:** Stock Table Final Polish
> **Scope:** `StockPage.tsx`, `StockTable.tsx`

## 1. Inventory & Entry Points
- `src/features/inventory/pages/StockPage.tsx`
- `src/features/inventory/components/StockTable.tsx`
- `src/features/inventory/components/StockTableHeader.tsx` (Tách mới)

## 2. Module Mapping
- **StockPage**: Page container quản lý state selection và filtering.
- **StockTable**: Component hiển thị dữ liệu dạng bảng (Desktop) và Card (Mobile).
- **StockTableHeader**: Component Standalone Header cho việc sticky cố định.

## 3. Business Logic Extraction
- **Selection:** State `selectedIds` được quản lý ở StockPage, truyền xuống StockTable.
- **Filtering:** Logic lọc theo `search`, `status` vẫn giữ nguyên.
- **UI Polish:** Loại bỏ shadow ở Filter Bar, thêm `table-fixed` để căn chỉnh cột.

## 4. Brittleness Hotspots
- **Column Width Matching:** Yêu cầu `StockTableHeader` và `StockTable` phải có cùng `w-[px]`.
- **Sticky Action Column:** `sticky right-0` cần `bg-white` để không bị trong suốt.

## 5. Coverage Gaps
- Unit test đã được cập nhật để kiểm tra Layout.
- E2E test mới được tạo để validate Polish.

## 6. Risks
- **Performance:** `table-fixed` có thể ảnh hưởng nhẹ đến render performance nếu bảng rất lớn (1000+ rows). Tuy nhiên, với độ lớn hiện tại (<100 rows) thì không đáng kể.

---
*Analysis completed by Agent CODEBASE_ANALYST.*