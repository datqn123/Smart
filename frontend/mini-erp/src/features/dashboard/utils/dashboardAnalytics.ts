import type { SalesOrderListItemDto } from "@/features/orders/api/salesOrdersApi"
import type { CashTransaction } from "@/features/cashflow/types"
import type { CustomerListItemDto } from "@/features/product-management/api/customersApi"

/** Một điểm dữ liệu doanh thu theo ngày trên biểu đồ. */
export type DailyRevenuePoint = {
  /** ISO date `yyyy-mm-dd` — khoá sắp xếp. */
  date: string
  /** Nhãn hiển thị `dd/mm`. */
  label: string
  revenue: number
  orders: number
}

/** So sánh doanh thu hôm nay với hôm qua. */
export type RevenueComparison = {
  todayRevenue: number
  yesterdayRevenue: number
  todayOrders: number
  /** % thay đổi so với hôm qua; null khi hôm qua = 0 (không chia được). */
  pctChange: number | null
  /** Giá trị trung bình mỗi đơn hôm nay. */
  avgOrderValue: number
}

/** Cơ cấu doanh thu theo kênh bán trong khoảng đang xét. */
export type ChannelBreakdown = {
  retail: number
  wholesale: number
  total: number
}

const CANCELLED = "Cancelled"

function num(v: number | string): number {
  const n = typeof v === "number" ? v : Number(v)
  return Number.isFinite(n) ? n : 0
}

/** `yyyy-mm-dd` theo local time (không lệch timezone như toISOString). */
function localDateKey(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, "0")
  const day = String(d.getDate()).padStart(2, "0")
  return `${y}-${m}-${day}`
}

function labelFromKey(key: string): string {
  const [, m, d] = key.split("-")
  return `${d}/${m}`
}

/**
 * Gộp danh sách đơn thành chuỗi doanh thu theo ngày cho `days` ngày gần nhất
 * (bao gồm hôm nay). Đơn `Cancelled` bị loại khỏi doanh thu.
 */
export function aggregateDailyRevenue(
  items: SalesOrderListItemDto[],
  days: number,
): DailyRevenuePoint[] {
  const buckets = new Map<string, { revenue: number; orders: number }>()

  // Khởi tạo đủ `days` ngày để biểu đồ không bị khuyết cột.
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(today.getDate() - i)
    buckets.set(localDateKey(d), { revenue: 0, orders: 0 })
  }

  for (const it of items) {
    if (it.status === CANCELLED) continue
    const key = localDateKey(new Date(it.createdAt))
    const bucket = buckets.get(key)
    if (!bucket) continue // ngoài cửa sổ thời gian
    bucket.revenue += num(it.finalAmount)
    bucket.orders += 1
  }

  return Array.from(buckets.entries()).map(([date, v]) => ({
    date,
    label: labelFromKey(date),
    revenue: v.revenue,
    orders: v.orders,
  }))
}

/** Doanh thu hôm nay vs hôm qua + giá trị đơn trung bình hôm nay. */
export function revenueComparison(items: SalesOrderListItemDto[]): RevenueComparison {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const todayKey = localDateKey(today)
  const yesterday = new Date(today)
  yesterday.setDate(today.getDate() - 1)
  const yesterdayKey = localDateKey(yesterday)

  let todayRevenue = 0
  let yesterdayRevenue = 0
  let todayOrders = 0

  for (const it of items) {
    if (it.status === CANCELLED) continue
    const key = localDateKey(new Date(it.createdAt))
    if (key === todayKey) {
      todayRevenue += num(it.finalAmount)
      todayOrders += 1
    } else if (key === yesterdayKey) {
      yesterdayRevenue += num(it.finalAmount)
    }
  }

  const pctChange =
    yesterdayRevenue > 0 ? ((todayRevenue - yesterdayRevenue) / yesterdayRevenue) * 100 : null
  const avgOrderValue = todayOrders > 0 ? todayRevenue / todayOrders : 0

  return { todayRevenue, yesterdayRevenue, todayOrders, pctChange, avgOrderValue }
}

/**
 * Cơ cấu doanh thu theo kênh trong `days` ngày gần nhất (mặc định toàn bộ tập).
 * "Return" được xem là âm doanh thu nên bỏ qua khỏi cơ cấu bán ra.
 */
export function channelBreakdown(
  items: SalesOrderListItemDto[],
  days?: number,
): ChannelBreakdown {
  let cutoff = -Infinity
  if (days != null) {
    const d = new Date()
    d.setHours(0, 0, 0, 0)
    d.setDate(d.getDate() - (days - 1))
    cutoff = d.getTime()
  }

  let retail = 0
  let wholesale = 0
  for (const it of items) {
    if (it.status === CANCELLED) continue
    if (days != null && new Date(it.createdAt).getTime() < cutoff) continue
    const amount = num(it.finalAmount)
    if (it.orderChannel === "Retail") retail += amount
    else if (it.orderChannel === "Wholesale") wholesale += amount
  }

  return { retail, wholesale, total: retail + wholesale }
}

/** Tổng thu / chi / số dư ròng từ các giao dịch tiền mặt (đã loại Cancelled). */
export type CashflowSummary = {
  income: number
  expense: number
  net: number
}

export function summarizeCashflow(items: CashTransaction[]): CashflowSummary {
  let income = 0
  let expense = 0
  for (const it of items) {
    if (it.status === "Cancelled") continue
    if (it.direction === "Income") income += num(it.amount)
    else if (it.direction === "Expense") expense += num(it.amount)
  }
  return { income, expense, net: income - expense }
}

/** Một dòng "Top khách hàng" theo tổng chi tiêu. */
export type TopCustomer = {
  id: number
  name: string
  orderCount: number
  totalSpent: number
}

/** Sắp xếp khách hàng theo `totalSpent` giảm dần, lấy `limit` đầu (mặc định 5). */
export function topCustomersBySpend(items: CustomerListItemDto[], limit = 5): TopCustomer[] {
  return items
    .map((c) => ({
      id: c.id,
      name: c.name,
      orderCount: typeof c.orderCount === "number" ? c.orderCount : Number(c.orderCount) || 0,
      totalSpent: num(c.totalSpent),
    }))
    .filter((c) => c.totalSpent > 0)
    .sort((a, b) => b.totalSpent - a.totalSpent)
    .slice(0, limit)
}

/** Khoảng thời gian từ đầu tháng hiện tại đến hôm nay (ISO `yyyy-mm-dd`). */
export function monthToDateRange(): { dateFrom: string; dateTo: string } {
  const now = new Date()
  const first = new Date(now.getFullYear(), now.getMonth(), 1)
  const key = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`
  return { dateFrom: key(first), dateTo: key(now) }
}
