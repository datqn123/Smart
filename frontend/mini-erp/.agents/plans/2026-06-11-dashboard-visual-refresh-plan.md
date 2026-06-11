# Dashboard Visual Refresh — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh Dashboard visual design to Enterprise Classic + Data Viz Polish style — gradient icon badges, corner accents, enhanced charts, refined typography.

**Architecture:** Update CSS classes in one file (DashboardPage.tsx). No API, store, or routing changes. No component extraction.

**Tech Stack:** React 19, TypeScript, Tailwind CSS v4, Recharts, shadcn/ui, lucide-react

---

### Task 1: DashboardPage.tsx — Header + Financial Stats

**Files:**
- Modify: `src/features/dashboard/pages/DashboardPage.tsx`

- [ ] **Step 1.1: Update Header**

Replace the header section (lines 226-234):

Current:
```tsx
      {/* Header */}
      <div>
        <h1
          className="text-2xl font-semibold text-slate-900 tracking-tight"
          style={{ letterSpacing: "-0.02em" }}
        >
          {getGreeting()}, {user?.fullName ?? "Admin"}!
        </h1>
        <p className="text-sm text-slate-400 mt-0.5 capitalize">{todayVN()}</p>
      </div>
```

New:
```tsx
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground tracking-tight">
          {getGreeting()}, {user?.fullName ?? "Admin"} 👋
        </h1>
        <p className="text-sm text-muted-foreground mt-0.5 capitalize">{todayVN()}</p>
      </div>
```

- [ ] **Step 1.2: Update Financial Stats cards**

Replace the 3 financial stat cards (lines 237-320) with updated styling. The data logic stays identical — only CSS classes change.

Replace the entire `{canSeeFinancials && (` block through the closing `)}` of the financial stats section with:

```tsx
      {/* Phân tích nhanh — chỉ role tài chính */}
      {canSeeFinancials && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Doanh thu hôm nay */}
          <div className="relative bg-white rounded-xl border border-border shadow-[0_1px_3px_rgba(0,0,0,0.04)] p-5 overflow-hidden">
            <div className="absolute top-0 right-0 w-16 h-16 bg-gradient-to-br from-emerald-100 to-transparent rounded-bl-3xl" />
            <div className="flex items-center gap-3 mb-3">
              <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-emerald-500 to-green-600 flex items-center justify-center shrink-0">
                <span className="text-white font-bold text-sm">₫</span>
              </div>
              <span className="text-xs font-medium text-muted-foreground">Doanh thu hôm nay</span>
            </div>
            <div className="h-9 flex items-center">
              {ordersLoading ? (
                <Loader2 className="h-5 w-5 animate-spin text-slate-200" />
              ) : (
                <p className="text-2xl font-bold text-foreground tracking-tight tabular-nums truncate">
                  {formatCurrency(comparison?.todayRevenue ?? 0)}
                </p>
              )}
            </div>
            <div className="h-5 mt-2 flex items-center gap-1.5">
              {!ordersLoading && comparison && (
                <>
                  {comparison.pctChange == null ? (
                    <span className="text-xs text-muted-foreground">So với hôm qua: —</span>
                  ) : (
                    <span
                      className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-xs font-semibold ${
                        comparison.pctChange >= 0
                          ? "bg-emerald-50 text-emerald-600"
                          : "bg-red-50 text-red-600"
                      }`}
                    >
                      {comparison.pctChange >= 0 ? (
                        <ArrowUpRight className="h-3 w-3" />
                      ) : (
                        <ArrowDownRight className="h-3 w-3" />
                      )}
                      {Math.abs(comparison.pctChange).toFixed(0)}%
                    </span>
                  )}
                  <span className="text-xs text-muted-foreground">so với hôm qua</span>
                </>
              )}
            </div>
          </div>

          {/* Số đơn hôm nay */}
          <div className="relative bg-white rounded-xl border border-border shadow-[0_1px_3px_rgba(0,0,0,0.04)] p-5 overflow-hidden">
            <div className="absolute top-0 right-0 w-16 h-16 bg-gradient-to-br from-blue-100 to-transparent rounded-bl-3xl" />
            <div className="flex items-center gap-3 mb-3">
              <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shrink-0">
                <Receipt className="h-4 w-4 text-white" />
              </div>
              <span className="text-xs font-medium text-muted-foreground">Số đơn hôm nay</span>
            </div>
            <div className="h-9 flex items-center">
              {ordersLoading ? (
                <Loader2 className="h-5 w-5 animate-spin text-slate-200" />
              ) : (
                <p className="text-2xl font-bold text-foreground tracking-tight tabular-nums">
                  {comparison?.todayOrders ?? 0}
                </p>
              )}
            </div>
            <p className="h-5 mt-2 flex items-center text-xs text-muted-foreground">đơn đã tạo trong ngày</p>
          </div>

          {/* Giá trị đơn trung bình */}
          <div className="relative bg-white rounded-xl border border-border shadow-[0_1px_3px_rgba(0,0,0,0.04)] p-5 overflow-hidden">
            <div className="absolute top-0 right-0 w-16 h-16 bg-gradient-to-br from-purple-100 to-transparent rounded-bl-3xl" />
            <div className="flex items-center gap-3 mb-3">
              <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-purple-500 to-violet-600 flex items-center justify-center shrink-0">
                <BarChart3 className="h-4 w-4 text-white" />
              </div>
              <span className="text-xs font-medium text-muted-foreground">Giá trị đơn TB</span>
            </div>
            <div className="h-9 flex items-center">
              {ordersLoading ? (
                <Loader2 className="h-5 w-5 animate-spin text-slate-200" />
              ) : (
                <p className="text-2xl font-bold text-foreground tracking-tight tabular-nums truncate">
                  {formatCurrency(comparison?.avgOrderValue ?? 0)}
                </p>
              )}
            </div>
            <p className="h-5 mt-2 flex items-center text-xs text-muted-foreground">trên mỗi đơn hôm nay</p>
          </div>
        </div>
      )}
```

- [ ] **Step 1.3: Verify TypeScript compiles**

Run: `npx tsc --noEmit`
Expected: No errors

- [ ] **Step 1.4: Commit**

```bash
git add src/features/dashboard/pages/DashboardPage.tsx
git commit -m "refactor(dashboard): refresh header + financial stats — gradient badges, corner accents"
```

---

### Task 2: DashboardPage.tsx — KPI Cards

**Files:**
- Modify: `src/features/dashboard/pages/DashboardPage.tsx`

- [ ] **Step 2.1: Update KPI card icon styling**

Update the `kpis` array icon definitions (lines 147-212). Change `iconBg` from `bg-{color}-50` to gradient classes, and `accentColor` from `text-{color}-600` to `text-white`:

```tsx
  const kpis: {
    title: string
    value: string | number | null
    sub: string | null
    subWarn: boolean
    icon: React.ElementType
    iconBg: string
    accentColor: string
    cornerGradient: string
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
      iconBg: "bg-gradient-to-br from-blue-500 to-blue-600",
      accentColor: "text-white",
      cornerGradient: "from-blue-100",
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
      iconBg: "bg-gradient-to-br from-orange-500 to-orange-600",
      accentColor: "text-white",
      cornerGradient: "from-orange-100",
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
      iconBg: "bg-gradient-to-br from-purple-500 to-purple-600",
      accentColor: "text-white",
      cornerGradient: "from-purple-100",
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
      iconBg: "bg-gradient-to-br from-emerald-500 to-emerald-600",
      accentColor: "text-white",
      cornerGradient: "from-emerald-100",
      onClick: () => navigate("/inventory/stock"),
      loading: dashboardLoading,
      show: canSeeFinancials,
    },
  ].filter((k) => k.show)
```

- [ ] **Step 2.2: Update KPI card rendering**

Replace the KPI card rendering section (lines 322-368) with updated styling:

```tsx
      {/* KPI Cards */}
      <div
        className={`grid grid-cols-1 sm:grid-cols-2 gap-4 ${
          kpis.length === 4 ? "lg:grid-cols-4" : "lg:grid-cols-3"
        }`}
      >
        {kpis.map((kpi) => (
          <div
            key={kpi.title}
            onClick={kpi.onClick}
            className="group relative bg-white rounded-xl border border-border shadow-[0_1px_3px_rgba(0,0,0,0.04)] p-5 cursor-pointer hover:shadow-md hover:border-slate-300 transition-all duration-200 flex flex-col overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-16 h-16 bg-gradient-to-br from-[color:var(--corner-from)] to-transparent rounded-bl-3xl" style={{ ["--corner-from" as string]: undefined }} />
            <div className="flex items-start justify-between relative z-10">
              <div className={`h-9 w-9 rounded-lg flex items-center justify-center ${kpi.iconBg}`}>
                <kpi.icon className={`h-4 w-4 ${kpi.accentColor}`} />
              </div>
            </div>
            <p className="text-xs font-medium text-muted-foreground mt-4 mb-1.5 relative z-10">
              {kpi.title}
            </p>
            <div className="h-10 flex items-center relative z-10">
              {kpi.loading ? (
                <Loader2 className="h-5 w-5 animate-spin text-slate-200" />
              ) : (
                <p className="text-2xl font-bold text-foreground tracking-tight leading-none tabular-nums truncate">
                  {kpi.value ?? "—"}
                </p>
              )}
            </div>
            <div className="h-5 mt-2 flex items-center relative z-10">
              {!kpi.loading && kpi.sub ? (
                <p
                  className={`text-xs leading-none ${
                    kpi.subWarn ? "text-amber-600 font-semibold" : "text-muted-foreground"
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
        ))}
      </div>
```

Note: The corner gradient uses CSS variable approach. Since Tailwind doesn't support dynamic gradient colors easily, we'll use inline style for the corner accent. Replace the corner div with:

```tsx
<div className={`absolute top-0 right-0 w-16 h-16 bg-gradient-to-br ${kpi.cornerGradient.replace("from-", "from-")} to-transparent rounded-bl-3xl opacity-60`} />
```

Actually, since `cornerGradient` is already a Tailwind class like `from-blue-100`, we can use it directly:

```tsx
<div className={`absolute top-0 right-0 w-16 h-16 bg-gradient-to-br ${kpi.cornerGradient} to-transparent rounded-bl-3xl opacity-60`} />
```

- [ ] **Step 2.3: Verify TypeScript compiles**

Run: `npx tsc --noEmit`
Expected: No errors

- [ ] **Step 2.4: Commit**

```bash
git add src/features/dashboard/pages/DashboardPage.tsx
git commit -m "refactor(dashboard): refresh KPI cards — gradient icons, corner accents, refined typography"
```

---

### Task 3: DashboardPage.tsx — Revenue Chart + Channel Breakdown

**Files:**
- Modify: `src/features/dashboard/pages/DashboardPage.tsx`

- [ ] **Step 3.1: Update chart card header**

Replace the chart card header (lines 374-398) with pill-style toggle:

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
            </div>
```

- [ ] **Step 3.2: Update chart gradient to 3-stop**

Replace the chart gradient definition (lines 407-412):

Current:
```tsx
                    <defs>
                      <linearGradient id="dashRevenue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                      </linearGradient>
                    </defs>
```

New:
```tsx
                    <defs>
                      <linearGradient id="dashRevenue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.5} />
                        <stop offset="50%" stopColor="#0ea5e9" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
```

- [ ] **Step 3.3: Update channel breakdown progress bars**

Replace the channel progress bars (lines 481-486) with gradient versions:

Current:
```tsx
                        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${ch.color} rounded-full transition-all`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
```

New:
```tsx
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

- [ ] **Step 3.4: Update channel total row**

Replace the total row (lines 493-498):

Current:
```tsx
                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-500">Tổng cộng</span>
                    <span className="text-sm font-black text-slate-900 tabular-nums">
                      {formatCurrency(channels.total)}
                    </span>
                  </div>
```

New:
```tsx
                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                    <span className="text-sm font-semibold text-muted-foreground">Tổng cộng</span>
                    <span className="text-base font-bold text-foreground tabular-nums">
                      {formatCurrency(channels.total)}
                    </span>
                  </div>
```

- [ ] **Step 3.5: Verify TypeScript compiles**

Run: `npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3.6: Commit**

```bash
git add src/features/dashboard/pages/DashboardPage.tsx
git commit -m "refactor(dashboard): enhance chart gradient, channel bars, pill toggle"
```

---

### Task 4: DashboardPage.tsx — Lists + Bottom sections (minor)

**Files:**
- Modify: `src/features/dashboard/pages/DashboardPage.tsx`

- [ ] **Step 4.1: Update list row hover and channel badge**

In the Recent Orders section, update row hover and channel badge:

Replace `hover:bg-slate-50/60` with `hover:bg-slate-50` (all occurrences in the file).

Replace channel badge:
```tsx
<span className="text-[10px] text-slate-400 border border-slate-200 rounded px-1 shrink-0">
```
with:
```tsx
<span className="text-[10px] text-slate-500 bg-slate-100 rounded px-1.5 shrink-0">
```

- [ ] **Step 4.2: Update Quick Shortcuts**

Replace the shortcuts section (lines 794-817):

```tsx
      {/* Quick Shortcuts */}
      <div>
        <p className="text-xs font-medium text-muted-foreground mb-3">
          Truy cập nhanh
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {shortcuts.map((s) => (
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
          ))}
        </div>
      </div>
```

- [ ] **Step 4.3: Verify TypeScript compiles**

Run: `npx tsc --noEmit`
Expected: No errors

- [ ] **Step 4.4: Commit**

```bash
git add src/features/dashboard/pages/DashboardPage.tsx
git commit -m "refactor(dashboard): polish lists, shortcuts — refined hover, badges, shadows"
```

---

### Task 5: Final verification

**Files:**
- No file changes

- [ ] **Step 5.1: Run all tests**

Run: `npx vitest run`
Expected: No new test failures (pre-existing ReceiptTable failures are unrelated)

- [ ] **Step 5.2: Verify TypeScript compiles**

Run: `npx tsc --noEmit`
Expected: No errors
