# Dashboard Visual Refresh — Design Spec

**Date:** 2026-06-11
**Style:** Enterprise Classic + Data Viz Polish
**Approach:** C — Hybrid (Gradient icon badges + Refined charts + Corner accents)

---

## 1. Goals

- Nâng cấp look & feel Dashboard theo hướng "Enterprise Classic + Data Viz Polish"
- Gradient icon badges cho mỗi stat card — dễ nhận diện, premium feel
- Chart có gradient 3-stop + endpoint indicator + total badge
- Corner gradient accent trên mỗi card — tinh tế
- Pill-style toggle buttons cho chart
- Trend badges với arrow icons

## 2. Files thay đổi

| File | Thay đổi |
|------|---------|
| `src/features/dashboard/pages/DashboardPage.tsx` | Toàn bộ visual refresh |

Không thay đổi API, store, hay routing.

---

## 3. Header + Financial Stats

### Header

| Token | Current | New |
|-------|---------|-----|
| Greeting | `{getGreeting()}, {user?.fullName}!` | `{getGreeting()}, {user?.fullName} 👋` |
| Description | `todayVN()` | Thêm subtitle: "Đây là tổng quan hôm nay của bạn" |

### Financial Stats Cards (3 cards — role-gated)

**Card 1: Doanh thu hôm nay**
| Token | Current | New |
|-------|---------|-----|
| Background | `bg-gradient-to-br from-slate-900 to-slate-800 text-white` | `bg-white border border-slate-200 rounded-xl shadow-[0_1px_3px_rgba(0,0,0,0.04)]` |
| Icon | `Wallet` small | Gradient badge: `bg-gradient-to-br from-emerald-500 to-green-600` với text "₫" |
| Label | `text-[10px] uppercase tracking-widest` | `text-xs font-medium text-slate-500` |
| Value | `text-2xl font-black` | `text-2xl font-bold tracking-tight` |
| Trend | Inline text | Pill badge: `bg-emerald-50 text-emerald-600` với arrow icon |
| Corner accent | Không | `absolute top-0 right-0 w-15 h-15 bg-gradient-to-br from-emerald-100 to-transparent rounded-bl-full` |

**Card 2: Số đơn hôm nay**
| Token | Current | New |
|-------|---------|-----|
| Background | `bg-white border border-slate-200` | Giữ nguyên + `shadow-[0_1px_3px_rgba(0,0,0,0.04)]` |
| Icon | `Receipt` small | Gradient badge: `bg-gradient-to-br from-blue-500 to-indigo-600` với icon 📦 |
| Label | `text-[10px] uppercase tracking-widest` | `text-xs font-medium text-slate-500` |
| Value | `text-2xl font-black` | `text-2xl font-bold tracking-tight` |
| Sub | `text-xs text-slate-400` | `text-xs text-slate-400` |
| Corner accent | Không | `absolute top-0 right-0 w-15 h-15 bg-gradient-to-br from-blue-100 to-transparent rounded-bl-full` |

**Card 3: Giá trị đơn TB**
| Token | Current | New |
|-------|---------|-----|
| Background | `bg-white border border-slate-200` | Giữ nguyên + `shadow-[0_1px_3px_rgba(0,0,0,0.04)]` |
| Icon | `BarChart3` small | Gradient badge: `bg-gradient-to-br from-purple-500 to-violet-600` với icon 💎 |
| Label | `text-[10px] uppercase tracking-widest` | `text-xs font-medium text-slate-500` |
| Value | `text-2xl font-black` | `text-2xl font-bold tracking-tight` |
| Trend | Không có | Thêm trend badge (nếu có data) |
| Corner accent | Không | `absolute top-0 right-0 w-15 h-15 bg-gradient-to-br from-purple-100 to-transparent rounded-bl-full` |

---

## 4. KPI Cards

| Token | Current | New |
|-------|---------|-----|
| Card | `bg-white border border-slate-200 rounded-xl` | + `shadow-[0_1px_3px_rgba(0,0,0,0.04)]` + corner accent gradient |
| Icon | `h-10 w-10 rounded-xl bg-{color}-50` + colored icon | `h-9 w-9 rounded-lg bg-gradient-to-br from-{color}-500 to-{color}-600` + white icon |
| Title | `text-[10px] uppercase tracking-widest` | `text-xs font-medium text-slate-500` (bỏ uppercase) |
| Value | `text-3xl font-black` | `text-2xl font-bold tracking-tight` |
| Sub text | `text-xs text-slate-400` | Giữ nguyên |
| Arrow right | `ArrowRight` icon góc phải | Bỏ (giữ hover effect) |
| Hover | `hover:shadow-md hover:-translate-y-0.5` | `hover:shadow-md hover:border-slate-300` (bỏ translate) |

**Corner accent:** Mỗi KPI card thêm `absolute top-0 right-0 w-15 h-15 bg-gradient-to-br from-{color}-100 to-transparent rounded-bl-full` (tương ứng màu icon).

**Các KPI giữ nguyên:** Tổng mặt hàng, Đơn chờ xử lý, Cần phê duyệt, Giá trị kho.

---

## 5. Revenue Chart + Channel Breakdown

### Revenue Chart Card

| Token | Current | New |
|-------|---------|-----|
| Card | `bg-white border border-slate-200 rounded-xl shadow-sm` | Giữ nguyên |
| Title | `text-sm font-semibold` | Giữ nguyên |
| Subtitle | `text-xs text-slate-400` | Thêm tổng doanh thu: "Tổng ₫X · 30 ngày gần nhất" |
| Toggle container | `bg-slate-100 rounded-lg p-0.5` | `bg-slate-100 rounded-lg p-1` |
| Toggle button | `px-2.5 py-1 text-xs` | `px-3 py-1.5 text-xs` |
| Toggle active | `bg-white text-slate-900 shadow-sm` | Giữ nguyên |

### Chart Enhancements

| Token | Current | New |
|-------|---------|-----|
| Gradient | 2-stop: `0.25 → 0` | 3-stop: `0.5 → 0.2 → 0.02` |
| Endpoint indicator | Không | Circle + pulse ring ở điểm cuối chart |
| Total badge | Không | `absolute top-2 right-2 bg-white border rounded-lg px-2 py-1 text-xs` |

### Channel Breakdown

| Token | Current | New |
|-------|---------|-----|
| Progress bar Retail | `bg-blue-500` | `bg-gradient-to-r from-blue-400 to-blue-600` |
| Progress bar Wholesale | `bg-emerald-500` | `bg-gradient-to-r from-emerald-400 to-emerald-600` |
| Percentage | `text-xs font-bold` | Giữ nguyên |
| Total label | `text-xs font-semibold` | `text-sm font-semibold` |
| Total value | `text-sm font-black` | `text-base font-bold` |

---

## 6. Lists + Bottom Sections

### Recent Orders / Pending Approvals / Top Customers

| Token | Current | New |
|-------|---------|-----|
| Row hover | `hover:bg-slate-50/60` | `hover:bg-slate-50` |
| Channel badge | `border border-slate-200` | `bg-slate-100 border-none` |

Giữ nguyên: status badges, rank badges, cashflow cards.

### Low Stock Alert

Giữ nguyên toàn bộ (amber theme đã tốt).

### Quick Shortcuts

| Token | Current | New |
|-------|---------|-----|
| Button | `border border-slate-200` | + `shadow-sm` |
| Icon box | `h-9 w-9 rounded-lg` | `h-10 w-10 rounded-xl` |
| Hover | `hover:shadow-md` | Giữ nguyên |

---

## 7. Non-goals

- Không thay đổi API layer (dashboardApi.ts)
- Không thay đổi data fetching logic
- Không thay đổi role-gating (FINANCIAL_ROLES)
- Không refactor component structure (giữ monolithic)
- Không thay đổi routing

---

## 8. Implementation order

1. Header + Financial Stats cards
2. KPI Cards
3. Revenue Chart + Channel Breakdown
4. Lists + Bottom sections (minor)
