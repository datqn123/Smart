# Plan Cải thiện Giao diện Quản lý Kho hàng (3 trang)

**Ngày:** 2026-06-06  
**Scope:** Tồn kho, Phiếu nhập kho, Phiếu xuất kho  
**Mục tiêu:** Tối ưu UX, cải thiện performance, rõ ràng luồng workflow

---

## 1. Tình trạng hiện tại

| Trang | Component | Vấn đề |
|---|---|---|
| **Tồn kho** (`StockPage`) | Bảng + KPI + Toolbar + 5 dialogs | State quá phức tạp, quản lý cột rối, UX tìm kiếm kém |
| **Phiếu nhập kho** (`InboundPage`) | List + Form + Panel chi tiết | Luồng Draft→Pending→Approved chưa rõ, form dài |
| **Phiếu xuất kho** (`DispatchPage`) | List + Form + Dialog duyệt/xóa | UX tạo phiếu không trực quan, logic duyệt/hủy cần rõ |

---

## 2. 3 Nhóm cải thiện

### A. **Tồn kho** — Tối ưu tìm kiếm + hiển thị

**Vấn đề chính:**
- Toolbar: search text + filter status rời rạc → khó cộng thêm filter theo ngày/danh mục
- KPI hiển thị giữa page → chiếm chỗ, không tập trung vào dữ liệu
- Bulk edit (100 hàng) chưa có cơ chế hỏi xác nhận
- "Bộ lọc nâng cao" (danh mục) chưa triển khai

**Cải thiện:**
- **Collapse bộ lọc nâng cao** (danh mục, vị trí kho, trạng thái) → toggle sidebar trái  
- **KPI-only header** (sticky): 4 số liệu nhỏ gọn ở top  
- **Quick filters row** (All / In Stock / Low Stock / Out of Stock) dưới search  
- **Bulk edit confirmation modal** trước khi patch 100 hàng  
- **Thêm cột "Giá trị (VNĐ)"** để quản lý giá trị tồn kho  

---

### B. **Phiếu nhập kho** — Rõ ràng luồng Draft→Pending→Approved

**Vấn đề chính:**
- Luồng "Lưu nháp" (Draft) vs "Gửi duyệt" (Pending) không trực quan → bấm nút gì để chuyển trạng thái?
- Form tạo quá dài (9 trường input + danh sách dòng lô) → phân tách thành steps
- Quyền "Owner chỉ xóa Draft, Staff xóa Pending" → cần badge/disable button rõ ràng
- Panel detail hiển thị số lượng hàng quá nhỏ

**Cải thiện:**
- **Wizard 3 bước** (cấp Supplier → Nhập dòng hàng → Xác nhận & Gửi duyệt)  
- **Status badge rõ** (Draft = nháp, Pending = đợi duyệt, Approved = đã duyệt)  
- **Nút "Lưu nháp" + "Gửi duyệt" riêng** — rõ ràng hành động tiếp theo  
- **Batch line entry** (quét barcode / nhập SKU + số lượng nhanh)  
- **Panel detail: expand dòng hàng** (lô, hạn dùng, giá) thay vì modal nhỏ  

---

### C. **Phiếu xuất kho** — Luồng tạo phiếu từ đơn hàng rõ ràng

**Vấn đề chính:**
- "Chờ xuất" trạng thái rối: có bao gồm Pending (chờ duyệt) hay không?  
- Tạo phiếu từ đơn bán → phiếu xuất chưa có wizard  
- Xóa mềm có input "reason" → nhưng lý do không được log rõ  
- Không hiển thị "tồn kho khả dụng" khi add dòng

**Cải thiện:**
- **Rõ ràng trạng thái:** Draft → Pending (chờ duyệt) → WaitingDispatch (chờ xuất thực) → Delivering → Delivered  
- **Wizard "Tạo từ đơn hàng"**: chọn đơn → duyệt số lượng khả dụng → confirm → tạo phiếu  
- **Inline edit hàng**: chỉnh số lượng xuất (so với tồn khả dụng)  
- **Log reason khi xóa** → lưu vào detail phiếu để audit  

---

## 3. Roadmap triển khai

| Phase | Trang | Task | Thời lượng |
|---|---|---|---|
| **Phase 1 — UI/UX** | Tồn kho | Collapse filter, KPI header, quick filters | 1-2 ngày |
| | Phiếu nhập | Wizard form, status badges, batch entry UI | 2 ngày |
| | Phiếu xuất | Status diagram, wizard từ đơn | 1-2 ngày |
| **Phase 2 — Logic** | 3 trang | Form validation, permission gates, API integration | 2-3 ngày |
| **Phase 3 — Polish** | 3 trang | Bulk operations, undo/redo, accessibility | 1 ngày |

---

## 4. Files sẽ thay đổi

```
frontend/mini-erp/src/features/inventory/
├── pages/
│   ├── StockPage.tsx          ← collapse filter sidebar, KPI header, quick filters
│   ├── InboundPage.tsx        ← wizard form, status UI
│   └── DispatchPage.tsx       ← wizard từ đơn, status diagram
├── components/
│   ├── InventoryFilterSidebar.tsx  ← MỚI (danh mục, vị trí kho, trạng thái)
│   ├── StockTableEnhanced.tsx      ← thêm cột giá trị, quick actions
│   ├── ReceiptWizardForm.tsx       ← MỚI (3 bước: supplier → dòng → confirm)
│   ├── DispatchWizardFromOrder.tsx ← MỚI (chọn đơn → duyệt số lượng → create)
│   └── ... (còn lại giữ nguyên / enhance)
└── utils/
    ├── inventoryValidation.ts  ← enhance validation
    └── dispatchLogic.ts        ← new: tính toán tồn khả dụng
```

---

## Quyết định cần xác nhận

1. **Tồn kho:** Có thêm cột "Giá trị (VNĐ)" không? (tính `quantity × costPrice`)  
2. **Phiếu nhập:** Có dùng wizard 3 bước hay form inline (less disruptive)?  
3. **Phiếu xuất:** "Chờ xuất" có gồm Draft + Pending hay riêng?  
4. **Chung:** Có thêm "undo/redo" hoặc "draft save" cho các phiếu không?  

Bạn muốn tôi soạn **SRS chi tiết** cho 3 trang này không? (Thay vì plan này)
