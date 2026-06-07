import { useEffect, useMemo, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { usePageTitle } from "@/context/PageTitleContext"
import { useAuthStore } from "@/features/auth/store/useAuthStore"
import type { Category } from "../types"
import { CategoryToolbar } from "../components/CategoryToolbar"
import { CategoryTable } from "../components/CategoryTable"
import { CategoryForm } from "../components/CategoryForm"
import { CategoryDetailDialog } from "../components/CategoryDetailDialog"
import { ConfirmDialog } from "@/components/shared/ConfirmDialog"
import { toast } from "sonner"
import { ApiRequestError } from "@/lib/api/http"
import { DATA_TABLE_SCROLL_CLASS, DATA_TABLE_SHELL_CLASS } from "@/lib/data-table-layout"
import { toastApiError } from "@/lib/api/toastApiError"
import {
  deleteCategory,
  getCategoryById,
  getCategoryList,
  mapDetailDtoToCategory,
  mapNodeDtoToCategory,
  patchCategory,
  postCategory,
  type CategoryPatchBody,
  type GetCategoryListParams,
} from "../api/categoriesApi"
import { useTableColumnOrder } from "@/features/inventory/hooks/useTableVisibleColumns"

const SEARCH_DEBOUNCE_MS = 400

function flattenCategories(categories: Category[]): Category[] {
  let result: Category[] = []
  categories.forEach((c) => {
    result.push(c)
    if (c.children?.length) {
      result = result.concat(flattenCategories(c.children))
    }
  })
  return result
}

/**
 * Toast theo envelope Task032: **409** / **400** (message + `details` khi không map form).
 * **400** + `details` có key: `CategoryForm` gọi `setError` — không toast (tránh trùng).
 */
function toastCategoryMutationEnvelope(e: unknown) {
  if (!(e instanceof ApiRequestError)) {
    toastApiError(e)
    return
  }
  const { status, body } = e
  const detailKeys = body.details ? Object.keys(body.details) : []
  if (status === 400 && detailKeys.length > 0) {
    return
  }
  if (status === 409) {
    const parts = [body.message ?? e.message]
    if (detailKeys.length > 0) {
      parts.push(
        ...detailKeys.map((k) => {
          const v = body.details![k]
          return v ? `${k}: ${v}` : k
        }),
      )
    }
    toast.error(parts.filter(Boolean).join(" — "))
    return
  }
  if (status === 400 && detailKeys.length === 0) {
    toast.error(body.message ?? e.message)
    return
  }
  toastApiError(e)
}

type CategoryFormData = {
  name: string
  categoryCode: string
  parentId?: number
  description?: string
  sortOrder: number
  status: "Active" | "Inactive"
}

function buildPatchBody(
  data: CategoryFormData,
  original: Category,
): CategoryPatchBody | null | "forbidden_root" {
  const body: CategoryPatchBody = {}
  if (data.name.trim() !== original.name.trim()) body.name = data.name.trim()
  if (data.categoryCode.trim() !== original.categoryCode.trim()) {
    body.categoryCode = data.categoryCode.trim()
  }
  const descNew = (data.description ?? "").trim()
  const descOld = (original.description ?? "").trim()
  if (descNew !== descOld) {
    body.description = descNew === "" ? "" : descNew
  }
  if (data.sortOrder !== original.sortOrder) body.sortOrder = data.sortOrder
  if (data.status !== original.status) body.status = data.status

  const newParent = data.parentId && data.parentId > 0 ? data.parentId : null
  const oldParent = original.parentId ?? null
  if (newParent !== oldParent) {
    if (oldParent != null && newParent == null) {
      return "forbidden_root"
    }
    if (newParent != null) body.parentId = newParent
  }

  if (Object.keys(body).length === 0) return null
  return body
}

export function CategoriesPage() {
  const queryClient = useQueryClient()
  const { setTitle } = usePageTitle()
  const isOwner = useAuthStore((s) => s.user?.role === "Owner")

  const [search, setSearch] = useState("")
  const visibleColumnKeys = useTableColumnOrder("product_categories", [
    "categoryCode",
    "categoryName",
    "productCount",
    "description",
    "status",
  ])
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [selectedIds, setSelectedIds] = useState<number[]>([])

  const [deleteTarget, setDeleteTarget] = useState<Category | null>(null)
  const [isDeletingBulk, setIsDeletingBulk] = useState(false)

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingCategory, setEditingCategory] = useState<Category | undefined>()
  const [viewingCategory, setViewingCategory] = useState<Category | null>(null)

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), SEARCH_DEBOUNCE_MS)
    return () => clearTimeout(t)
  }, [search])

  useEffect(() => {
    setTitle("Danh mục sản phẩm")
  }, [setTitle])

  const listQueryKey = useMemo(
    () => ["product-management", "categories", "list", debouncedSearch, statusFilter] as const,
    [debouncedSearch, statusFilter],
  )

  const listParams: GetCategoryListParams = useMemo(
    () => ({
      format: "tree",
      search: debouncedSearch.trim() || undefined,
      status: statusFilter as GetCategoryListParams["status"],
    }),
    [debouncedSearch, statusFilter],
  )

  const {
    data: listData,
    isPending,
    isError,
    error,
  } = useQuery({
    queryKey: listQueryKey,
    queryFn: () => getCategoryList(listParams),
  })

  const categories: Category[] = useMemo(
    () => (listData?.items ?? []).map(mapNodeDtoToCategory),
    [listData],
  )
  const flattenedCategories = useMemo(() => flattenCategories(categories), [categories])

  const detailQuery = useQuery({
    queryKey: ["product-management", "categories", "detail", viewingCategory?.id] as const,
    queryFn: () => getCategoryById(viewingCategory!.id),
    enabled: Boolean(viewingCategory?.id),
  })

  const detailCategory: Category | null = useMemo(() => {
    if (!viewingCategory) return null
    if (detailQuery.data) return mapDetailDtoToCategory(detailQuery.data)
    return viewingCategory
  }, [viewingCategory, detailQuery.data])

  /** List (`…/list/…`) + detail (`…/detail/…`) — prefix `["product-management","categories"]`. */
  const invalidateCategories = () =>
    queryClient.invalidateQueries({ queryKey: ["product-management", "categories"] })

  const createMutation = useMutation({
    mutationFn: postCategory,
    onSuccess: async () => {
      await invalidateCategories()
      toast.success("Thêm danh mục thành công")
    },
    onError: toastCategoryMutationEnvelope,
  })

  const patchMutation = useMutation({
    mutationFn: ({ id, body }: { id: number; body: CategoryPatchBody }) => patchCategory(id, body),
    onSuccess: async () => {
      await invalidateCategories()
      toast.success("Cập nhật danh mục thành công")
    },
    onError: toastCategoryMutationEnvelope,
  })

  const deleteMutation = useMutation({
    mutationFn: ({ id }: { id: number; name: string }) => deleteCategory(id),
    onSuccess: async (_data, { id, name }) => {
      await invalidateCategories()
      setSelectedIds((prev) => prev.filter((i) => i !== id))
      setViewingCategory((v) => (v?.id === id ? null : v))
      setDeleteTarget(null)
      toast.success(`Đã xóa danh mục: ${name}`)
    },
    onError: toastCategoryMutationEnvelope,
  })

  const handleSelect = (id: number) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]))
  }

  const handleSelectAll = (checked: boolean) => {
    setSelectedIds(checked ? flattenedCategories.map((c) => c.id) : [])
  }

  const handleToolbarAction = (action: string) => {
    switch (action) {
      case "delete":
        setIsDeletingBulk(true)
        break
      case "create":
        setEditingCategory(undefined)
        setIsFormOpen(true)
        break
    }
  }

  const handleView = (item: Category) => {
    setViewingCategory(item)
  }

  const handleEdit = (item: Category) => {
    setEditingCategory(item)
    setIsFormOpen(true)
  }

  const handleAddSub = (parent: Category) => {
    setEditingCategory({
      parentId: parent.id,
      parentName: parent.name,
      categoryCode: `SUB-${parent.categoryCode}`,
      status: "Active",
      sortOrder: 0,
      name: "",
    } as Category)
    setIsFormOpen(true)
  }

  const handleDelete = (item: Category) => {
    setDeleteTarget(item)
  }

  const confirmDelete = () => {
    if (!deleteTarget) return
    void deleteMutation.mutateAsync({ id: deleteTarget.id, name: deleteTarget.name })
  }

  const confirmBulkDelete = async () => {
    const ids = [...selectedIds]
    setIsDeletingBulk(false)
    let ok = 0
    for (const id of ids) {
      try {
        await deleteCategory(id)
        ok++
        setViewingCategory((v) => (v?.id === id ? null : v))
      } catch (e) {
        toastCategoryMutationEnvelope(e)
      }
    }
    await invalidateCategories()
    if (ok > 0) {
      toast.success(`Đã xóa ${ok} danh mục`)
    }
    setSelectedIds([])
  }

  const handleFormSubmit = async (data: CategoryFormData) => {
    if (editingCategory?.id) {
      const body = buildPatchBody(data, editingCategory)
      if (body === "forbidden_root") {
        toast.error("Không thể đưa danh mục về gốc qua cập nhật — chỉ đổi sang danh mục cha khác.")
        throw new Error("forbidden_root")
      }
      if (body === null) {
        toast.info("Không có thay đổi để lưu.")
        throw new Error("no_changes")
      }
      await patchMutation.mutateAsync({ id: editingCategory.id, body })
      return
    }
    await createMutation.mutateAsync({
      categoryCode: data.categoryCode,
      name: data.name,
      description: data.description,
      parentId: data.parentId && data.parentId > 0 ? data.parentId : null,
      sortOrder: data.sortOrder,
      status: data.status,
    })
  }

  return (
    <div className="p-4 md:p-6 lg:p-8 flex flex-col h-full min-h-0 gap-4 md:gap-5 overflow-hidden">
      <div className="shrink-0">
        <h1 className="text-xl md:text-2xl font-semibold text-slate-900 tracking-tight">Danh mục sản phẩm</h1>
        <p className="text-sm text-slate-500 mt-1">Phân loại sản phẩm theo cấu trúc cây phân cấp</p>
      </div>

      <CategoryToolbar
        searchStr={search}
        onSearch={setSearch}
        statusFilter={statusFilter}
        onStatusChange={setStatusFilter}
        selectedIds={selectedIds}
        onAction={handleToolbarAction}
        canBulkDelete={isOwner}
      />

      <div className={DATA_TABLE_SHELL_CLASS}>
        {isPending && !listData ? (
          <div className="p-8 text-center text-slate-500 flex-1" role="status">
            Đang tải danh sách…
          </div>
        ) : isError && !listData ? (
          <div className="p-8 text-center text-red-600 flex-1" role="alert">
            {error instanceof ApiRequestError ? error.body.message : "Không tải được danh mục."}
          </div>
          ) : (
          <>
            <div className={DATA_TABLE_SCROLL_CLASS}>
              <CategoryTable
                data={categories}
                visibleColumnKeys={visibleColumnKeys}
                selectedIds={selectedIds}
                onSelect={handleSelect}
                onSelectAll={handleSelectAll}
                onView={handleView}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onAddSub={handleAddSub}
                canDelete={isOwner}
              />
            </div>
            <div className="flex items-center justify-between flex-wrap gap-2 px-3 py-2 border-t border-slate-200 bg-slate-50/80 text-sm text-slate-600 min-h-11 shrink-0">
              <span>Đang hiển thị {flattenedCategories.length} / {flattenedCategories.length} danh mục</span>
            </div>
          </>
        )}
      </div>

      <CategoryDetailDialog
        category={detailCategory}
        isOpen={!!viewingCategory}
        onClose={() => setViewingCategory(null)}
        detailLoading={Boolean(viewingCategory) && detailQuery.isFetching}
        canDelete={isOwner}
        onRequestDelete={
          isOwner && detailCategory
            ? () => {
                setDeleteTarget(detailCategory)
                setViewingCategory(null)
              }
            : undefined
        }
      />

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        onConfirm={confirmDelete}
        title="Xác nhận xóa"
        confirmText="Xóa"
        description={`Danh mục sẽ được xóa và không còn trong danh sách hoạt động. Xóa "${deleteTarget?.name}"?`}
      />

      <ConfirmDialog
        open={isDeletingBulk}
        onOpenChange={setIsDeletingBulk}
        onConfirm={confirmBulkDelete}
        title="Xác nhận xóa nhiều"
        confirmText="Xóa"
        description={`Xóa ${selectedIds.length} danh mục đã chọn? Một số mục có thể bị từ chối nếu còn ràng buộc hoặc không đủ quyền.`}
      />

      <CategoryForm
        open={isFormOpen}
        onOpenChange={setIsFormOpen}
        category={editingCategory}
        allCategories={categories}
        onSubmit={handleFormSubmit}
      />
    </div>
  )
}
