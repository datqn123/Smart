/** Nhãn hiển thị — khớp giá trị DB / API Task063 */

const TRANSACTION_TYPE_LABELS: Record<string, string> = {
  SalesRevenue: "Doanh thu bán",
  PurchaseCost: "Giá vốn mua",
  OperatingExpense: "Chi phí vận hành",
  Refund: "Hoàn tiền",
}

const REFERENCE_TYPE_LABELS: Record<string, string> = {
  SalesOrder: "Đơn bán",
  CashTransaction: "Phiếu thu chi",
  StockReceipt: "Phiếu nhập kho",
  StockDispatch: "Phiếu xuất kho",
}

export function ledgerTransactionTypeLabel(raw: string | null | undefined): string {
  if (!raw) return "—"
  return TRANSACTION_TYPE_LABELS[raw] ?? raw
}

export function ledgerReferenceTypeLabel(raw: string | null | undefined): string {
  if (!raw) return "—"
  return REFERENCE_TYPE_LABELS[raw] ?? raw
}

export const LEDGER_TRANSACTION_TYPE_FILTER_OPTIONS = [
  { value: "all", label: "Tất cả loại NV" },
  { value: "SalesRevenue", label: TRANSACTION_TYPE_LABELS.SalesRevenue },
  { value: "PurchaseCost", label: TRANSACTION_TYPE_LABELS.PurchaseCost },
  { value: "OperatingExpense", label: TRANSACTION_TYPE_LABELS.OperatingExpense },
  { value: "Refund", label: TRANSACTION_TYPE_LABELS.Refund },
] as const

export const LEDGER_REFERENCE_TYPE_FILTER_OPTIONS = [
  { value: "all", label: "Tất cả nguồn" },
  { value: "SalesOrder", label: REFERENCE_TYPE_LABELS.SalesOrder },
  { value: "CashTransaction", label: REFERENCE_TYPE_LABELS.CashTransaction },
  { value: "StockReceipt", label: REFERENCE_TYPE_LABELS.StockReceipt },
  { value: "StockDispatch", label: REFERENCE_TYPE_LABELS.StockDispatch },
] as const
