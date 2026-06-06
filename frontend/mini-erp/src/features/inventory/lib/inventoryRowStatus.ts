import type { InventoryItem } from "../types"

export type InventoryRowStatusDisplay = {
  label: string
  badgeClass: string
  dotClass: string
}

/** Khớp cột Trạng thái trên `StockTable` — dùng cho dialog chi tiết và chỗ khác cần đồng bộ. */
export function getInventoryRowStatusDisplay(
  item: Pick<InventoryItem, "status" | "quantity" | "isLowStock" | "isExpiringSoon">,
): InventoryRowStatusDisplay {
  if (item.status === "Draft") {
    return { label: "Nháp",      badgeClass: "bg-slate-100 text-slate-600 border border-slate-300",   dotClass: "bg-slate-400" }
  }
  if (item.quantity === 0) {
    return { label: "Hết hàng",  badgeClass: "bg-rose-100 text-rose-600 border border-rose-200",       dotClass: "bg-rose-400" }
  }
  if (item.isLowStock) {
    return { label: "Sắp hết",   badgeClass: "bg-amber-100 text-amber-700 border border-amber-200",   dotClass: "bg-amber-400" }
  }
  if (item.isExpiringSoon) {
    return { label: "Cận date",  badgeClass: "bg-orange-50 text-orange-600 border border-orange-200", dotClass: "bg-orange-400" }
  }
  return { label: "Bình thường", badgeClass: "bg-emerald-100 text-emerald-700 border border-emerald-200", dotClass: "bg-emerald-500" }
}
