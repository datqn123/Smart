import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search, Plus, Download, Trash2, Edit2, Calendar } from "lucide-react"
import { cn } from "@/lib/utils"

interface TransactionToolbarProps {
  searchStr: string
  onSearch: (val: string) => void
  statusFilter: string
  onStatusChange: (val: string) => void
  typeFilter: string
  onTypeChange: (val: string) => void
  dateFrom: string
  dateTo: string
  onDateFromChange: (val: string) => void
  onDateToChange: (val: string) => void
  selectedIds: number[]
  onAction: (action: string) => void
}

export function TransactionToolbar({ 
  searchStr,
  onSearch,
  statusFilter,
  onStatusChange,
  typeFilter,
  onTypeChange,
  dateFrom,
  dateTo,
  onDateFromChange,
  onDateToChange,
  selectedIds,
  onAction,
}: TransactionToolbarProps) {
  const hasSelection = selectedIds.length > 0

  return (
    <div className="bg-white p-4 border border-slate-200 rounded-lg shrink-0 shadow-sm flex flex-col gap-4">
      <div className="flex flex-col xl:flex-row items-stretch xl:items-center justify-between gap-4">
      <div className="flex flex-col lg:flex-row items-start lg:items-center gap-3 w-full">
        <div className="relative w-full lg:w-[320px] group">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 group-focus-within:text-slate-600 transition-colors" />
          <Input 
            placeholder="Tìm theo mã giao dịch, nội dung..." 
            className="pl-10 h-11 bg-slate-50 border-slate-200 focus:bg-white focus:border-slate-400 focus:ring-2 focus:ring-slate-100 transition-all rounded-lg"
            value={searchStr}
            onChange={(e) => onSearch(e.target.value)}
          />
        </div>

        <div className="flex flex-col gap-2">
          <PillGroup
            value={typeFilter}
            onChange={onTypeChange}
            options={[
              { value: "all", label: "Tất cả" },
              { value: "Income", label: "Thu tiền" },
              { value: "Expense", label: "Chi tiền" },
            ]}
          />
          <PillGroup
            value={statusFilter}
            onChange={onStatusChange}
            options={[
              { value: "all", label: "Tất cả" },
              { value: "Completed", label: "Hoàn thành" },
              { value: "Pending", label: "Chờ xử lý" },
              { value: "Cancelled", label: "Đã huỷ" },
            ]}
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full lg:w-auto">
          <Calendar className="h-4 w-4 text-slate-400 shrink-0" />
          <Input
            type="date"
            value={dateFrom}
            onChange={(e) => onDateFromChange(e.target.value)}
            className="h-11 bg-slate-50 border-slate-200 focus:bg-white focus:border-slate-400 focus:ring-2 focus:ring-slate-100 rounded-lg w-full sm:w-40"
          />
          <span className="text-xs font-bold text-slate-400 hidden sm:inline">—</span>
          <Input
            type="date"
            value={dateTo}
            onChange={(e) => onDateToChange(e.target.value)}
            className="h-11 bg-slate-50 border-slate-200 focus:bg-white focus:border-slate-400 focus:ring-2 focus:ring-slate-100 rounded-lg w-full sm:w-40"
          />
        </div>
      </div>

      <div className="flex items-center gap-2 w-full sm:w-auto">
        {hasSelection ? (
          <div className="flex items-center gap-2 animate-in fade-in slide-in-from-right-2 duration-200">
            <Button 
              variant="outline" 
              size="sm" 
              className="h-10 px-4 text-slate-700 border-slate-200 bg-white hover:bg-slate-50 rounded-md"
              onClick={() => onAction("edit")}
            >
              <Edit2 className="h-4 w-4 mr-2" />
              Sửa ({selectedIds.length})
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              className="h-10 px-4 text-slate-700 border-slate-200 bg-white hover:bg-slate-50 rounded-md"
              onClick={() => onAction("delete")}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Xoá
            </Button>
          </div>
        ) : (
          <>
            <Button 
              variant="outline" 
              size="sm" 
              className="h-11 px-4 text-slate-600 border-slate-200 hover:bg-slate-50 rounded-lg"
              onClick={() => onAction("export")}
            >
              <Download className="h-4 w-4 mr-2" />
              Xuất Excel
            </Button>
            <Button 
              className="h-11 px-4 bg-slate-900 hover:bg-slate-800 text-white rounded-lg ml-auto"
              onClick={() => onAction("create")}
            >
              <Plus className="h-4 w-4 mr-2" />
              Tạo phiếu
            </Button>
          </>
        )}
      </div>
      </div>
    </div>
  )
}

function PillGroup({
  value,
  onChange,
  options,
}: {
  value: string
  onChange: (value: string) => void
  options: { value: string; label: string }[]
}) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {options.map((option) => {
        const active = value === option.value
        return (
          <button
            key={option.value}
            type="button"
            className={cn(
              "h-8 rounded-full border px-3 text-xs font-semibold transition-colors",
              active
                ? "bg-slate-900 text-white border-slate-900"
                : "bg-white text-slate-600 border-slate-200 hover:border-slate-400",
            )}
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
