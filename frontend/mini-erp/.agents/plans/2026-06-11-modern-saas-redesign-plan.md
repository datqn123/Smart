# Modern SaaS Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Đổi phong cách Sidebar + Header + Dashboard sang Modern SaaS tối giản (Linear/Vercel) theo spec `frontend/mini-erp/.agents/designs/2026-06-11-modern-saas-redesign-design.md`.

**Architecture:** Token-first — thêm token vào `@theme` (index.css) trước, rồi restyle 3 file theo token. Chỉ đổi class/markup trình bày; toàn bộ data, store, routing, phân quyền giữ nguyên. Không tách component.

**Tech Stack:** React 19, TypeScript, Tailwind CSS v4 (`@theme` trong CSS), Recharts, shadcn/ui, lucide-react.

**Verification chung:** Đây là restyle thuần CSS/JSX — không có unit test cho style. Mỗi task xác minh bằng `npx tsc --noEmit` + `npm run build` (chạy trong `frontend/mini-erp/`), task cuối chạy app xem trực quan.

---

### Task 1: index.css — tokens + hợp nhất font

**Files:**

- Modify: `frontend/mini-erp/src/index.css`

- [ ] **Step 1.1: Thêm token mới vào `@theme`**

Trong block `@theme`, sau dòng `--color-border: #e2e8f0;`, thêm:

```css
  --color-accent: #4f46e5; /* Indigo 600 — active nav, link, chart line */
  --color-accent-light: #eef2ff; /* Indigo 50 — nền active state nhạt */
  --color-surface: #fafafa; /* Nền vùng content; card trắng nổi trên nền này */

  --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.04); /* Bóng duy nhất cho card */
```

- [ ] **Step 1.2: Hợp nhất font về Inter**

Thay:

```css
  --font-display: 'Public Sans', system-ui, -apple-system, sans-serif;
```

bằng:

```css
  --font-display: 'Inter', system-ui, -apple-system, sans-serif;
```

- [ ] **Step 1.3: Verify**

Run (trong `frontend/mini-erp/`): `npx tsc --noEmit && npm run build`
Expected: exit 0, không lỗi.

- [ ] **Step 1.4: Commit**

```bash
git add frontend/mini-erp/src/index.css
git commit -m "feat(theme): add accent/surface/shadow-xs tokens, unify font to Inter"
```

---

### Task 2: Sidebar.tsx — restyle (giữ cấu trúc + logic)

**Files:**

- Modify: `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx`

Chỉ đổi class trong JSX phần `return` (từ `<aside>`). Không đổi logic, props, store, permission.

- [ ] **Step 2.1: Nền aside**

Thay:

```tsx
      className={`relative bg-slate-100 flex flex-col flex-shrink-0 h-screen ${
```

bằng:

```tsx
      className={`relative bg-surface flex flex-col flex-shrink-0 h-screen ${
```

- [ ] **Step 2.2: Logo phẳng**

Thay:

```tsx
        <div className="h-8 w-8 bg-primary rounded-lg flex items-center justify-center shadow-sm flex-shrink-0">
          <span className="text-white font-bold text-sm">M</span>
        </div>
```

bằng:

```tsx
        <div className="h-7 w-7 bg-slate-900 rounded-md flex items-center justify-center flex-shrink-0">
          <span className="text-white font-semibold text-xs">M</span>
        </div>
```

- [ ] **Step 2.3: Khoảng cách nhóm — bỏ div đệm**

Thay nav container:

```tsx
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-3">
```

bằng:

```tsx
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
```

Thay group wrapper:

```tsx
          <div key={item.id} className="space-y-2">
```

bằng:

```tsx
          <div key={item.id} className="space-y-1">
```

Xóa hẳn dòng div đệm cuối group:

```tsx
            {/* Reduced vertical whitespace between groups: 12px */}
            {item.id !== "settings" && <div className="h-3" />}
```

- [ ] **Step 2.4: Nút nhóm — gọn, active chỉ đổi màu chữ**

Thay:

```tsx
                <button 
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-md transition-all duration-200 h-11 ${
                    isParentActive(item) 
                      ? "text-slate-900 bg-slate-200/50" 
                      : "text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
                    <div className={`${isParentActive(item) ? "text-primary" : "text-slate-600"} flex-shrink-0`}>
                      {item.icon}
                    </div>
                    <span className={`text-sm ${isParentActive(item) ? "font-semibold" : "font-medium"} truncate`}>
                      {item.label}
                    </span>
                  </div>
                  {item.subItems && (
                    <ChevronDown
                      className={`h-4 w-4 transition-transform duration-200 flex-shrink-0 ${
                        isParentActive(item) ? "text-primary" : "text-slate-600"
                      } ${
                        expandedItems.has(item.id) ? "rotate-180" : ""
                      }`}
                    />
                  )}
                </button>
```

bằng:

```tsx
                <button
                  className={`w-full flex items-center justify-between px-3 rounded-md transition-colors duration-150 h-9 ${
                    isParentActive(item)
                      ? "text-slate-900"
                      : "text-slate-600 hover:bg-slate-200/40"
                  }`}
                >
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
                    <div className={`${isParentActive(item) ? "text-slate-900" : "text-slate-500"} flex-shrink-0`}>
                      {item.icon}
                    </div>
                    <span className="text-[13px] font-medium truncate">
                      {item.label}
                    </span>
                  </div>
                  {item.subItems && (
                    <ChevronDown
                      className={`h-3.5 w-3.5 text-slate-400 transition-transform duration-150 flex-shrink-0 ${
                        expandedItems.has(item.id) ? "rotate-180" : ""
                      }`}
                    />
                  )}
                </button>
```

- [ ] **Step 2.5: Mục con — active pill trắng, bỏ thanh dọc**

Thay:

```tsx
                      className={`w-full text-left px-3 py-2 rounded-md text-sm transition-all duration-200 h-10 flex items-center truncate ${
                        isActiveRoute(subItem.path)
                          ? "relative bg-slate-200 text-slate-900 font-medium before:absolute before:left-0 before:top-0 before:bottom-0 before:w-1 before:bg-primary overflow-hidden"
                          : "text-slate-700 hover:bg-slate-200/50 hover:text-slate-900"
                      }`}
```

bằng:

```tsx
                      className={`w-full text-left px-3 rounded-md text-[13px] transition-colors duration-150 h-8 flex items-center truncate ${
                        isActiveRoute(subItem.path)
                          ? "bg-white border border-slate-200 shadow-xs text-slate-900 font-medium"
                          : "text-slate-600 hover:text-slate-900"
                      }`}
```

- [ ] **Step 2.6: Đăng xuất — trung tính, đỏ khi hover**

Thay:

```tsx
          className="w-full h-11 justify-start space-x-3 text-alert hover:bg-alert-light rounded-md transition-all truncate"
```

bằng:

```tsx
          className="w-full h-10 justify-start space-x-3 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors truncate"
```

- [ ] **Step 2.7: Verify**

Run (trong `frontend/mini-erp/`): `npx tsc --noEmit && npm run build`
Expected: exit 0.

- [ ] **Step 2.8: Commit**

```bash
git add frontend/mini-erp/src/components/shared/layout/Sidebar.tsx
git commit -m "refactor(sidebar): modern SaaS restyle — surface bg, white active pill, tighter rows"
```

---

### Task 3: Header.tsx — restyle (giữ logic)

**Files:**

- Modify: `frontend/mini-erp/src/components/shared/layout/Header.tsx`

- [ ] **Step 3.1: Thanh header phẳng + backdrop blur**

Thay:

```tsx
    <header className="h-14 bg-white border-b border-slate-200 flex items-center px-4 md:px-6 shadow-sm sticky top-0 z-50">
```

bằng:

```tsx
    <header className="h-14 bg-white/80 backdrop-blur border-b border-slate-200 flex items-center px-4 md:px-6 sticky top-0 z-50">
```

- [ ] **Step 3.2: Breadcrumb**

Thay:

```tsx
        <div className="flex items-center space-x-2 text-sm text-slate-600">
```

bằng:

```tsx
        <div className="flex items-center space-x-2 text-[13px] text-slate-500">
```

Thay:

```tsx
          <Link to="/" className="flex items-center hover:text-slate-900 transition-colors">
            <Home className="w-4 h-4 md:mr-2" />
```

bằng:

```tsx
          <Link to="/" className="flex items-center hover:text-slate-900 transition-colors">
            <Home className="h-3.5 w-3.5 md:mr-2" />
```

- [ ] **Step 3.3: Nút chuông + badge**

Thay:

```tsx
              className="relative hover:bg-slate-100 rounded-full h-11 w-11 min-h-11 min-w-11"
```

bằng:

```tsx
              className="relative hover:bg-slate-100 rounded-md h-9 w-9"
```

Thay badge:

```tsx
                <span className="absolute top-1.5 right-1.5 min-w-[18px] h-[18px] px-1 flex items-center justify-center text-[10px] font-bold bg-red-500 text-white rounded-full border-2 border-white">
```

bằng:

```tsx
                <span className="absolute top-1 right-1 min-w-4 h-4 px-1 flex items-center justify-center text-[10px] font-semibold bg-red-500 text-white rounded-full">
```

- [ ] **Step 3.4: Dropdown thông báo — hạ độ nặng**

Thay container:

```tsx
              <div className="absolute right-0 mt-2 w-[400px] bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-200 z-[100]">
```

bằng:

```tsx
              <div className="absolute right-0 mt-2 w-[400px] bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-200 z-[100]">
```

Thay tiêu đề:

```tsx
                    <span className="font-bold text-sm text-slate-900">Thông báo</span>
```

bằng:

```tsx
                    <span className="text-[13px] font-semibold text-slate-900">Thông báo</span>
```

Thay nút mark-all:

```tsx
                    className="text-[11px] font-bold text-slate-500 hover:text-blue-600 flex items-center gap-1 transition-colors disabled:opacity-40 disabled:pointer-events-none"
```

bằng:

```tsx
                    className="text-[11px] font-medium text-slate-500 hover:text-accent flex items-center gap-1 transition-colors disabled:opacity-40 disabled:pointer-events-none"
```

Thay tên item:

```tsx
                            <span className="font-bold text-sm text-slate-900 leading-snug">{n.title}</span>
```

bằng:

```tsx
                            <span className="font-medium text-sm text-slate-900 leading-snug">{n.title}</span>
```

Thay message item:

```tsx
                          <p className="text-xs text-slate-500 leading-relaxed font-medium pl-3">{n.message}</p>
```

bằng:

```tsx
                          <p className="text-xs text-slate-500 leading-relaxed pl-3">{n.message}</p>
```

- [ ] **Step 3.5: User block**

Thay:

```tsx
            <div className="text-right">
              <div className="text-sm font-medium text-slate-900 leading-none">
                {user?.fullName ?? "Người dùng"}
              </div>
              <div className="text-xs text-slate-500 leading-none mt-1">{user?.email ?? ""}</div>
            </div>
            <Avatar className="h-9 w-9 border border-slate-200">
```

bằng:

```tsx
            <div className="text-right">
              <div className="text-[13px] font-medium text-slate-900 leading-none">
                {user?.fullName ?? "Người dùng"}
              </div>
              <div className="text-xs text-slate-400 leading-none mt-1">{user?.email ?? ""}</div>
            </div>
            <Avatar className="h-8 w-8 border border-slate-200">
```

- [ ] **Step 3.6: Verify**

Run (trong `frontend/mini-erp/`): `npx tsc --noEmit && npm run build`
Expected: exit 0.

- [ ] **Step 3.7: Commit**

```bash
git add frontend/mini-erp/src/components/shared/layout/Header.tsx
git commit -m "refactor(header): modern SaaS restyle — flat blur bar, lighter dropdown"
```

---

### Task 4: DashboardPage — nền surface + header trang + 3 card tài chính

**Files:**

- Modify: `frontend/mini-erp/src/features/dashboard/pages/DashboardPage.tsx`

- [ ] **Step 4.1: Bọc nền surface**

Root hiện tại là một div duy nhất vừa padding vừa max-width — bg đặt lên đó sẽ hở mép trắng hai bên. Bọc thêm một lớp:

Thay:

```tsx
  return (
    <div className="p-6 space-y-6 max-w-screen-xl mx-auto">
```

bằng:

```tsx
  return (
    <div className="min-h-full bg-surface">
      <div className="p-6 space-y-6 max-w-screen-xl mx-auto">
```

Và ở cuối file, thay JSX đóng:

```tsx
        </div>
      </div>
    </div>
  )
}
```

bằng (thêm một `</div>`):

```tsx
        </div>
      </div>
      </div>
    </div>
  )
}
```

(Sau khi sửa, chạy lint/format nếu cần để chỉnh indentation; quan trọng là cây JSX đóng đúng.)

- [ ] **Step 4.2: Header trang — bỏ emoji**

Thay:

```tsx
        <h1 className="text-2xl font-bold text-foreground tracking-tight">
          {getGreeting()}, {user?.fullName ?? "Admin"} 👋
        </h1>
        <p className="text-sm text-muted-foreground mt-0.5 capitalize">{todayVN()}</p>
```

bằng:

```tsx
        <h1 className="text-xl font-semibold text-foreground tracking-tight">
          {getGreeting()}, {user?.fullName ?? "Admin"}
        </h1>
        <p className="text-[13px] text-slate-500 mt-0.5 capitalize">{todayVN()}</p>
```

- [ ] **Step 4.3: 3 card tài chính — phẳng, bỏ icon badge + corner accent + trend pill**

Thay toàn bộ block từ `{canSeeFinancials && (` (sau comment `{/* Phân tích nhanh — chỉ role tài chính */}`) đến `)}` đóng block đó (hiện là 3 card có `bg-gradient-to-br`, kết thúc ngay trước comment `{/* KPI Cards */}`) bằng:

```tsx
      {canSeeFinancials && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Doanh thu hôm nay */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5">
            <p className="text-[13px] font-medium text-slate-500">Doanh thu hôm nay</p>
            <div className="h-9 mt-2 flex items-center">
              {ordersLoading ? (
                <Loader2 className="h-5 w-5 animate-spin text-slate-200" />
              ) : (
                <p className="text-2xl font-semibold text-foreground tracking-tight tabular-nums truncate">
                  {formatCurrency(comparison?.todayRevenue ?? 0)}
                </p>
              )}
            </div>
            <div className="h-5 mt-1.5 flex items-center gap-1">
              {!ordersLoading && comparison && (
                <>
                  {comparison.pctChange == null ? (
                    <span className="text-xs text-slate-400">So với hôm qua: —</span>
                  ) : (
                    <>
                      <span
                        className={`inline-flex items-center gap-0.5 text-xs font-medium tabular-nums ${
                          comparison.pctChange >= 0 ? "text-emerald-600" : "text-red-600"
                        }`}
                      >
                        {comparison.pctChange >= 0 ? (
                          <ArrowUpRight className="h-3 w-3" />
                        ) : (
                          <ArrowDownRight className="h-3 w-3" />
                        )}
                        {Math.abs(comparison.pctChange).toFixed(0)}%
                      </span>
                      <span className="text-xs text-slate-400">so với hôm qua</span>
                    </>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Số đơn hôm nay */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5">
            <p className="text-[13px] font-medium text-slate-500">Số đơn hôm nay</p>
            <div className="h-9 mt-2 flex items-center">
              {ordersLoading ? (
                <Loader2 className="h-5 w-5 animate-spin text-slate-200" />
              ) : (
                <p className="text-2xl font-semibold text-foreground tracking-tight tabular-nums">
                  {comparison?.todayOrders ?? 0}
                </p>
              )}
            </div>
            <p className="h-5 mt-1.5 flex items-center text-xs text-slate-400">đơn đã tạo trong ngày</p>
          </div>

          {/* Giá trị đơn trung bình */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5">
            <p className="text-[13px] font-medium text-slate-500">Giá trị đơn TB</p>
            <div className="h-9 mt-2 flex items-center">
              {ordersLoading ? (
                <Loader2 className="h-5 w-5 animate-spin text-slate-200" />
              ) : (
                <p className="text-2xl font-semibold text-foreground tracking-tight tabular-nums truncate">
                  {formatCurrency(comparison?.avgOrderValue ?? 0)}
                </p>
              )}
            </div>
            <p className="h-5 mt-1.5 flex items-center text-xs text-slate-400">trên mỗi đơn hôm nay</p>
          </div>
        </div>
      )}
```

- [ ] **Step 4.4: Dọn import thừa**

`Receipt` không còn dùng (chỉ ở icon badge cũ) — xóa khỏi import lucide-react. Giữ `Wallet` (dòng tiền), `BarChart3` (shortcuts), `ArrowUpRight`/`ArrowDownRight` (trend).

- [ ] **Step 4.5: Verify**

Run (trong `frontend/mini-erp/`): `npx tsc --noEmit && npm run build`
Expected: exit 0, không cảnh báo unused import.

- [ ] **Step 4.6: Commit**

```bash
git add frontend/mini-erp/src/features/dashboard/pages/DashboardPage.tsx
git commit -m "refactor(dashboard): surface bg, flat financial cards, plain-text trend"
```

---

### Task 5: DashboardPage — KPI cards phẳng

**Files:**

- Modify: `frontend/mini-erp/src/features/dashboard/pages/DashboardPage.tsx`

- [ ] **Step 5.1: Gọn kpi array — bỏ field trang trí**

Thay khai báo type + array `kpis` (hiện có `iconBg`, `accentColor`, `cornerGradient`) bằng:

```tsx
  const kpis: {
    title: string
    value: string | number | null
    sub: string | null
    subWarn: boolean
    icon: React.ElementType
    onClick: () => void
    loading: boolean
    show: boolean
  }[] = [
    {
      title: "Tổng mặt hàng",
      value: invData?.totalSkus ?? null,
      sub: invData ? `${invData.lowStockCount} mặt hàng tồn thấp` : null,
      subWarn: (invData?.lowStockCount ?? 0) > 0,
      icon: Package,
      onClick: () => navigate("/inventory/stock"),
      loading: dashboardLoading,
      show: true,
    },
    {
      title: "Đơn chờ xử lý",
      value: invData?.pendingOrders ?? null,
      sub: invData ? `/ ${invData.allOrdersTotal} tổng đơn hàng` : null,
      subWarn: false,
      icon: ShoppingCart,
      onClick: () => navigate("/orders/wholesale"),
      loading: dashboardLoading,
      show: true,
    },
    {
      title: "Cần phê duyệt",
      value: approvalData?.summary.totalPending ?? null,
      sub: approvalData
        ? Object.entries(approvalData.summary.byType)
            .slice(0, 2)
            .map(([k, v]) => `${k} ${v}`)
            .join(" · ") || "Không có mục nào"
        : null,
      subWarn: (approvalData?.summary.totalPending ?? 0) > 0,
      icon: ClipboardCheck,
      onClick: () => navigate("/approvals/pending"),
      loading: dashboardLoading,
      show: true,
    },
    {
      title: "Giá trị kho",
      value: invData ? shortCurrency(invData.totalValue) : null,
      sub: invData ? `${invData.expiringSoonCount} sản phẩm sắp hết hạn` : null,
      subWarn: (invData?.expiringSoonCount ?? 0) > 0,
      icon: TrendingUp,
      onClick: () => navigate("/inventory/stock"),
      loading: dashboardLoading,
      show: canSeeFinancials,
    },
  ].filter((k) => k.show)
```

- [ ] **Step 5.2: Card JSX phẳng — icon trần cạnh label**

Thay body của `kpis.map((kpi) => (...))` bằng:

```tsx
          <div
            key={kpi.title}
            onClick={kpi.onClick}
            className="bg-white rounded-lg border border-slate-200 shadow-xs p-5 cursor-pointer hover:border-slate-300 transition-colors duration-150 flex flex-col"
          >
            <div className="flex items-center gap-2">
              <kpi.icon className="h-4 w-4 text-slate-400" />
              <p className="text-[13px] font-medium text-slate-500">{kpi.title}</p>
            </div>
            <div className="h-10 mt-3 flex items-center">
              {kpi.loading ? (
                <Loader2 className="h-5 w-5 animate-spin text-slate-200" />
              ) : (
                <p className="text-2xl font-semibold text-foreground tracking-tight leading-none tabular-nums truncate">
                  {kpi.value ?? "—"}
                </p>
              )}
            </div>
            <div className="h-5 mt-1.5 flex items-center">
              {!kpi.loading && kpi.sub ? (
                <p
                  className={`text-xs leading-none ${
                    kpi.subWarn ? "text-amber-600 font-medium" : "text-slate-400"
                  }`}
                >
                  {kpi.subWarn && (
                    <AlertTriangle className="h-3 w-3 inline mr-0.5 -mt-px shrink-0" />
                  )}
                  {kpi.sub}
                </p>
              ) : null}
            </div>
          </div>
```

- [ ] **Step 5.3: Verify**

Run (trong `frontend/mini-erp/`): `npx tsc --noEmit && npm run build`
Expected: exit 0.

- [ ] **Step 5.4: Commit**

```bash
git add frontend/mini-erp/src/features/dashboard/pages/DashboardPage.tsx
git commit -m "refactor(dashboard): flat KPI cards — plain icons, no gradients"
```

---

### Task 6: DashboardPage — chart kiểu Vercel Analytics + channel breakdown

**Files:**

- Modify: `frontend/mini-erp/src/features/dashboard/pages/DashboardPage.tsx`

- [ ] **Step 6.1: Header card chart — tổng doanh thu thành số lớn**

Thay:

```tsx
          <div className="lg:col-span-2 bg-white rounded-xl border border-border shadow-[0_1px_3px_rgba(0,0,0,0.04)] p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-sm font-semibold text-foreground">Xu hướng doanh thu</h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Tổng {formatCurrency(revenueTrend.reduce((s, p) => s + p.revenue, 0))} ·{" "}
                  {trendDays} ngày gần nhất
                </p>
              </div>
```

bằng:

```tsx
          <div className="lg:col-span-2 bg-white rounded-lg border border-slate-200 shadow-xs p-5">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-sm font-medium text-slate-900">Xu hướng doanh thu</h2>
                <p className="text-2xl font-semibold text-foreground tracking-tight tabular-nums mt-1">
                  {formatCurrency(revenueTrend.reduce((s, p) => s + p.revenue, 0))}
                </p>
                <p className="text-xs text-slate-400 mt-0.5">{trendDays} ngày gần nhất</p>
              </div>
```

- [ ] **Step 6.2: Toggle segmented control**

Thay:

```tsx
              <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
                {([7, 30] as const).map((d) => (
                  <button
                    key={d}
                    onClick={() => setTrendDays(d)}
                    className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                      trendDays === d
                        ? "bg-white text-foreground shadow-sm"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {d} ngày
                  </button>
                ))}
              </div>
```

bằng:

```tsx
              <div className="flex items-center gap-0.5 bg-slate-100 rounded-md p-0.5">
                {([7, 30] as const).map((d) => (
                  <button
                    key={d}
                    onClick={() => setTrendDays(d)}
                    className={`px-2.5 py-1 text-xs font-medium rounded transition-colors ${
                      trendDays === d
                        ? "bg-white border border-slate-200 shadow-xs text-slate-900"
                        : "border border-transparent text-slate-500 hover:text-slate-900"
                    }`}
                  >
                    {d} ngày
                  </button>
                ))}
              </div>
```

- [ ] **Step 6.3: Chart — line accent indigo, fill cực nhạt**

Thay gradient defs:

```tsx
                      <linearGradient id="dashRevenue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.5} />
                        <stop offset="50%" stopColor="#0ea5e9" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0.02} />
                      </linearGradient>
```

bằng:

```tsx
                      <linearGradient id="dashRevenue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.08} />
                        <stop offset="95%" stopColor="#4f46e5" stopOpacity={0} />
                      </linearGradient>
```

Thay grid:

```tsx
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
```

bằng:

```tsx
                    <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="#f1f5f9" />
```

Thay Tooltip contentStyle:

```tsx
                      contentStyle={{
                        borderRadius: "12px",
                        border: "none",
                        boxShadow: "0 10px 15px -3px rgb(0 0 0 / 0.1)",
                        fontSize: "12px",
                      }}
```

bằng:

```tsx
                      contentStyle={{
                        borderRadius: "8px",
                        border: "1px solid #e2e8f0",
                        boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.05)",
                        fontSize: "12px",
                      }}
```

Thay Area:

```tsx
                    <Area
                      type="monotone"
                      dataKey="revenue"
                      stroke="#0ea5e9"
                      strokeWidth={2}
                      fill="url(#dashRevenue)"
                    />
```

bằng:

```tsx
                    <Area
                      type="monotone"
                      dataKey="revenue"
                      stroke="#4f46e5"
                      strokeWidth={1.5}
                      fill="url(#dashRevenue)"
                    />
```

- [ ] **Step 6.4: Channel breakdown — bar mảnh màu đặc**

Thay card container:

```tsx
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col">
            <h2 className="text-sm font-semibold text-slate-900">Cơ cấu doanh thu theo kênh</h2>
            <p className="text-xs text-slate-400 mt-0.5">{trendDays} ngày gần nhất</p>
```

bằng:

```tsx
          <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5 flex flex-col">
            <h2 className="text-sm font-medium text-slate-900">Cơ cấu doanh thu theo kênh</h2>
            <p className="text-xs text-slate-400 mt-0.5">{trendDays} ngày gần nhất</p>
```

Thay mảng kênh (đổi blue → indigo cho khớp accent):

```tsx
                      { label: "Bán lẻ", value: channels.retail, color: "bg-blue-500", text: "text-blue-600" },
                      { label: "Bán sỉ", value: channels.wholesale, color: "bg-emerald-500", text: "text-emerald-600" },
```

bằng:

```tsx
                      { label: "Bán lẻ", value: channels.retail, color: "bg-indigo-500", text: "text-indigo-600" },
                      { label: "Bán sỉ", value: channels.wholesale, color: "bg-emerald-500", text: "text-emerald-600" },
```

Thay phần pct + bar:

```tsx
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-xs font-medium text-slate-600">{ch.label}</span>
                          <span className={`text-xs font-bold ${ch.text}`}>{pct.toFixed(0)}%</span>
                        </div>
                        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${
                              ch.label === "Bán lẻ"
                                ? "bg-gradient-to-r from-blue-400 to-blue-600"
                                : "bg-gradient-to-r from-emerald-400 to-emerald-600"
                            }`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
```

bằng:

```tsx
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-xs font-medium text-slate-600">{ch.label}</span>
                          <span className={`text-xs font-semibold tabular-nums ${ch.text}`}>{pct.toFixed(0)}%</span>
                        </div>
                        <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${ch.color}`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
```

Thay dòng tổng:

```tsx
                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                    <span className="text-sm font-semibold text-muted-foreground">Tổng cộng</span>
                    <span className="text-base font-bold text-foreground tabular-nums">
                      {formatCurrency(channels.total)}
                    </span>
                  </div>
```

bằng:

```tsx
                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                    <span className="text-[13px] font-medium text-slate-500">Tổng cộng</span>
                    <span className="text-base font-semibold text-foreground tabular-nums">
                      {formatCurrency(channels.total)}
                    </span>
                  </div>
```

- [ ] **Step 6.5: Verify**

Run (trong `frontend/mini-erp/`): `npx tsc --noEmit && npm run build`
Expected: exit 0.

- [ ] **Step 6.6: Commit**

```bash
git add frontend/mini-erp/src/features/dashboard/pages/DashboardPage.tsx
git commit -m "refactor(dashboard): Vercel-style chart header, indigo accent, solid channel bars"
```

---

### Task 7: DashboardPage — lists (status dot), cashflow, low stock, shortcuts

**Files:**

- Modify: `frontend/mini-erp/src/features/dashboard/pages/DashboardPage.tsx`

- [ ] **Step 7.1: statusColor → statusDot**

Thay hàm:

```tsx
function statusColor(s: string) {
  if (s === "Pending") return "bg-amber-100 text-amber-800"
  if (s === "Processing") return "bg-indigo-100 text-indigo-700"
  if (s === "Delivered" || s === "Completed") return "bg-green-100 text-green-700"
  if (s === "Cancelled") return "bg-red-100 text-red-700"
  return "bg-slate-100 text-slate-700"
}
```

bằng:

```tsx
/** Màu chấm trạng thái cho style dot + text (Linear-style). */
function statusDot(s: string) {
  if (s === "Pending") return "bg-amber-500"
  if (s === "Processing") return "bg-indigo-500"
  if (s === "Delivered" || s === "Completed") return "bg-emerald-500"
  if (s === "Cancelled") return "bg-red-500"
  return "bg-slate-400"
}
```

- [ ] **Step 7.2: Status badge đơn hàng → dot + text**

Trong Recent Orders, thay:

```tsx
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${statusColor(order.status)}`}
                    >
                      {statusLabel(order.status)}
                    </span>
```

bằng:

```tsx
                    <span className="inline-flex items-center gap-1.5 text-xs text-slate-600">
                      <span className={`h-1.5 w-1.5 rounded-full ${statusDot(order.status)}`} />
                      {statusLabel(order.status)}
                    </span>
```

- [ ] **Step 7.3: Chuẩn hóa card 4 khối list**

Áp dụng cho 4 container: Recent Orders, Pending Approvals, Top khách hàng, Dòng tiền tháng này.

Thay (3 lần — Recent Orders, Pending Approvals, Top khách hàng):

```tsx
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
```

bằng:

```tsx
        <div className="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
```

(Lưu ý: Top khách hàng có indent khác một cấp — match theo nội dung, không theo khoảng trắng đầu dòng.)

Thay (Dòng tiền tháng này):

```tsx
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col">
```

bằng:

```tsx
          <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5 flex flex-col">
```

Thay tất cả (3 chỗ) `divide-y divide-slate-50` bằng `divide-y divide-slate-100`.

- [ ] **Step 7.4: Top khách hàng — rank badge đơn sắc**

Thay:

```tsx
                    <div
                      className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                        idx === 0
                          ? "bg-amber-100 text-amber-700"
                          : idx === 1
                            ? "bg-slate-200 text-slate-600"
                            : idx === 2
                              ? "bg-orange-100 text-orange-700"
                              : "bg-slate-100 text-slate-400"
                      }`}
                    >
                      {idx === 0 ? <Crown className="h-3.5 w-3.5" /> : idx + 1}
                    </div>
```

bằng:

```tsx
                    <div
                      className={`h-7 w-7 rounded-full bg-slate-100 flex items-center justify-center text-xs font-medium shrink-0 ${
                        idx === 0 ? "text-slate-900" : "text-slate-500"
                      }`}
                    >
                      {idx === 0 ? <Crown className="h-3.5 w-3.5" /> : idx + 1}
                    </div>
```

Thay giá trị khách hàng:

```tsx
                  <p className="text-sm font-bold text-slate-900 tabular-nums shrink-0 ml-3">
```

bằng:

```tsx
                  <p className="text-sm font-semibold text-slate-900 tabular-nums shrink-0 ml-3">
```

- [ ] **Step 7.5: Dòng tiền — bỏ uppercase label, hạ font-black**

Thay khối Thu:

```tsx
                <div className="flex items-center gap-1.5 text-emerald-600">
                  <ArrowDownLeft className="h-4 w-4" />
                  <span className="text-[10px] font-bold uppercase tracking-wider">Tổng thu</span>
                </div>
                <p className="text-lg font-black text-emerald-700 mt-2 tabular-nums truncate">
```

bằng:

```tsx
                <div className="flex items-center gap-1.5 text-emerald-600">
                  <ArrowDownLeft className="h-4 w-4" />
                  <span className="text-xs font-medium">Tổng thu</span>
                </div>
                <p className="text-lg font-semibold text-emerald-700 mt-2 tabular-nums truncate">
```

Thay khối Chi:

```tsx
                <div className="flex items-center gap-1.5 text-red-600">
                  <ArrowUpLeft className="h-4 w-4" />
                  <span className="text-[10px] font-bold uppercase tracking-wider">Tổng chi</span>
                </div>
                <p className="text-lg font-black text-red-700 mt-2 tabular-nums truncate">
```

bằng:

```tsx
                <div className="flex items-center gap-1.5 text-red-600">
                  <ArrowUpLeft className="h-4 w-4" />
                  <span className="text-xs font-medium">Tổng chi</span>
                </div>
                <p className="text-lg font-semibold text-red-700 mt-2 tabular-nums truncate">
```

Thay số dư ròng:

```tsx
              <span className="text-xs font-semibold text-slate-500">Số dư ròng</span>
              <span
                className={`text-base font-black tabular-nums ${
```

bằng:

```tsx
              <span className="text-[13px] font-medium text-slate-500">Số dư ròng</span>
              <span
                className={`text-base font-semibold tabular-nums ${
```

- [ ] **Step 7.6: Low stock — card trắng chuẩn, amber chỉ ở icon + số**

Thay container + header:

```tsx
        <div className="bg-white rounded-xl border border-amber-200 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-amber-100 bg-amber-50/60">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              <h2 className="text-sm font-semibold text-amber-900">
                Cảnh báo tồn kho thấp
                {lowStockData && (
                  <span className="text-amber-500 font-normal ml-1">
                    ({lowStockData.total} mặt hàng)
                  </span>
                )}
              </h2>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-amber-700 h-7 px-2 hover:bg-amber-100"
              onClick={() => navigate("/inventory/stock")}
            >
```

bằng:

```tsx
        <div className="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              <h2 className="text-sm font-medium text-slate-900">
                Cảnh báo tồn kho thấp
                {lowStockData && (
                  <span className="text-amber-600 font-normal ml-1">
                    ({lowStockData.total} mặt hàng)
                  </span>
                )}
              </h2>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-slate-500 h-7 px-2 hover:text-slate-900"
              onClick={() => navigate("/inventory/stock")}
            >
```

Thay item:

```tsx
                  className={`px-4 py-3 cursor-pointer hover:bg-amber-50/40 transition-colors ${
                    idx < (lowStockData?.items.length ?? 0) - 1
                      ? "border-b xl:border-b-0 xl:border-r border-amber-100"
                      : ""
                  }`}
```

bằng:

```tsx
                  className={`px-4 py-3 cursor-pointer hover:bg-slate-50 transition-colors ${
                    idx < (lowStockData?.items.length ?? 0) - 1
                      ? "border-b xl:border-b-0 xl:border-r border-slate-100"
                      : ""
                  }`}
```

Thay item name + số:

```tsx
                  <p className="text-sm font-semibold text-slate-900 line-clamp-1">
                    {item.productName}
                  </p>
                  <p className="text-[10px] text-slate-400 font-mono mt-0.5">{item.skuCode}</p>
                  <div className="flex items-baseline gap-1 mt-1.5">
                    <span className="text-xl font-black text-amber-600 tabular-nums">
                      {item.quantity}
                    </span>
```

bằng:

```tsx
                  <p className="text-sm font-medium text-slate-900 line-clamp-1">
                    {item.productName}
                  </p>
                  <p className="text-[10px] text-slate-400 font-mono mt-0.5">{item.skuCode}</p>
                  <div className="flex items-baseline gap-1 mt-1.5">
                    <span className="text-xl font-semibold text-amber-600 tabular-nums">
                      {item.quantity}
                    </span>
```

- [ ] **Step 7.7: Shortcuts — phẳng, icon trần**

Thay label:

```tsx
        <p className="text-xs font-medium text-muted-foreground mb-3">
          Truy cập nhanh
        </p>
```

bằng:

```tsx
        <p className="text-[13px] font-medium text-slate-500 mb-3">
          Truy cập nhanh
        </p>
```

Thay mảng shortcuts (bỏ field `color`):

```tsx
  const shortcuts = [
    { label: "Bán lẻ (POS)", icon: ShoppingBag, to: "/orders/retail", color: "bg-blue-600" },
    { label: "Nhập kho", icon: Warehouse, to: "/inventory/inbound", color: "bg-emerald-600" },
    { label: "Tồn kho", icon: Package, to: "/inventory/stock", color: "bg-orange-600" },
    { label: "Báo cáo", icon: BarChart3, to: "/analytics/revenue", color: "bg-purple-600" },
  ]
```

bằng:

```tsx
  const shortcuts = [
    { label: "Bán lẻ (POS)", icon: ShoppingBag, to: "/orders/retail" },
    { label: "Nhập kho", icon: Warehouse, to: "/inventory/inbound" },
    { label: "Tồn kho", icon: Package, to: "/inventory/stock" },
    { label: "Báo cáo", icon: BarChart3, to: "/analytics/revenue" },
  ]
```

Thay button:

```tsx
            <button
              key={s.to}
              onClick={() => navigate(s.to)}
              className="flex items-center gap-3 bg-white border border-border shadow-sm rounded-xl p-4 hover:shadow-md hover:border-slate-300 transition-all text-left group"
            >
              <div
                className={`h-10 w-10 rounded-xl ${s.color} flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform`}
              >
                <s.icon className="h-5 w-5 text-white" />
              </div>
              <span className="text-sm font-semibold text-slate-700 group-hover:text-foreground">
                {s.label}
              </span>
            </button>
```

bằng:

```tsx
            <button
              key={s.to}
              onClick={() => navigate(s.to)}
              className="flex items-center gap-3 bg-white border border-slate-200 rounded-lg p-4 hover:bg-slate-50 hover:border-slate-300 transition-colors duration-150 text-left"
            >
              <s.icon className="h-5 w-5 text-slate-600 shrink-0" />
              <span className="text-sm font-medium text-slate-700">
                {s.label}
              </span>
            </button>
```

- [ ] **Step 7.8: Verify**

Run (trong `frontend/mini-erp/`): `npx tsc --noEmit && npm run build`
Expected: exit 0. Kiểm tra `statusColor` không còn được tham chiếu ở đâu (đã đổi tên thành `statusDot`).

- [ ] **Step 7.9: Commit**

```bash
git add frontend/mini-erp/src/features/dashboard/pages/DashboardPage.tsx
git commit -m "refactor(dashboard): dot-style status, monochrome ranks, flat low-stock & shortcuts"
```

---

### Task 8: Kiểm chứng trực quan toàn cục

**Files:** không sửa file (chỉ verify; nếu phát hiện lỗi nhỏ thì sửa + commit `fix:`).

- [ ] **Step 8.1: Chạy app**

Run (trong `frontend/mini-erp/`): `npm run dev`
Mở dashboard trong browser.

- [ ] **Step 8.2: Checklist trực quan**

- Sidebar: nền #fafafa, active pill trắng có border + bóng nhẹ, không còn thanh dọc trái, logout xám (đỏ khi hover), resizer còn hoạt động.
- Header: không bóng, blur nhẹ khi scroll, chuông 9×9 rounded-md, dropdown thông báo rounded-xl.
- Dashboard: nền surface, card trắng phẳng không gradient/emoji/corner accent, chart line indigo + tổng doanh thu là số lớn trên header card, status đơn hàng dạng chấm + chữ.
- Mobile (thu hẹp viewport): sidebar overlay mở/đóng bình thường.
- Loading state: reload trang, spinner hiển thị đúng vị trí trong card.
- Role-gating: nếu có tài khoản role Staff (không thuộc Owner/Admin/Manager) — 3 card tài chính + chart + dòng tiền ẩn, layout không vỡ.
- Trang khác (Tồn kho, Đơn hàng): mở 1-2 trang xác nhận chỉ đổi font heading + shell, không vỡ layout.

- [ ] **Step 8.3: Commit cuối (nếu có sửa lỗi nhỏ)**

```bash
git add -A frontend/mini-erp/src
git commit -m "fix(dashboard): visual polish after manual verification"
```

---

## Spec coverage

| Spec section | Task |
| --- | --- |
| §3 Tokens + font | Task 1 |
| §4 Sidebar | Task 2 |
| §5 Header | Task 3 |
| §6 Header trang + 3 card tài chính + nền surface | Task 4 |
| §6 KPI cards | Task 5 |
| §6 Chart + toggle + channel breakdown | Task 6 |
| §6 Status dot, lists, cashflow, low stock, shortcuts | Task 7 |
| §8 Kiểm chứng | Task 8 + verify từng task |
