# 📖 USER STORY SPECIFICATION (USS) - Task033_Story001

> **Mã USS:** `USS_Task033_Story001_standardize-stock-table`
> **Trạng thái:** 🟢 Draft
> **Tính năng:** Chuẩn hóa UI Bảng Tồn kho (StockTable).

---

## 1. User Story Overview
- **As a** Quản lý kho,
- **I want** giao diện bảng Tồn kho chuyên nghiệp, đồng nhất với trang Nhập kho,
- **So that** tôi có thể dễ dàng theo dõi SKU và số lượng mà không bị trôi Header khi cuộn.

## 2. Mockup & Layout Definition (UI Spec)

### 2.1 Cấu trúc mới của StockPage
```tsx
<div className="h-full flex flex-col p-4 md:p-6 lg:p-8 gap-4 md:gap-5">
  <HeaderSection />
  <KPICardsSection />
  <FilterBarSection (StockToolbar) />
  <div className="flex-1 flex flex-col min-h-0 bg-white border border-slate-200/60 rounded-xl overflow-hidden shadow-md">
    <div className="bg-slate-50 border-b border-slate-200 pr-[10px]">
      <StockTableHeader />
    </div>
    <div className="flex-1 overflow-y-auto relative scroll-smooth">
      <StockTableBody />
    </div>
  </div>
</div>
```

### 2.2 Quy cách Table Columns (Alignment)

| Cột | Width (px) | Kiểu dữ liệu | Style đặc thù |
| :--- | :--- | :--- | :--- |
| **Checkbox** | `w-[48px]` | Selection | Căn giữa. |
| **Mã SP** | `w-[110px]` | SKU Code | `font-mono text-xs font-semibold text-slate-900`. |
| **Tên sản phẩm** | `min-w-[200px]` | Name | `text-sm font-medium text-slate-900 truncate`. |
| **Vị trí** | `w-[120px]` | Position | Badge rỗng (`outline`). |
| **Tồn kho** | `w-[110px]` | Qty | Căn phải, `Package` icon. |
| **Hạn SD** | `w-[140px]` | Date | `text-sm text-slate-600`. |
| **Trạng thái** | `w-[130px]` | Status | `StatusBadge` chung. |
| **Thao tác** | `w-[80px]` | Actions | `sticky right-0 bg-white` (khi cuộn ngang). |

## 3. Sequence Spec & Logic
- **Selection Logic:** Duy trì `selectedIds` state từ `StockPage`. Khi click checkbox ở Header, chọn/bỏ chọn toàn bộ items đang hiển thị.
- **Scroll Behavior:** Chỉ `StockTableBody` có `overflow-y-auto`. `StockTableHeader` cố định ở trên.

## 4. Activity Rule Spec (Validation)
- **Rule 1:** Nếu danh sách trống, hiển thị "Không tìm thấy sản phẩm nào" căn giữa.
- **Rule 2:** Các cell trong Header và Body PHẢI có cùng width (`w-[px]`) để khớp hàng.
- **Rule 3:** Mobile Viewport: Ẩn bảng desktop, hiển thị danh sách dạng Card (giữ nguyên logic mobile card cũ của StockTable nhưng update padding/spacing đồng bộ).

---
**Người lập:** Agent BA
**Ngày:** 17/04/2026
