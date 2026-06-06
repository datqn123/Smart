# SRS-017: Thiết kế lại giao diện Bán lẻ (POS)

**Ngày:** 2026-06-06  
**Trạng thái:** Draft  
**Phạm vi:** `frontend/mini-erp/src/features/orders/`

---

## 1. Bối cảnh & Mục tiêu

### 1.1 Vấn đề nghiệp vụ

Giao diện POS hiện tại (`RetailPage` + `POSProductSelector` + `POSCartPanel`) được xây dựng như một prototype chức năng — đủ để demo nhưng **chưa phù hợp cho vận hành thực tế**. Nhân viên thu ngân không thể thực hiện giao dịch nhanh, đặc biệt:

- Không chọn/tìm được khách hàng (nút "Thay đổi" không hoạt động).
- Không nhập tiền khách đưa → không tính được tiền thừa.
- Không có ghi chú đơn, không in hoá đơn sau thanh toán.
- Bộ lọc sản phẩm chưa triển khai (stub), chỉ load 40 sản phẩm, không phân trang.
- Ô giảm giá (`setDiscount`) tồn tại trong store nhưng không có UI.
- Thanh toán "Partial" không có luồng nhập số tiền cụ thể.

### 1.2 Mục tiêu thiết kế lại

| Mục tiêu | Tiêu chí thành công |
|---|---|
| Thu ngân hoàn thành 1 đơn < 60 giây | Chọn sp → checkout ≤ 4 bước |
| Không cần dùng chuột để thanh toán nhanh | Hỗ trợ barcode scan + phím tắt |
| Thông tin khách hàng đầy đủ | Tìm KH theo tên/SĐT hoặc "Khách lẻ" |
| Minh bạch tài chính | Hiển thị rõ: tiền hàng, giảm giá, tiền KH đưa, tiền thừa |
| Vận hành di động | Layout responsive, thao tác tốt trên tablet 10" |

---

## 2. Phân tích hiện trạng (Gap Analysis)

### 2.1 POSProductSelector — Vấn đề

| # | Vấn đề | Mức độ |
|---|---|---|
| P1 | Chỉ load 40 sản phẩm, không có pagination/infinite-scroll | Cao |
| P2 | Nút "Lọc" là stub — không lọc được theo danh mục | Cao |
| P3 | Không có ô nhập barcode (scan súng quét) | Cao |
| P4 | Card sản phẩm chỉ hiện SKU khi không có ảnh → khó nhận dạng | Trung bình |
| P5 | Không có tab/danh mục để duyệt nhanh | Trung bình |

### 2.2 POSCartPanel — Vấn đề

| # | Vấn đề | Mức độ |
|---|---|---|
| C1 | Nút "Thay đổi" khách hàng không có action | Rất cao |
| C2 | Không có UI nhập giảm giá thủ công (store có `setDiscount` nhưng không expose) | Cao |
| C3 | Không tính tiền thừa (khách đưa bao nhiêu) | Cao |
| C4 | Không có ghi chú đơn | Cao |
| C5 | Thanh toán "Partial" không có luồng nhập số tiền đã nhận | Cao |
| C6 | Không hiện receipt sau checkout | Trung bình |
| C7 | Vùng voucher list (max-h-28) quá nhỏ, bị cuộn ngay | Trung bình |
| C8 | Không có "Giữ đơn" (hold order) | Thấp |

### 2.3 RetailPage — Vấn đề layout

| # | Vấn đề | Mức độ |
|---|---|---|
| L1 | Tỉ lệ 8/4 (67%/33%) → cart panel quá hẹp khi nhiều sản phẩm | Trung bình |
| L2 | Trên mobile/tablet: không có cơ chế chuyển giữa giỏ hàng và lưới sản phẩm | Cao |
| L3 | Không có tab "Lịch sử" trên trang POS (phải thoát sang trang khác) | Thấp |

---

## 3. Yêu cầu chức năng

### FR-01: Barcode / Quick-add input

**Mô tả:** Thêm ô input cố định ở đầu vùng chọn sản phẩm. Khi scan súng quét (hoặc gõ tay), hệ thống tìm sản phẩm khớp `skuCode` → tự động thêm 1 đơn vị vào giỏ → focus trở lại ô input.

**Luồng:**
1. Nhân viên scan barcode vào ô "Quét/Nhập mã".
2. Gọi `searchPosProducts({ search: barcode, limit: 1 })`.
3. Nếu khớp đúng 1 kết quả → `addItem()` → toast + clear input.
4. Nếu không khớp → hiện inline error "Không tìm thấy mã: {barcode}".
5. Nếu khớp nhiều → mở dropdown chọn.

**Ưu tiên:** P0 (nghiệp vụ cốt lõi)

---

### FR-02: Lọc sản phẩm theo danh mục

**Mô tả:** Hiển thị tabs ngang ở đầu vùng sản phẩm: "Tất cả", sau đó là các danh mục từ API. Khi chọn tab, danh sách sản phẩm lọc theo `categoryId`.

**Yêu cầu API:** `searchPosProducts` cần thêm param `categoryId?: number`. Backend cần expose endpoint danh sách danh mục POS (hoặc tái sử dụng API categories hiện có).

**UI:**
```
[ Tất cả ] [ Thực phẩm ] [ Đồ uống ] [ Văn phòng phẩm ] ...  →  overflow scroll
```

**Ưu tiên:** P1

---

### FR-03: Pagination / Infinite scroll sản phẩm

**Mô tả:** Chuyển từ single-page query (40 items) sang `useInfiniteQuery` với nút "Tải thêm" hoặc scroll trigger ở cuối grid.

**Thay đổi kỹ thuật:**
- `searchPosProducts` nhận thêm `page` param.
- `POSProductSelector` dùng `useInfiniteQuery`.

**Ưu tiên:** P1

---

### FR-04: Chọn khách hàng

**Mô tả:** Click vào vùng "Khách hàng" mở `CustomerSearchDialog`. Dialog cho phép:
- Tìm theo tên / SĐT.
- Chọn từ danh sách gợi ý.
- Hoặc giữ "Khách lẻ" (không cần tài khoản).

Khi chọn xong → `setCustomer(id, name)` trong store.

**UI Dialog:**
```
┌─────────────────────────────┐
│  Tìm khách hàng             │
│  [ 🔍 Nhập tên hoặc SĐT ] │
│  ─────────────────────────  │
│  • Nguyễn Văn A — 0901...  │
│  • Trần Thị B  — 0912...  │
│  ─────────────────────────  │
│  [ Tiếp tục là Khách lẻ ]  │
└─────────────────────────────┘
```

**Ưu tiên:** P0

---

### FR-05: Giảm giá thủ công (order-level)

**Mô tả:** Hiển thị ô "Giảm giá đơn" trong cart panel, cho phép nhập số tiền giảm (VNĐ). Kết nối với `setDiscount()` trong store. Hiện tại store đã có logic nhưng UI chưa expose.

**UI:** Thêm row trong phần summary:
```
Giảm giá:  [ _____________ ] VNĐ
```

**Ưu tiên:** P1

---

### FR-06: Ghi chú đơn hàng

**Mô tả:** Thêm textarea "Ghi chú" trong cart panel. Giá trị được lưu vào store (`notes`) và gửi kèm khi checkout (`buildRetailCheckoutBody`).

**Thay đổi kỹ thuật:**
- Thêm `notes: string | null` vào `OrderState`.
- Cập nhật `buildRetailCheckoutBody` để truyền `notes`.

**Ưu tiên:** P1

---

### FR-07: Thanh toán nâng cao

#### FR-07a: Tính tiền thừa (Cash calculator)

Khi chọn "Tiền mặt", hiện thêm ô:
```
Khách đưa:  [ 500,000 ]  VNĐ
Tiền thừa:    50,000    VNĐ   ← real-time
```

#### FR-07b: Thanh toán một phần (Partial)

Thêm nút "Trả trước một phần". Khi click mở modal:
```
Tổng đơn:       450,000 VNĐ
Đã nhận:    [ 200,000 ] VNĐ
Còn lại:        250,000 VNĐ
[ Xác nhận Partial ]
```
Gọi `checkoutMutation.mutate("Partial")`.

#### FR-07c: Thanh toán thẻ/chuyển khoản

Đổi label "Thẻ/Chuyển khoản" → `paymentStatus: "Unpaid"` (giữ nguyên, nhưng UX rõ hơn). Có thể thêm sub-label "Ghi nhận nợ".

**Ưu tiên:** FR-07a: P0 | FR-07b: P1 | FR-07c: P2

---

### FR-08: Receipt dialog sau thanh toán

**Mô tả:** Sau khi checkout thành công, thay vì chỉ toast, hiện `ReceiptDialog`:

```
┌──────────────────────────────────┐
│  ✓ Thanh toán thành công         │
│  Mã đơn: SO-20260606-0042        │
│  ──────────────────────────────  │
│  Sản phẩm A × 2     200,000 VNĐ │
│  Sản phẩm B × 1     150,000 VNĐ │
│  ──────────────────────────────  │
│  Giảm giá:           -20,000 VNĐ│
│  Tổng cộng:          330,000 VNĐ│
│  Khách đưa:          500,000 VNĐ│
│  Tiền thừa:          170,000 VNĐ│
│  ──────────────────────────────  │
│  [ 🖨 In hoá đơn ]  [ Đơn mới ] │
└──────────────────────────────────┘
```

**Ưu tiên:** P1

---

### FR-09: Layout responsive (Mobile/Tablet)

**Mô tả:** Trên màn hình < 1024px, thay thế grid 2 cột bằng layout 1 cột với tab bar:

```
[ 🛒 Giỏ hàng (3) ] [ 📦 Sản phẩm ]
```

Tab "Giỏ hàng" có badge số lượng item. Người dùng có thể toggle qua lại.

**Ưu tiên:** P1

---

## 4. Yêu cầu phi chức năng

| # | Yêu cầu | Chỉ tiêu |
|---|---|---|
| NFR-01 | Phản hồi sau scan barcode | < 300ms đến khi sản phẩm xuất hiện trong giỏ |
| NFR-02 | Tải trang POS lần đầu | < 2s (TTI) |
| NFR-03 | Không mất giỏ hàng khi refresh | Persist qua localStorage (đã có) |
| NFR-04 | Accessibility | Tất cả nút có label ARIA; keyboard navigable |
| NFR-05 | Phím tắt | F2 = focus barcode input; Escape = đóng modal |

---

## 5. Thiết kế giao diện mới

### 5.1 Layout Desktop (≥ 1024px)

```
┌─────────────────────────────────────────────────────────────────────┐
│  [🏪 Bán lẻ POS]   Nhân viên: Nguyễn Văn A   [F2: Quét mã]        │
├──────────────────────────────────────┬──────────────────────────────┤
│  VÙNG SẢN PHẨM (col 7/12)           │  VÙNG GIỎ HÀNG (col 5/12)  │
│                                      │                              │
│  ┌─────────────────────────────┐    │  ┌──────────────────────┐   │
│  │ [🔍 Tìm sản phẩm / SKU...] │    │  │ 👤 Khách lẻ  [Chọn] │   │
│  │ [Quét mã: ______________ ]  │    │  └──────────────────────┘   │
│  └─────────────────────────────┘    │                              │
│                                      │  Cart items...               │
│  [Tất cả][Thực phẩm][Đồ uống]...   │  ─────────────────────────  │
│                                      │  Giảm giá: [_________] VNĐ  │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐       │  Ghi chú: [___________]     │
│  │ SP │ │ SP │ │ SP │ │ SP │       │  Voucher: [TAG] [Thêm mã]   │
│  └────┘ └────┘ └────┘ └────┘       │  ─────────────────────────  │
│  ...                                 │  Tạm tính:    450,000 VNĐ   │
│                                      │  Giảm giá:    -20,000 VNĐ   │
│  [Tải thêm sản phẩm...]             │  Tổng cộng:   430,000 VNĐ  │
│                                      │  ─────────────────────────  │
│                                      │  [Tiền mặt] [Thẻ] [Trả trước]│
└──────────────────────────────────────┴──────────────────────────────┘
```

**Tỉ lệ cột:** Đổi từ `lg:grid-cols-12 [8/4]` → `[7/5]` (58%/42%) để cart rộng hơn.

---

### 5.2 Layout Mobile/Tablet (< 1024px)

```
┌────────────────────────────────────┐
│  Bán lẻ POS                        │
├────────────────────────────────────┤
│  [ 📦 Sản phẩm ] [ 🛒 Giỏ (3) ]  │  ← Tab bar
├────────────────────────────────────┤
│                                    │
│  [Active tab content]              │
│                                    │
├────────────────────────────────────┤
│  Tổng: 430,000 VNĐ  [Thanh toán]  │  ← Sticky footer
└────────────────────────────────────┘
```

---

### 5.3 Thanh toán tiền mặt — luồng mới

```
[ Tiền mặt ] được click
    ↓
Inline expand trong cart (không cần modal):
┌──────────────────────────────────────┐
│  Tổng cần trả:    430,000 VNĐ        │
│  Khách đưa: [500,000        ] VNĐ   │
│  Tiền thừa:        70,000 VNĐ  ← live│
│  [ ✓ Xác nhận thanh toán tiền mặt ] │
└──────────────────────────────────────┘
```

---

## 6. Kế hoạch triển khai

### Phase 1 — Sửa lỗi nghiệp vụ cấp bách (P0)

| Task | File | Thay đổi |
|---|---|---|
| FR-04: Customer selector | `POSCartPanel.tsx` + mới `CustomerSearchDialog.tsx` | Kết nối nút "Thay đổi" → dialog tìm KH |
| FR-01: Barcode input | `POSProductSelector.tsx` | Thêm ô "Quét mã", handle Enter/change → `addItem` |
| FR-07a: Cash calculator | `POSCartPanel.tsx` | Thêm inline expand khi click "Tiền mặt" |

### Phase 2 — Hoàn thiện cart (P1)

| Task | File | Thay đổi |
|---|---|---|
| FR-05: Discount UI | `POSCartPanel.tsx` + `useOrderStore.ts` | Expose `setDiscount` |
| FR-06: Notes | `POSCartPanel.tsx` + store + `salesOrdersApi.ts` | Thêm notes field |
| FR-07b: Partial payment | `POSCartPanel.tsx` | Modal partial amount |
| FR-08: Receipt dialog | Mới `ReceiptDialog.tsx` | Hiện sau checkout success |
| FR-09: Mobile layout | `RetailPage.tsx` | Tab bar mobile |

### Phase 3 — Product browser (P1)

| Task | File | Thay đổi |
|---|---|---|
| FR-02: Category tabs | `POSProductSelector.tsx` + `posProductsApi.ts` | Fetch categories, render tabs |
| FR-03: Infinite scroll | `POSProductSelector.tsx` | Migrate sang `useInfiniteQuery` |

---

## 7. Quyết định thiết kế (Open Questions — Đã giải quyết)

| # | Câu hỏi | Quyết định |
|---|---|---|
| OQ-1 | API danh mục POS cần endpoint riêng hay tái dùng? | **Tái dùng** `/categories` hiện có — không cần endpoint mới |
| OQ-2 | "In hoá đơn" thermal hay PDF? | **Bỏ khỏi scope** — receipt dialog chỉ hiện thông tin, không in |
| OQ-3 | Giữ đơn có cần thiết? | **Có** — cơ chế "Lưu nháp": button "Nháp", lưu tạm vào store/localStorage; tự xóa khi hết phiên hoặc người dùng hủy |
| OQ-4 | Voucher / discount per-line? | **Giới hạn scope**: voucher xử lý data mẫu trước; nhiều loại voucher sẽ mở rộng sau; không làm discount per-line ở giai đoạn này |
| OQ-5 | Customer search API? | **Đã có** — `getCustomerList({ search })` → `GET /api/v1/customers?search=...` trong `customersApi.ts`; dùng ngay, không cần tạo mới |

---

### FR-10: Lưu nháp đơn (Draft / Hold Order)

**Mô tả:** Thêm nút "Lưu nháp" trong cart panel. Khi click, trạng thái giỏ hàng hiện tại (items, khách hàng, giảm giá, ghi chú) được đánh dấu là `draft` và giữ nguyên trong localStorage. Người dùng có thể tiếp tục phiên mới hoặc load lại nháp đó sau.

**Cơ chế:**

- Store đã dùng `persist` (Zustand) → chỉ cần thêm flag `isDraft: boolean`.
- Khi checkout thành công → `clearCart()` → nháp tự mất.
- Khi người dùng bấm "Huỷ / Đơn mới" → `clearCart()` → nháp mất.
- Khi refresh trang → load lại từ localStorage, hiện banner "Có đơn nháp chưa thanh toán" với nút "Tiếp tục" / "Huỷ nháp".

**UI banner:**

```
┌──────────────────────────────────────────────┐
│  ⚠️  Có 3 sản phẩm trong đơn nháp chưa xong │
│  [ Tiếp tục đơn nháp ]   [ Xoá nháp ]        │
└──────────────────────────────────────────────┘
```

**Ưu tiên:** P2

---

## 8. Files sẽ thay đổi

```
frontend/mini-erp/src/features/orders/
├── pages/
│   └── RetailPage.tsx                    ← Layout cols + mobile tabs
├── components/
│   ├── POSProductSelector.tsx            ← Barcode input, category tabs, infinite scroll
│   ├── POSCartPanel.tsx                  ← Customer, discount, notes, payment flow
│   ├── CustomerSearchDialog.tsx          ← MỚI
│   └── ReceiptDialog.tsx                 ← MỚI
├── store/
│   └── useOrderStore.ts                  ← Thêm notes, cashReceived
└── api/
    └── salesOrdersApi.ts                 ← buildRetailCheckoutBody nhận notes
```
