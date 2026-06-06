import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search, Edit2, ArrowDownToLine, ArrowUpFromLine } from "lucide-react"
import { cn } from "@/lib/utils"

const STOCK_FILTERS = [
  { value: "all", label: "Tất cả" },
  { value: "in-stock", label: "Còn hàng" },
  { value: "low-stock", label: "Sắp hết" },
  { value: "out-of-stock", label: "Hết hàng" },
] as const

interface StockToolbarProps {
  searchStr: string
  onSearch: (val: string) => void
  status: string
  onStatusChange: (val: string) => void
  selectedIds: number[]
  onAction: (action: string) => void
}

export function StockToolbar({ searchStr, onSearch, status, onStatusChange, selectedIds, onAction }: StockToolbarProps) {
  const hasSelection = selectedIds.length > 0

  return (
    <div className="space-y-3">
      {/* Row 1: Search + bulk actions */}
      <div className="flex flex-col xl:flex-row gap-3 justify-between items-start xl:items-center">
        <div className="relative w-full xl:max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Tìm theo tên hoặc mã SP..."
            value={searchStr}
            onChange={(e) => onSearch(e.target.value)}
            className="pl-9 h-10 w-full"
          />
        </div>

        <div className={cn("flex flex-wrap items-center gap-2 w-full xl:w-auto xl:justify-end", !hasSelection && "opacity-50")}>
          <span className="text-sm font-medium text-slate-600 mr-1">
            Đã chọn: {selectedIds.length}
          </span>
          <Button variant="outline" size="sm" onClick={() => onAction("import")} disabled={!hasSelection} className="h-9">
            <ArrowDownToLine className="mr-1.5 h-4 w-4" />Nhập
          </Button>
          <Button variant="outline" size="sm" onClick={() => onAction("export")} disabled={!hasSelection} className="h-9">
            <ArrowUpFromLine className="mr-1.5 h-4 w-4" />Xuất
          </Button>
          <Button variant="outline" size="sm" onClick={() => onAction("edit")} disabled={!hasSelection} className="h-9">
            <Edit2 className="mr-1.5 h-4 w-4" />Sửa
          </Button>
        </div>
      </div>

      {/* Row 2: Quick-filter tabs */}
      <div className="flex flex-wrap gap-1.5">
        {STOCK_FILTERS.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => onStatusChange(f.value)}
            className={cn(
              "h-8 px-3 rounded-full text-sm font-medium transition-colors border",
              status === f.value
                ? "bg-slate-900 text-white border-slate-900"
                : "bg-white text-slate-600 border-slate-200 hover:border-slate-400 hover:text-slate-900",
            )}
          >
            {f.label}
          </button>
        ))}
      </div>
    </div>
  )
}
