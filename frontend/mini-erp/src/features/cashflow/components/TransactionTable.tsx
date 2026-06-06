import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Eye, Edit2, Trash2 } from "lucide-react"
import { formatCurrency } from "@/features/inventory/utils"
import { 
  DATA_TABLE_ROOT_CLASS, 
  DATA_TABLE_ACTION_HEAD_CLASS, 
  DATA_TABLE_ACTION_CELL_CLASS,
  TRANSACTION_TABLE_COL,
  TABLE_HEAD_CLASS,
  TABLE_CELL_PRIMARY_CLASS,
  TABLE_CELL_SECONDARY_CLASS,
  TABLE_CELL_MONO_CLASS,
  TABLE_CELL_NUMBER_CLASS,
} from "@/lib/data-table-layout"
import { cn } from "@/lib/utils"
import type { Transaction } from "../types"

interface TransactionTableProps {
  data: Transaction[]
  selectedIds: number[]
  onSelect: (id: number) => void
  onSelectAll: (checked: boolean) => void
  onView: (item: Transaction) => void
  onEdit: (item: Transaction) => void
  onDelete: (item: Transaction) => void
}

function StatusBadge({ status }: { status: string }) {
  if (status === "Completed") return (
    <Badge className="text-xs font-semibold bg-emerald-100 text-emerald-700 border border-emerald-200 shadow-none gap-1.5">
      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
      Hoàn thành
    </Badge>
  )
  if (status === "Pending") return (
    <Badge className="text-xs font-semibold bg-amber-100 text-amber-700 border border-amber-200 shadow-none gap-1.5">
      <span className="w-1.5 h-1.5 rounded-full bg-amber-400 inline-block" />
      Chờ xử lý
    </Badge>
  )
  return (
    <Badge className="text-xs font-semibold bg-rose-100 text-rose-600 border border-rose-200 shadow-none gap-1.5">
      <span className="w-1.5 h-1.5 rounded-full bg-rose-400 inline-block" />
      Đã huỷ
    </Badge>
  )
}

function DirectionBadge({ direction }: { direction: string }) {
  if (direction === "Income") return (
    <Badge className="text-[10px] font-bold border border-emerald-200 bg-emerald-50 text-emerald-700 h-5 px-1.5 uppercase tracking-tight shadow-none">
      ↑ Thu
    </Badge>
  )
  return (
    <Badge className="text-[10px] font-bold border border-rose-200 bg-rose-50 text-rose-600 h-5 px-1.5 uppercase tracking-tight shadow-none">
      ↓ Chi
    </Badge>
  )
}

export function TransactionTable({ data, selectedIds, onSelect, onSelectAll, onView, onEdit, onDelete }: TransactionTableProps) {
  const allSelected = data.length > 0 && selectedIds.length === data.length;
  const someSelected = selectedIds.length > 0 && selectedIds.length < data.length;

  return (
    <Table className={DATA_TABLE_ROOT_CLASS}>
      <TableHeader className="sticky top-0 z-30 bg-slate-50 shadow-sm border-b">
        <TableRow className="hover:bg-transparent border-slate-200 border-b">
          <TableHead className={cn(TRANSACTION_TABLE_COL.select, TABLE_HEAD_CLASS, "px-4 text-center")}>
            <Checkbox 
              checked={allSelected ? true : someSelected ? "indeterminate" : false} 
              onCheckedChange={(checked) => onSelectAll(checked as boolean)}
              className="border-slate-300 data-[state=checked]:bg-slate-800 data-[state=checked]:text-white data-[state=checked]:border-slate-800"
            />
          </TableHead>
          <TableHead className={cn(TRANSACTION_TABLE_COL.code, TABLE_HEAD_CLASS, "px-4")}>Mã GD</TableHead>
          <TableHead className={cn(TRANSACTION_TABLE_COL.type, TABLE_HEAD_CLASS, "px-4")}>Loại</TableHead>
          <TableHead className={cn(TRANSACTION_TABLE_COL.category, TABLE_HEAD_CLASS, "px-4")}>Phân loại</TableHead>
          <TableHead className={cn(TRANSACTION_TABLE_COL.amount, TABLE_HEAD_CLASS, "text-right px-4")}>Số tiền</TableHead>
          <TableHead className={cn(TRANSACTION_TABLE_COL.date, TABLE_HEAD_CLASS, "px-4")}>Ngày GD</TableHead>
          <TableHead className={cn(TRANSACTION_TABLE_COL.status, TABLE_HEAD_CLASS, "text-center px-4")}>Trạng thái</TableHead>
          <TableHead className={cn(DATA_TABLE_ACTION_HEAD_CLASS, TABLE_HEAD_CLASS)}>Thao tác</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody className="divide-y divide-slate-100">
        {data.length === 0 ? (
          <TableRow>
            <TableCell colSpan={8} className="h-64 text-center">
              <div className="flex flex-col items-center justify-center text-slate-400 gap-2">
                <p className="text-sm">Không tìm thấy giao dịch nào</p>
              </div>
            </TableCell>
          </TableRow>
        ) : (
          data.map((item) => {
            const isSelected = selectedIds.includes(item.id);
            return (
              <TableRow key={item.id} className={cn(
                "group h-16 transition-colors",
                isSelected
                  ? "bg-slate-100"
                  : "hover:bg-slate-50/60"
              )}>
                <TableCell className="px-4 text-center">
                  <Checkbox 
                    checked={isSelected}
                    onCheckedChange={() => onSelect(item.id)}
                    className="border-slate-300 data-[state=checked]:bg-slate-800 data-[state=checked]:text-white data-[state=checked]:border-slate-800"
                  />
                </TableCell>
                <TableCell className={cn(TRANSACTION_TABLE_COL.code, TABLE_CELL_MONO_CLASS, "px-4")}>{item.transactionCode}</TableCell>
                <TableCell className="px-4">
                  <DirectionBadge direction={item.direction} />
                </TableCell>
                <TableCell className="px-4">
                  <div className="flex flex-col">
                    <span className={cn(TABLE_CELL_PRIMARY_CLASS, "truncate")}>{item.category}</span>
                    <span className={cn(TABLE_CELL_SECONDARY_CLASS, "text-xs truncate max-w-[140px]")}>{item.description ?? ""}</span>
                  </div>
                </TableCell>
                <TableCell className={cn(TRANSACTION_TABLE_COL.amount, TABLE_CELL_NUMBER_CLASS, "text-right px-4 font-semibold", item.direction === 'Income' ? 'text-emerald-600' : 'text-rose-600')}>
                  {item.direction === 'Income' ? '+' : '-'}{formatCurrency(item.amount)}
                </TableCell>
                <TableCell className={cn(TRANSACTION_TABLE_COL.date, TABLE_CELL_SECONDARY_CLASS, "px-4")}>
                  {new Date(item.transactionDate).toLocaleDateString('vi-VN')}
                </TableCell>
                <TableCell className="px-4 text-center">
                  <StatusBadge status={item.status} />
                </TableCell>
                <TableCell className={DATA_TABLE_ACTION_CELL_CLASS}>
                  <div className="flex items-center justify-center gap-1">
                    <Button variant="ghost" size="icon" onClick={() => onView(item)} title="Xem chi tiết" className="h-8 w-8 text-slate-400 hover:text-slate-900 transition-colors">
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => onEdit(item)} title="Chỉnh sửa" className="h-8 w-8 text-slate-400 hover:text-slate-900 transition-colors">
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => onDelete(item)} title="Xóa giao dịch" className="h-8 w-8 text-slate-400 hover:text-slate-700 transition-colors">
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
