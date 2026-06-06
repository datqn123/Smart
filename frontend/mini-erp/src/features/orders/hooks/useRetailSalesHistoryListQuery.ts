import { useEffect, useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { ApiRequestError } from "@/lib/api/http"
import { toast } from "sonner"
import type { Order } from "../types"
import {
  getRetailSalesHistoryList,
  mapSalesOrderListItemDtoToOrder,
  RETAIL_SALES_HISTORY_LIST_QUERY_KEY,
  RETAIL_HISTORY_SORT_WHITELIST,
  type GetRetailSalesHistoryListParams,
  type RetailHistoryListSort,
} from "../api/salesOrdersApi"

const SEARCH_DEBOUNCE_MS = 400
const PAGE_SIZE = 20

function errToast(e: unknown) {
  if (e instanceof ApiRequestError) {
    toast.error(e.body?.message ?? e.message)
  } else {
    toast.error(e instanceof Error ? e.message : "Đã xảy ra lỗi")
  }
}

export function useRetailSalesHistoryListQuery() {
  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [page, setPage] = useState(1)
  const [sort, setSort] = useState<RetailHistoryListSort>("createdAt:desc")
  const [statusFilter, setStatusFilter] = useState<"all" | "Delivered" | "Cancelled">("all")
  const [paymentStatusFilter, setPaymentStatusFilter] = useState<"all" | "Paid" | "Unpaid" | "Partial">("all")

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), SEARCH_DEBOUNCE_MS)
    return () => clearTimeout(t)
  }, [search])

  useEffect(() => {
    setPage(1)
  }, [debouncedSearch, dateFrom, dateTo, sort])

  const listParams: GetRetailSalesHistoryListParams = useMemo(
    () => ({
      search: debouncedSearch.trim() || undefined,
      dateFrom: dateFrom.trim() || undefined,
      dateTo: dateTo.trim() || undefined,
      page,
      limit: PAGE_SIZE,
      sort,
    }),
    [debouncedSearch, dateFrom, dateTo, page, sort],
  )

  const listQueryKey = useMemo(
    () => [...RETAIL_SALES_HISTORY_LIST_QUERY_KEY, listParams] as const,
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
    queryFn: () => getRetailSalesHistoryList(listParams),
    retry: false,
  })

  const orders: Order[] = useMemo(
    () => (listPage?.items ?? []).map(mapSalesOrderListItemDtoToOrder),
    [listPage],
  )

  const filteredOrders = useMemo(
    () =>
      orders
        .filter((o) => statusFilter === "all" || o.status === statusFilter)
        .filter((o) => paymentStatusFilter === "all" || o.paymentStatus === paymentStatusFilter),
    [orders, statusFilter, paymentStatusFilter],
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
    errToast(listError)
  }, [isListError, listError])

  return {
    orders: filteredOrders,
    search,
    setSearch,
    dateFrom,
    setDateFrom,
    dateTo,
    setDateTo,
    page,
    setPage,
    sort,
    setSort,
    sortWhitelist: RETAIL_HISTORY_SORT_WHITELIST,
    statusFilter,
    setStatusFilter,
    paymentStatusFilter,
    setPaymentStatusFilter,
    isListPending,
    isListFetching,
    isListError,
    total,
    totalPages,
  }
}
