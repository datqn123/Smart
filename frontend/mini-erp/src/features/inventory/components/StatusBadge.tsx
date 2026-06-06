import { Badge } from "@/components/ui/badge";

interface StatusBadgeProps {
  status: string;
  type?: "receipt" | "dispatch" | "audit" | "inventory";
  /** Phiếu xuất: Partial kèm cảnh báo thiếu tồn → nhãn riêng. */
  shortageWarning?: boolean;
}

const receiptConfig: Record<string, { label: string; bg: string; text: string; border: string; dot: string }> = {
  Draft:    { label: "Nháp",      bg: "bg-slate-100",   text: "text-slate-600",   border: "border-slate-300",   dot: "bg-slate-400" },
  Pending:  { label: "Chờ duyệt", bg: "bg-amber-100",   text: "text-amber-700",   border: "border-amber-200",   dot: "bg-amber-400" },
  Approved: { label: "Đã duyệt",  bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  Rejected: { label: "Từ chối",   bg: "bg-rose-100",    text: "text-rose-600",    border: "border-rose-200",    dot: "bg-rose-400" },
};

const dispatchConfig: Record<string, { label: string; bg: string; text: string; border: string; dot: string }> = {
  WaitingDispatch: { label: "Chờ xuất kho",  bg: "bg-amber-100",   text: "text-amber-700",   border: "border-amber-200",   dot: "bg-amber-400" },
  Delivering:      { label: "Đang xuất kho", bg: "bg-blue-50",     text: "text-blue-600",    border: "border-blue-200",    dot: "bg-blue-400" },
  Delivered:       { label: "Đã giao hàng",  bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  Pending:         { label: "Chờ duyệt",     bg: "bg-amber-100",   text: "text-amber-700",   border: "border-amber-200",   dot: "bg-amber-400" },
  Full:            { label: "Đã xuất đủ",    bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  Partial:         { label: "Xuất một phần", bg: "bg-amber-100",   text: "text-amber-700",   border: "border-amber-200",   dot: "bg-amber-400" },
  Cancelled:       { label: "Đã hủy",        bg: "bg-rose-100",    text: "text-rose-600",    border: "border-rose-200",    dot: "bg-rose-400" },
};

const auditConfig: Record<string, { label: string; bg: string; text: string; border: string; dot: string }> = {
  Pending:                  { label: "Chờ kiểm",         bg: "bg-amber-100",   text: "text-amber-700",   border: "border-amber-200",   dot: "bg-amber-400" },
  "In Progress":            { label: "Đang kiểm",        bg: "bg-blue-50",     text: "text-blue-600",    border: "border-blue-200",    dot: "bg-blue-400" },
  "Pending Owner Approval": { label: "Chờ duyệt Owner",  bg: "bg-amber-100",   text: "text-amber-700",   border: "border-amber-200",   dot: "bg-amber-400" },
  Completed:                { label: "Hoàn thành",       bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  Cancelled:                { label: "Đã hủy",           bg: "bg-rose-100",    text: "text-rose-600",    border: "border-rose-200",    dot: "bg-rose-400" },
  "Re-check":               { label: "Kiểm lại",         bg: "bg-orange-50",   text: "text-orange-600",  border: "border-orange-200",  dot: "bg-orange-400" },
};

const inventoryConfig: Record<string, { label: string; bg: string; text: string; border: string; dot: string }> = {
  "in-stock":      { label: "Còn hàng",   bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  "low-stock":     { label: "Sắp hết",    bg: "bg-amber-100",   text: "text-amber-700",   border: "border-amber-200",   dot: "bg-amber-400" },
  "out-of-stock":  { label: "Hết hàng",   bg: "bg-rose-100",    text: "text-rose-600",    border: "border-rose-200",    dot: "bg-rose-400" },
  "expiring-soon": { label: "Sắp hết hạn",bg: "bg-orange-50",   text: "text-orange-600",  border: "border-orange-200",  dot: "bg-orange-400" },
};

export function StatusBadge({ status, type = "receipt", shortageWarning }: StatusBadgeProps) {
  const configMap = {
    receipt: receiptConfig,
    dispatch: dispatchConfig,
    audit: auditConfig,
    inventory: inventoryConfig,
  };

  let config = configMap[type][status];
  if (type === "dispatch" && status === "Partial" && shortageWarning) {
    config = { label: "Thiếu hàng cần xử lý", bg: "bg-rose-100", text: "text-rose-600", border: "border-rose-200", dot: "bg-rose-400" };
  }
  if (!config) {
    config = { label: status, bg: "bg-slate-100", text: "text-slate-600", border: "border-slate-200", dot: "bg-slate-400" };
  }

  return (
    <Badge className={`${config.bg} ${config.text} ${config.border} font-semibold text-xs border shadow-none gap-1.5`}>
      <span className={`w-1.5 h-1.5 rounded-full inline-block shrink-0 ${config.dot}`} />
      {config.label}
    </Badge>
  );
}
