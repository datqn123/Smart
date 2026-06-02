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
  DATA_TABLE_ACTION_SINGLE_HEAD_CLASS,
  DATA_TABLE_ACTION_SINGLE_CELL_CLASS,
  DATA_TABLE_CHECKBOX_CLASS,
  ORDER_TABLE_COL,
  TABLE_HEAD_CLASS,
  TABLE_CELL_PRIMARY_CLASS,
  TABLE_CELL_SECONDARY_CLASS,
  TABLE_CELL_MONO_CLASS,
  TABLE_CELL_NUMBER_CLASS,
} from "@/lib/data-table-layout"
import { cn } from "@/lib/utils"
import type { Order } from "../types"

interface OrderTableProps {
  data: Order[]
  selectedIds: number[]
  onSelect: (id: number) => void
  onSelectAll: (checked: boolean) => void
  onView: (item: Order) => void
  onEdit?: (item: Order) => void
  onDelete?: (item: Order) => void
  renderCustomActions?: (item: Order) => React.ReactNode
  showCheckbox?: boolean
  /** Task102 — ẩn cột trạng thái trên list lịch sử bán lẻ. */
  hideStatusColumn?: boolean
}

function StatusBadge({ status }: { status: string }) {
  switch (status) {
    case 'Completed':
    case 'Delivered':
      return <Badge className="bg-green-50 text-green-700 text-xs border-none font-normal">Hoàn thành</Badge>;
    case 'Shipped':
      return <Badge className="bg-blue-50 text-blue-700 text-xs border-none font-normal">Đang giao</Badge>;
    case 'Processing':
      return <Badge className="bg-indigo-50 text-indigo-700 text-xs border-none font-normal">Đang xử lý</Badge>;
    case 'Partial':
      return <Badge className="bg-amber-50 text-amber-700 text-xs border-none font-normal">Giao một phần</Badge>;
    case 'Pending':
      return <Badge className="bg-amber-100 text-amber-900 icon-xs border-none font-normal">Chờ duyệt</Badge>;
    case 'Cancelled':
      return <Badge className="bg-red-50 text-red-700 text-xs border-none font-normal">Đã huỷ</Badge>;
    default:
      return <Badge className="bg-slate-50 text-slate-700 text-xs border-none font-normal">{status}</Badge>;
  }
}

function TypeBadge({ type }: { type: string }) {
  if (type === 'Wholesale') return <Badge className="h-5 border-slate-200 bg-slate-50 px-1.5 text-[10px] font-semibold uppercase tracking-normal text-slate-600">Bán buôn</Badge>;
  if (type === 'Retail') return <Badge className="h-5 border-slate-200 bg-slate-50 px-1.5 text-[10px] font-semibold uppercase tracking-normal text-slate-600">Bán lẻ</Badge>;
  return <Badge className="h-5 border-slate-200 bg-slate-50 px-1.5 text-[10px] font-semibold uppercase tracking-normal text-slate-600">Trả hàng</Badge>;
}

export function OrderTable({ 
  data, 
  selectedIds, 
  onSelect, 
  onSelectAll, 
  onView, 
  onEdit, 
  onDelete,
  renderCustomActions,
  showCheckbox = true,
  hideStatusColumn = false,
}: OrderTableProps) {
  const allSelected = data.length > 0 && selectedIds.length === data.length;
  const someSelected = selectedIds.length > 0 && selectedIds.length < data.length;
  const colCount = (showCheckbox ? 1 : 0) + 4 + (hideStatusColumn ? 0 : 1) + 1;
  const singleViewAction = !renderCustomActions && !onEdit && !onDelete;

  return (
    <Table className={DATA_TABLE_ROOT_CLASS}>
      <TableHeader className="sticky top-0 z-30 bg-slate-50 shadow-sm border-b">
        <TableRow className="hover:bg-transparent border-slate-200 border-b">
          {showCheckbox && (
            <TableHead className={cn(ORDER_TABLE_COL.select, TABLE_HEAD_CLASS, "px-4 text-center")}>
              <Checkbox 
                checked={allSelected ? true : someSelected ? "indeterminate" : false} 
                onCheckedChange={(checked) => onSelectAll(checked as boolean)}
                className={DATA_TABLE_CHECKBOX_CLASS}
              />
            </TableHead>
          )}
          <TableHead className={cn(ORDER_TABLE_COL.code, TABLE_HEAD_CLASS, "px-4")}>Mã hóa đơn</TableHead>
          <TableHead className={cn(ORDER_TABLE_COL.customer, TABLE_HEAD_CLASS, "px-4")}>Khách hàng</TableHead>
          <TableHead className={cn(ORDER_TABLE_COL.date, TABLE_HEAD_CLASS, "px-4")}>Ngày lập</TableHead>
          <TableHead className={cn(ORDER_TABLE_COL.total, TABLE_HEAD_CLASS, "text-right px-4")}>Thành tiền</TableHead>
          {!hideStatusColumn && (
            <TableHead className={cn(ORDER_TABLE_COL.status, TABLE_HEAD_CLASS, "text-center px-4")}>Trạng thái</TableHead>
          )}
          <TableHead className={cn(singleViewAction ? DATA_TABLE_ACTION_SINGLE_HEAD_CLASS : DATA_TABLE_ACTION_HEAD_CLASS, TABLE_HEAD_CLASS)}>Thao tác</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody className="divide-y divide-slate-100">
        {data.length === 0 ? (
          <TableRow>
            <TableCell colSpan={colCount} className="h-64 text-center">
               <div className="flex flex-col items-center justify-center text-slate-400 gap-2">
                  <p className="text-sm">Không tìm thấy đơn hàng nào</p>
               </div>
            </TableCell>
          </TableRow>
        ) : (
          data.map((item) => {
            const isSelected = selectedIds.includes(item.id);
            return (
              <TableRow key={item.id} className={cn("group h-16", isSelected ? "bg-slate-50" : "hover:bg-slate-50/50")}>
                {showCheckbox && (
                  <TableCell className="px-4 text-center">
                    <Checkbox 
                      checked={isSelected}
                      onCheckedChange={() => onSelect(item.id)}
                      className={DATA_TABLE_CHECKBOX_CLASS}
                    />
                  </TableCell>
                )}
                <TableCell className={cn(ORDER_TABLE_COL.code, TABLE_CELL_MONO_CLASS, "px-4 min-w-0")}>
                  <span className="block truncate">{item.orderCode}</span>
                </TableCell>
                <TableCell className={cn(ORDER_TABLE_COL.customer, "px-4 min-w-0")}>
                  <div className="flex min-w-0 flex-col gap-1">
                    <span className={cn(TABLE_CELL_PRIMARY_CLASS, "block min-w-0 truncate")}>{item.customerName}</span>
                    <div className="flex gap-1 items-center">
                      <TypeBadge type={item.type} />
                      <span className={cn(TABLE_CELL_MONO_CLASS, "text-[10px] text-slate-400")}>• {item.itemsCount} mặt hàng</span>
                    </div>
                  </div>
                </TableCell>
                <TableCell className={cn(ORDER_TABLE_COL.date, TABLE_CELL_SECONDARY_CLASS, "px-4")}>
                  {new Date(item.date).toLocaleDateString('vi-VN')}
                </TableCell>
                <TableCell className={cn(ORDER_TABLE_COL.total, TABLE_CELL_NUMBER_CLASS, "text-right px-4")}>
                  {formatCurrency(item.finalAmount)}
                </TableCell>
                {!hideStatusColumn && (
                  <TableCell className={cn(ORDER_TABLE_COL.status, "px-4 text-center min-w-0")}>
                    <StatusBadge status={item.status} />
                  </TableCell>
                )}
                <TableCell className={singleViewAction ? DATA_TABLE_ACTION_SINGLE_CELL_CLASS : DATA_TABLE_ACTION_CELL_CLASS}>
                  <div className="flex items-center justify-center gap-1">
                    {renderCustomActions ? (
                      renderCustomActions(item)
                    ) : (
                      <>
                        <Button variant="ghost" size="icon" onClick={() => onView(item)} title="Xem chi tiết hóa đơn" className="h-8 w-8 text-slate-400 hover:text-slate-900 transition-colors">
                          <Eye className="h-4 w-4" />
                        </Button>
                        {onEdit && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => onEdit(item)}
                            title="Chỉnh sửa đơn"
                            className="h-8 w-8 text-slate-400 hover:text-blue-600 transition-colors"
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                        )}
                        {onDelete && (
                          <Button variant="ghost" size="icon" onClick={() => onDelete(item)} title="Hủy đơn hàng" className="h-8 w-8 text-slate-400 hover:text-red-600 transition-colors">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </>
                    )}
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
