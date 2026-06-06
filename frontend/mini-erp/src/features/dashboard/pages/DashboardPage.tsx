import { useEffect, useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"
import {
  Package,
  ShoppingCart,
  ClipboardCheck,
  AlertTriangle,
  ArrowRight,
  ArrowUpRight,
  ArrowDownRight,
  Loader2,
  TrendingUp,
  ShoppingBag,
  Warehouse,
  BarChart3,
  Wallet,
  Receipt,
  Users,
  ArrowDownLeft,
  ArrowUpLeft,
  Crown,
} from "lucide-react"
import { usePageTitle } from "@/context/PageTitleContext"
import { useAuthStore } from "@/features/auth/store/useAuthStore"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { formatCurrency } from "@/features/inventory/utils"
import { getDashboard } from "@/features/dashboard/api/dashboardApi"

function getGreeting() {
  const h = new Date().getHours()
  if (h < 12) return "Chào buổi sáng"
  if (h < 18) return "Chào buổi chiều"
  return "Chào buổi tối"
}

function todayVN() {
  return new Date().toLocaleDateString("vi-VN", {
    weekday: "long",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  })
}

/** Rút gọn số tiền lớn thành "30,5 tr đ" / "1,2 tỷ đ" cho KPI card. */
function shortCurrency(n: number): string {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1).replace(".", ",")} tỷ đ`
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1).replace(".", ",")} tr đ`
  return `${n.toLocaleString("vi-VN")} đ`
}

function statusLabel(s: string) {
  const map: Record<string, string> = {
    Pending: "Chờ duyệt",
    Processing: "Đang xử lý",
    Partial: "Giao một phần",
    Shipped: "Đang giao",
    Delivered: "Hoàn thành",
    Completed: "Hoàn thành",
    Cancelled: "Đã huỷ",
  }
  return map[s] ?? s
}

function statusColor(s: string) {
  if (s === "Pending") return "bg-amber-100 text-amber-800"
  if (s === "Processing") return "bg-indigo-100 text-indigo-700"
  if (s === "Delivered" || s === "Completed") return "bg-green-100 text-green-700"
  if (s === "Cancelled") return "bg-red-100 text-red-700"
  return "bg-slate-100 text-slate-700"
}

function channelLabel(c: string) {
  if (c === "Retail") return "Lẻ"
  if (c === "Wholesale") return "Sỉ"
  return "Trả hàng"
}

/** Roles được xem dữ liệu tài chính (doanh thu, giá trị kho). */
const FINANCIAL_ROLES = ["Owner", "Admin", "Manager"] as const

export function DashboardPage() {
  const { setTitle } = usePageTitle()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const [trendDays, setTrendDays] = useState<7 | 30>(7)

  const canSeeFinancials = FINANCIAL_ROLES.includes(
    (user?.role ?? "Owner") as (typeof FINANCIAL_ROLES)[number],
  )

  useEffect(() => {
    setTitle("Bảng Điều Khiển")
  }, [setTitle])

  const dashboardQ = useQuery({
    queryKey: ["dashboard", "overview", trendDays],
    queryFn: () => getDashboard({ trendDays, recentLimit: 5, topCustomerLimit: 5, alertLimit: 5 }),
    staleTime: 60_000,
  })

  const dashboardData = dashboardQ.data
  const invData = dashboardData?.kpis
  const approvalData = useMemo(
    () =>
      dashboardData?.kpis
        ? {
            summary: {
              totalPending: dashboardData.kpis.pendingApprovals,
              byType: dashboardData.kpis.approvalByType,
            },
            items: dashboardData.pendingApprovals ?? [],
          }
        : undefined,
    [dashboardData],
  )
  const lowStockData = useMemo(
    () =>
      dashboardData
        ? {
            items: dashboardData.lowStockAlerts ?? [],
            total: dashboardData.kpis?.lowStockCount ?? dashboardData.lowStockAlerts?.length ?? 0,
          }
        : undefined,
    [dashboardData],
  )
  const recentOrders = dashboardData?.recentOrders ?? []

  const revenueTrend = canSeeFinancials ? dashboardData?.revenueTrend ?? [] : []
  const comparison = canSeeFinancials ? dashboardData?.financial ?? null : null
  const channels = canSeeFinancials ? dashboardData?.channelBreakdown ?? null : null
  const topCustomers = dashboardData?.topCustomers ?? []
  const cashflow = canSeeFinancials ? dashboardData?.cashflow ?? null : null
  const dashboardLoading = dashboardQ.isLoading

  const kpis: {
    title: string
    value: string | number | null
    sub: string | null
    subWarn: boolean
    icon: React.ElementType
    iconBg: string
    accentColor: string
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
      iconBg: "bg-blue-50",
      accentColor: "text-blue-600",
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
      iconBg: "bg-orange-50",
      accentColor: "text-orange-600",
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
      iconBg: "bg-purple-50",
      accentColor: "text-purple-600",
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
      iconBg: "bg-emerald-50",
      accentColor: "text-emerald-600",
      onClick: () => navigate("/inventory/stock"),
      loading: dashboardLoading,
      show: canSeeFinancials,
    },
  ].filter((k) => k.show)

  const shortcuts = [
    { label: "Bán lẻ (POS)", icon: ShoppingBag, to: "/orders/retail", color: "bg-blue-600" },
    { label: "Nhập kho", icon: Warehouse, to: "/inventory/inbound", color: "bg-emerald-600" },
    { label: "Tồn kho", icon: Package, to: "/inventory/stock", color: "bg-orange-600" },
    { label: "Báo cáo", icon: BarChart3, to: "/analytics/revenue", color: "bg-purple-600" },
  ]

  const ordersLoading = dashboardLoading

  return (
    <div className="p-6 space-y-6 max-w-screen-xl mx-auto">
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

      {/* Phân tích nhanh — chỉ role tài chính */}
      {canSeeFinancials && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Doanh thu hôm nay + so sánh */}
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-5 text-white shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
                Doanh thu hôm nay
              </p>
              <Wallet className="h-4 w-4 text-slate-500" />
            </div>
            <div className="h-9 flex items-center mt-3">
              {ordersLoading ? (
                <Loader2 className="h-5 w-5 animate-spin text-slate-600" />
              ) : (
                <p className="text-2xl font-black tabular-nums truncate">
                  {formatCurrency(comparison?.todayRevenue ?? 0)}
                </p>
              )}
            </div>
            <div className="h-5 mt-2 flex items-center gap-1.5">
              {!ordersLoading && comparison && (
                <>
                  {comparison.pctChange == null ? (
                    <span className="text-xs text-slate-400">So với hôm qua: —</span>
                  ) : (
                    <span
                      className={`inline-flex items-center gap-0.5 text-xs font-semibold ${
                        comparison.pctChange >= 0 ? "text-emerald-400" : "text-red-400"
                      }`}
                    >
                      {comparison.pctChange >= 0 ? (
                        <ArrowUpRight className="h-3.5 w-3.5" />
                      ) : (
                        <ArrowDownRight className="h-3.5 w-3.5" />
                      )}
                      {Math.abs(comparison.pctChange).toFixed(0)}% so với hôm qua
                    </span>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Số đơn hôm nay */}
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
                Số đơn hôm nay
              </p>
              <Receipt className="h-4 w-4 text-slate-300" />
            </div>
            <div className="h-9 flex items-center mt-3">
              {ordersLoading ? (
                <Loader2 className="h-5 w-5 animate-spin text-slate-200" />
              ) : (
                <p className="text-2xl font-black text-slate-900 tabular-nums">
                  {comparison?.todayOrders ?? 0}
                </p>
              )}
            </div>
            <p className="h-5 mt-2 flex items-center text-xs text-slate-400">đơn đã tạo trong ngày</p>
          </div>

          {/* Giá trị đơn trung bình */}
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
                Giá trị đơn TB
              </p>
              <BarChart3 className="h-4 w-4 text-slate-300" />
            </div>
            <div className="h-9 flex items-center mt-3">
              {ordersLoading ? (
                <Loader2 className="h-5 w-5 animate-spin text-slate-200" />
              ) : (
                <p className="text-2xl font-black text-slate-900 tabular-nums truncate">
                  {formatCurrency(comparison?.avgOrderValue ?? 0)}
                </p>
              )}
            </div>
            <p className="h-5 mt-2 flex items-center text-xs text-slate-400">trên mỗi đơn hôm nay</p>
          </div>
        </div>
      )}

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
            className="group bg-white rounded-xl border border-slate-200 p-5 cursor-pointer hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 flex flex-col"
          >
            <div className="flex items-start justify-between">
              <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${kpi.iconBg}`}>
                <kpi.icon className={`h-5 w-5 ${kpi.accentColor}`} />
              </div>
              <ArrowRight className="h-4 w-4 text-slate-200 group-hover:text-slate-400 transition-colors mt-0.5" />
            </div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mt-4 mb-1.5">
              {kpi.title}
            </p>
            <div className="h-10 flex items-center">
              {kpi.loading ? (
                <Loader2 className="h-5 w-5 animate-spin text-slate-200" />
              ) : (
                <p className="text-3xl font-black text-slate-900 leading-none tabular-nums truncate">
                  {kpi.value ?? "—"}
                </p>
              )}
            </div>
            <div className="h-5 mt-2 flex items-center">
              {!kpi.loading && kpi.sub ? (
                <p
                  className={`text-xs leading-none ${
                    kpi.subWarn ? "text-amber-600 font-semibold" : "text-slate-400"
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

      {/* Biểu đồ doanh thu + cơ cấu kênh — chỉ role tài chính */}
      {canSeeFinancials && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Revenue trend chart */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">Xu hướng doanh thu</h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Tổng {formatCurrency(revenueTrend.reduce((s, p) => s + p.revenue, 0))} ·{" "}
                  {trendDays} ngày gần nhất
                </p>
              </div>
              <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-0.5">
                {([7, 30] as const).map((d) => (
                  <button
                    key={d}
                    onClick={() => setTrendDays(d)}
                    className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-colors ${
                      trendDays === d
                        ? "bg-white text-slate-900 shadow-sm"
                        : "text-slate-500 hover:text-slate-700"
                    }`}
                  >
                    {d} ngày
                  </button>
                ))}
              </div>
            </div>
            <div className="h-[260px] w-full">
              {ordersLoading ? (
                <div className="h-full flex items-center justify-center text-slate-300">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={revenueTrend} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
                    <defs>
                      <linearGradient id="dashRevenue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis
                      dataKey="label"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 11, fill: "#94a3b8" }}
                      interval="preserveStartEnd"
                      minTickGap={trendDays === 30 ? 24 : 8}
                      dy={6}
                    />
                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 11, fill: "#94a3b8" }}
                      tickFormatter={(v) => (v >= 1_000_000 ? `${v / 1_000_000}tr` : `${v / 1000}k`)}
                      width={40}
                    />
                    <Tooltip
                      contentStyle={{
                        borderRadius: "12px",
                        border: "none",
                        boxShadow: "0 10px 15px -3px rgb(0 0 0 / 0.1)",
                        fontSize: "12px",
                      }}
                      labelFormatter={(label) => `Ngày ${label}`}
                      formatter={(value) => [formatCurrency(Number(value)), "Doanh thu"] as [string, string]}
                    />
                    <Area
                      type="monotone"
                      dataKey="revenue"
                      stroke="#0ea5e9"
                      strokeWidth={2}
                      fill="url(#dashRevenue)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Channel breakdown */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col">
            <h2 className="text-sm font-semibold text-slate-900">Cơ cấu doanh thu theo kênh</h2>
            <p className="text-xs text-slate-400 mt-0.5">{trendDays} ngày gần nhất</p>
            <div className="flex-1 flex flex-col justify-center gap-4 mt-4">
              {ordersLoading ? (
                <div className="flex items-center justify-center py-8 text-slate-300">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : !channels || channels.total === 0 ? (
                <p className="text-sm text-slate-400 text-center py-8">
                  Chưa có doanh thu trong kỳ
                </p>
              ) : (
                <>
                  {(
                    [
                      { label: "Bán lẻ", value: channels.retail, color: "bg-blue-500", text: "text-blue-600" },
                      { label: "Bán sỉ", value: channels.wholesale, color: "bg-emerald-500", text: "text-emerald-600" },
                    ] as const
                  ).map((ch) => {
                    const pct = channels.total > 0 ? (ch.value / channels.total) * 100 : 0
                    return (
                      <div key={ch.label}>
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-xs font-medium text-slate-600">{ch.label}</span>
                          <span className={`text-xs font-bold ${ch.text}`}>{pct.toFixed(0)}%</span>
                        </div>
                        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${ch.color} rounded-full transition-all`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <p className="text-xs text-slate-500 mt-1 tabular-nums">
                          {formatCurrency(ch.value)}
                        </p>
                      </div>
                    )
                  })}
                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-500">Tổng cộng</span>
                    <span className="text-sm font-black text-slate-900 tabular-nums">
                      {formatCurrency(channels.total)}
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Lists: Recent orders + Pending approvals */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Orders */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <h2 className="text-sm font-semibold text-slate-900">Đơn hàng gần đây</h2>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-slate-400 h-7 px-2 hover:text-slate-700"
              onClick={() => navigate("/orders/wholesale")}
            >
              Xem tất cả <ArrowRight className="h-3 w-3 ml-1" />
            </Button>
          </div>
          <div className="divide-y divide-slate-50">
            {ordersLoading ? (
              <div className="flex items-center justify-center py-10 text-slate-300">
                <Loader2 className="h-5 w-5 animate-spin" />
              </div>
            ) : recentOrders.length === 0 ? (
              <p className="text-sm text-slate-400 text-center py-10">Chưa có đơn hàng nào</p>
            ) : (
              recentOrders.map((order) => (
                <div
                  key={order.id}
                  className="flex items-center justify-between px-4 py-3 hover:bg-slate-50/60 transition-colors"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-sm font-mono font-semibold text-slate-900">
                        {order.orderCode}
                      </span>
                      <span className="text-[10px] text-slate-400 border border-slate-200 rounded px-1 shrink-0">
                        {channelLabel(order.orderChannel)}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5 truncate">{order.customerName}</p>
                  </div>
                  <div className="text-right shrink-0 ml-3">
                    <p className="text-sm font-semibold text-slate-900 tabular-nums">
                      {formatCurrency(Number(order.finalAmount))}
                    </p>
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${statusColor(order.status)}`}
                    >
                      {statusLabel(order.status)}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Pending Approvals */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold text-slate-900">Cần phê duyệt</h2>
              {(approvalData?.summary.totalPending ?? 0) > 0 && (
                <Badge className="h-4 text-[10px] bg-red-500 text-white border-none px-1.5 font-bold">
                  {approvalData!.summary.totalPending}
                </Badge>
              )}
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-slate-400 h-7 px-2 hover:text-slate-700"
              onClick={() => navigate("/approvals/pending")}
            >
              Xem tất cả <ArrowRight className="h-3 w-3 ml-1" />
            </Button>
          </div>
          <div className="divide-y divide-slate-50">
            {dashboardLoading ? (
              <div className="flex items-center justify-center py-10 text-slate-300">
                <Loader2 className="h-5 w-5 animate-spin" />
              </div>
            ) : (approvalData?.items.length ?? 0) === 0 ? (
              <p className="text-sm text-slate-400 text-center py-10">Không có mục nào cần duyệt</p>
            ) : (
              approvalData!.items.map((item) => (
                <div
                  key={`${item.entityType}-${item.entityId}`}
                  className="flex items-center justify-between px-4 py-3 hover:bg-slate-50/60 transition-colors"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-sm font-mono font-semibold text-slate-900">
                        {item.transactionCode}
                      </span>
                      <span className="text-[10px] text-slate-400 border border-slate-200 rounded px-1 shrink-0">
                        {item.type}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">{item.creatorName}</p>
                  </div>
                  <div className="text-right shrink-0 ml-3">
                    <p className="text-sm font-semibold text-slate-900 tabular-nums">
                      {formatCurrency(Number(item.totalAmount))}
                    </p>
                    <p className="text-[10px] text-slate-400">
                      {new Date(item.date).toLocaleDateString("vi-VN")}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Top khách hàng + Dòng tiền tháng này */}
      <div className={`grid grid-cols-1 gap-6 ${canSeeFinancials ? "lg:grid-cols-2" : ""}`}>
        {/* Top khách hàng */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-slate-400" />
              <h2 className="text-sm font-semibold text-slate-900">Khách hàng hàng đầu</h2>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-slate-400 h-7 px-2 hover:text-slate-700"
              onClick={() => navigate("/products/customers")}
            >
              Xem tất cả <ArrowRight className="h-3 w-3 ml-1" />
            </Button>
          </div>
          <div className="divide-y divide-slate-50">
            {dashboardLoading ? (
              <div className="flex items-center justify-center py-10 text-slate-300">
                <Loader2 className="h-5 w-5 animate-spin" />
              </div>
            ) : topCustomers.length === 0 ? (
              <p className="text-sm text-slate-400 text-center py-10">Chưa có dữ liệu khách hàng</p>
            ) : (
              topCustomers.map((c, idx) => (
                <div
                  key={c.id}
                  className="flex items-center justify-between px-4 py-3 hover:bg-slate-50/60 transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0">
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
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-900 truncate">{c.name}</p>
                      <p className="text-xs text-slate-400">{c.orderCount} đơn hàng</p>
                    </div>
                  </div>
                  <p className="text-sm font-bold text-slate-900 tabular-nums shrink-0 ml-3">
                    {formatCurrency(c.totalSpent)}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Dòng tiền tháng này — chỉ role tài chính */}
        {canSeeFinancials && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Wallet className="h-4 w-4 text-slate-400" />
                <h2 className="text-sm font-semibold text-slate-900">Dòng tiền tháng này</h2>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-slate-400 h-7 px-2 hover:text-slate-700"
                onClick={() => navigate("/cashflow/transactions")}
              >
                Chi tiết <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            </div>
            <div className="flex-1 grid grid-cols-2 gap-3 mt-4">
              {/* Thu */}
              <div className="rounded-lg bg-emerald-50 p-4">
                <div className="flex items-center gap-1.5 text-emerald-600">
                  <ArrowDownLeft className="h-4 w-4" />
                  <span className="text-[10px] font-bold uppercase tracking-wider">Tổng thu</span>
                </div>
                <p className="text-lg font-black text-emerald-700 mt-2 tabular-nums truncate">
                  {dashboardLoading ? "…" : formatCurrency(cashflow?.income ?? 0)}
                </p>
              </div>
              {/* Chi */}
              <div className="rounded-lg bg-red-50 p-4">
                <div className="flex items-center gap-1.5 text-red-600">
                  <ArrowUpLeft className="h-4 w-4" />
                  <span className="text-[10px] font-bold uppercase tracking-wider">Tổng chi</span>
                </div>
                <p className="text-lg font-black text-red-700 mt-2 tabular-nums truncate">
                  {dashboardLoading ? "…" : formatCurrency(cashflow?.expense ?? 0)}
                </p>
              </div>
            </div>
            {/* Số dư ròng */}
            <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500">Số dư ròng</span>
              <span
                className={`text-base font-black tabular-nums ${
                  (cashflow?.net ?? 0) >= 0 ? "text-emerald-600" : "text-red-600"
                }`}
              >
                {dashboardLoading
                  ? "…"
                  : `${(cashflow?.net ?? 0) >= 0 ? "+" : ""}${formatCurrency(cashflow?.net ?? 0)}`}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Low Stock Alert */}
      {((lowStockData?.items.length ?? 0) > 0 || dashboardLoading) && (
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
              Xem tất cả <ArrowRight className="h-3 w-3 ml-1" />
            </Button>
          </div>
          {dashboardLoading ? (
            <div className="flex items-center justify-center py-6 text-slate-300">
              <Loader2 className="h-5 w-5 animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
              {lowStockData?.items.map((item, idx) => (
                <div
                  key={item.id}
                  onClick={() => navigate("/inventory/stock")}
                  className={`px-4 py-3 cursor-pointer hover:bg-amber-50/40 transition-colors ${
                    idx < (lowStockData?.items.length ?? 0) - 1
                      ? "border-b xl:border-b-0 xl:border-r border-amber-100"
                      : ""
                  }`}
                >
                  <p className="text-sm font-semibold text-slate-900 line-clamp-1">
                    {item.productName}
                  </p>
                  <p className="text-[10px] text-slate-400 font-mono mt-0.5">{item.skuCode}</p>
                  <div className="flex items-baseline gap-1 mt-1.5">
                    <span className="text-xl font-black text-amber-600 tabular-nums">
                      {item.quantity}
                    </span>
                    <span className="text-xs text-slate-400">
                      / {item.minQuantity} {item.unitName}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Quick Shortcuts */}
      <div>
        <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-3">
          Truy cập nhanh
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {shortcuts.map((s) => (
            <button
              key={s.to}
              onClick={() => navigate(s.to)}
              className="flex items-center gap-3 bg-white border border-slate-200 rounded-xl p-4 hover:shadow-md hover:border-slate-300 transition-all text-left group"
            >
              <div
                className={`h-9 w-9 rounded-lg ${s.color} flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform`}
              >
                <s.icon className="h-5 w-5 text-white" />
              </div>
              <span className="text-sm font-semibold text-slate-700 group-hover:text-slate-900">
                {s.label}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
