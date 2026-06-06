import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search, Trash2, Edit2, Plus, Download } from "lucide-react"
import { cn } from "@/lib/utils"

const RETAIL_HISTORY_STATUS_FILTERS = [
  { value: "all",       label: "Tất cả" },
  { value: "Delivered", label: "Hoàn thành" },
  { value: "Cancelled", label: "Đã huỷ" },
] as const

const RETAIL_HISTORY_PAYMENT_FILTERS = [
  { value: "all",     label: "Tất cả" },
  { value: "Paid",    label: "Đã TT" },
  { value: "Unpaid",  label: "Chưa TT" },
  { value: "Partial", label: "Một phần" },
] as const

interface OrderToolbarProps {
  searchStr: string
  onSearch: (val: string) => void
  statusFilter: string
  onStatusChange: (val: string) => void
  /** Task054 — lọc thanh toán; mặc định ẩn nếu không truyền. */
  paymentStatusFilter?: "all" | "Paid" | "Unpaid" | "Partial"
  onPaymentStatusChange?: (val: "all" | "Paid" | "Unpaid" | "Partial") => void
  selectedIds: number[]
  onAction: (action: string) => void
  showCreate?: boolean
  /** Task102 — chỉ tìm kiếm + lọc ngày; không thao tác sửa/xóa/tạo. */
  variant?: "default" | "retailHistory"
  dateFrom?: string
  dateTo?: string
  onDateFromChange?: (val: string) => void
  onDateToChange?: (val: string) => void
  /** SRS-020 — pill tabs cho variant retailHistory */
  onStatusFilterChange?: (val: string) => void
  onPaymentStatusFilterChange?: (val: string) => void
  /** SRS-020 — sort tích hợp vào toolbar */
  sort?: string
  onSortChange?: (val: string) => void
  sortWhitelist?: readonly string[]
  getSortLabel?: (s: string) => string
}

export function OrderToolbar({
  searchStr,
  onSearch,
  statusFilter,
  onStatusChange,
  paymentStatusFilter,
  onPaymentStatusChange,
  selectedIds,
  onAction,
  showCreate = true,
  variant = "default",
  dateFrom = "",
  dateTo = "",
  onDateFromChange,
  onDateToChange,
  onStatusFilterChange,
  onPaymentStatusFilterChange,
  sort,
  onSortChange,
  sortWhitelist,
  getSortLabel,
}: OrderToolbarProps) {
  const hasSelection = selectedIds.length > 0

  if (variant === "retailHistory") {
    return (
      <div className="bg-white p-4 border border-slate-200 rounded-lg shrink-0 shadow-sm flex flex-col gap-3">
        {/* Dòng 1: search + date range */}
        <div className="flex flex-col lg:flex-row gap-3 w-full flex-wrap">
          <div className="relative flex-1 min-w-50 group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 group-focus-within:text-blue-600 transition-colors" />
            <Input
              placeholder="Tìm theo mã đơn hoặc tên KH..."
              value={searchStr}
              onChange={(e) => onSearch(e.target.value)}
              className="pl-10 h-10 border-slate-200 focus:border-slate-400 focus:ring-slate-100 transition-all rounded-md"
            />
          </div>
          <div className="flex flex-col sm:flex-row gap-2 sm:items-center">
            <Input
              type="date"
              value={dateFrom}
              onChange={(e) => onDateFromChange?.(e.target.value)}
              className="h-10 w-full sm:w-40 border-slate-200 rounded-md"
            />
            <span className="text-slate-400 text-sm hidden sm:block">–</span>
            <Input
              type="date"
              value={dateTo}
              onChange={(e) => onDateToChange?.(e.target.value)}
              className="h-10 w-full sm:w-40 border-slate-200 rounded-md"
            />
          </div>
        </div>

        {/* Dòng 2: status pill tabs */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {RETAIL_HISTORY_STATUS_FILTERS.map((f) => (
            <button
              key={f.value}
              type="button"
              onClick={() => onStatusFilterChange?.(f.value)}
              className={cn(
                "h-8 px-3 rounded-full text-sm font-medium transition-colors border shrink-0",
                (statusFilter ?? "all") === f.value
                  ? "bg-slate-900 text-white border-slate-900"
                  : "bg-white text-slate-600 border-slate-200 hover:border-slate-400 hover:text-slate-900",
              )}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Dòng 3: payment pill tabs + sort */}
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-1.5 flex-wrap">
            {RETAIL_HISTORY_PAYMENT_FILTERS.map((f) => (
              <button
                key={f.value}
                type="button"
                onClick={() => onPaymentStatusFilterChange?.(f.value)}
                className={cn(
                  "h-8 px-3 rounded-full text-sm font-medium transition-colors border shrink-0",
                  (paymentStatusFilter ?? "all") === f.value
                    ? "bg-slate-900 text-white border-slate-900"
                    : "bg-white text-slate-600 border-slate-200 hover:border-slate-400 hover:text-slate-900",
                )}
              >
                {f.label}
              </button>
            ))}
          </div>
          {sortWhitelist && sort && onSortChange && (
            <select
              value={sort}
              onChange={(e) => onSortChange(e.target.value)}
              className="h-8 px-2 border border-slate-200 bg-white rounded-md text-sm text-slate-900 min-w-50"
            >
              {sortWhitelist.map((s) => (
                <option key={s} value={s}>
                  {getSortLabel?.(s) ?? s}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white p-4 space-y-3 border-b md:border border-slate-200 md:rounded-t-md shrink-0">
      <div className="flex flex-col xl:flex-row gap-4 justify-between items-start xl:items-center">
        {/* Search & Filter */}
        <div className="flex flex-col sm:flex-row gap-3 w-full xl:max-w-2xl">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Tìm theo mã đơn hoặc tên KH..."
              value={searchStr}
              onChange={(e) => onSearch(e.target.value)}
              className="pl-9 min-h-[44px] sm:min-h-[36px] w-full"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => onStatusChange(e.target.value)}
            className="h-11 sm:h-9 px-3 border border-slate-200 bg-white text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-400 w-full sm:min-w-[160px] sm:w-fit rounded-md"
          >
            <option value="all">Tất cả trạng thái</option>
            <option value="Pending">Chờ duyệt</option>
            <option value="Processing">Đang xử lý</option>
            <option value="Partial">Giao một phần</option>
            <option value="Shipped">Đang giao</option>
            <option value="Delivered">Hoàn thành</option>
            <option value="Cancelled">Đã huỷ</option>
          </select>
          {paymentStatusFilter != null && onPaymentStatusChange != null && (
            <select
              value={paymentStatusFilter}
              onChange={(e) =>
                onPaymentStatusChange(e.target.value as "all" | "Paid" | "Unpaid" | "Partial")
              }
              className="h-11 sm:h-9 px-3 border border-slate-200 bg-white text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-400 w-full sm:min-w-[160px] sm:w-fit rounded-md"
            >
              <option value="all">Tất cả thanh toán</option>
              <option value="Paid">Đã thanh toán</option>
              <option value="Unpaid">Chưa thanh toán</option>
              <option value="Partial">Thanh toán một phần</option>
            </select>
          )}
        </div>

        {/* Group Actions */}
        <div className="flex flex-wrap items-center gap-2 pt-2 xl:pt-0 pb-1 xl:pb-0 w-full xl:w-auto xl:justify-end">
          <div className={`flex items-center gap-2 ${!hasSelection ? 'opacity-50' : ''}`}>
            <span className="text-sm font-medium text-slate-700 mr-2 min-w-[100px] xl:min-w-0 hidden sm:inline-block">
              Đã chọn: {selectedIds.length}
            </span>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => hasSelection ? onAction("edit") : undefined}
              className="min-h-[44px] sm:min-h-[36px]"
            >
              <Edit2 className="mr-1.5 h-4 w-4" />Sửa
            </Button>
            <Button 
              variant="destructive" 
              size="sm" 
              onClick={() => hasSelection ? onAction("delete") : undefined}
              className="min-h-[44px] sm:min-h-[36px] bg-red-600 hover:bg-red-700 text-white"
            >
              <Trash2 className="mr-1.5 h-4 w-4" />Xoá
            </Button>
          </div>
          
          <div className="w-px h-6 bg-slate-200 hidden sm:block mx-1"></div>
          
          {showCreate && (
            <Button onClick={() => onAction("create")} className="h-11 sm:h-9 bg-slate-900 hover:bg-slate-800 text-white ml-auto sm:ml-0">
              <Plus className="h-4 w-4 mr-2" /> Tạo đơn hàng
            </Button>
          )}
          <Button onClick={() => onAction("export")} variant="outline" className="h-11 sm:h-9 hidden sm:flex">
            <Download className="h-4 w-4 mr-2" /> Export
          </Button>
        </div>
      </div>
    </div>
  )
}
