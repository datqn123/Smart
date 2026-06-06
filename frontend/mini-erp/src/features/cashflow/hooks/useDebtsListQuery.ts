import { useEffect, useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"

import {
  DEBTS_LIST_QUERY_KEY,
  getDebtsList,
  type GetDebtsListParams,
} from "../api/debtsApi"

export const DEBTS_PAGE_SIZE = 20
const SEARCH_DEBOUNCE_MS = 400

export function useDebtsListQuery() {
  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [partnerTypeFilter, setPartnerTypeFilter] = useState("all")
  const [dueDateFrom, setDueDateFrom] = useState("")
  const [dueDateTo, setDueDateTo] = useState("")
  const [page, setPage] = useState(1)

  useEffect(() => {
    const t = window.setTimeout(() => setDebouncedSearch(search.trim()), SEARCH_DEBOUNCE_MS)
    return () => window.clearTimeout(t)
  }, [search])

  useEffect(() => {
    const t = window.setTimeout(() => setPage(1), 0)
    return () => window.clearTimeout(t)
  }, [debouncedSearch, statusFilter, partnerTypeFilter, dueDateFrom, dueDateTo])

  const filters: GetDebtsListParams = useMemo(
    () => ({
      search: debouncedSearch || undefined,
      status: statusFilter === "all" ? undefined : (statusFilter as "InDebt" | "Cleared"),
      partnerType:
        partnerTypeFilter === "all" ? undefined : (partnerTypeFilter as "Customer" | "Supplier"),
      dueDateFrom: dueDateFrom || undefined,
      dueDateTo: dueDateTo || undefined,
      page,
      limit: DEBTS_PAGE_SIZE,
    }),
    [debouncedSearch, statusFilter, partnerTypeFilter, dueDateFrom, dueDateTo, page],
  )

  const query = useQuery({
    queryKey: [...DEBTS_LIST_QUERY_KEY, filters],
    queryFn: () => getDebtsList(filters),
  })

  const debts = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / DEBTS_PAGE_SIZE))

  return {
    debts,
    total,
    totalPages,
    page,
    setPage,
    search,
    setSearch,
    statusFilter,
    setStatusFilter,
    partnerTypeFilter,
    setPartnerTypeFilter,
    dueDateFrom,
    setDueDateFrom,
    dueDateTo,
    setDueDateTo,
    isListPending: query.isPending,
    isFetching: query.isFetching,
    isError: query.isError,
    error: query.error,
    query,
  }
}
