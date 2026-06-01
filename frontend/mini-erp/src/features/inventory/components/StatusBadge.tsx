import { Badge } from "@/components/ui/badge";

interface StatusBadgeProps {
  status: string;
  type?: "receipt" | "dispatch" | "audit" | "inventory";
  /** Phiếu xuất: Partial kèm cảnh báo thiếu tồn → nhãn riêng. */
  shortageWarning?: boolean;
}

const receiptConfig: Record<string, { label: string; bg: string; text: string }> = {
  Draft: { label: "Nháp", bg: "bg-slate-100", text: "text-slate-600" },
  Pending: { label: "Chờ duyệt", bg: "bg-amber-50", text: "text-amber-700" },
  Approved: { label: "Đã duyệt", bg: "bg-green-50", text: "text-green-700" },
  Rejected: { label: "Từ chối", bg: "bg-red-50", text: "text-red-700" },
};

const dispatchConfig: Record<string, { label: string; bg: string; text: string }> = {
  WaitingDispatch: { label: "Chờ xuất kho", bg: "bg-amber-50", text: "text-amber-700" },
  Delivering: { label: "Đang xuất kho", bg: "bg-slate-100", text: "text-slate-700" },
  Delivered: { label: "Đã giao hàng", bg: "bg-green-50", text: "text-green-800" },
  Pending: { label: "Chờ duyệt", bg: "bg-amber-50", text: "text-amber-700" },
  Full: { label: "Đã xuất đủ", bg: "bg-green-50", text: "text-green-700" },
  Partial: { label: "Xuất một phần", bg: "bg-amber-50", text: "text-amber-800" },
  Cancelled: { label: "Đã hủy", bg: "bg-red-50", text: "text-red-700" },
};

const auditConfig: Record<string, { label: string; bg: string; text: string }> = {
  Pending: { label: "Chờ kiểm", bg: "bg-amber-50", text: "text-amber-700" },
  "In Progress": { label: "Đang kiểm", bg: "bg-slate-100", text: "text-slate-700" },
  "Pending Owner Approval": { label: "Chờ duyệt Owner", bg: "bg-amber-100", text: "text-amber-800" },
  Completed: { label: "Hoàn thành", bg: "bg-green-50", text: "text-green-700" },
  Cancelled: { label: "Đã hủy", bg: "bg-slate-100", text: "text-slate-600" },
  "Re-check": { label: "Kiểm lại", bg: "bg-orange-50", text: "text-orange-700" },
};

const inventoryConfig: Record<string, { label: string; bg: string; text: string }> = {
  "in-stock": { label: "Còn hàng", bg: "bg-green-50", text: "text-green-700" },
  "low-stock": { label: "Sắp hết", bg: "bg-red-50", text: "text-red-700" },
  "out-of-stock": { label: "Hết hàng", bg: "bg-red-100", text: "text-red-800" },
  "expiring-soon": { label: "Sắp hết hạn", bg: "bg-amber-50", text: "text-amber-700" },
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
    config = { label: "Thiếu hàng cần xử lý", bg: "bg-red-50", text: "text-red-700" };
  }
  if (!config) {
    config = { label: status, bg: "bg-slate-100", text: "text-slate-600" };
  }

  return (
    <Badge className={`${config.bg} ${config.text} font-medium text-xs px-2.5 py-1`}>
      {config.label}
    </Badge>
  );
}
