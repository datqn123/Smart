import { useEffect, useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { ApiRequestError } from "@/lib/api/http"
import { toast } from "sonner"
import { toastApiError } from "@/lib/api/toastApiError"
import type { Order } from "../types"
import {
  getSalesOrderList,
  mapSalesOrderListItemDtoToOrder,
  SALES_ORDER_LIST_QUERY_KEY,
  type GetSalesOrderListParams,
  type SalesOrderChannel,
  type SalesOrderListSort,
} from "../api/salesOrdersApi"

const SEARCH_DEBOUNCE_MS = 400
const PAGE_SIZE = 20

type Options = {
  /** Luôn gửi lên BE để Staff không bị 403 (OQ-8a). */
  orderChannel: SalesOrderChannel
}

export function useSalesOrdersListQuery({ orderChannel }: Options) {
  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [paymentStatusFilter, setPaymentStatusFilter] = useState<"all" | "Paid" | "Unpaid" | "Partial">("all")
  const [page, setPage] = useState(1)
  const [sort, setSort] = useState<SalesOrderListSort>("createdAt:desc")
  const [selectedIds, setSelectedIds] = useState<number[]>([])

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), SEARCH_DEBOUNCE_MS)
    return () => clearTimeout(t)
  }, [search])

  useEffect(() => {
    setPage(1)
  }, [debouncedSearch, statusFilter, paymentStatusFilter, sort])

  const listParams: GetSalesOrderListParams = useMemo(
    () => ({
      orderChannel,
      search: debouncedSearch.trim() || undefined,
      status: statusFilter,
      paymentStatus: paymentStatusFilter,
      page,
      limit: PAGE_SIZE,
      sort,
    }),
    [orderChannel, debouncedSearch, statusFilter, paymentStatusFilter, page, sort],
  )

  const listQueryKey = useMemo(
    () => [...SALES_ORDER_LIST_QUERY_KEY, listParams] as const,
    [listParams],
  )

  const {
    data: listPage,
    isPending: isListPending,
    isError: isListError,
    error: listError,
    isFetching: isListFetching,
  } = useQuery({
    queryKey: listQueryKey,
    queryFn: () => getSalesOrderList(listParams),
    /** Tránh lặp toast 403/400 khi BE từ chối ngay (OQ-8a, validation). */
    retry: false,
  })

  const orders: Order[] = useMemo(
    () => (listPage?.items ?? []).map(mapSalesOrderListItemDtoToOrder),
    [listPage],
  )

  const total = listPage?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages)
    }
  }, [page, totalPages])

  useEffect(() => {
    if (!isListError || !listError) return
    if (listError instanceof ApiRequestError && listError.status === 403) {
      toast.error(
        listError.body?.message ??
          "Không có quyền xem danh sách theo bộ lọc này. Nhân viên cần chọn kênh đơn (đúng màn hàng).",
      )
      return
    }
    toastApiError(listError)
  }, [isListError, listError])

  useEffect(() => {
    setSelectedIds([])
  }, [page, debouncedSearch, statusFilter, paymentStatusFilter, sort])

  return {
    orders,
    search,
    setSearch,
    statusFilter,
    setStatusFilter,
    paymentStatusFilter,
    setPaymentStatusFilter,
    page,
    setPage,
    sort,
    setSort,
    selectedIds,
    setSelectedIds,
    isListPending,
    isListFetching,
    isListError,
    total,
    totalPages,
  }
}
