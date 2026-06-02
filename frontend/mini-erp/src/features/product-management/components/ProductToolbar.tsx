import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search, Trash2, Edit2, Plus } from "lucide-react"

export type ProductCategoryFilterOption = { id: number; name: string }

interface ProductToolbarProps {
  searchStr: string
  onSearch: (val: string) => void
  statusFilter: string
  onStatusChange: (val: string) => void
  /** `"all"` hoặc `${categoryId}` — khớp query `categoryId` API. */
  categoryFilter: string
  onCategoryChange: (val: string) => void
  categoryOptions: ProductCategoryFilterOption[]
  selectedIds: number[]
  onAction: (action: string) => void
  /** Task041 — `POST …/bulk-delete` chỉ Owner (khớp BE `assertOwnerOnly`). */
  canBulkDelete: boolean
}

export function ProductToolbar({
  searchStr, onSearch, statusFilter, onStatusChange,
  categoryFilter, onCategoryChange, categoryOptions,
  selectedIds, onAction, canBulkDelete,
}: ProductToolbarProps) {
  const hasSelection = selectedIds.length > 0;

  return (
    <div className="bg-white p-4 border border-slate-200 rounded-lg shrink-0 shadow-sm">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Search & Filter Group */}
        <div className="flex flex-col sm:flex-row items-center gap-3 w-full sm:w-auto flex-1 max-w-4xl">
          <div className="relative flex-1 w-full sm:min-w-[300px] group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 group-focus-within:text-blue-600 transition-colors" />
            <Input
              placeholder="Tìm theo tên, SKU hoặc barcode..."
              value={searchStr}
              onChange={(e) => onSearch(e.target.value)}
              className="pl-10 h-10 border-slate-200 focus:border-slate-400 focus:ring-slate-100 transition-all rounded-md"
            />
          </div>
          
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <select 
              value={statusFilter} 
              onChange={(e) => onStatusChange(e.target.value)}
              className="h-10 px-3 border border-slate-200 bg-white text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-100 w-full sm:min-w-[140px] rounded-md"
            >
              <option value="all">Trạng thái</option>
              <option value="Active">Hoạt động</option>
              <option value="Inactive">Ngừng</option>
            </select>

            <select 
              value={categoryFilter} 
              onChange={(e) => onCategoryChange(e.target.value)}
              className="h-10 px-3 border border-slate-200 bg-white text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-100 w-full sm:min-w-[160px] rounded-md"
            >
              <option value="all">Danh mục</option>
              {categoryOptions.map((c) => (
                <option key={c.id} value={String(c.id)}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Action Group */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          {hasSelection && (
            <div className="flex items-center gap-2 animate-in fade-in slide-in-from-right-1">
              <Button variant="outline" size="sm" onClick={() => onAction("edit")} className="h-10 px-3 rounded-md">
                <Edit2 className="h-4 w-4 mr-1.5" /> Sửa
              </Button>
              {canBulkDelete && (
                <Button variant="destructive" size="sm" onClick={() => onAction("delete")} className="h-10 px-3 rounded-md bg-red-600 hover:bg-red-700" title="Xóa hàng loạt (Owner)">
                  <Trash2 className="h-4 w-4 mr-1.5" /> Xoá
                </Button>
              )}
            </div>
          )}
          
          <Button onClick={() => onAction("create")} className="h-10 bg-slate-900 hover:bg-slate-800 text-white rounded-md shadow-sm">
            <Plus className="h-4 w-4 mr-1.5" /> Tạo sản phẩm
          </Button>
        </div>
      </div>
    </div>
  )
}
