import { Checkbox } from "@/components/ui/checkbox"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Eye, Edit2 } from "lucide-react"
import { formatCurrency } from "@/features/inventory/utils"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { 
  DATA_TABLE_ROOT_CLASS, 
  DATA_TABLE_ACTION_SINGLE_HEAD_CLASS,
  DATA_TABLE_ACTION_SINGLE_CELL_CLASS,
  DEBT_TABLE_COL,
  TABLE_HEAD_CLASS,
  TABLE_CELL_PRIMARY_CLASS,
  TABLE_CELL_SECONDARY_CLASS,
  TABLE_CELL_MONO_CLASS,
  TABLE_CELL_NUMBER_CLASS,
  DATA_TABLE_CHECKBOX_CLASS,
} from "@/lib/data-table-layout"
import { cn } from "@/lib/utils"
import type { Debt } from "../types"

interface DebtTableProps {
  data: Debt[]
  selectedIds: number[]
  onSelect: (id: number) => void
  onSelectAll: (checked: boolean) => void
  onView: (item: Debt) => void
  onEdit: (item: Debt) => void
}

function PartnerTypeBadge({ type }: { type: string }) {
  const base = "bg-white text-slate-700 text-[10px] font-semibold border-slate-200 h-5 px-1.5 uppercase tracking-tight shadow-none"
  if (type === "Customer") return <Badge className={base}>Khách hàng</Badge>
  return <Badge className={base}>Nhà cung cấp</Badge>
}

function formatDueDate(item: Debt) {
  if (!item.dueDate) return "—"
  return new Date(item.dueDate).toLocaleDateString("vi-VN")
}

function isOverdue(item: Debt) {
  if (!item.dueDate || item.status === "Cleared") return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const due = new Date(item.dueDate)
  due.setHours(0, 0, 0, 0)
  return due < today
}

export function DebtTable({ data, selectedIds, onSelect, onSelectAll, onView, onEdit }: DebtTableProps) {
  const allSelected = data.length > 0 && selectedIds.length === data.length
  const someSelected = selectedIds.length > 0 && selectedIds.length < data.length

  return (
    <Table className={DATA_TABLE_ROOT_CLASS}>
      <TableHeader className="sticky top-0 z-30 bg-slate-50 shadow-sm border-b">
        <TableRow className="hover:bg-transparent border-slate-200 border-b">
          <TableHead className={cn(DEBT_TABLE_COL.select, TABLE_HEAD_CLASS, "px-4 text-center")}>
            <Checkbox 
              checked={allSelected ? true : someSelected ? "indeterminate" : false} 
              onCheckedChange={(checked) => onSelectAll(checked as boolean)}
              className={DATA_TABLE_CHECKBOX_CLASS}
            />
          </TableHead>
          <TableHead className={cn(DEBT_TABLE_COL.code, TABLE_HEAD_CLASS, "px-4")}>Mã nợ</TableHead>
          <TableHead className={cn(DEBT_TABLE_COL.partner, TABLE_HEAD_CLASS, "px-4")}>Đối tác</TableHead>
          <TableHead className={cn(DEBT_TABLE_COL.type, TABLE_HEAD_CLASS, "px-4")}>Phân loại</TableHead>
          <TableHead className={cn(DEBT_TABLE_COL.total, TABLE_HEAD_CLASS, "text-right px-4")}>Tổng nợ</TableHead>
          <TableHead className={cn(DEBT_TABLE_COL.paid, TABLE_HEAD_CLASS, "text-right px-4")}>Đã trả</TableHead>
          <TableHead className={cn(DEBT_TABLE_COL.remaining, TABLE_HEAD_CLASS, "text-right px-4")}>Còn lại</TableHead>
          <TableHead className={cn(DEBT_TABLE_COL.dueDate, TABLE_HEAD_CLASS, "px-4")}>Hạn tất toán</TableHead>
          <TableHead className={cn(DEBT_TABLE_COL.status, TABLE_HEAD_CLASS, "text-center px-4")}>Trạng thái</TableHead>
          <TableHead className={cn(DATA_TABLE_ACTION_SINGLE_HEAD_CLASS, TABLE_HEAD_CLASS)}>Thao tác</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody className="divide-y divide-slate-100">
        {data.length === 0 ? (
          <TableRow>
            <TableCell colSpan={10} className="h-64 text-center">
              <div className="flex flex-col items-center justify-center text-slate-400 gap-2">
                <p className="text-sm">Không tìm thấy khoản nợ nào</p>
              </div>
            </TableCell>
          </TableRow>
        ) : (
          data.map((item) => {
            const isSelected = selectedIds.includes(item.id)
            const overdue = isOverdue(item)
            return (
              <TableRow key={item.id} className={cn("group h-16", isSelected ? "bg-slate-50" : "hover:bg-slate-50/50")}>
                <TableCell className="px-4 text-center">
                  <Checkbox 
                    checked={isSelected}
                    onCheckedChange={() => onSelect(item.id)}
                    className={DATA_TABLE_CHECKBOX_CLASS}
                  />
                </TableCell>
                <TableCell className={cn(DEBT_TABLE_COL.code, TABLE_CELL_MONO_CLASS, "px-4")}>{item.debtCode}</TableCell>
                <TableCell className="px-4 text-left">
                  <span className={cn(TABLE_CELL_PRIMARY_CLASS, "truncate block")}>{item.partnerName}</span>
                </TableCell>
                <TableCell className="px-4">
                  <PartnerTypeBadge type={item.partnerType} />
                </TableCell>
                <TableCell className={cn(DEBT_TABLE_COL.total, TABLE_CELL_NUMBER_CLASS, "text-right px-4 text-slate-700")}>
                  {formatCurrency(item.totalAmount)}
                </TableCell>
                <TableCell className={cn(DEBT_TABLE_COL.paid, TABLE_CELL_NUMBER_CLASS, "text-right px-4 text-emerald-600")}>
                  {formatCurrency(item.paidAmount)}
                </TableCell>
                <TableCell className={cn(DEBT_TABLE_COL.remaining, TABLE_CELL_NUMBER_CLASS, "text-right px-4 text-rose-600 font-bold")}>
                  {formatCurrency(item.remainingAmount)}
                </TableCell>
                <TableCell className={cn(DEBT_TABLE_COL.dueDate, TABLE_CELL_SECONDARY_CLASS, "px-4", overdue && "text-rose-600 font-semibold")}>
                  {formatDueDate(item)}
                </TableCell>
                <TableCell className="px-4 text-center">
                  <StatusBadge status={item.status === "Active" ? "Active_debt" : item.status} />
                </TableCell>
                <TableCell className={DATA_TABLE_ACTION_SINGLE_CELL_CLASS}>
                  <div className="flex items-center justify-center gap-1">
                    <Button variant="ghost" size="icon" onClick={() => onView(item)} title="Xem chi tiết" className="h-8 w-8 text-slate-400 hover:text-slate-900 transition-colors">
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => onEdit(item)} title="Cập nhật công nợ" className="h-8 w-8 text-slate-400 hover:text-slate-900 transition-colors">
                      <Edit2 className="h-4 w-4" />
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
