import { Badge } from "@/components/ui/badge"

type StatusContext =
  | "finance"
  | "order"
  | "warehouse"
  | "audit"
  | "receipt"
  | "dispatch"
  | "inventory"

type StatusConfig = {
  label: string
  bg: string
  text: string
  border: string
  dot: string
}

const STATUS_CONFIG: Record<string, StatusConfig> = {
  Active: { label: "Hoạt động", bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  Inactive: { label: "Ngừng", bg: "bg-slate-100", text: "text-slate-500", border: "border-slate-200", dot: "bg-slate-400" },
  Draft: { label: "Nháp", bg: "bg-slate-100", text: "text-slate-600", border: "border-slate-300", dot: "bg-slate-400" },
  Pending: { label: "Chờ duyệt", bg: "bg-amber-100", text: "text-amber-700", border: "border-amber-200", dot: "bg-amber-400" },
  Approved: { label: "Đã duyệt", bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  Rejected: { label: "Từ chối", bg: "bg-rose-100", text: "text-rose-600", border: "border-rose-200", dot: "bg-rose-400" },
  WaitingDispatch: { label: "Chờ xuất kho", bg: "bg-amber-100", text: "text-amber-700", border: "border-amber-200", dot: "bg-amber-400" },
  Delivering: { label: "Đang xuất kho", bg: "bg-blue-50", text: "text-blue-600", border: "border-blue-200", dot: "bg-blue-400" },
  Delivered: { label: "Đã giao hàng", bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  Full: { label: "Đã xuất đủ", bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  Partial: { label: "Xuất một phần", bg: "bg-amber-100", text: "text-amber-700", border: "border-amber-200", dot: "bg-amber-400" },
  Cancelled: { label: "Đã hủy", bg: "bg-rose-100", text: "text-rose-600", border: "border-rose-200", dot: "bg-rose-400" },
  "In Progress": { label: "Đang kiểm", bg: "bg-blue-50", text: "text-blue-600", border: "border-blue-200", dot: "bg-blue-400" },
  "Pending Owner Approval": { label: "Chờ duyệt Owner", bg: "bg-amber-100", text: "text-amber-700", border: "border-amber-200", dot: "bg-amber-400" },
  Completed: { label: "Hoàn thành", bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  "Re-check": { label: "Kiểm lại", bg: "bg-orange-50", text: "text-orange-600", border: "border-orange-200", dot: "bg-orange-400" },
  "in-stock": { label: "Còn hàng", bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  "low-stock": { label: "Sắp hết", bg: "bg-amber-100", text: "text-amber-700", border: "border-amber-200", dot: "bg-amber-400" },
  "out-of-stock": { label: "Hết hàng", bg: "bg-rose-100", text: "text-rose-600", border: "border-rose-200", dot: "bg-rose-400" },
  "expiring-soon": { label: "Sắp hết hạn", bg: "bg-orange-50", text: "text-orange-600", border: "border-orange-200", dot: "bg-orange-400" },
  Processing: { label: "Đang xử lý", bg: "bg-indigo-50", text: "text-indigo-600", border: "border-indigo-200", dot: "bg-indigo-400" },
  Shipped: { label: "Đang giao", bg: "bg-blue-50", text: "text-blue-600", border: "border-blue-200", dot: "bg-blue-400" },
  Cleared: { label: "Đã tất toán", bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  Overdue: { label: "Quá hạn", bg: "bg-rose-100", text: "text-rose-600", border: "border-rose-200", dot: "bg-rose-400" },
  Active_debt: { label: "Còn nợ", bg: "bg-amber-100", text: "text-amber-700", border: "border-amber-200", dot: "bg-amber-400" },
}

export interface StatusBadgeProps {
  status: string
  context?: StatusContext
  type?: "receipt" | "dispatch" | "audit" | "inventory"
  shortageWarning?: boolean
}

export function StatusBadge({ status, context, type, shortageWarning }: StatusBadgeProps) {
  const resolvedContext = context ?? type
  let config = STATUS_CONFIG[status]

  if (status === "Pending") {
    const label =
      resolvedContext === "finance" || resolvedContext === "order"
        ? "Chờ xử lý"
        : resolvedContext === "audit"
          ? "Chờ duyệt"
          : "Chờ duyệt"
    config = { ...STATUS_CONFIG.Pending, label }
  }

  if (status === "Partial" && shortageWarning) {
    config = {
      label: "Thiếu hàng cần xử lý",
      bg: "bg-rose-100",
      text: "text-rose-600",
      border: "border-rose-200",
      dot: "bg-rose-400",
    }
  }

  if (!config) {
    config = {
      label: status,
      bg: "bg-slate-100",
      text: "text-slate-600",
      border: "border-slate-200",
      dot: "bg-slate-400",
    }
  }

  return (
    <Badge className={`${config.bg} ${config.text} ${config.border} border gap-1.5 text-xs font-semibold shadow-none`}>
      <span className={`inline-block h-1.5 w-1.5 shrink-0 rounded-full ${config.dot}`} />
      {config.label}
    </Badge>
  )
}
