import { apiJson } from "@/lib/api/http"

export type DashboardFinancial = {
  todayRevenue: number
  yesterdayRevenue: number
  todayOrders: number
  pctChange: number | null
  avgOrderValue: number
}

export type DashboardRevenueTrendPoint = {
  date: string
  label: string
  revenue: number
  orders: number
}

export type DashboardChannelBreakdown = {
  retail: number
  wholesale: number
  total: number
}

export type DashboardKpis = {
  totalSkus: number
  totalValue: number
  lowStockCount: number
  expiringSoonCount: number
  pendingOrders: number
  allOrdersTotal: number
  pendingApprovals: number
  approvalByType: Record<string, number>
}

export type DashboardRecentOrder = {
  id: number
  orderCode: string
  orderChannel: string
  customerName: string
  finalAmount: number
  status: string
  createdAt: string
}

export type DashboardPendingApproval = {
  entityType: string
  entityId: number
  transactionCode: string
  type: string
  creatorName: string
  totalAmount: number
  date: string
}

export type DashboardTopCustomer = {
  id: number
  name: string
  orderCount: number
  totalSpent: number
}

export type DashboardCashflow = {
  income: number
  expense: number
  net: number
}

export type DashboardLowStockAlert = {
  id: number
  productName: string
  skuCode: string
  quantity: number
  minQuantity: number
  unitName: string
}

export type DashboardData = {
  financial: DashboardFinancial | null
  revenueTrend: DashboardRevenueTrendPoint[] | null
  channelBreakdown: DashboardChannelBreakdown | null
  kpis: DashboardKpis | null
  recentOrders: DashboardRecentOrder[] | null
  pendingApprovals: DashboardPendingApproval[] | null
  topCustomers: DashboardTopCustomer[] | null
  cashflow: DashboardCashflow | null
  lowStockAlerts: DashboardLowStockAlert[] | null
}

export type GetDashboardParams = {
  trendDays?: 7 | 30
  recentLimit?: number
  topCustomerLimit?: number
  alertLimit?: number
  include?: string
}

export function getDashboard(params: GetDashboardParams = {}) {
  const q = new URLSearchParams()
  if (params.trendDays) q.set("trendDays", String(params.trendDays))
  if (params.recentLimit != null) q.set("recentLimit", String(params.recentLimit))
  if (params.topCustomerLimit != null) q.set("topCustomerLimit", String(params.topCustomerLimit))
  if (params.alertLimit != null) q.set("alertLimit", String(params.alertLimit))
  if (params.include?.trim()) q.set("include", params.include.trim())
  const qs = q.toString()
  return apiJson<DashboardData>(qs ? `/api/v1/dashboard?${qs}` : "/api/v1/dashboard", {
    method: "GET",
    auth: true,
  })
}
