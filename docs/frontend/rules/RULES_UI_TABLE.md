# RULES — Quy tắc thiết kế Table Layout chuẩn (Master Table Pattern)

Để đảm bảo tính nhất quán trên toàn hệ thống Mini-ERP, các trang danh sách dạng bảng **phải** tuân thủ bộ khung dưới đây. Thay đổi lệch chuẩn cần ADR phê duyệt.

---

## 0. Mã nguồn tham chiếu (bắt buộc khi code bảng mới)

| Nội dung | Đường dẫn |
| :--- | :--- |
| **Class & width token dùng chung** | `mini-erp/src/lib/data-table-layout.ts` |
| **Primitive UI** | `mini-erp/src/components/ui/table.tsx` |
| **Ví dụ áp dụng** | `ReceiptTable.tsx`, `DispatchTable.tsx`, `StockTable.tsx`, `AuditSessionsTable.tsx` trong `mini-erp/src/features/inventory/components/` |

**Quy tắc:** Khi thêm bảng danh sách mới, import `DATA_TABLE_ROOT_CLASS`, `DATA_TABLE_ACTION_*`, và (nếu cần) mở rộng object cột tương tự `RECEIPT_TABLE_COL` / `DISPATCH_TABLE_COL` trong cùng file `data-table-layout.ts` rồi dùng trong component — **không hard-code width lệch tùy ý** ngoài file chuẩn.

---

## 1. Cấu trúc Layout Trang (Page Wrapper)

- **Container chính**: `h-full flex flex-col p-4 md:p-6 lg:p-8 gap-4 md:gap-5 overflow-hidden`.
- **Header trang**: Tiêu đề + nút (Export, Import, Tạo) trong `flex shrink-0`.
- **Filter bar**: `bg-white p-4 rounded-lg border border-slate-200 space-y-3 shrink-0` (shadow lớn tránh dùng ở đây).

---

## 2. Framework Bảng Dữ Liệu (một `<table>`, không tách header)

### 2.1 Vì sao không tách `TableHeader` / `TableBody` ra hai `<Table>`

Component `Table` (shadcn) bọc `<table>` trong `div` có `overflow-x-auto`. Hai bảng riêng → **độ rộn khác nhau** khi có thanh cuộn dọc / gutter → **`table-fixed` bị lệch cột** so với tiêu đề.

### 2.2 Table Wrapper (một vùng cuộn)

```tsx
<div className="flex-1 flex flex-col min-h-0 bg-white border border-slate-200/60 rounded-xl overflow-hidden shadow-md">
  <div
    data-testid="…-list-container"
    className="flex-1 overflow-y-auto relative scroll-smooth [scrollbar-gutter:stable] min-h-0"
  >
    <YourDataTable /> {/* một <Table> gồm TableHeader + TableBody */}
    {/* Sentinel infinite scroll + spinner */}
  </div>
</div>
```

- **`[scrollbar-gutter:stable]`**: giảm nhảy layout khi scrollbar xuất hiện.
- **`min-h-0`**: flex con được phép co để cuộn đúng.
- **Sticky header hàng tiêu đề**: đặt `className="sticky top-0 z-20 bg-slate-50 …"` trên `<TableHeader>` **bên trong** cùng `<Table>` với body.

### 2.3 Gốc `<Table>` (class chuẩn)

Dùng constant **`DATA_TABLE_ROOT_CLASS`** từ `@/lib/data-table-layout` (gồm `table-fixed`, `min-w-[1024px]` để bảng rộng đủ cột; màn hẹp cuộn ngang trong wrapper của `Table`).

---

## 3. Quy cách cột và typography

| Loại cột | Quy tắc |
| :--- | :--- |
| **Mã (phiếu, SKU, đơn)** | `font-mono text-xs font-semibold text-slate-900` |
| **Tên / mô tả** | `text-sm` + `truncate` nếu dài; tên chính đậm vừa phải |
| **Số lượng dòng** | Icon `Package` nhỏ + số, căn giữa |
| **Cột NV / Thao tác (cuối)** | **Tối thiểu `w-[168px]`** (`DATA_TABLE_ACTION_COL_WIDTH`) — đủ **3** nút `size="icon"` `h-8 w-8` + `gap-0.5` + padding cell. **`sticky right-0`** + nền + shadow (dùng `DATA_TABLE_ACTION_HEAD_CLASS` / `DATA_TABLE_ACTION_CELL_CLASS`). |
| **Căn chỉnh** | `thead` / `tbody` **cùng** object width (ví dụ `RECEIPT_TABLE_COL`) — khớp từng cột. |

**Cấm:** đặt `display: flex` trực tiếp trên `<th>` / `<td>` (phá layout bảng). Nhóm nút trong `<div className="flex flex-nowrap items-center justify-center gap-0.5">`.

---

## 4. Bảng tham chiếu width (Phiếu nhập / Xuất — đồng bộ code)

Các giá trị nằm trong `RECEIPT_TABLE_COL` và `DISPATCH_TABLE_COL`; dưới đây là mô tả ngắn:

| Cột | Khoảng width (Tailwind) |
| :--- | :--- |
| Mã phiếu / mã đơn | `w-[116px]` |
| Nhà cung cấp / Khách hàng | `min-w-[200px]` (cột “linh hoạt” theo chiều ngang) |
| Ngày | `w-[100px]` |
| Người tạo / Người xuất | `w-[152px]` |
| Số HĐ (nhập) | `w-[92px]` |
| Dòng SP / Số lượng | `w-[72px]` |
| Tổng tiền (nhập) | `w-[124px]` |
| Trạng thái | `w-[112px]` |
| **NV** | **`w-[168px]`** + sticky phải |

**Tồn kho (`STOCK_TABLE_COL`):** checkbox, mã SP, tên, vị trí, tồn, hạn SD, trạng thái; cột NV một nút dùng `DATA_TABLE_ACTION_SINGLE_*` (`w-[96px]`).

**Kiểm kê (`AUDIT_SESSION_TABLE_COL`):** mã đợt, tên đợt, ngày, người tạo, tiến độ, lệch dòng, trạng thái, NV (mở/đóng chi tiết — `DATA_TABLE_ACTION_SINGLE_*`).

---

## 5. UX

- **Hover**: `group` trên `TableRow` + `hover:bg-slate-50/50` (cột sticky action dùng `group-hover:bg-slate-50/50` trên cell).
- **Infinite scroll**: `IntersectionObserver` + `sentinel`; spinner khi `isLoadingMore`.
- **Mobile (`< md`)**: ưu tiên **card list**; bảng đầy cột chỉ desktop / tablet ngang.

---

---

## 7. Quy tắc Toolbar & Dropdown (Select)

Để đảm bảo các bộ lọc và hành động trên bảng hoạt động trơn tru:

### 7.1 Cấu trúc Toolbar (bộ lọc)
- **Container**: Phải sử dụng `border-x border-t rounded-t-xl` để khớp nối liền mạch với Table (có `border-x border-b rounded-b-xl`).
- **Nền**: Ưu tiên `bg-white/60 backdrop-blur-md` để tạo hiệu ứng lớp hiện đại.

### 7.2 Dropdown (Select component)
- **Vị trí**: Luôn đặt `position="popper"` và `align="start"`. Điều này đảm bảo dropdown luôn xuất hiện phía dưới Select Trigger, không bị nhảy loạn xạ khi cuộn trang (do Radix tự động tính toán vị trí Popper).
- **Độ rộng (Width)**: 
  - **Phải luôn co giãn theo nội dung**: Ưu tiên sử dụng `w-fit` kết hợp với `min-w-[140px...180px]` tùy nội dung. Điều này đảm bảo khi người dùng chọn một option dài, text không bị cắt bớt (`truncate`) gây khó chịu.
  - **Dàn hàng (Toolbar)**: Trong thanh công cụ, các trigger nên có padding ngang (`px-4`) để text không sát mép icon/mũi tên.
- **Hiển thị**: 
  - Nền của dropdown (`SelectContent`) phải có màu nền đặc (`bg-white` hoặc `bg-popover` với opacity 100%) để đảm bảo đọc rõ chữ trên mọi nền nội dung phía dưới.
  - Box-shadow phải rõ ràng (`shadow-md` hoặc `shadow-xl`) để phân tách với lớp nền.

---

## 8. QA checklist cho Toolbar/Select

- [ ] Select Trigger đủ rộng để hiển thị toàn bộ text mặc định ("Tất cả ...").
- [ ] `SelectContent` sử dụng `position="popper"` (kiểm tra trong `ui/select.tsx`).
- [ ] Toolbar và Table khớp nối border (`border-t-0` trên table if toolbar is present).

---

*Agent DEV: mỗi task có bảng danh sách mới — đọc file này và `data-table-layout.ts` trước khi implement.*
