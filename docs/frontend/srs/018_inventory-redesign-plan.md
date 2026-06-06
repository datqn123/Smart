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

---

### Q1 — Tồn kho: Có hiển thị cột "Giá trị tồn kho (VNĐ)" không?

**Bối cảnh từ DB:**  
Bảng `inventory` chỉ lưu `quantity` (số lượng). Giá vốn (`cost_price`) nằm ở bảng `productpricehistory` — cần JOIN thêm để tính `quantity × cost_price`. Không phải truy vấn đơn giản.

**Option A — Có:** Thêm cột "Giá trị (VNĐ)" vào bảng tồn kho  
- Cần BE endpoint mới trả về `costPrice` kèm theo mỗi dòng tồn  
- FE tính và hiển thị `quantity × costPrice`  
- Giá trị sẽ là **giá vốn tại thời điểm tra cứu gần nhất** (theo `effective_date`)

**Option B — Không:** Bỏ qua, chỉ hiển thị số lượng như hiện tại  
- Không cần thêm endpoint hay JOIN

> **Bạn cần làm rõ:** Người dùng có cần biết tổng giá trị kho từng dòng không? Hay chỉ cần tổng trên Dashboard là đủ?

---

### Q2 — Phiếu nhập: Dùng Wizard hay Form inline để tạo phiếu?

**Bối cảnh từ DB:**  
Bảng `stockreceipts` cần: `supplier_id`, `receipt_date`, `invoice_number`, `notes`. Bảng `stockreceiptdetails` cần N dòng, mỗi dòng có: `product_id`, `unit_id`, `quantity`, `cost_price`, **`batch_number`**, **`expiry_date`**. Tổng cộng 5–6 trường header + ít nhất 1 dòng hàng → form khá dài.

**Option A — Wizard 3 bước:**
```
Bước 1: Nhà cung cấp + Số hóa đơn + Ngày nhập
Bước 2: Nhập dòng hàng (SKU / quét barcode, Lô, Hạn dùng, SL, Giá vốn)
Bước 3: Xem lại tổng tiền → chọn "Lưu nháp (Draft)" hoặc "Gửi duyệt (Pending)"
```

**Option B — Form một trang duy nhất:**  
Tất cả header + bảng dòng hàng nằm trên 1 trang, cuộn xuống để thêm dòng.

> **Bạn cần làm rõ:** Nhân viên tạo phiếu có thường xuyên nhập nhiều dòng hàng (>10 SKU) không? Nếu có → Wizard dễ theo dõi hơn. Nếu thường chỉ 1–3 dòng → Form inline tiện hơn.

---

### Q3 — Phiếu xuất: Luồng trạng thái thực tế là gì?

**Bối cảnh từ DB:**  
Bảng `stockdispatches` **không có trạng thái Draft**. Các trạng thái thực tế trong DB là:

```
Pending → WaitingDispatch → Delivering → Delivered
                         ↘ Full / Partial  (hoàn tất xuất)
              Cancelled (huỷ ở bất kỳ bước nào)
```

- `Pending` = Chờ Admin/Owner duyệt phiếu xuất  
- `WaitingDispatch` = Đã duyệt, chờ nhân viên kho thực hiện pick hàng  
- `Full` / `Partial` = Đã xuất xong toàn bộ / một phần  
- `Delivering` / `Delivered` = Đang vận chuyển / Đã giao  
- `Cancelled` = Đã hủy (có lưu `delete_reason` trong DB)

> **Bạn cần làm rõ:** Nghiệp vụ có cần trạng thái "nháp" (tức là tạo phiếu rồi lưu lại, chưa gửi duyệt) không? Nếu có thì cần thêm `Draft` vào CHECK constraint ở DB. Nếu không cần → tạo phiếu = gửi duyệt luôn (Pending).

---

### Q4 — Chung: Có cần "Lưu nháp tự động" (auto-save draft) không?

**Bối cảnh từ DB:**  
- **Phiếu nhập (`stockreceipts`):** Đã có trạng thái `Draft` trong DB → lưu nháp được, chỉ cần gọi API tạo Draft.  
- **Phiếu xuất (`stockdispatches`):** **Không có Draft** trong DB → nếu muốn lưu nháp phiếu xuất thì phải lưu client-side (localStorage) hoặc bổ sung `Draft` vào DB.

**Option A — Chỉ lưu nháp thủ công (click "Lưu nháp"):**  
- Phiếu nhập: Bấm nút → tạo bản ghi `Draft` trên server  
- Phiếu xuất: Chưa hỗ trợ (tạo = Pending luôn)  
- Đơn giản, không tốn thêm API

**Option B — Auto-save draft sau mỗi lần thay đổi (debounce 5–10s):**  
- Chỉ áp dụng cho phiếu nhập (có sẵn Draft trong DB)  
- Phiếu xuất vẫn không auto-save được (không có Draft)  
- Cần xử lý debounce, conflict nếu 2 tab cùng mở

> **Bạn cần làm rõ:** Nhân viên có thường xuyên bị mất dữ liệu do refresh/đóng tab không? Nếu có → nên làm Option B cho phiếu nhập. Nếu không → Option A đủ dùng.
