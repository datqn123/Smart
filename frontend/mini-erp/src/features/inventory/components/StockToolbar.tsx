import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search, Edit2, ArrowDownToLine, ArrowUpFromLine } from "lucide-react"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface StockToolbarProps {
  searchStr: string
  onSearch: (val: string) => void
  status: string
  onStatusChange: (val: string) => void
  selectedIds: number[]
  onAction: (action: string) => void
}

export function StockToolbar({ searchStr, onSearch, status, onStatusChange, selectedIds, onAction }: StockToolbarProps) {
  const hasSelection = selectedIds.length > 0;

  return (
    <div className="space-y-3">
      <div className="flex flex-col xl:flex-row gap-4 justify-between items-start xl:items-center">
        {/* Search & Filter */}
        <div className="flex flex-col sm:flex-row gap-3 w-full xl:max-w-xl">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Tìm theo tên hoặc mã SP..."
              value={searchStr}
              onChange={(e) => onSearch(e.target.value)}
              className="pl-9 min-h-[44px] w-full"
            />
          </div>
          <Select value={status} onValueChange={onStatusChange}>
            <SelectTrigger className="w-full sm:min-w-[200px] sm:w-fit min-h-[44px] bg-white text-slate-900 border-slate-200 focus:ring-2 focus:ring-slate-100 focus:border-slate-400 data-[state=open]:border-slate-400 transition-colors px-4">
              <SelectValue placeholder="Trạng thái" />
            </SelectTrigger>
            <SelectContent position="popper" sideOffset={4} className="bg-white border-slate-200 text-slate-900 shadow-lg min-w-[200px]">
              <SelectItem value="all" className="focus:bg-slate-100 focus:text-slate-900 cursor-pointer py-3 px-3">Tất cả trạng thái</SelectItem>
              <SelectItem value="in-stock" className="focus:bg-slate-100 focus:text-slate-900 cursor-pointer py-3 px-3">Còn hàng</SelectItem>
              <SelectItem value="low-stock" className="focus:bg-slate-100 focus:text-slate-900 cursor-pointer py-3 px-3">Sắp hết</SelectItem>
              <SelectItem value="out-of-stock" className="focus:bg-slate-100 focus:text-slate-900 cursor-pointer py-3 px-3">Hết hàng</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Group Actions - Always visible */}
        <div className={`flex flex-wrap items-center gap-2 pt-2 xl:pt-0 pb-1 xl:pb-0 w-full xl:w-auto xl:justify-end ${!hasSelection ? 'opacity-50' : ''}`}>
          <span className="text-sm font-medium text-slate-700 mr-2 min-w-[100px] xl:min-w-0">
            Đã chọn: {selectedIds.length}
          </span>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => onAction("import")}
            disabled={!hasSelection}
            className="min-h-[44px] xl:min-h-[36px]"
          >
            <ArrowDownToLine className="mr-1.5 h-4 w-4" />Nhập
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => onAction("export")}
            disabled={!hasSelection}
            className="min-h-[44px] xl:min-h-[36px]"
          >
            <ArrowUpFromLine className="mr-1.5 h-4 w-4" />Xuất
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => onAction("edit")}
            disabled={!hasSelection}
            className="min-h-[44px] xl:min-h-[36px]"
          >
            <Edit2 className="mr-1.5 h-4 w-4" />Sửa
          </Button>
        </div>
      </div>
    </div>
  )
}
