import { Package, Eye, Edit2, Trash2 } from "lucide-react"
import React from "react"
import { formatCurrency, formatDate } from "../utils"
import type { StockReceipt } from "../types"
import { StatusBadge } from "./StatusBadge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import {
  DATA_TABLE_ROOT_CLASS,
  DATA_TABLE_ACTION_HEAD_CLASS,
  DATA_TABLE_ACTION_CELL_CLASS,
  RECEIPT_TABLE_COL,
  TABLE_HEAD_CLASS,
  TABLE_CELL_PRIMARY_CLASS,
  TABLE_CELL_SECONDARY_CLASS,
  TABLE_CELL_MONO_CLASS,
  TABLE_CELL_NUMBER_CLASS,
} from "@/lib/data-table-layout"

interface ReceiptTableProps {
  receipts: StockReceipt[]
  visibleColumnKeys: string[]
  onAction: (receipt: StockReceipt) => void
  onEdit?: (receipt: StockReceipt) => void
  onDelete?: (id: number) => void
  /** Nếu có — nút xóa luôn chiếm chỗ; `false` = ẩn + disabled (khớp quyền/trạng thái trên BE). */
  canDeleteReceipt?: (receipt: StockReceipt) => boolean
}

/**
 * Một bảng duy nhất (thead + tbody) — class cột lấy từ `@/lib/data-table-layout` (chuẩn dự án).
 */
export function ReceiptTable({ receipts, visibleColumnKeys, onAction, onEdit, onDelete, canDeleteReceipt }: ReceiptTableProps) {
  const columnRenderers = {
    receiptCode: {
      head: <TableHead className={cn(RECEIPT_TABLE_COL.receiptCode, TABLE_HEAD_CLASS)}>Mã phiếu</TableHead>,
      cell: (receipt: StockReceipt) => <TableCell className={cn(RECEIPT_TABLE_COL.receiptCode, TABLE_CELL_MONO_CLASS)}>{receipt.receiptCode}</TableCell>,
    },
    supplierName: {
      head: <TableHead className={cn(RECEIPT_TABLE_COL.supplierName, TABLE_HEAD_CLASS)}>Nhà cung cấp</TableHead>,
      cell: (receipt: StockReceipt) => <TableCell className={cn(RECEIPT_TABLE_COL.supplierName, TABLE_CELL_PRIMARY_CLASS, "truncate")}>{receipt.supplierName}</TableCell>,
    },
    receiptDate: {
      head: <TableHead className={cn(RECEIPT_TABLE_COL.receiptDate, TABLE_HEAD_CLASS)}>Ngày nhập</TableHead>,
      cell: (receipt: StockReceipt) => <TableCell className={cn(RECEIPT_TABLE_COL.receiptDate, TABLE_CELL_SECONDARY_CLASS)}>{formatDate(receipt.receiptDate)}</TableCell>,
    },
    staffName: {
      head: <TableHead className={cn(RECEIPT_TABLE_COL.staffName, TABLE_HEAD_CLASS)}>Người tạo</TableHead>,
      cell: (receipt: StockReceipt) => (
        <TableCell className={cn(RECEIPT_TABLE_COL.staffName, TABLE_CELL_SECONDARY_CLASS)}>
          <div className="flex items-center gap-2 min-w-0">
            <div className="h-6 w-6 shrink-0 rounded-full bg-slate-100 flex items-center justify-center text-[10px] font-bold text-slate-600 border border-slate-200 uppercase">
              {receipt.staffName.split(" ").map((n) => n[0]).join("")}
            </div>
            <span className="truncate">{receipt.staffName}</span>
          </div>
        </TableCell>
      ),
    },
    invoiceNumber: {
      head: <TableHead className={cn(RECEIPT_TABLE_COL.invoiceNumber, TABLE_HEAD_CLASS)}>Số hóa đơn</TableHead>,
      cell: (receipt: StockReceipt) => <TableCell className={cn(RECEIPT_TABLE_COL.invoiceNumber, TABLE_CELL_SECONDARY_CLASS, "italic text-xs")}>{receipt.invoiceNumber || "—"}</TableCell>,
    },
    lineCount: {
      head: <TableHead className={cn(RECEIPT_TABLE_COL.lineCount, "text-center", TABLE_HEAD_CLASS)}>Số dòng hàng</TableHead>,
      cell: (receipt: StockReceipt) => (
        <TableCell className={cn(RECEIPT_TABLE_COL.lineCount, "text-center")}>
          <div className="flex items-center justify-center gap-1 text-xs text-slate-500">
            <Package className="h-3 w-3 shrink-0" />
            {receipt.lineCount ?? receipt.details.length}
          </div>
        </TableCell>
      ),
    },
    totalAmount: {
      head: <TableHead className={cn(RECEIPT_TABLE_COL.totalAmount, "text-right", TABLE_HEAD_CLASS)}>Tổng tiền</TableHead>,
      cell: (receipt: StockReceipt) => <TableCell className={cn(RECEIPT_TABLE_COL.totalAmount, "text-right font-semibold text-emerald-600", TABLE_CELL_NUMBER_CLASS)}>{formatCurrency(receipt.totalAmount)}</TableCell>,
    },
    status: {
      head: <TableHead className={cn(RECEIPT_TABLE_COL.status, "text-center", TABLE_HEAD_CLASS)}>Trạng thái</TableHead>,
      cell: (receipt: StockReceipt) => <TableCell className={cn(RECEIPT_TABLE_COL.status, "text-center")}><StatusBadge status={receipt.status} /></TableCell>,
    },
  } satisfies Record<string, { head: React.ReactNode; cell: (receipt: StockReceipt) => React.ReactNode }>
  const orderedColumns = visibleColumnKeys
    .map((key) => ({ key, renderer: columnRenderers[key as keyof typeof columnRenderers] }))
    .filter((entry): entry is { key: string; renderer: (typeof columnRenderers)[keyof typeof columnRenderers] } => entry.renderer != null)
  const emptyColSpan = orderedColumns.length + 1
  return (
    <Table data-testid="receipt-table" className={DATA_TABLE_ROOT_CLASS}>
      <TableHeader className="sticky top-0 z-20 shadow-sm border-b">
        <TableRow className="hover:bg-transparent border-b border-slate-200">
          {orderedColumns.map((column) => <React.Fragment key={column.key}>{column.renderer.head}</React.Fragment>)}
          <TableHead className={cn(DATA_TABLE_ACTION_HEAD_CLASS, TABLE_HEAD_CLASS)}>Thao tác</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {receipts.length === 0 ? (
          <TableRow>
            <TableCell colSpan={emptyColSpan} className="h-24 text-center text-slate-500 text-sm">
              Không tìm thấy phiếu nhập kho nào.
            </TableCell>
          </TableRow>
        ) : receipts.map((receipt) => {
          const deleteAllowed = Boolean(onDelete && (canDeleteReceipt?.(receipt) ?? true))
          return (
          <TableRow
            key={receipt.id}
            className="group hover:bg-slate-50/60 transition-colors cursor-pointer h-14"
            onClick={() => onAction(receipt)}
          >
            {orderedColumns.map((column) => <React.Fragment key={column.key}>{column.renderer.cell(receipt)}</React.Fragment>)}
            <TableCell className={DATA_TABLE_ACTION_CELL_CLASS} onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-center gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-slate-500 hover:text-slate-900 transition-colors"
                  onClick={() => onAction(receipt)}
                  title="Xem chi tiết"
                  data-testid="view-detail-btn"
                >
                  <Eye className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-slate-500 hover:text-slate-900 transition-colors"
                  onClick={() => onEdit?.(receipt)}
                  title="Sửa phiếu"
                >
                  <Edit2 className="h-4 w-4" />
                </Button>
                {onDelete ? (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    data-testid="delete-receipt-btn"
                    className={cn(
                      "h-8 w-8 transition-colors",
                      deleteAllowed
                        ? "text-slate-500 hover:text-red-600"
                        : "text-slate-300 cursor-not-allowed",
                    )}
                    onClick={() => {
                      if (deleteAllowed) {
                        onDelete(receipt.id)
                      }
                    }}
                    disabled={!deleteAllowed}
                    title={
                      deleteAllowed
                        ? "Xóa phiếu"
                        : "Không thể xóa ở trạng thái hiện tại hoặc không đủ quyền"
                    }
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                ) : null}
              </div>
            </TableCell>
          </TableRow>
          )
        })}
      </TableBody>
    </Table>
  )
}
