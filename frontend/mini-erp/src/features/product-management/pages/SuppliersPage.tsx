import { useEffect, useMemo, useState, useRef } from "react"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { usePageTitle } from "@/context/PageTitleContext"
import { useAuthStore } from "@/features/auth/store/useAuthStore"
import type { Supplier } from "../types"
import { SupplierToolbar } from "../components/SupplierToolbar"
import { SupplierTable } from "../components/SupplierTable"
import { SupplierDetailDialog } from "../components/SupplierDetailDialog"
import { SupplierForm, SupplierFormSubmitAborted, type SupplierFormData } from "../components/SupplierForm"
import { ConfirmDialog } from "@/components/shared/ConfirmDialog"
import { toast } from "sonner"
import { ApiRequestError } from "@/lib/api/http"
import {
  buildSupplierCreateBody,
  buildSupplierPatchBody,
  deleteSupplier,
  postSuppliersBulkDelete,
  getSupplierById,
  getSupplierList,
  mapSupplierDetailDtoToSupplier,
  mapSupplierListItemDtoToSupplier,
  patchSupplier,
  postSupplier,
  supplierEditSnapshotFromDetail,
  supplierEditSnapshotFromListRow,
  SUPPLIER_LIST_SORT_LABEL_VI,
  SUPPLIER_LIST_SORT_WHITELIST,
  type GetSupplierListParams,
  type SupplierListSort,
} from "../api/suppliersApi"
import { useTableColumnOrder } from "@/features/inventory/hooks/useTableVisibleColumns"

const SEARCH_DEBOUNCE_MS = 400
const PAGE_SIZE = 20

function errToast(e: unknown) {
  if (e instanceof ApiRequestError) {
    toast.error(e.body?.message ?? e.message)
  } else {
    toast.error(e instanceof Error ? e.message : "Đã xảy ra lỗi")
  }
}

function toastSupplierDeleteError(e: ApiRequestError) {
  const d = e.body?.details
  const reason = d?.reason
  const base = e.body?.message ?? e.message
  const failedId = d?.failedId
  const idHint =
    failedId != null && String(failedId).length > 0 ? ` — failedId: ${String(failedId)}` : ""
  if (reason === "HAS_RECEIPTS") {
    toast.error("Không thể xóa: nhà cung cấp (đã có phiếu nhập kho)." + idHint + (base ? ` — ${base}` : ""))
    return
  }
  if (reason === "HAS_PARTNER_DEBTS") {
    toast.error("Không thể xóa: còn công nợ đối tác (PartnerDebts)." + idHint + (base ? ` — ${base}` : ""))
    return
  }
  if (reason === "NOT_FOUND") {
    toast.error("Không thể xóa toàn bộ: có id không tồn tại." + idHint + (base ? ` — ${base}` : ""))
    return
  }
  toast.error(base + idHint)
}

export function SuppliersPage() {
  const { setTitle } = usePageTitle()
  const queryClient = useQueryClient()
  const isOwner = useAuthStore((s) => s.user?.role === "Owner")
  const scrollRootRef = useRef<HTMLDivElement>(null)
  const loadMoreSentinelRef = useRef<HTMLDivElement>(null)

  const [search, setSearch] = useState("")
  const visibleColumnKeys = useTableColumnOrder("product_suppliers", [
    "supplierCode",
    "supplierName",
    "contactName",
    "email",
    "address",
    "status",
  ])
  const debouncedSearch = useDebouncedValue(search, SEARCH_DEBOUNCE_MS)
  const [statusFilter, setStatusFilter] = useState("all")
  const [sort, setSort] = useState<SupplierListSort>("updatedAt:desc")
  const [selectedIds, setSelectedIds] = useState<number[]>([])

  const [deleteTarget, setDeleteTarget] = useState<Supplier | null>(null)
  const [isDeletingBulk, setIsDeletingBulk] = useState(false)

  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingSupplier, setEditingSupplier] = useState<Supplier | undefined>()

  useEffect(() => {
    setTitle("Nhà cung cấp")
  }, [setTitle])

  useEffect(() => {
    setSelectedIds([])
  }, [debouncedSearch, statusFilter, sort])

  const listQueryKey = useMemo(
    () =>
      [
        "product-management",
        "suppliers",
        "list",
        debouncedSearch,
        statusFilter,
        sort,
        PAGE_SIZE,
      ] as const,
    [debouncedSearch, statusFilter, sort],
  )

  const {
    data: listInfinite,
    isPending,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: listQueryKey,
    initialPageParam: 1,
    queryFn: ({ pageParam }) =>
      getSupplierList({
        search: debouncedSearch.trim() || undefined,
        status: statusFilter as GetSupplierListParams["status"],
        page: pageParam,
        limit: PAGE_SIZE,
        sort,
      }),
    getNextPageParam: (lastPage) => {
      if (lastPage.items.length < lastPage.limit) {
        return undefined
      }
      if (lastPage.page * lastPage.limit >= lastPage.total) {
        return undefined
      }
      return lastPage.page + 1
    },
  })

  useEffect(() => {
    const root = scrollRootRef.current
    const sentinel = loadMoreSentinelRef.current
    if (!root || !sentinel) {
      return
    }
    const observer = new IntersectionObserver(
      (entries) => {
        const e = entries[0]
        if (e?.isIntersecting && hasNextPage && !isFetchingNextPage) {
          void fetchNextPage()
        }
      },
      { root, rootMargin: "80px", threshold: 0 },
    )
    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [fetchNextPage, hasNextPage, isFetchingNextPage, listInfinite?.pages])

  const selectedSupplierId = selectedSupplier?.id
  const {
    data: supplierDetailDto,
    isPending: isSupplierDetailPending,
    isError: isSupplierDetailError,
    error: supplierDetailError,
  } = useQuery({
    queryKey: ["product-management", "suppliers", "detail", selectedSupplierId ?? 0] as const,
    queryFn: () => getSupplierById(selectedSupplierId!),
    enabled: isDetailOpen && selectedSupplierId != null && selectedSupplierId > 0,
  })

  const displaySupplier: Supplier | null = useMemo(() => {
    if (supplierDetailDto) {
      return mapSupplierDetailDtoToSupplier(supplierDetailDto)
    }
    return selectedSupplier
  }, [supplierDetailDto, selectedSupplier])

  useEffect(() => {
    if (!isSupplierDetailError || !isDetailOpen) return
    errToast(supplierDetailError)
  }, [isSupplierDetailError, supplierDetailError, isDetailOpen])

  const createSupplierMutation = useMutation({
    mutationFn: (data: SupplierFormData) => postSupplier(buildSupplierCreateBody(data)),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["product-management", "suppliers", "list"] })
      toast.success("Đã tạo nhà cung cấp")
    },
  })

  const patchSupplierMutation = useMutation({
    mutationFn: (args: { id: number; body: Record<string, unknown> }) => patchSupplier(args.id, args.body),
    onSuccess: (_d, v) => {
      void queryClient.invalidateQueries({ queryKey: ["product-management", "suppliers", "list"] })
      void queryClient.invalidateQueries({ queryKey: ["product-management", "suppliers", "detail", v.id] })
      toast.success("Đã cập nhật nhà cung cấp")
    },
  })

  const deleteSupplierMutation = useMutation({
    mutationFn: (id: number) => deleteSupplier(id),
    onSuccess: (_data, deletedId) => {
      void queryClient.invalidateQueries({ queryKey: ["product-management", "suppliers", "list"] })
      void queryClient.invalidateQueries({ queryKey: ["product-management", "suppliers", "detail", deletedId] })
      setSelectedIds((prev) => prev.filter((i) => i !== deletedId))
      setDeleteTarget(null)
      setSelectedSupplier((p) => {
        if (p?.id === deletedId) {
          setIsDetailOpen(false)
          return null
        }
        return p
      })
      setEditingSupplier((p) => {
        if (p?.id === deletedId) {
          setIsFormOpen(false)
          return undefined
        }
        return p
      })
      toast.success("Đã xóa nhà cung cấp")
    },
    onError: (e) => {
      if (e instanceof ApiRequestError) {
        if (e.status === 409) {
          toastSupplierDeleteError(e)
          return
        }
        if (e.status === 403) {
          toast.error(e.body?.message ?? e.message)
          return
        }
      }
      errToast(e)
    },
  })

  const bulkDeleteSuppliersMutation = useMutation({
    mutationFn: (ids: number[]) => postSuppliersBulkDelete(ids),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ["product-management", "suppliers", "list"] })
      for (const id of data.deletedIds) {
        void queryClient.invalidateQueries({ queryKey: ["product-management", "suppliers", "detail", id] })
      }
      setSelectedIds([])
      setIsDeletingBulk(false)
      setSelectedSupplier((p) => {
        if (p && data.deletedIds.includes(p.id)) {
          setIsDetailOpen(false)
          return null
        }
        return p
      })
      setEditingSupplier((p) => {
        if (p && data.deletedIds.includes(p.id)) {
          setIsFormOpen(false)
          return undefined
        }
        return p
      })
      toast.success(
        data.deletedCount > 0 ? `Đã xóa ${data.deletedCount} nhà cung cấp` : "Đã xóa nhà cung cấp",
      )
    },
    onError: (e) => {
      setIsDeletingBulk(false)
      if (e instanceof ApiRequestError) {
        if (e.status === 409) {
          toastSupplierDeleteError(e)
          return
        }
        if (e.status === 403) {
          toast.error(e.body?.message ?? e.message)
          return
        }
        if (e.status === 400) {
          errToast(e)
          return
        }
      }
      errToast(e)
    },
  })

  const editingFormId = isFormOpen && editingSupplier ? editingSupplier.id : null
  const {
    data: editFormDetailDto,
    isPending: isEditFormDetailLoading,
  } = useQuery({
    queryKey: ["product-management", "suppliers", "detail", editingFormId ?? 0] as const,
    queryFn: () => getSupplierById(editingFormId!),
    enabled: isFormOpen && editingFormId != null && editingFormId > 0,
  })

  const supplierForForm: Supplier | undefined = useMemo(() => {
    if (!isFormOpen) return undefined
    if (editingSupplier && editFormDetailDto && editFormDetailDto.id === editingSupplier.id) {
      return mapSupplierDetailDtoToSupplier(editFormDetailDto)
    }
    return editingSupplier
  }, [isFormOpen, editingSupplier, editFormDetailDto])

  const suppliers: Supplier[] = useMemo(
    () =>
      listInfinite?.pages
        ? listInfinite.pages.flatMap((p) => p.items).map(mapSupplierListItemDtoToSupplier)
        : [],
    [listInfinite],
  )

  const total = listInfinite?.pages[0]?.total ?? 0

  useEffect(() => {
    if (!isError) return
    errToast(error)
  }, [isError, error])

  const handleSelect = (id: number) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]))
  }

  const handleSelectAll = (checked: boolean) => {
    setSelectedIds(checked ? suppliers.map((s) => s.id) : [])
  }

  const handleToolbarAction = (action: string) => {
    switch (action) {
      case "edit":
        toast.info(`Chỉnh sửa ${selectedIds.length} nhà cung cấp`)
        break
      case "delete":
        if (!isOwner) {
          toast.error("Chỉ tài khoản Owner mới được xóa hàng loạt nhà cung cấp.")
          return
        }
        setIsDeletingBulk(true)
        break
      case "create":
        setEditingSupplier(undefined)
        setIsFormOpen(true)
        break
    }
  }

  const handleView = (item: Supplier) => {
    setSelectedSupplier(item)
    setIsDetailOpen(true)
  }

  const handleEdit = (item: Supplier) => {
    setEditingSupplier(item)
    setIsFormOpen(true)
  }

  const handleDelete = (item: Supplier) => {
    if (!isOwner) {
      toast.error("Chỉ tài khoản Owner mới được xóa nhà cung cấp.")
      return
    }
    setDeleteTarget(item)
  }

  const confirmDelete = () => {
    const target = deleteTarget
    if (!target) return
    void deleteSupplierMutation.mutateAsync(target.id)
  }

  const confirmBulkDelete = () => {
    if (!isOwner) {
      toast.error("Chỉ tài khoản Owner mới được xóa hàng loạt nhà cung cấp.")
      setIsDeletingBulk(false)
      return
    }
    const ids = [...new Set(selectedIds)]
    if (ids.length === 0) {
      setIsDeletingBulk(false)
      return
    }
    void bulkDeleteSuppliersMutation.mutateAsync(ids)
  }

  return (
    <div className="p-4 md:p-6 lg:p-8 flex flex-col h-full min-h-0 gap-4 md:gap-5 overflow-hidden">
      <div className="shrink-0">
        <h1 className="text-xl md:text-2xl font-semibold text-slate-900 tracking-tight">Nhà cung cấp</h1>
        <p className="text-sm text-slate-500 mt-1">Quản lý thông tin nhà cung cấp hàng hóa</p>
      </div>

      <SupplierToolbar
        searchStr={search}
        onSearch={setSearch}
        statusFilter={statusFilter}
        onStatusChange={setStatusFilter}
        selectedIds={selectedIds}
        onAction={handleToolbarAction}
        canBulkDelete={isOwner}
      />

      <div className="flex flex-col sm:flex-row sm:items-center gap-3 shrink-0 text-sm">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-slate-500 whitespace-nowrap">Sắp xếp</span>
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as SupplierListSort)}
            className="h-9 px-2 border border-slate-200 bg-white rounded-md text-slate-900 min-w-[200px]"
          >
            {SUPPLIER_LIST_SORT_WHITELIST.map((s) => (
              <option key={s} value={s}>
                {SUPPLIER_LIST_SORT_LABEL_VI[s]}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex-1 flex flex-col min-h-0 bg-white border border-slate-200/60 rounded-xl overflow-hidden shadow-md">
        {isPending && !listInfinite ? (
          <div className="p-8 text-center text-slate-500 flex-1" role="status">
            Đang tải danh sách…
          </div>
        ) : isError && !listInfinite ? (
          <div className="p-8 text-center text-red-600 flex-1" role="alert">
            Không tải được danh sách nhà cung cấp.
          </div>
        ) : null}
        {!isError && listInfinite ? (
          <>
            <div
              ref={scrollRootRef}
              className="flex-1 overflow-y-auto relative scroll-smooth [scrollbar-gutter:stable] min-h-0"
            >
              <SupplierTable
                data={suppliers}
                visibleColumnKeys={visibleColumnKeys}
                selectedIds={selectedIds}
                onSelect={handleSelect}
                onSelectAll={handleSelectAll}
                onView={handleView}
                onEdit={handleEdit}
                onDelete={handleDelete}
                canDelete={isOwner}
              />
              <div ref={loadMoreSentinelRef} className="h-1 w-full shrink-0" aria-hidden />
            </div>
            <div className="flex items-center justify-between flex-wrap gap-2 px-3 py-2 border-t border-slate-200 bg-slate-50/80 text-sm text-slate-600 min-h-11 shrink-0">
              <span>
                Đang hiển thị {suppliers.length} / {total} nhà cung cấp
              </span>
              {isFetchingNextPage ? <span className="text-slate-500">Đang tải thêm…</span> : null}
              {hasNextPage && !isFetchingNextPage ? (
                <span className="text-slate-400 text-xs hidden sm:inline">Cuộn xuống để tải thêm</span>
              ) : null}
            </div>
          </>
        ) : null}
      </div>

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        onConfirm={confirmDelete}
        title="Xác nhận xóa"
        description={`Bạn có chắc chắn muốn xóa nhà cung cấp "${deleteTarget?.name}"? Hành động này không thể hoàn tác.`}
      />

      <ConfirmDialog
        open={isDeletingBulk}
        onOpenChange={setIsDeletingBulk}
        onConfirm={confirmBulkDelete}
        title="Xác nhận xóa nhiều"
        description={`Bạn có chắc chắn muốn xóa ${selectedIds.length} nhà cung cấp đã chọn?`}
      />

      <SupplierDetailDialog
        supplier={displaySupplier}
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        isDetailLoading={isDetailOpen && Boolean(selectedSupplier) && isSupplierDetailPending}
        isDetailError={isDetailOpen && isSupplierDetailError}
      />

      <SupplierForm
        key={!isFormOpen ? "closed" : editingSupplier ? `edit-${editingSupplier.id}-${editFormDetailDto?.updatedAt ?? "row"}` : "create"}
        open={isFormOpen}
        onOpenChange={(open) => {
          setIsFormOpen(open)
          if (!open) {
            setEditingSupplier(undefined)
          }
        }}
        supplier={supplierForForm}
        onSubmit={async (data: SupplierFormData) => {
          if (editingSupplier) {
            if (isEditFormDetailLoading) {
              toast.error("Vui lòng đợi tải xong chi tiết nhà cung cấp.")
              throw new SupplierFormSubmitAborted()
            }
            const snap =
              editFormDetailDto && editFormDetailDto.id === editingSupplier.id
                ? supplierEditSnapshotFromDetail(editFormDetailDto)
                : supplierEditSnapshotFromListRow(editingSupplier)
            const body = buildSupplierPatchBody(snap, data)
            if (Object.keys(body).length === 0) {
              toast.info("Không có thay đổi để lưu")
              throw new SupplierFormSubmitAborted()
            }
            await patchSupplierMutation.mutateAsync({ id: editingSupplier.id, body })
            return
          }
          await createSupplierMutation.mutateAsync(data)
        }}
      />
    </div>
  )
}
