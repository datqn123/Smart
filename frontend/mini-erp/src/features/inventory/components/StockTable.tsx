import { Checkbox } from "@/components/ui/checkbox"
import React from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Eye, Package } from "lucide-react"
import type { InventoryItem } from "../types"
import { getInventoryRowStatusDisplay } from "../lib/inventoryRowStatus"
import { cn } from "@/lib/utils"
import {
  DATA_TABLE_ROOT_CLASS,
  DATA_TABLE_ACTION_SINGLE_HEAD_CLASS,
  DATA_TABLE_ACTION_SINGLE_CELL_CLASS,
  DATA_TABLE_CHECKBOX_CLASS,
  STOCK_TABLE_COL,
  TABLE_HEAD_CLASS,
  TABLE_CELL_PRIMARY_CLASS,
  TABLE_CELL_SECONDARY_CLASS,
  TABLE_CELL_MONO_CLASS,
  TABLE_CELL_NUMBER_CLASS,
} from "@/lib/data-table-layout"

interface StockTableProps {
  data: InventoryItem[]
  visibleColumnKeys: string[]
  selectedIds: number[]
  onSelect: (id: number) => void
  onViewDetails: (item: InventoryItem) => void
  allSelected: boolean
  someSelected: boolean
  onSelectAll: (checked: boolean) => void
}

export function StockTable({
  data,
  visibleColumnKeys,
  selectedIds,
  onSelect,
  onViewDetails,
  allSelected,
  someSelected,
  onSelectAll,
}: StockTableProps) {
  const columnRenderers = {
    skuCode: {
      head: <TableHead className={cn(STOCK_TABLE_COL.skuCode, TABLE_HEAD_CLASS, "px-4 text-left")}>Mã SP</TableHead>,
      cell: (item: InventoryItem) => <TableCell className={cn(STOCK_TABLE_COL.skuCode, TABLE_CELL_MONO_CLASS, "px-4 text-left")}>{item.skuCode}</TableCell>,
    },
    productName: {
      head: <TableHead className={cn(STOCK_TABLE_COL.productName, TABLE_HEAD_CLASS, "px-4 text-left")}>Tên sản phẩm</TableHead>,
      cell: (item: InventoryItem) => <TableCell className={cn(STOCK_TABLE_COL.productName, TABLE_CELL_PRIMARY_CLASS, "px-4 text-left truncate min-w-0")}>{item.productName}</TableCell>,
    },
    location: {
      head: <TableHead className={cn(STOCK_TABLE_COL.location, TABLE_HEAD_CLASS, "px-4 text-left")}>Vị trí</TableHead>,
      cell: (item: InventoryItem) => (
        <TableCell className={cn(STOCK_TABLE_COL.location, TABLE_CELL_SECONDARY_CLASS, "px-4 text-left")}>
          <Badge variant="outline" className="text-xs font-normal border-slate-200 h-6">
            {item.warehouseCode}-{item.shelfCode}
          </Badge>
        </TableCell>
      ),
    },
    quantity: {
      head: <TableHead className={cn(STOCK_TABLE_COL.quantity, TABLE_HEAD_CLASS, "px-4 text-left")}>Tồn kho</TableHead>,
      cell: (item: InventoryItem) => (
        <TableCell className={cn(STOCK_TABLE_COL.quantity, TABLE_CELL_NUMBER_CLASS, "px-4 text-left min-w-0")}>
          <div className="flex w-full min-w-0 justify-start">
            <div className="inline-grid max-w-full grid-cols-[0.875rem_minmax(1.25rem,1fr)_2.75rem] items-center gap-x-1.5 text-sm">
              <span className="flex w-3.5 shrink-0 justify-start" aria-hidden>
                <Package className="h-3 w-3 text-slate-400" />
              </span>
              <span className="tabular-nums text-left font-medium text-slate-900">{item.quantity}</span>
              <span className="truncate text-left text-xs font-normal text-slate-500" title={item.unitName}>
                {item.unitName}
              </span>
            </div>
          </div>
        </TableCell>
      ),
    },
    expiryDate: {
      head: <TableHead className={cn(STOCK_TABLE_COL.expiryDate, TABLE_HEAD_CLASS, "px-4 text-left")}>Hạn SD</TableHead>,
      cell: (item: InventoryItem) => (
        <TableCell className={cn(STOCK_TABLE_COL.expiryDate, TABLE_CELL_SECONDARY_CLASS, "px-4 text-left")}>
          {item.expiryDate ? new Date(item.expiryDate).toLocaleDateString("vi-VN") : "—"}
        </TableCell>
      ),
    },
    status: {
      head: <TableHead className={cn(STOCK_TABLE_COL.status, TABLE_HEAD_CLASS, "px-4 text-left")}>Trạng thái</TableHead>,
      cell: (item: InventoryItem) => {
        const status = getInventoryRowStatusDisplay(item)
        return (
          <TableCell className={cn(STOCK_TABLE_COL.status, "px-4 text-left")}>
            <Badge variant="secondary" className={`${status.badgeClass} text-xs font-normal border-none`}>
              {status.label}
            </Badge>
          </TableCell>
        )
      },
    },
  } satisfies Record<string, { head: React.ReactNode; cell: (item: InventoryItem) => React.ReactNode }>
  const orderedColumns = visibleColumnKeys
    .map((key) => ({ key, renderer: columnRenderers[key as keyof typeof columnRenderers] }))
    .filter((entry): entry is { key: string; renderer: (typeof columnRenderers)[keyof typeof columnRenderers] } => entry.renderer != null)
  const emptyColSpan = orderedColumns.length + 2

  return (
    <Table data-testid="stock-table" className={DATA_TABLE_ROOT_CLASS}>
      <TableHeader className="sticky top-0 z-20 bg-slate-50 shadow-sm border-b">
        <TableRow className="hover:bg-transparent border-b border-slate-200">
          <TableHead className={cn(STOCK_TABLE_COL.select, TABLE_HEAD_CLASS, "px-4 text-left")}>
            <Checkbox
              checked={allSelected ? true : someSelected ? "indeterminate" : false}
              onCheckedChange={(checked) => onSelectAll(checked as boolean)}
              aria-label="Select all"
              className={DATA_TABLE_CHECKBOX_CLASS}
            />
          </TableHead>
          {orderedColumns.map((column) => <React.Fragment key={column.key}>{column.renderer.head}</React.Fragment>)}
          <TableHead className={cn(DATA_TABLE_ACTION_SINGLE_HEAD_CLASS, TABLE_HEAD_CLASS, "text-center")}>
            Thao tác
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody className="divide-y divide-slate-100 bg-white">
        {data.length === 0 ? (
          <TableRow>
            <TableCell colSpan={emptyColSpan} className="h-24 text-center text-slate-500 text-sm">
              Không tìm thấy sản phẩm nào.
            </TableCell>
          </TableRow>
        ) : (
          data.map((item) => {
            const isSelected = selectedIds.includes(item.id)
            return (
              <TableRow
                key={item.id}
                className={cn("group h-14 cursor-pointer", isSelected ? "bg-slate-50" : "hover:bg-slate-50/50")}
                onClick={() => onSelect(item.id)}
              >
                <TableCell className={cn(STOCK_TABLE_COL.select, "px-4 text-left")} onClick={(e) => e.stopPropagation()}>
                  <Checkbox
                    checked={isSelected}
                    onCheckedChange={() => onSelect(item.id)}
                    aria-label={`Select ${item.productName}`}
                    className={DATA_TABLE_CHECKBOX_CLASS}
                  />
                </TableCell>
                {orderedColumns.map((column) => <React.Fragment key={column.key}>{column.renderer.cell(item)}</React.Fragment>)}
                <TableCell className={cn(DATA_TABLE_ACTION_SINGLE_CELL_CLASS, "px-2 text-center")}>
                  <div className="flex items-center justify-center">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 shrink-0 text-slate-400 hover:text-slate-900 transition-colors"
                      onClick={(e) => {
                        e.stopPropagation()
                        onViewDetails(item)
                      }}
                      title="Xem chi tiết lô"
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            )
          })
        )}
      </TableBody>
    </Table>
  )
}
