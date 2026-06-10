import { useEffect, useMemo, useState, useRef } from "react"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { usePageTitle } from "@/context/PageTitleContext"
import { useAuthStore } from "@/features/auth/store/useAuthStore"
import type { Customer } from "../types"
import { CustomerToolbar } from "../components/CustomerToolbar"
import { CustomerTable } from "../components/CustomerTable"
import { CustomerDetailDialog } from "../components/CustomerDetailDialog"
import {
  CustomerForm,
  CustomerFormSubmitAborted,
  type CustomerFormData,
} from "../components/CustomerForm"
import { ConfirmDialog } from "@/components/shared/ConfirmDialog"
import { toast } from "sonner"
import { ApiRequestError } from "@/lib/api/http"
import {
  buildCustomerCreateBody,
  buildCustomerPatchBody,
  CUSTOMER_LIST_QUERY_KEY,
  CUSTOMER_LIST_SORT_LABEL_VI,
  CUSTOMER_LIST_SORT_WHITELIST,
  customerEditSnapshotFromDetail,
  customerEditSnapshotFromListRow,
  deleteCustomer,
  getCustomerById,
  getCustomerList,
  mapCustomerDetailDtoToCustomer,
  mapCustomerListItemDtoToCustomer,
  patchCustomer,
  postCustomer,
  postCustomersBulkDelete,
  type CustomerListSort,
  type GetCustomerListParams,
} from "../api/customersApi"
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

function toastCustomerDeleteError(e: ApiRequestError) {
  const d = e.body?.details
  const reason = d?.reason
  const base = e.body?.message ?? e.message
  const failedId = d?.failedId
  const idHint = failedId != null && String(failedId).length > 0 ? ` — failedId: ${String(failedId)}` : ""
  if (reason === "HAS_OPEN_SALES_ORDERS") {
    toast.error("Không thể xóa: khách hàng còn đơn hàng chưa hoàn tất." + idHint + (base ? ` — ${base}` : ""))
    return
  }
  if (reason === "HAS_SALES_ORDERS") {
    toast.error("Không thể xóa: khách hàng đã có đơn bán hàng." + idHint + (base ? ` — ${base}` : ""))
    return
  }
  if (reason === "HAS_PARTNER_DEBTS") {
    toast.error("Không thể xóa: khách hàng còn công nợ đối tác." + idHint + (base ? ` — ${base}` : ""))
    return
  }
  if (reason === "NOT_FOUND") {
    toast.error("Không thể xóa toàn bộ: có id không tồn tại." + idHint + (base ? ` — ${base}` : ""))
    return
  }
  toast.error(base + idHint)
}

export function CustomersPage() {
  const { setTitle } = usePageTitle()
  const queryClient = useQueryClient()
  const isStaff = useAuthStore((s) => s.user?.role === "Staff")
  const canEditLoyaltyPoints = !isStaff
  const scrollRootRef = useRef<HTMLDivElement>(null)
  const loadMoreSentinelRef = useRef<HTMLDivElement>(null)

  const [search, setSearch] = useState("")
  const visibleColumnKeys = useTableColumnOrder("product_customers", [
    "customerCode",
    "customerName",
    "phone",
    "email",
    "orderCount",
    "status",
  ])
  const debouncedSearch = useDebouncedValue(search, SEARCH_DEBOUNCE_MS)
  const [statusFilter, setStatusFilter] = useState("all")
  const [sort, setSort] = useState<CustomerListSort>("updatedAt:desc")
  const [selectedIds, setSelectedIds] = useState<number[]>([])

  const [deleteTarget, setDeleteTarget] = useState<Customer | null>(null)
  const [isDeletingBulk, setIsDeletingBulk] = useState(false)

  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingCustomer, setEditingCustomer] = useState<Customer | undefined>()

  const selectedCustomerId = selectedCustomer?.id
  const {
    data: customerDetailDto,
    isPending: isCustomerDetailPending,
    isError: isCustomerDetailError,
    error: customerDetailError,
  } = useQuery({
    queryKey: ["product-management", "customers", "detail", selectedCustomerId ?? 0] as const,
    queryFn: () => getCustomerById(selectedCustomerId!),
    enabled: isDetailOpen && selectedCustomerId != null && selectedCustomerId > 0,
  })

  const displayCustomer: Customer | null = useMemo(() => {
    if (customerDetailDto) {
      return mapCustomerDetailDtoToCustomer(customerDetailDto)
    }
    return selectedCustomer
  }, [customerDetailDto, selectedCustomer])

  useEffect(() => {
    if (!isCustomerDetailError || !isDetailOpen) return
    errToast(customerDetailError)
  }, [isCustomerDetailError, customerDetailError, isDetailOpen])

  useEffect(() => {
    setTitle("Khách hàng")
  }, [setTitle])

  const listFilters: Omit<GetCustomerListParams, "page"> = useMemo(
    () => ({
      search: debouncedSearch.trim() || undefined,
      status: statusFilter as GetCustomerListParams["status"],
      limit: PAGE_SIZE,
      sort,
    }),
    [debouncedSearch, statusFilter, sort],
  )

  const infiniteListQueryKey = useMemo(
    () => [...CUSTOMER_LIST_QUERY_KEY, "infinite", listFilters] as const,
    [listFilters],
  )

  const {
    data: listInfinite,
    isPending: isListPending,
    isError: isListError,
    error: listError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: infiniteListQueryKey,
    initialPageParam: 1,
    queryFn: ({ pageParam }) =>
      getCustomerList({
        ...listFilters,
        page: pageParam,
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

  const customers: Customer[] = useMemo(
    () =>
      listInfinite?.pages
        ? listInfinite.pages.flatMap((p) => p.items).map(mapCustomerListItemDtoToCustomer)
        : [],
    [listInfinite],
  )

  const editingFormId = isFormOpen && editingCustomer ? editingCustomer.id : null
  const {
    data: editFormDetailDto,
    isPending: isEditFormDetailLoading,
  } = useQuery({
    queryKey: ["product-management", "customers", "detail", editingFormId ?? 0] as const,
    queryFn: () => getCustomerById(editingFormId!),
    enabled: isFormOpen && editingFormId != null && editingFormId > 0,
  })

  const customerForForm: Customer | undefined = useMemo(() => {
    if (!isFormOpen) {
      return undefined
    }
    if (editingCustomer && editFormDetailDto && editFormDetailDto.id === editingCustomer.id) {
      return mapCustomerDetailDtoToCustomer(editFormDetailDto)
    }
    return editingCustomer
  }, [isFormOpen, editingCustomer, editFormDetailDto])

  const total = listInfinite?.pages[0]?.total ?? 0

  useEffect(() => {
    if (!isListError) return
    errToast(listError)
  }, [isListError, listError])

  useEffect(() => {
    setSelectedIds([])
  }, [debouncedSearch, statusFilter, sort])

  const deleteCustomerMutation = useMutation({
    mutationFn: (id: number) => deleteCustomer(id),
    onSuccess: (_data, deletedId) => {
      void queryClient.invalidateQueries({ queryKey: [...CUSTOMER_LIST_QUERY_KEY] })
      void queryClient.invalidateQueries({ queryKey: ["product-management", "customers", "detail", deletedId] })
      setSelectedIds((prev) => prev.filter((i) => i !== deletedId))
      setDeleteTarget(null)
      setSelectedCustomer((p) => {
        if (p?.id === deletedId) {
          setIsDetailOpen(false)
          return null
        }
        return p
      })
      setEditingCustomer((p) => {
        if (p?.id === deletedId) {
          setIsFormOpen(false)
          return undefined
        }
        return p
      })
      toast.success("Đã xóa khách hàng")
    },
    onError: (e) => {
      if (e instanceof ApiRequestError) {
        if (e.status === 409) {
          toastCustomerDeleteError(e)
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

  const bulkDeleteCustomersMutation = useMutation({
    mutationFn: (ids: number[]) => postCustomersBulkDelete(ids),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: [...CUSTOMER_LIST_QUERY_KEY] })
      for (const id of data.deletedIds) {
        void queryClient.invalidateQueries({ queryKey: ["product-management", "customers", "detail", id] })
      }
      setSelectedIds([])
      setIsDeletingBulk(false)
      setSelectedCustomer((p) => {
        if (p && data.deletedIds.includes(p.id)) { setIsDetailOpen(false); return null }
        return p
      })
      setEditingCustomer((p) => {
        if (p && data.deletedIds.includes(p.id)) { setIsFormOpen(false); return undefined }
        return p
      })
      toast.success(data.deletedCount > 0 ? `Đã xóa ${data.deletedCount} khách hàng` : "Đã xóa khách hàng")
    },
    onError: (e) => {
      setIsDeletingBulk(false)
      if (e instanceof ApiRequestError) {
        if (e.status === 409) { toastCustomerDeleteError(e); return }
        if (e.status === 403) { toast.error(e.body?.message ?? e.message); return }
        if (e.status === 400) { errToast(e); return }
      }
      errToast(e)
    },
  })

  const createCustomerMutation = useMutation({
    mutationFn: (data: CustomerFormData) => postCustomer(buildCustomerCreateBody(data)),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [...CUSTOMER_LIST_QUERY_KEY] })
      toast.success("Đã tạo khách hàng")
    },
  })

  const patchCustomerMutation = useMutation({
    mutationFn: (args: { id: number; body: Record<string, unknown> }) => patchCustomer(args.id, args.body),
    onSuccess: (_d, v) => {
      void queryClient.invalidateQueries({ queryKey: [...CUSTOMER_LIST_QUERY_KEY] })
      void queryClient.invalidateQueries({ queryKey: ["product-management", "customers", "detail", v.id] })
      toast.success("Đã cập nhật khách hàng")
    },
  })

  const handleSelect = (id: number) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]))
  }

  const handleSelectAll = (checked: boolean) => {
    setSelectedIds(checked ? customers.map((c) => c.id) : [])
  }

  const handleToolbarAction = (action: string) => {
    switch (action) {
      case "edit":
        toast.info(`Chỉnh sửa ${selectedIds.length} khách hàng`)
        break
      case "delete":
        if (isStaff) {
          toast.error("Chỉ Owner hoặc Admin mới được xóa hàng loạt khách hàng.")
          return
        }
        setIsDeletingBulk(true)
        break
      case "create":
        setEditingCustomer(undefined)
        setIsFormOpen(true)
        break
    }
  }

  const confirmBulkDelete = () => {
    if (isStaff) { setIsDeletingBulk(false); return }
    const ids = [...new Set(selectedIds)]
    if (ids.length === 0) { setIsDeletingBulk(false); return }
    void bulkDeleteCustomersMutation.mutateAsync(ids)
  }

  const handleView = (item: Customer) => {
    setSelectedCustomer(item)
    setIsDetailOpen(true)
  }

  const handleEdit = (item: Customer) => {
    setEditingCustomer(item)
    setIsFormOpen(true)
  }

  const handleDelete = (item: Customer) => {
    if (isStaff) {
      toast.error("Chỉ Owner hoặc Admin mới được xóa khách hàng.")
      return
    }
    setDeleteTarget(item)
  }

  const confirmDelete = () => {
    const target = deleteTarget
    if (!target) {
      return
    }
    void deleteCustomerMutation.mutateAsync(target.id)
  }

  return (
    <div className="p-4 md:p-6 lg:p-8 flex flex-col h-full min-h-0 gap-4 md:gap-5 overflow-hidden">
      <div className="shrink-0">
        <h1 className="text-xl md:text-2xl font-semibold text-slate-900 tracking-tight">Khách hàng</h1>
        <p className="text-sm text-slate-500 mt-1">Quản lý thông tin khách hàng và điểm tích lũy</p>
      </div>

      <CustomerToolbar
        searchStr={search}
        onSearch={setSearch}
        statusFilter={statusFilter}
        onStatusChange={setStatusFilter}
        selectedIds={selectedIds}
        onAction={handleToolbarAction}
        canBulkDelete={!isStaff}
      />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 shrink-0 text-sm">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-slate-500 whitespace-nowrap">Sắp xếp</span>
          <select
            value={sort}
            onChange={(e) => {
              setSort(e.target.value as CustomerListSort)
            }}
            className="h-9 px-2 border border-slate-200 bg-white rounded-md text-slate-900 min-w-[200px]"
          >
            {CUSTOMER_LIST_SORT_WHITELIST.map((s) => (
              <option key={s} value={s}>
                {CUSTOMER_LIST_SORT_LABEL_VI[s]}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="flex-1 flex flex-col min-h-0 bg-white border border-slate-200/60 rounded-xl overflow-hidden shadow-md">
        {isListPending && !listInfinite ? (
          <div className="p-8 text-center text-slate-500 flex-1" role="status">
            Đang tải danh sách…
          </div>
        ) : isListError && !listInfinite ? (
          <div className="p-8 text-center text-red-600 flex-1" role="alert">
            Không tải được danh sách khách hàng.
          </div>
        ) : (
          <div className="flex flex-1 flex-col min-h-0">
            <div
              ref={scrollRootRef}
              className="flex-1 overflow-y-auto relative scroll-smooth [scrollbar-gutter:stable] min-h-0"
            >
              <CustomerTable
                data={customers}
                visibleColumnKeys={visibleColumnKeys}
                selectedIds={selectedIds}
                onSelect={handleSelect}
                onSelectAll={handleSelectAll}
                onView={handleView}
                onEdit={handleEdit}
                onDelete={handleDelete}
                canDelete={!isStaff}
              />
              <div ref={loadMoreSentinelRef} className="h-1 w-full shrink-0" aria-hidden />
            </div>
            {!isListError && (
              <div className="flex items-center justify-between flex-wrap gap-2 px-3 py-2 border-t border-slate-200 bg-slate-50/80 text-sm text-slate-600 min-h-11 shrink-0">
                <span className="tabular-nums">Đang hiển thị {customers.length} / {total} khách hàng</span>
                {isFetchingNextPage && <span className="text-slate-500">Đang tải thêm…</span>}
                {hasNextPage && !isFetchingNextPage && (
                  <span className="text-slate-400 text-xs hidden sm:inline">Cuộn xuống để tải thêm</span>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => {
          if (!open) {
            setDeleteTarget(null)
          }
        }}
        onConfirm={confirmDelete}
        title="Xác nhận xóa"
        description={
          deleteTarget
            ? `Bạn có chắc chắn muốn xóa khách hàng "${deleteTarget.name}"? Khách sẽ được ẩn khỏi danh sách (xóa mềm).`
            : undefined
        }
      />

      <ConfirmDialog
        open={isDeletingBulk}
        onOpenChange={setIsDeletingBulk}
        onConfirm={confirmBulkDelete}
        title="Xác nhận xóa nhiều"
        description={`Bạn có chắc chắn muốn xóa ${selectedIds.length} khách hàng đã chọn? (Xóa mềm)`}
      />

      <CustomerDetailDialog
        customer={displayCustomer}
        isOpen={isDetailOpen}
        onClose={() => {
          setIsDetailOpen(false)
        }}
        isDetailLoading={isCustomerDetailPending}
        isDetailError={isCustomerDetailError}
      />

      <CustomerForm
        key={
          !isFormOpen
            ? "closed"
            : editingCustomer
              ? `edit-${editingCustomer.id}-${editFormDetailDto?.updatedAt ?? "row"}`
              : "create"
        }
        open={isFormOpen}
        onOpenChange={(open) => {
          setIsFormOpen(open)
          if (!open) {
            setEditingCustomer(undefined)
          }
        }}
        customer={customerForForm}
        canEditLoyaltyPoints={canEditLoyaltyPoints}
        onSubmit={async (data: CustomerFormData) => {
          if (editingCustomer) {
            if (isEditFormDetailLoading) {
              toast.error("Vui lòng đợi tải xong chi tiết khách hàng.")
              throw new CustomerFormSubmitAborted()
            }
            const snap =
              editFormDetailDto && editFormDetailDto.id === editingCustomer.id
                ? customerEditSnapshotFromDetail(editFormDetailDto)
                : customerEditSnapshotFromListRow(editingCustomer)
            const patchInput = {
              customerCode: data.customerCode,
              name: data.name,
              phone: data.phone,
              email: data.email,
              address: data.address,
              status: data.status,
              ...(canEditLoyaltyPoints ? { loyaltyPoints: data.loyaltyPoints } : {}),
            }
            const body = buildCustomerPatchBody(snap, patchInput, {
              includeLoyaltyPoints: canEditLoyaltyPoints,
            })
            if (Object.keys(body).length === 0) {
              toast.info("Không có thay đổi để lưu")
              throw new CustomerFormSubmitAborted()
            }
            await patchCustomerMutation.mutateAsync({ id: editingCustomer.id, body })
            return
          }
          await createCustomerMutation.mutateAsync(data)
        }}
      />
    </div>
  )
}
