import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search, Plus, Filter, CreditCard, Calendar } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface DebtToolbarProps {
  searchStr: string
  onSearch: (val: string) => void
  statusFilter: string
  onStatusChange: (val: string) => void
  typeFilter: string
  onTypeChange: (val: string) => void
  dueDateFrom: string
  dueDateTo: string
  onDueDateFromChange: (val: string) => void
  onDueDateToChange: (val: string) => void
  selectedIds: number[]
  onAction: (action: string) => void
}

export function DebtToolbar({ 
  searchStr,
  onSearch,
  statusFilter,
  onStatusChange,
  typeFilter,
  onTypeChange,
  dueDateFrom,
  dueDateTo,
  onDueDateFromChange,
  onDueDateToChange,
  selectedIds,
  onAction,
}: DebtToolbarProps) {
  const hasSelection = selectedIds.length > 0

  return (
    <div className="bg-white p-4 border border-slate-200 rounded-lg shrink-0 shadow-sm flex flex-col gap-4">
      <div className="flex flex-col xl:flex-row items-stretch xl:items-center justify-between gap-4">
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center gap-3 w-full">
        <div className="relative w-full lg:w-[320px] group">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 group-focus-within:text-slate-600 transition-colors" />
          <Input 
            placeholder="Tìm theo mã nợ, tên đối tác..." 
            className="pl-10 h-11 bg-slate-50 border-slate-200 focus:bg-white focus:border-slate-400 focus:ring-2 focus:ring-slate-100 transition-all rounded-lg"
            value={searchStr}
            onChange={(e) => onSearch(e.target.value)}
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full lg:w-auto">
          <Select value={statusFilter} onValueChange={onStatusChange}>
            <SelectTrigger className="min-w-[170px] w-fit h-11 border-slate-200 rounded-lg bg-white shadow-sm">
              <Filter className="h-4 w-4 mr-2 text-slate-400" />
              <SelectValue placeholder="Trạng thái" />
            </SelectTrigger>
            <SelectContent position="popper" className="bg-white border-slate-200 rounded-xl shadow-xl">
              <SelectItem value="all">Tất cả trạng thái</SelectItem>
              <SelectItem value="InDebt">Còn nợ</SelectItem>
              <SelectItem value="Cleared">Đã tất toán</SelectItem>
            </SelectContent>
          </Select>

          <Select value={typeFilter} onValueChange={onTypeChange}>
            <SelectTrigger className="min-w-[170px] w-fit h-11 border-slate-200 rounded-lg bg-white shadow-sm">
              <SelectValue placeholder="Loại đối tác" />
            </SelectTrigger>
            <SelectContent position="popper" className="bg-white border-slate-200 rounded-xl shadow-xl">
              <SelectItem value="all">Tất cả đối tác</SelectItem>
              <SelectItem value="Customer">Khách hàng</SelectItem>
              <SelectItem value="Supplier">Nhà cung cấp</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full lg:w-auto">
          <Calendar className="h-4 w-4 text-slate-400 shrink-0" />
          <Input
            type="date"
            value={dueDateFrom}
            onChange={(e) => onDueDateFromChange(e.target.value)}
            className="h-11 bg-slate-50 border-slate-200 focus:bg-white focus:border-slate-400 focus:ring-2 focus:ring-slate-100 rounded-lg w-full sm:w-40"
          />
          <span className="text-xs font-bold text-slate-400 hidden sm:inline">—</span>
          <Input
            type="date"
            value={dueDateTo}
            onChange={(e) => onDueDateToChange(e.target.value)}
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
              onClick={() => onAction("repay")}
            >
              <CreditCard className="h-4 w-4 mr-2" />
              Thanh toán ({selectedIds.length})
            </Button>
          </div>
        ) : (
          <>
            <Button 
              className="h-11 px-4 bg-slate-900 hover:bg-slate-800 text-white rounded-lg ml-auto"
              onClick={() => onAction("create")}
            >
              <Plus className="h-4 w-4 mr-2" />
              Tạo khoản nợ
            </Button>
          </>
        )}
      </div>
      </div>
    </div>
  )
}
