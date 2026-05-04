import { render, screen } from "@testing-library/react"
import { describe, it, expect } from "vitest"
import { StockBatchDetailsDialog } from "../StockBatchDetailsDialog"
import type { InventoryItem } from "../../../types"
import type { InventoryDetailResponse } from "../../api/inventoryApi"

const mockItem: InventoryItem = {
  id: 1,
  productId: 1,
  productName: "Sữa Ông Thọ Hộp Giấy",
  skuCode: "SP001",
  locationId: 1,
  warehouseCode: "WH01",
  shelfCode: "A1",
  quantity: 150,
  minQuantity: 50,
  unitName: "Hộp",
  costPrice: 25000,
  updatedAt: "2026-04-12T10:30:00Z",
  isLowStock: false,
  isExpiringSoon: false,
  totalValue: 3750000,
}

const mockDetail: InventoryDetailResponse = {
  id: 1,
  productId: 1,
  productName: "Sữa Ông Thọ Hộp Giấy",
  skuCode: "SP001",
  barcode: "8930001",
  locationId: 1,
  warehouseCode: "WH01",
  shelfCode: "A1",
  batchNumber: "LOT-1",
  expiryDate: "2027-06-01",
  quantity: 150,
  minQuantity: 50,
  unitId: 1,
  unitName: "Hộp",
  costPrice: 25000,
  updatedAt: "2026-04-12T10:30:00Z",
  isLowStock: false,
  isExpiringSoon: false,
  totalValue: 3750000,
  relatedLines: [],
}

describe("StockBatchDetailsDialog", () => {
  it("renders header from list while detail loads", () => {
    render(
      <StockBatchDetailsDialog
        isOpen
        onClose={() => {}}
        listItem={mockItem}
        detail={null}
        isDetailPending
        isDetailError={false}
      />,
    )
    expect(screen.getByText("Sữa Ông Thọ Hộp Giấy")).toBeInTheDocument()
    expect(screen.getByText(/Đang tải chi tiết/)).toBeInTheDocument()
  })

  it("renders detail + financial when API data ready", () => {
    render(
      <StockBatchDetailsDialog
        isOpen
        onClose={() => {}}
        listItem={mockItem}
        detail={mockDetail}
        isDetailPending={false}
        isDetailError={false}
      />,
    )
    expect(screen.getByText("Sữa Ông Thọ Hộp Giấy")).toBeInTheDocument()
    const skuElements = screen.getAllByText(/SP001/)
    expect(skuElements.length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText(/8930001/)).toBeInTheDocument()
    expect(screen.getByText(/25\.000/)).toBeInTheDocument()
    expect(screen.getByText(/3\.750\.000/)).toBeInTheDocument()
    expect(screen.getByText("Bình thường")).toBeInTheDocument()
    expect(screen.getByText(/Định mức: 50/)).toBeInTheDocument()
    expect(screen.getByText("LOT-1")).toBeInTheDocument()
  })

  it("returns null when listItem is null", () => {
    const { container } = render(
      <StockBatchDetailsDialog
        isOpen
        onClose={() => {}}
        listItem={null}
        detail={null}
        isDetailPending={false}
        isDetailError={false}
      />,
    )
    expect(container.firstChild).toBeNull()
  })
})
