# Dashboard Color Accents — Design Spec

**Date:** 2026-06-12
**Style:** Điểm nhấn màu theo nhóm chỉ số, trên nền Modern SaaS tối giản
**Extends:** `2026-06-11-modern-saas-redesign-design.md` (không supersede — bổ sung màu, giữ nguyên token/layout/typography)

---

## 1. Goals

- Khắc phục feedback "dashboard quá đơn điệu / ít màu sắc" sau bản Modern SaaS.
- Thêm màu **theo nhóm chỉ số** (semantic hue): mỗi nhóm dữ liệu một hue Tailwind, dùng nhất quán mọi nơi nhóm đó xuất hiện.
- Giữ nền tối giản: card vẫn trắng border slate, không gradient trang trí, không nền card màu.

## 2. Files thay đổi

| File | Thay đổi |
| --- | --- |
| `src/features/dashboard/pages/DashboardPage.tsx` | Thêm icon chip màu, status pill, tag màu — chỉ class + icon, không đổi layout/logic |

Không sửa `index.css` (không cần token mới — dùng utility Tailwind trực tiếp). Không sửa Sidebar/Header. Không thay đổi API, store, routing, phân quyền.

## 3. Hệ màu theo nhóm

| Nhóm | Hue | Xuất hiện ở |
| --- | --- | --- |
| Doanh thu / phân tích | `indigo` | Card "Doanh thu hôm nay", chart line, shortcut Báo cáo, kênh Bán lẻ, status "Đang xử lý" |
| Đơn hàng | `sky` | Card "Số đơn hôm nay", KPI "Đơn chờ xử lý", shortcut POS, status "Đang giao / Giao một phần" |
| Phê duyệt | `violet` | KPI "Cần phê duyệt", tag loại phiếu trong list chờ duyệt, shortcut Nhập kho |
| Kho / cảnh báo | `amber` | KPI "Tổng mặt hàng", low stock, status "Chờ duyệt", crown top khách hàng |
| Tiền vào / hoàn thành | `emerald` | Card "Giá trị đơn TB", KPI "Giá trị kho", trend dương, "Tổng thu", kênh Bán sỉ, status "Hoàn thành" |
| Tiền ra / huỷ | `red` | Trend âm, "Tổng chi", status "Đã huỷ", tag kênh "Trả hàng" |
| Khách hàng | `teal` | Icon header "Khách hàng hàng đầu" |

### Nguyên tắc

- Công thức tint thống nhất: **nền `{hue}-50` + nội dung `{hue}-600` (icon) hoặc `{hue}-700` (chữ trong pill)**.
- Màu chỉ xuất hiện qua 3 hình thức: icon chip, pill/tag, chữ màu trần. Không gradient, không shadow màu.
- Icon chip: `rounded-md bg-{hue}-50` chứa icon `text-{hue}-600`; card lớn dùng chip `h-8 w-8` + icon `h-4 w-4`, shortcut dùng chip `h-9 w-9` + icon `h-[18px] w-[18px]`.
- Số liệu chính giữ `text-foreground` (slate-900); label giữ `text-slate-500`.

## 4. Card tài chính (3 card)

Layout header card: label trái, icon chip góc phải (`flex items-start justify-between`). Số + trend + skeleton giữ nguyên.

| Card | Icon | Hue |
| --- | --- | --- |
| Doanh thu hôm nay | `Banknote` (import mới) | indigo |
| Số đơn hôm nay | `ShoppingCart` | sky |
| Giá trị đơn TB | `Receipt` (import lại) | emerald |

## 5. Card KPI (4 card)

Bỏ icon trần `text-slate-400` cạnh label; chuyển thành icon chip góc phải, cùng layout với card tài chính.

| KPI | Icon | Hue |
| --- | --- | --- |
| Tổng mặt hàng | `Package` | amber |
| Đơn chờ xử lý | `ShoppingCart` | sky |
| Cần phê duyệt | `ClipboardCheck` | violet |
| Giá trị kho | `TrendingUp` | emerald |

Sub-text cảnh báo giữ `text-amber-600 font-medium` + `AlertTriangle` như hiện tại.

## 6. Chart + channel

- Gradient fill: stop trên `stopOpacity 0.08 → 0.15` (vẫn 2-stop).
- Line: `strokeWidth 1.5 → 2`, màu giữ `#4f46e5`.
- Toggle 7/30 ngày: tab active đổi `text-slate-900 → text-indigo-600` (nền trắng + border + shadow-xs giữ nguyên).
- Channel bars giữ indigo (Lẻ) / emerald (Sỉ) như hiện tại.

## 7. Status pill + tags

`statusDot()` thay bằng `statusBadge()` trả về cặp class nền + chữ:

| Status | Class |
| --- | --- |
| Pending | `bg-amber-50 text-amber-700` |
| Processing | `bg-indigo-50 text-indigo-700` |
| Shipped / Partial | `bg-sky-50 text-sky-700` |
| Delivered / Completed | `bg-emerald-50 text-emerald-700` |
| Cancelled | `bg-red-50 text-red-700` |
| khác | `bg-slate-100 text-slate-600` |

Pill render: `inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full ${statusBadge(s)}` — bỏ dot.

Tag kênh trong "Đơn hàng gần đây" (hiện `bg-slate-100 text-slate-500`), khớp màu channel bars:

| Kênh | Class |
| --- | --- |
| Retail (Lẻ) | `bg-indigo-50 text-indigo-700` |
| Wholesale (Sỉ) | `bg-emerald-50 text-emerald-700` |
| khác (Trả hàng) | `bg-red-50 text-red-700` |

Tag loại phiếu trong "Cần phê duyệt": `bg-slate-100 text-slate-500 → bg-violet-50 text-violet-700`. Badge đếm đỏ giữ nguyên.

## 8. Lists + cashflow + low stock

- **Khách hàng hàng đầu:** icon `Users` header `text-slate-400 → text-teal-500`; vòng rank #1 `bg-slate-100 → bg-amber-50`, Crown `text-amber-600`; rank 2-5 giữ slate.
- **Dòng tiền tháng này:** icon `Wallet` header `text-slate-400 → text-emerald-500`; phần còn lại giữ nguyên (đã có hộp emerald-50/red-50).
- **Low stock:** giữ nguyên (đã đúng hue amber).
- **Đơn hàng gần đây / Cần phê duyệt:** ngoài pill + tag ở §7, không đổi gì khác.

## 9. Shortcuts

Icon trần `h-5 w-5 text-slate-600` → icon chip `h-9 w-9 rounded-md bg-{hue}-50` chứa icon `h-[18px] w-[18px] text-{hue}-600`:

| Shortcut | Hue |
| --- | --- |
| Bán lẻ (POS) | sky |
| Nhập kho | violet |
| Tồn kho | amber |
| Báo cáo | indigo |

Nút giữ trắng + border slate; hover giữ nguyên.

## 10. Non-goals

- Không token mới trong `index.css`, không đổi Sidebar/Header.
- Không đổi layout, spacing, typography, logic, role-gating.
- Không quay lại gradient/corner accent của bản Enterprise Classic.
- Không đụng trang khác.

## 11. Amendment (2026-06-12, sau visual QA): badge tròn màu đặc

Mức `-50` quá nhạt với user. Card giữ nền trắng; icon chip trên 7 card đầu (3 tài chính + 4 KPI) đổi thành badge tròn màu đặc: `h-10 w-10 rounded-full bg-{hue}-500 text-white`, icon `h-5 w-5`.

## 12. Kiểm chứng

- `tsc --noEmit` và `npm run build` pass.
- Xem trực quan: 7 card có chip màu đúng hue; status pill đúng map; tag kênh khớp màu channel bars; crown vàng; chart line dày hơn + fill đậm hơn.
- Role không có quyền tài chính: 3 card tài chính + chart ẩn, KPI còn 3 card vẫn hiển thị chip đúng.
