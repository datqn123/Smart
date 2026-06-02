import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Eye, Edit2, Trash2 } from "lucide-react"
import {
  DATA_TABLE_ROOT_CLASS,
  DATA_TABLE_ACTION_HEAD_CLASS,
  DATA_TABLE_ACTION_CELL_CLASS,
  CUSTOMER_TABLE_COL,
  TABLE_HEAD_CLASS,
  TABLE_CELL_PRIMARY_CLASS,
  TABLE_CELL_SECONDARY_CLASS,
  TABLE_CELL_MONO_CLASS,
  TABLE_CELL_NUMBER_CLASS,
  DATA_TABLE_CHECKBOX_CLASS,
} from "@/lib/data-table-layout"
import { cn } from "@/lib/utils"
import type { Customer } from "../types"

interface CustomerTableProps {
  data: Customer[]
  visibleColumnKeys?: string[]
  selectedIds: number[]
  onSelect: (id: number) => void
  onSelectAll: (checked: boolean) => void
  onView: (item: Customer) => void
  onEdit: (item: Customer) => void
  onDelete: (item: Customer) => void
  canDelete?: boolean
}

export function CustomerTable({
  data,
  visibleColumnKeys,
  selectedIds,
  onSelect,
  onSelectAll,
  onView,
  onEdit,
  onDelete,
  canDelete = false,
}: CustomerTableProps) {
  const defaultColumnKeys = ["customerCode", "customerName", "phone", "email", "orderCount", "status"] as const
  const visibleSet = new Set(visibleColumnKeys ?? defaultColumnKeys)
  const orderedBusinessColumns = defaultColumnKeys.filter((key) => visibleSet.has(key))
  const allSelected = data.length > 0 && selectedIds.length === data.length
  const someSelected = selectedIds.length > 0 && selectedIds.length < data.length

  return (
    <Table className={DATA_TABLE_ROOT_CLASS}>
      <TableHeader className="sticky top-0 z-30 bg-slate-50 shadow-sm border-b">
        <TableRow className="hover:bg-transparent border-slate-200 border-b">
          <TableHead className={cn(CUSTOMER_TABLE_COL.select, "px-4 text-center", TABLE_HEAD_CLASS)}>
            <Checkbox
              checked={allSelected ? true : someSelected ? "indeterminate" : false}
              onCheckedChange={(checked) => onSelectAll(checked as boolean)}
              className={DATA_TABLE_CHECKBOX_CLASS}
            />
          </TableHead>
          {orderedBusinessColumns.includes("customerCode") && (
            <TableHead className={cn(CUSTOMER_TABLE_COL.code, TABLE_HEAD_CLASS, "px-4")}>Mã khách hàng</TableHead>
          )}
          {orderedBusinessColumns.includes("customerName") && (
            <TableHead className={cn(CUSTOMER_TABLE_COL.name, TABLE_HEAD_CLASS, "px-4")}>Khách hàng</TableHead>
          )}
          {orderedBusinessColumns.includes("phone") && (
            <TableHead className={cn(CUSTOMER_TABLE_COL.phone, TABLE_HEAD_CLASS, "px-4")}>Số điện thoại</TableHead>
          )}
          {orderedBusinessColumns.includes("email") && (
            <TableHead className={cn(CUSTOMER_TABLE_COL.email, TABLE_HEAD_CLASS, "px-4")}>Email</TableHead>
          )}
          {orderedBusinessColumns.includes("orderCount") && (
            <TableHead className={cn(CUSTOMER_TABLE_COL.orders, TABLE_HEAD_CLASS, "px-4 text-center")}>Số đơn hàng</TableHead>
          )}
          {orderedBusinessColumns.includes("status") && (
            <TableHead className={cn(CUSTOMER_TABLE_COL.status, TABLE_HEAD_CLASS, "px-4")}>Trạng thái</TableHead>
          )}
          <TableHead className={cn(DATA_TABLE_ACTION_HEAD_CLASS, TABLE_HEAD_CLASS)}>Thao tác</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody className="divide-y divide-slate-100">
        {data.length === 0 ? (
          <TableRow>
            <TableCell colSpan={8} className="h-24 text-center text-slate-500 text-sm">
              Không tìm thấy khách hàng nào.
            </TableCell>
          </TableRow>
        ) : (
          data.map((item) => {
            const isSelected = selectedIds.includes(item.id)
            return (
              <TableRow key={item.id} className={cn("group h-14", isSelected ? "bg-slate-50" : "hover:bg-slate-50/50")}>
                <TableCell className="px-4 text-center">
                  <Checkbox
                    checked={isSelected}
                    onCheckedChange={() => onSelect(item.id)}
                    className={DATA_TABLE_CHECKBOX_CLASS}
                  />
                </TableCell>
                {orderedBusinessColumns.map((columnKey) => {
                  if (columnKey === "customerCode") {
                    return <TableCell key={columnKey} className={cn(CUSTOMER_TABLE_COL.code, TABLE_CELL_MONO_CLASS, "px-4")}>{item.customerCode}</TableCell>
                  }
                  if (columnKey === "customerName") {
                    return <TableCell key={columnKey} className={cn(CUSTOMER_TABLE_COL.name, TABLE_CELL_PRIMARY_CLASS, "px-4 truncate")}>{item.name}</TableCell>
                  }
                  if (columnKey === "phone") {
                    return <TableCell key={columnKey} className={cn(CUSTOMER_TABLE_COL.phone, TABLE_CELL_SECONDARY_CLASS, "px-4")}>{item.phone}</TableCell>
                  }
                  if (columnKey === "email") {
                    return <TableCell key={columnKey} className={cn(CUSTOMER_TABLE_COL.email, TABLE_CELL_SECONDARY_CLASS, "px-4 truncate")}>{item.email || "-"}</TableCell>
                  }
                  if (columnKey === "orderCount") {
                    return <TableCell key={columnKey} className={cn(CUSTOMER_TABLE_COL.orders, TABLE_CELL_NUMBER_CLASS, "text-center px-4")}>{item.orderCount ?? 0}</TableCell>
                  }
                  return (
                    <TableCell key={columnKey} className={cn(CUSTOMER_TABLE_COL.status, "px-4")}>
                      <Badge className={cn("text-xs font-normal border-none", item.status === "Active" ? "bg-green-50 text-green-700" : "bg-slate-100 text-slate-500")}>
                        {item.status === "Active" ? "Hoạt động" : "Ngừng"}
                      </Badge>
                    </TableCell>
                  )
                })}
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
                      title={canDelete ? "Xóa" : "Chỉ Admin mới được xóa"}
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
