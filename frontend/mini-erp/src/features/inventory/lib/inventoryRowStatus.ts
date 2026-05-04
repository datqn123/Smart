import type { InventoryItem } from "../types"

export type InventoryRowStatusDisplay = {
  label: string
  badgeClass: string
}

/** Khớp cột Trạng thái trên `StockTable` — dùng cho dialog chi tiết và chỗ khác cần đồng bộ. */
export function getInventoryRowStatusDisplay(
  item: Pick<InventoryItem, "status" | "quantity" | "isLowStock" | "isExpiringSoon">,
): InventoryRowStatusDisplay {
  if (item.status === "Draft") {
    return { label: "Nháp", badgeClass: "bg-slate-100 text-slate-700" }
  }
  if (item.quantity === 0) {
    return { label: "Hết hàng", badgeClass: "bg-red-100 text-red-800" }
  }
  if (item.isLowStock) {
    return { label: "Sắp hết", badgeClass: "bg-red-50 text-red-700 hover:bg-red-100" }
  }
  if (item.isExpiringSoon) {
    return { label: "Cận date", badgeClass: "bg-amber-50 text-amber-700 hover:bg-amber-100" }
  }
  return { label: "Bình thường", badgeClass: "bg-green-50 text-green-700 hover:bg-green-100" }
}
