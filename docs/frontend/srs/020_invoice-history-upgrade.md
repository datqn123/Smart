# SRS-020 — Upgrade giao diện Lịch sử hoá đơn (`WholesalePage`)

**Ngày:** 2026-06-06
**Tác giả:** SRS_WRITER (auto)
**Trạng thái:** Draft

---

## 1. Bối cảnh

Trang "Lịch sử hoá đơn" (`WholesalePage.tsx`) hiển thị danh sách đơn bán lẻ đã hoàn thành hoặc đã huỷ (endpoint `GET /api/v1/sales-orders/retail/history`). Giao diện hiện tại có nhiều điểm không nhất quán so với các trang đã được nâng cấp (product-management, inventory) và chứa dữ liệu hardcode trong dialog chi tiết.

### 1.1. Phân tích hiện trạng

| Khu vực | Vấn đề |
|---------|--------|
| Sort control | Native `<select>` nằm **ngoài** toolbar — không nhất quán với các trang khác |
| Toolbar | Thiếu filter trạng thái (Hoàn thành / Đã huỷ) và filter thanh toán (Đã TT / Chưa TT / Một phần) |
| Toolbar | Không dùng pill tabs pattern — dùng `<Input type="date">` trần, thiếu shadow / border-radius |
| Table | Thiếu cột `paymentStatus` — dữ liệu có sẵn trong `SalesOrderListItemDto` |
| Table | Cột `status` bị ẩn hẳn (`hideStatusColumn={true}`) — history chỉ có Delivered/Cancelled nên nên hiện |
| Table | TypeBadge "Bán lẻ" luôn cố định (endpoint chỉ trả Retail) → thừa chỗ, nên bỏ |
| Detail dialog | Địa chỉ hardcode: `"123 Đường ABC, Quận X, TP. Hồ Chí Minh"` |
| Detail dialog | Phương thức thanh toán hardcode: `"Chuyển khoản ngân hàng (Bank Transfer)"` |
| Detail dialog | Progress tracker không xử lý trạng thái `Cancelled` (vẫn render bình thường) |
| Detail dialog | Không hiển thị voucher code (`voucherCode`) dù API detail trả về |
| Detail dialog | Không hiển thị thông tin huỷ đơn (`cancelledAt`) khi status = Cancelled |
| Detail dialog | Không hiển thị `paymentStatus` dưới dạng tiếng Việt |

### 1.2. Dữ liệu API liên quan

**List DTO (`SalesOrderListItemDto`):**
- `orderCode`, `customerName`, `finalAmount`, `totalAmount`, `discountAmount`
- `status` (Pending | Processing | Partial | Shipped | Delivered | Cancelled)
- `paymentStatus` (Paid | Unpaid | Partial)
- `itemsCount`, `orderChannel`, `createdAt`

**Detail DTO (`SalesOrderDetailDto` — thêm so với List):**
- `shippingAddress` — địa chỉ giao (null với đơn POS)
- `posShiftRef` — tham chiếu ca POS
- `voucherId`, `voucherCode` — voucher áp dụng
- `cancelledAt`, `cancelledBy` — thông tin huỷ
- `lines[]` — chi tiết sản phẩm

**Schema DB (`salesorders`):**
- `order_channel`: `CHECK(Retail, Wholesale, Return)` — endpoint retail/history chỉ trả `Retail`
- `status`: `CHECK(Pending, Processing, Partial, Shipped, Delivered, Cancelled)`
- `payment_status`: `CHECK(Paid, Unpaid, Partial)`

---

## 2. Phạm vi

Chỉ tác động đến feature `orders`:

| File | Loại thay đổi |
|------|---------------|
| `components/OrderToolbar.tsx` | Sửa variant `retailHistory` |
| `components/OrderTable.tsx` | Thêm cột, xoá TypeBadge |
| `components/OrderDetailDialog.tsx` | Fix dữ liệu hardcode, bổ sung section |
| `pages/WholesalePage.tsx` | Tích hợp sort vào toolbar, thêm filter state |
| `hooks/useRetailSalesHistoryListQuery.ts` | Thêm `paymentStatus` filter state (xem Q1) |
| `api/salesOrdersApi.ts` | Thêm param `paymentStatus` vào `GetRetailSalesHistoryListParams` (xem Q1) |
| `lib/data-table-layout.ts` | Thêm key `paymentStatus` vào `ORDER_TABLE_COL` nếu cần |

---

## 3. Yêu cầu chức năng

### 3.1. Toolbar — Tích hợp sort + thêm filter pill tabs

**Hiện tại:** Sort `<select>` nằm trong page header, toolbar chỉ có search + date range.

**Mới:** Toolbar gồm 3 dòng (tương tự `SupplierToolbar`):

```
Dòng 1: [Search input ─────────────] [Từ ngày input] [─] [Đến ngày input]
Dòng 2: [Tất cả] [Hoàn thành] [Đã huỷ]          ← pill tabs status
Dòng 3: [Tất cả] [Đã TT] [Chưa TT] [Một phần]   ← pill tabs paymentStatus
         [Sắp xếp: Ngày tạo (mới nhất) ▾ ]        ← sort dropdown đặt cuối dòng 3
```

Chi tiết:
- Toolbar style: `bg-white p-4 border border-slate-200 rounded-lg shrink-0 shadow-sm flex flex-col gap-3` — nhất quán với CategoryToolbar
- Pill tabs dùng `cn()` active: `"bg-slate-900 text-white border-slate-900"` / inactive: `"bg-white text-slate-600 border-slate-200 hover:border-slate-400"`
- Sort dropdown: `<select>` kiểu native, nằm trong dòng 3 ở bên phải
- Truyền thêm props: `sort`, `onSortChange`, `statusFilter`, `onStatusChange`, `paymentStatusFilter`, `onPaymentStatusChange`

Constant pill:
```ts
const STATUS_FILTERS = [
  { value: "all",       label: "Tất cả" },
  { value: "Delivered", label: "Hoàn thành" },
  { value: "Cancelled", label: "Đã huỷ" },
] as const

const PAYMENT_FILTERS = [
  { value: "all",     label: "Tất cả" },
  { value: "Paid",    label: "Đã TT" },
  { value: "Unpaid",  label: "Chưa TT" },
  { value: "Partial", label: "Một phần" },
] as const
```

### 3.2. Table — Thêm cột `paymentStatus`

Thêm cột **"Thanh toán"** sau cột "Thành tiền":

| paymentStatus | Label | Badge style |
|---------------|-------|-------------|
| Paid | Đã TT | `bg-green-50 text-green-700` |
| Unpaid | Chưa TT | `bg-red-50 text-red-700` |
| Partial | Một phần | `bg-amber-50 text-amber-700` |

Width: dùng `ORDER_TABLE_COL.payment` (`w-[112px]` đã có sẵn).

### 3.3. Table — Khôi phục cột `status`

- Bỏ prop `hideStatusColumn` khỏi call trong `WholesalePage` (hoặc truyền `hideStatusColumn={false}`)
- `StatusBadge` đã có Delivered (xanh) / Cancelled (đỏ) → dùng lại, không cần sửa
- Đặt cột status sau cột paymentStatus: `…Thành tiền | Thanh toán | Trạng thái | Thao tác`

### 3.4. Table — Bỏ `TypeBadge` khỏi dòng khách hàng

Endpoint `retail/history` chỉ trả `orderChannel: "Retail"` → badge "Bán lẻ" luôn cố định, không có thông tin thêm.

Dòng khách hàng sau khi sửa:
```tsx
<span className={TABLE_CELL_PRIMARY_CLASS}>{item.customerName}</span>
<span className="text-[10px] text-slate-400 font-mono">{item.itemsCount} mặt hàng</span>
```
(xoá `<TypeBadge type={item.type} />`)

### 3.5. Detail Dialog — Fix dữ liệu hardcode

**3.5.1. Địa chỉ giao hàng**

```tsx
// Cũ (hardcode):
<div>123 Đường ABC, Quận X, TP. Hồ Chí Minh</div>

// Mới (từ API):
<div>{detailQuery.data?.shippingAddress?.trim() || "Tại cửa hàng (POS)"}</div>
```

Lưu ý: `OrderDetailDialog` cần nhận thêm prop `shippingAddress?: string | null` từ caller hoặc thêm `detailDto?: SalesOrderDetailDto` — xem §3.5.4.

**3.5.2. Phương thức thanh toán → Trạng thái thanh toán**

Thay ô "Phương thức thanh toán" (hardcode) bằng "Trạng thái thanh toán" (thực tế từ `order.paymentStatus`):

```tsx
// Label + icon: CreditCard giữ nguyên
// Value:
const paymentLabel = {
  Paid: "Đã thanh toán",
  Unpaid: "Chưa thanh toán",
  Partial: "Thanh toán một phần",
}[order.paymentStatus] ?? order.paymentStatus
```

**3.5.3. Progress tracker — xử lý Cancelled**

Khi `order.status === "Cancelled"`:
- Thay progress tracker bằng một banner đỏ: `"Đơn hàng đã bị huỷ"`
- Hiển thị `cancelledAt` (formatted) nếu có từ `detailDto`

```tsx
{order.status === "Cancelled" ? (
  <div className="flex items-center gap-3 bg-red-50 border border-red-100 rounded-xl p-4 text-red-700">
    <XCircle size={20} />
    <div>
      <p className="font-semibold text-sm">Đơn hàng đã bị huỷ</p>
      {detailDto?.cancelledAt && (
        <p className="text-xs text-red-500 mt-0.5">
          Thời điểm huỷ: {formatDate(detailDto.cancelledAt)}
        </p>
      )}
    </div>
  </div>
) : (
  /* Progress tracker hiện tại */ ...
)}
```

**3.5.4. Truyền `detailDto` vào dialog**

Thêm prop `detailDto?: SalesOrderDetailDto` vào `OrderDetailDialogProps` để lấy `shippingAddress`, `cancelledAt`, `posShiftRef`, `voucherCode`.

`WholesalePage` đã có `detailQuery.data` → truyền thêm:
```tsx
<OrderDetailDialog
  ...
  detailDto={detailQuery.data ?? undefined}
/>
```

**3.5.5. Section voucher**

Nếu `detailDto?.voucherCode`:
```tsx
<div className="space-y-2">
  <Label>Voucher áp dụng</Label>
  <div className="h-14 bg-slate-50 rounded-2xl flex items-center px-5 font-bold text-slate-900">
    <Tag size={14} className="mr-2 text-slate-400" />
    {detailDto.voucherCode}
  </div>
</div>
```

**3.5.6. Section POS shift ref**

Nếu `detailDto?.posShiftRef`:
```tsx
<div className="space-y-2">
  <Label>Ca POS</Label>
  <div className="h-14 bg-slate-50 rounded-2xl flex items-center px-5 font-mono text-slate-900">
    {detailDto.posShiftRef}
  </div>
</div>
```

### 3.6. WholesalePage — Dọn dẹp layout

- Xoá block `<div className="flex ... gap-2 ...">` chứa sort `<select>` riêng lẻ (dòng 76–91 hiện tại)
- Sort state + handler truyền vào toolbar
- Thêm state: `statusFilter` (default `"all"`), `paymentStatusFilter` (default `"all"`) — xem Q1 về BE support

---

## 4. Yêu cầu phi chức năng

- Không thêm dependency mới
- `npx tsc --noEmit` phải pass sau khi sửa
- `SalesOrderDetailDto` type import từ `salesOrdersApi.ts` vào `OrderDetailDialog.tsx` chỉ khi cần (không circular)
- Giữ `readOnly` prop flow — không phá vỡ `WholesalePage` và `ReturnsPage`

---

## 5. Kết quả điều tra (câu hỏi đã giải quyết)

### Q1 — BE có support `status` / `paymentStatus` filter không?

**Kết quả: KHÔNG.** Đọc `SalesOrdersController.java:56–68`:

```java
@GetMapping("/retail/history")
public ResponseEntity<...> retailHistory(...,
    @RequestParam(required = false) String search,
    @RequestParam(required = false) String dateFrom,
    @RequestParam(required = false) String dateTo,
    @RequestParam(required = false, defaultValue = "1") int page,
    @RequestParam(required = false, defaultValue = "20") int limit,
    @RequestParam(required = false) String sort) {
```

Endpoint chỉ nhận `search / dateFrom / dateTo / page / limit / sort` — **không có `status` hay `paymentStatus`**.

So sánh: main list endpoint (`GET /api/v1/sales-orders`) có cả `status` và `paymentStatus`, nhưng retail/history thì không.

**Quyết định:** Filter `status` và `paymentStatus` sẽ thực hiện **client-side** trên trang hiện tại (chấp nhận được vì `PAGE_SIZE = 20` nhỏ và lịch sử chỉ có 2 trạng thái: Delivered / Cancelled). Không sửa `GetRetailSalesHistoryListParams`, không thêm params vào API call. Hook `useRetailSalesHistoryListQuery` trả thêm `statusFilter`/`paymentStatusFilter` state nhưng chỉ để lọc mảng `orders` trước khi truyền vào table:

```ts
const filteredOrders = useMemo(() => {
  return orders
    .filter((o) => statusFilter === "all" || o.status === statusFilter)
    .filter((o) => paymentStatusFilter === "all" || o.paymentStatus === paymentStatusFilter)
}, [orders, statusFilter, paymentStatusFilter])
```

Cập nhật phạm vi §2: `api/salesOrdersApi.ts` **không cần sửa** (loại bỏ khỏi bảng file).

### Q2 — Thêm `detailDto?` vào `OrderDetailDialog` có breaking không?

**Kết quả: KHÔNG breaking.** `OrderDetailDialog` được dùng ở đúng 3 caller khác (ngoài `WholesalePage`):

| Caller | Props truyền vào | Ghi chú |
| ------ | --------------- | ------- |
| `ReturnsPage.tsx:251` | `order, isOpen, onClose, onCancelOrder, onEditOrder` | Không truyền `detailDto` → behavior cũ giữ nguyên (hardcode address / payment) |
| `ApprovalHistoryPage.tsx:271` | `order, isOpen, onClose` | Không truyền → behavior cũ |
| `PendingApprovalsPage.tsx` | `order, isOpen, onClose` (xác nhận qua import) | Không truyền → behavior cũ |

Vì `detailDto?: SalesOrderDetailDto` là **optional**, tất cả caller không truyền sẽ nhận `undefined` → dialog fallback về hardcode data như cũ. Không có breaking change. Chỉ `WholesalePage` (truyền `detailDto={detailQuery.data}`) được hưởng lợi từ dữ liệu thực.

---

## 6. Ranh giới ngoài phạm vi

- Không sửa endpoint BE
- Không thêm chức năng export hoá đơn
- Không thêm chức năng in bill từ history
- Không sửa `RetailPage`, `ReturnsPage` hay wholesale order flow

---

## 7. Tiêu chí nghiệm thu

- [ ] Sort dropdown nằm trong toolbar, không còn `<select>` rời ở page header
- [ ] Toolbar có pill tabs: "Tất cả / Hoàn thành / Đã huỷ"
- [ ] Toolbar có pill tabs: "Tất cả / Đã TT / Chưa TT / Một phần"
- [ ] Table có cột "Thanh toán" với badge màu
- [ ] Table hiển thị cột "Trạng thái" (Hoàn thành xanh / Đã huỷ đỏ)
- [ ] Table không còn TypeBadge "Bán lẻ" cố định
- [ ] Detail dialog không còn hardcode địa chỉ "123 Đường ABC"
- [ ] Detail dialog hiển thị paymentStatus bằng tiếng Việt
- [ ] Detail dialog hiển thị banner đỏ + cancelledAt với đơn Cancelled
- [ ] Detail dialog hiển thị voucherCode nếu có
- [ ] `npx tsc --noEmit` pass
