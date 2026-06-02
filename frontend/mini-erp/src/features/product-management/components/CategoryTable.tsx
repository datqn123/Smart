import { useState } from "react"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Eye, Edit2, Trash2, ChevronDown, ChevronRight, PlusCircle } from "lucide-react"
import type { Category } from "../types"
import { cn } from "@/lib/utils"
import {
  CATEGORY_TABLE_COL,
  DATA_TABLE_ACTION_CELL_CLASS,
  DATA_TABLE_ACTION_HEAD_CLASS,
  DATA_TABLE_ROOT_CLASS,
  TABLE_HEAD_CLASS,
  TABLE_CELL_PRIMARY_CLASS,
  TABLE_CELL_SECONDARY_CLASS,
  TABLE_CELL_MONO_CLASS,
  TABLE_CELL_NUMBER_CLASS,
  DATA_TABLE_CHECKBOX_CLASS,
} from "@/lib/data-table-layout"

interface CategoryRowProps {
  category: Category
  level: number
  visibleColumnKeys: readonly string[]
  selectedIds: number[]
  onSelect: (id: number) => void
  onView: (item: Category) => void
  onEdit: (item: Category) => void
  onDelete: (item: Category) => void
  onAddSub: (parent: Category) => void
  canDelete: boolean
}

function CategoryRow({
  category,
  level,
  visibleColumnKeys,
  selectedIds,
  onSelect,
  onView,
  onEdit,
  onDelete,
  onAddSub,
  canDelete,
}: CategoryRowProps) {
  const [expanded, setExpanded] = useState(false)
  const hasChildren = category.children && category.children.length > 0
  const isSelected = selectedIds.includes(category.id)

  const handleToggle = () => {
    if (hasChildren) {
      setExpanded(!expanded)
    }
  }

  return (
    <>
      <TableRow className={cn("group h-14", isSelected ? "bg-slate-50" : "hover:bg-slate-50/50")}>
        <TableCell className="px-4 text-center">
          <Checkbox checked={isSelected} onCheckedChange={() => onSelect(category.id)} className={DATA_TABLE_CHECKBOX_CLASS} />
        </TableCell>
        {visibleColumnKeys.map((columnKey) => {
          if (columnKey === "categoryCode") {
            return (
              <TableCell key={columnKey} className="px-4">
                <div className="flex items-center gap-2" style={{ paddingLeft: `${level * 24}px` }}>
                  {hasChildren ? (
                    <button onClick={handleToggle} className="p-1 hover:bg-slate-200 rounded shrink-0">
                      {expanded ? <ChevronDown className="h-4 w-4 text-slate-500" /> : <ChevronRight className="h-4 w-4 text-slate-500" />}
                    </button>
                  ) : (
                    <span className="w-6 shrink-0" />
                  )}
                  <span className={TABLE_CELL_MONO_CLASS}>{category.categoryCode}</span>
                </div>
              </TableCell>
            )
          }
          if (columnKey === "categoryName") {
            return <TableCell key={columnKey} className={cn(TABLE_CELL_PRIMARY_CLASS, "px-4 truncate")}>{category.name}</TableCell>
          }
          if (columnKey === "productCount") {
            return <TableCell key={columnKey} className={cn(TABLE_CELL_NUMBER_CLASS, "px-4 text-center")}>{category.productCount ?? 0}</TableCell>
          }
          if (columnKey === "description") {
            return <TableCell key={columnKey} className={cn(TABLE_CELL_SECONDARY_CLASS, "px-4 max-w-[200px] truncate")}>{category.description || "-"}</TableCell>
          }
          return (
            <TableCell key={columnKey} className="px-4">
              <Badge className={`${category.status === "Active" ? "bg-green-50 text-green-700" : "bg-slate-100 text-slate-500"} text-xs font-normal border-none`}>
                {category.status === "Active" ? "Hoạt động" : "Ngưng"}
              </Badge>
            </TableCell>
          )
        })}
        <TableCell className={DATA_TABLE_ACTION_CELL_CLASS}>
          <div className="flex items-center justify-center gap-1">
            <Button variant="ghost" size="icon" onClick={() => onView(category)} title="Xem chi tiết" className="h-8 w-8 text-slate-400 hover:text-slate-900 hover:bg-slate-100">
              <Eye className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => onAddSub(category)} title="Thêm danh mục con" className="h-8 w-8 text-slate-400 hover:text-blue-600 hover:bg-blue-50">
              <PlusCircle className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => onEdit(category)} title="Chỉnh sửa" className="h-8 w-8 text-slate-400 hover:text-slate-900 hover:bg-slate-100">
              <Edit2 className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              disabled={!canDelete}
              onClick={() => {
                if (!canDelete) return
                onDelete(category)
              }}
              title={canDelete ? "Xóa" : "Chỉ Owner mới được xóa"}
              className="h-8 w-8 text-slate-400 hover:text-red-600 hover:bg-red-50 disabled:opacity-40 disabled:pointer-events-none"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </TableCell>
      </TableRow>
      {expanded && category.children?.map((child) => (
        <CategoryRow
          key={child.id}
          category={child}
          level={level + 1}
          visibleColumnKeys={visibleColumnKeys}
          selectedIds={selectedIds}
          onSelect={onSelect}
          onView={onView}
          onEdit={onEdit}
          onDelete={onDelete}
          onAddSub={onAddSub}
          canDelete={canDelete}
        />
      ))}
    </>
  )
}

function flattenCategories(categories: Category[]): Category[] {
  let result: Category[] = []
  categories.forEach((c) => {
    result.push(c)
    if (c.children) {
      result = result.concat(flattenCategories(c.children))
    }
  })
  return result
}

interface CategoryTableProps {
  data: Category[]
  visibleColumnKeys?: string[]
  selectedIds: number[]
  onSelect: (id: number) => void
  onSelectAll: (checked: boolean) => void
  onView: (item: Category) => void
  onEdit: (item: Category) => void
  onDelete: (item: Category) => void
  onAddSub: (parent: Category) => void
  canDelete: boolean
}

export function CategoryTable({
  data,
  visibleColumnKeys,
  selectedIds,
  onSelect,
  onSelectAll,
  onView,
  onEdit,
  onDelete,
  onAddSub,
  canDelete,
}: CategoryTableProps) {
  const defaultColumnKeys = ["categoryCode", "categoryName", "productCount", "description", "status"] as const
  const visibleSet = new Set(visibleColumnKeys ?? defaultColumnKeys)
  const orderedBusinessColumns = defaultColumnKeys.filter((key) => visibleSet.has(key))
  const flatData = flattenCategories(data)
  const allSelected = flatData.length > 0 && selectedIds.length === flatData.length
  const someSelected = selectedIds.length > 0 && selectedIds.length < flatData.length

  return (
    <Table className={DATA_TABLE_ROOT_CLASS}>
      <TableHeader className="sticky top-0 z-30 bg-slate-50 shadow-sm border-b">
        <TableRow className="hover:bg-transparent border-slate-200 border-b">
          <TableHead className={cn(CATEGORY_TABLE_COL.select, "px-4 text-center", TABLE_HEAD_CLASS)}>
            <Checkbox
              checked={allSelected ? true : someSelected ? "indeterminate" : false}
              onCheckedChange={(checked) => onSelectAll(checked as boolean)}
              className={DATA_TABLE_CHECKBOX_CLASS}
            />
          </TableHead>
          {orderedBusinessColumns.includes("categoryCode") && (
            <TableHead className={cn(CATEGORY_TABLE_COL.categoryCode, TABLE_HEAD_CLASS, "px-4")}>Mã phân loại</TableHead>
          )}
          {orderedBusinessColumns.includes("categoryName") && (
            <TableHead className={cn(CATEGORY_TABLE_COL.categoryName, TABLE_HEAD_CLASS, "px-4")}>Tên danh mục</TableHead>
          )}
          {orderedBusinessColumns.includes("productCount") && (
            <TableHead className={cn(CATEGORY_TABLE_COL.productCount, TABLE_HEAD_CLASS, "px-4 text-center")}>Số sản phẩm</TableHead>
          )}
          {orderedBusinessColumns.includes("description") && (
            <TableHead className={cn(CATEGORY_TABLE_COL.description, TABLE_HEAD_CLASS, "px-4")}>Mô tả</TableHead>
          )}
          {orderedBusinessColumns.includes("status") && (
            <TableHead className={cn(CATEGORY_TABLE_COL.status, TABLE_HEAD_CLASS, "px-4")}>Trạng thái</TableHead>
          )}
          <TableHead className={cn(DATA_TABLE_ACTION_HEAD_CLASS, TABLE_HEAD_CLASS)}>Thao tác</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody className="divide-y divide-slate-100">
        {data.length === 0 ? (
          <TableRow>
            <TableCell colSpan={7} className="h-24 text-center text-slate-500 text-sm">
              Không tìm thấy danh mục nào.
            </TableCell>
          </TableRow>
        ) : (
          data.map((item) => (
            <CategoryRow
              key={item.id}
              category={item}
              level={0}
              visibleColumnKeys={orderedBusinessColumns}
              selectedIds={selectedIds}
              onSelect={onSelect}
              onView={onView}
              onEdit={onEdit}
              onDelete={onDelete}
              onAddSub={onAddSub}
              canDelete={canDelete}
            />
          ))
        )}
      </TableBody>
    </Table>
  )
}
