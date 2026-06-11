# Modern SaaS Redesign — Design Spec

**Date:** 2026-06-11
**Style:** Modern SaaS tối giản (Linear/Vercel)
**Approach:** A — Token-first restyle (không tách component)
**Supersedes:** `2026-06-11-dashboard-visual-refresh-design.md` (Enterprise Classic — đã implement nhưng đổi hướng)

---

## 1. Goals

- Đổi hẳn phong cách Dashboard + khung app (Sidebar, Header) sang Modern SaaS tối giản.
- Bề mặt phẳng: border 1px thay shadow; bóng chỉ dùng cho popover và hover.
- **Gỡ bỏ** các trang trí của bản Enterprise Classic: gradient icon badge, corner accent, emoji, endpoint pulse, total badge nổi trên chart.
- Token-first: định nghĩa token mới trong `@theme` trước, restyle 3 file theo token.

## 2. Files thay đổi

| File | Thay đổi |
| ------ | --------- |
| `src/index.css` | Thêm token mới, hợp nhất font |
| `src/components/shared/layout/Sidebar.tsx` | Restyle toàn bộ (giữ cấu trúc + logic) |
| `src/components/shared/layout/Header.tsx` | Restyle toàn bộ (giữ logic) |
| `src/features/dashboard/pages/DashboardPage.tsx` | Restyle toàn bộ (giữ data/logic) |

Không thay đổi API, store, routing, phân quyền, cấu trúc component.

---

## 3. Design tokens & nguyên tắc chung

### Token thêm/sửa trong `@theme` (index.css)

| Token | Giá trị | Dùng cho |
| ------- | --------- | ---------- |
| `--color-brand` | `#4f46e5` (indigo-600) | Active nav, link, chart line, focus ring |
| `--color-brand-light` | `#eef2ff` (indigo-50) | Nền active state nhạt |
| `--color-surface` | `#fafafa` | Nền vùng content; card trắng nổi trên nền này |
| `--shadow-xs` | `0 1px 2px rgba(0,0,0,0.04)` | Bóng duy nhất cho card |

### Nguyên tắc

- **Neutral giữ slate** (toàn codebase đã dùng). Primary giữ `slate-900` — nút đen kiểu Vercel.
- **Một font duy nhất: Inter.** `--font-display` trỏ về Inter (bỏ Public Sans cho heading).
- Số liệu thống kê dùng `tabular-nums`.
- Bỏ label kiểu `UPPERCASE tracking-widest` → chữ thường `text-[13px] font-medium text-slate-500`.
- Radius card thống nhất `rounded-lg`; popover/dropdown dùng `rounded-xl`; không dùng `rounded-2xl` ở bất kỳ đâu.
- Không gradient, không emoji, không corner accent. Transition 150ms.

**Side effect chấp nhận:** đổi font heading + shell mới ảnh hưởng thụ động đến các trang khác (chủ đích — user đã duyệt phạm vi cả khung).

---

## 4. Sidebar (giữ cấu trúc collapsible, resizer, logic phân quyền)

| Thành phần | Hiện tại | Mới |
| --- | --- | --- |
| Nền | `bg-slate-100` | `bg-surface` + `border-r border-slate-200` |
| Logo | Ô vuông primary h-8 + chữ "M" | Ô đen phẳng `h-7 w-7 rounded-md`, tên app `text-sm font-semibold` |
| Nút nhóm | `h-11 py-2.5`, active đổi nền | `h-9 text-[13px] font-medium text-slate-600`; active chỉ `text-slate-900` (không nền); hover `bg-slate-200/40` |
| Mục con | `h-10`, active = nền xám + thanh dọc trái `before:` | `h-8 text-[13px] rounded-md`; active = pill trắng `bg-white border border-slate-200 shadow-xs text-slate-900 font-medium`; bỏ thanh dọc; hover `text-slate-900` |
| Khoảng cách nhóm | `space-y-3` + div đệm `h-3` | Bỏ div đệm; `space-y-1` trong nhóm, `mt-5` giữa nhóm |
| Chevron | `h-4 w-4`, đổi màu theo active | `h-3.5 w-3.5 text-slate-400` cố định |
| Đăng xuất | Chữ đỏ thường trực (`text-alert`) | `text-slate-500`, đỏ khi hover |

## 5. Header

| Thành phần | Hiện tại | Mới |
| --- | --- | --- |
| Thanh | `bg-white shadow-sm` | `bg-white/80 backdrop-blur border-b` — bỏ shadow |
| Breadcrumb | `text-sm` | `text-[13px]`; "Trang chủ" `text-slate-500` hover đậm; trang hiện tại `font-medium text-slate-900`; icon Home `h-3.5` |
| Chuông | `h-11 w-11` tròn | `h-9 w-9 rounded-md`; badge đỏ `h-4 min-w-4 text-[10px]` |
| Dropdown thông báo | `rounded-2xl shadow-2xl`, nhiều `font-bold` | `rounded-xl shadow-lg border-slate-200`; tiêu đề `font-semibold`, tên item `font-medium` |
| User block | Avatar h-9, tên `text-sm` | Avatar `h-8 w-8`; tên `text-[13px] font-medium`; email `text-xs text-slate-400` |

Hành vi (notifications, mark read, mở phiếu, mobile overlay) giữ nguyên 100%.

## 6. Trang Dashboard

Nền trang `bg-surface`, padding `p-6`. Card chuẩn: `bg-white border border-slate-200 rounded-lg shadow-xs`.

| Khu vực | Hiện tại (Enterprise Classic) | Mới |
| --- | --- | --- |
| Chào mừng | `font-bold` + emoji 👋 | `text-xl font-semibold tracking-tight`, bỏ emoji; ngày `text-[13px] text-slate-500` |
| 3 card tài chính | Icon badge gradient, corner accent, trend pill nền màu | Card phẳng `p-5`; bỏ icon badge + corner accent; label `text-[13px] text-slate-500`; số `text-2xl font-semibold tabular-nums`; trend = chữ màu trần kèm arrow (`text-emerald-600` / `text-red-600`), không pill |
| 4 card KPI | Icon box gradient + corner accent | Icon lucide trần `h-4 w-4 text-slate-400` cạnh label; số `text-2xl font-semibold tabular-nums`; hover chỉ `border-slate-300` |
| Chart doanh thu | Gradient 3-stop, endpoint pulse, total badge nổi | Tổng doanh thu lên header card thành số lớn (kiểu Vercel Analytics); line accent indigo 1.5px; fill gradient 2-stop cực nhạt (0.08→0); grid ngang nét đứt `slate-100`; trục `text-[11px] slate-400` |
| Toggle 7/30 ngày | Pill nền slate-100 | Segmented control `text-xs`; active = nền trắng + border + shadow-xs |
| Channel breakdown | Progress bar gradient | Bar `h-1.5 rounded-full` màu đặc (indigo / emerald) |
| Status badge đơn hàng | Pill nền màu (`bg-amber-100`…) | Dot + text: chấm `h-1.5 w-1.5` màu trạng thái + `text-xs text-slate-600` |
| Danh sách (đơn gần đây, chờ duyệt, top KH) | Hover `bg-slate-50` | Giữ hover; divider `slate-100`; rank/crown badge đơn sắc hóa |
| Cảnh báo tồn kho | Amber theme đậm cả card | Card trắng chuẩn; amber chỉ ở icon + con số |
| Shortcut | Icon box màu + shadow | Nút phẳng border; icon trần `text-slate-600`; hover `bg-slate-50 border-slate-300` |

Map màu status cho dot: Pending → amber-500, Processing → indigo-500, Shipped/Partial → blue-500, Delivered/Completed → emerald-500, Cancelled → red-500, khác → slate-400.

---

## 7. Non-goals

- Không thay đổi API layer, data fetching, store, routing.
- Không thay đổi role-gating (`FINANCIAL_ROLES`, `MenuPermissions`).
- Không tách component (giữ monolithic DashboardPage).
- Không dark mode.
- Không chủ động sửa trang khác (chỉ hưởng thụ động font + shell mới).

## 8. Kiểm chứng

- `tsc --noEmit` và `npm run build` pass.
- Chạy app, xem trực quan: dashboard, sidebar (desktop + mobile overlay + resizer), header (breadcrumb, notification dropdown).
- Kiểm tra loading/error state của dashboard query.
- Kiểm tra role không có quyền tài chính: 3 card tài chính ẩn đúng.

## 9. Thứ tự implement

1. `index.css` — token + font.
2. `Sidebar.tsx`.
3. `Header.tsx`.
4. `DashboardPage.tsx` — header trang + 3 card tài chính → KPI → chart + channel → lists + low stock + shortcuts.
