import { describe, it, expect } from "vitest"
import { getInventoryRowStatusDisplay } from "./inventoryRowStatus"

describe("getInventoryRowStatusDisplay", () => {
  it("matches StockTable priority: Draft, zero qty, low, expiring, normal", () => {
    expect(getInventoryRowStatusDisplay({ status: "Draft", quantity: 0, isLowStock: true, isExpiringSoon: true }).label).toBe(
      "Nháp",
    )
    expect(getInventoryRowStatusDisplay({ status: "Active", quantity: 0, isLowStock: true, isExpiringSoon: true }).label).toBe(
      "Hết hàng",
    )
    expect(getInventoryRowStatusDisplay({ status: "Active", quantity: 5, isLowStock: true, isExpiringSoon: false }).label).toBe(
      "Sắp hết",
    )
    expect(getInventoryRowStatusDisplay({ status: "Active", quantity: 5, isLowStock: false, isExpiringSoon: true }).label).toBe(
      "Cận date",
    )
    expect(getInventoryRowStatusDisplay({ status: "Active", quantity: 5, isLowStock: false, isExpiringSoon: false }).label).toBe(
      "Bình thường",
    )
  })
})
