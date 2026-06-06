import React from "react"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Eye, Edit2, Trash2 } from "lucide-react"
import {
  DATA_TABLE_ROOT_CLASS,
  DATA_TABLE_ACTION_HEAD_CLASS,
  DATA_TABLE_ACTION_CELL_CLASS,
  SUPPLIER_TABLE_COL,
  TABLE_HEAD_CLASS,
  TABLE_CELL_PRIMARY_CLASS,
  TABLE_CELL_SECONDARY_CLASS,
  TABLE_CELL_MONO_CLASS,
  DATA_TABLE_CHECKBOX_CLASS,
} from "@/lib/data-table-layout"
import { cn } from "@/lib/utils"
import type { Supplier } from "../types"

interface SupplierTableProps {
  data: Supplier[]
  visibleColumnKeys?: string[]
  selectedIds: number[]
  onSelect: (id: number) => void
  onSelectAll: (checked: boolean) => void
  onView: (item: Supplier) => void
  onEdit: (item: Supplier) => void
  onDelete: (item: Supplier) => void
  canDelete?: boolean
}

const REQUIRED_COLUMNS = new Set(["supplierCode", "supplierName"])
const DEFAULT_COLUMNS = ["supplierCode", "supplierName", "contactName", "receiptCount", "status"]

export function SupplierTable({
  data,
  visibleColumnKeys = DEFAULT_COLUMNS,
  selectedIds,
  onSelect,
  onSelectAll,
  onView,
  onEdit,
  onDelete,
  canDelete = false,
}: SupplierTableProps) {
  const allSelected = data.length > 0 && selectedIds.length === data.length
  const someSelected = selectedIds.length > 0 && selectedIds.length < data.length

  const columnRenderers = {
    supplierCode: {
      head: <TableHead className={cn(SUPPLIER_TABLE_COL.code, TABLE_HEAD_CLASS, "px-4")}>Mã nhà cung cấp</TableHead>,
      cell: (item: Supplier) => <TableCell className={cn(SUPPLIER_TABLE_COL.code, TABLE_CELL_MONO_CLASS, "px-4")}>{item.supplierCode}</TableCell>,
    },
    supplierName: {
      head: <TableHead className={cn(SUPPLIER_TABLE_COL.name, TABLE_HEAD_CLASS, "px-4")}>Nhà cung cấp</TableHead>,
      cell: (item: Supplier) => <TableCell className={cn(SUPPLIER_TABLE_COL.name, TABLE_CELL_PRIMARY_CLASS, "px-4 truncate min-w-0")}>{item.name}</TableCell>,
    },
    contactName: {
      head: <TableHead className={cn(SUPPLIER_TABLE_COL.contact, TABLE_HEAD_CLASS, "px-4")}>Người liên hệ</TableHead>,
      cell: (item: Supplier) => <TableCell className={cn(SUPPLIER_TABLE_COL.contact, TABLE_CELL_SECONDARY_CLASS, "px-4 truncate min-w-0")}>{item.contactPerson || "-"}</TableCell>,
    },
    email: {
      head: <TableHead className={cn(SUPPLIER_TABLE_COL.email, TABLE_HEAD_CLASS, "px-4")}>Email</TableHead>,
      cell: (item: Supplier) => <TableCell className={cn(SUPPLIER_TABLE_COL.email, TABLE_CELL_SECONDARY_CLASS, "px-4 truncate min-w-0")}>{item.email || "-"}</TableCell>,
    },
    address: {
      head: <TableHead className={cn(SUPPLIER_TABLE_COL.address, TABLE_HEAD_CLASS, "px-4 text-left")}>Địa chỉ</TableHead>,
      cell: (item: Supplier) => <TableCell className={cn(SUPPLIER_TABLE_COL.address, TABLE_CELL_SECONDARY_CLASS, "px-4 text-left truncate min-w-0")}>{item.address || "-"}</TableCell>,
    },
    receiptCount: {
      head: <TableHead className={cn(SUPPLIER_TABLE_COL.receiptCount, TABLE_HEAD_CLASS, "px-4 text-center")}>Phiếu nhập</TableHead>,
      cell: (item: Supplier) => (
        <TableCell className={cn(SUPPLIER_TABLE_COL.receiptCount, "px-4 text-center")}>
          <span className={cn(
            "inline-flex items-center justify-center min-w-7 h-6 px-2 rounded-full text-xs font-semibold",
            (item.receiptCount ?? 0) > 0 ? "bg-blue-50 text-blue-700" : "bg-slate-100 text-slate-400",
          )}>
            {item.receiptCount ?? 0}
          </span>
        </TableCell>
      ),
    },
    status: {
      head: <TableHead className={cn(SUPPLIER_TABLE_COL.status, TABLE_HEAD_CLASS, "px-4")}>Trạng thái</TableHead>,
      cell: (item: Supplier) => (
        <TableCell className={cn(SUPPLIER_TABLE_COL.status, "px-4")}>
          <Badge className={cn("text-xs font-semibold border shadow-none gap-1.5", item.status === "Active" ? "bg-emerald-100 text-emerald-700 border-emerald-200" : "bg-slate-100 text-slate-500 border-slate-200")}>
            <span className={cn("w-1.5 h-1.5 rounded-full inline-block", item.status === "Active" ? "bg-emerald-500" : "bg-slate-400")} />
            {item.status === "Active" ? "Hoạt động" : "Ngừng"}
          </Badge>
        </TableCell>
      ),
    },
  } satisfies Record<string, { head: React.ReactNode; cell: (item: Supplier) => React.ReactNode }>

  const visibleKeySet = new Set(visibleColumnKeys)
  const orderedColumns = DEFAULT_COLUMNS
    .filter((key) => visibleKeySet.has(key) || REQUIRED_COLUMNS.has(key))
    .map((key) => ({ key, renderer: columnRenderers[key] }))
    .filter((entry): entry is { key: string; renderer: (typeof columnRenderers)[keyof typeof columnRenderers] } => entry.renderer != null)

  const emptyColSpan = orderedColumns.length + 2

  return (
    <Table className={DATA_TABLE_ROOT_CLASS}>
      <TableHeader className="sticky top-0 z-30 bg-slate-50 shadow-sm border-b">
        <TableRow className="hover:bg-transparent border-slate-200 border-b">
          <TableHead className={cn(SUPPLIER_TABLE_COL.select, "px-4 text-center", TABLE_HEAD_CLASS)}>
            <Checkbox
              checked={allSelected ? true : someSelected ? "indeterminate" : false}
              onCheckedChange={(checked) => onSelectAll(checked as boolean)}
              className={DATA_TABLE_CHECKBOX_CLASS}
            />
          </TableHead>
          {orderedColumns.map((column) => <React.Fragment key={column.key}>{column.renderer.head}</React.Fragment>)}
          <TableHead className={cn(DATA_TABLE_ACTION_HEAD_CLASS, TABLE_HEAD_CLASS)}>Thao tác</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody className="divide-y divide-slate-100">
        {data.length === 0 ? (
          <TableRow>
            <TableCell colSpan={emptyColSpan} className="h-24 text-center text-slate-500 text-sm">
              Không tìm thấy nhà cung cấp nào.
            </TableCell>
          </TableRow>
        ) : (
          data.map((item) => {
            const isSelected = selectedIds.includes(item.id)
            return (
              <TableRow key={item.id} className={cn("group h-14 transition-colors", isSelected ? "bg-slate-100" : "hover:bg-slate-50/60")}>
                <TableCell className="px-4 text-center">
                  <Checkbox
                    checked={isSelected}
                    onCheckedChange={() => onSelect(item.id)}
                    className={DATA_TABLE_CHECKBOX_CLASS}
                  />
                </TableCell>
                {orderedColumns.map((column) => <React.Fragment key={column.key}>{column.renderer.cell(item)}</React.Fragment>)}
                <TableCell className={DATA_TABLE_ACTION_CELL_CLASS}>
                  <div className="flex items-center justify-center gap-1">
                    <Button variant="ghost" size="icon" onClick={() => onView(item)} title="Xem chi tiết" className="h-8 w-8 text-slate-500 hover:text-slate-900 transition-colors">
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => onEdit(item)} title="Chỉnh sửa" className="h-8 w-8 text-slate-500 hover:text-slate-900 transition-colors">
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      disabled={!canDelete}
                      onClick={() => {
                        if (!canDelete) return
                        onDelete(item)
                      }}
                      title={canDelete ? "Xóa" : "Chỉ Owner mới được xóa"}
                      className="h-8 w-8 text-slate-500 hover:text-red-600 transition-colors disabled:opacity-40 disabled:pointer-events-none"
                    >
                      <Trash2 className="h-4 w-4" />
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
