import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search, Trash2, Edit2, Plus } from "lucide-react"
import { cn } from "@/lib/utils"

const SUPPLIER_STATUS_FILTERS = [
  { value: "all",      label: "Tất cả" },
  { value: "Active",   label: "Đang hợp tác" },
  { value: "Inactive", label: "Ngừng hợp tác" },
] as const

interface SupplierToolbarProps {
  searchStr: string
  onSearch: (val: string) => void
  statusFilter: string
  onStatusChange: (val: string) => void
  selectedIds: number[]
  onAction: (action: string) => void
  /** Task047 bulk — Task046: chỉ Owner xóa. */
  canBulkDelete?: boolean
}

export function SupplierToolbar({
  searchStr, onSearch, statusFilter, onStatusChange,
  selectedIds, onAction,
  canBulkDelete = false,
}: SupplierToolbarProps) {
  const hasSelection = selectedIds.length > 0

  return (
    <div className="bg-white p-4 border border-slate-200 rounded-lg shrink-0 shadow-sm flex flex-col gap-3">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative flex-1 w-full sm:min-w-75 group">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 group-focus-within:text-blue-600 transition-colors" />
          <Input
            placeholder="Tìm theo tên, mã NCC hoặc SĐT..."
            value={searchStr}
            onChange={(e) => onSearch(e.target.value)}
            className="pl-10 h-10 border-slate-200 focus:border-slate-400 focus:ring-slate-100 transition-all rounded-md"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          {hasSelection && (
            <div className="flex items-center gap-2 animate-in fade-in slide-in-from-right-1">
              <Button variant="outline" size="sm" onClick={() => onAction("edit")} className="h-10 px-3 rounded-md">
                <Edit2 className="h-4 w-4 mr-1.5" /> Sửa
              </Button>
              {canBulkDelete && (
                <Button variant="destructive" size="sm" onClick={() => onAction("delete")} className="h-10 px-3 rounded-md bg-red-600 hover:bg-red-700">
                  <Trash2 className="h-4 w-4 mr-1.5" /> Xoá
                </Button>
              )}
            </div>
          )}
          <Button onClick={() => onAction("create")} className="h-10 bg-slate-900 hover:bg-slate-800 text-white rounded-md shadow-sm">
            <Plus className="h-4 w-4 mr-1.5" /> Tạo nhà cung cấp
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-1.5 flex-wrap">
        {SUPPLIER_STATUS_FILTERS.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => onStatusChange(f.value)}
            className={cn(
              "h-8 px-3 rounded-full text-sm font-medium transition-colors border shrink-0",
              statusFilter === f.value
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
