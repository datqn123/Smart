import { useEffect, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Loader2, Search, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  CUSTOMER_LIST_QUERY_KEY,
  getCustomerList,
  type CustomerListItemDto,
} from "@/features/product-management/api/customersApi"

const CUSTOMER_SEARCH_DEBOUNCE_MS = 300

type CustomerSearchDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSelectCustomer: (customer: CustomerListItemDto) => void
  onSelectWalkIn: () => void
}

export function CustomerSearchDialog({
  open,
  onOpenChange,
  onSelectCustomer,
  onSelectWalkIn,
}: CustomerSearchDialogProps) {
  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")

  useEffect(() => {
    if (!open) return
    const t = window.setTimeout(() => setDebouncedSearch(search), CUSTOMER_SEARCH_DEBOUNCE_MS)
    return () => window.clearTimeout(t)
  }, [open, search])

  const customerQuery = useQuery({
    queryKey: [...CUSTOMER_LIST_QUERY_KEY, "pos-selector", debouncedSearch],
    enabled: open,
    queryFn: () =>
      getCustomerList({
        search: debouncedSearch.trim() || undefined,
        page: 1,
        limit: 8,
        status: "Active",
        sort: "updatedAt:desc",
      }),
    staleTime: 30_000,
  })

  const customers = customerQuery.data?.items ?? []

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl p-0 gap-0">
        <DialogHeader className="px-5 pt-5 pb-4 border-b border-slate-200">
          <DialogTitle>Chọn khách hàng</DialogTitle>
          <DialogDescription>Tìm và gắn khách hàng vào đơn bán lẻ hiện tại.</DialogDescription>
        </DialogHeader>

        <div className="p-5 space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Tìm theo tên, mã hoặc số điện thoại..."
              className="h-10 pl-9 border-slate-200 focus-visible:ring-1 focus-visible:ring-slate-400"
              autoFocus
            />
          </div>

          <Button
            type="button"
            variant="outline"
            className="h-11 w-full justify-start border-slate-200 text-slate-900 hover:bg-slate-50"
            onClick={() => {
              onSelectWalkIn()
              onOpenChange(false)
            }}
          >
            <User className="h-4 w-4 text-slate-500" />
            Khách lẻ
          </Button>

          <div className="min-h-[260px] rounded-lg border border-slate-200 bg-white overflow-hidden">
            {customerQuery.isLoading ? (
              <div className="flex h-[260px] items-center justify-center gap-2 text-sm text-slate-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Đang tải khách hàng...
              </div>
            ) : customerQuery.isError ? (
              <div className="flex h-[260px] flex-col items-center justify-center gap-3 text-center text-sm text-slate-600">
                <p>Không tải được danh sách khách hàng.</p>
                <Button variant="outline" size="sm" type="button" onClick={() => void customerQuery.refetch()}>
                  Thử lại
                </Button>
              </div>
            ) : customers.length === 0 ? (
              <div className="flex h-[260px] items-center justify-center text-sm text-slate-500">
                Không tìm thấy khách hàng phù hợp.
              </div>
            ) : (
              <ul className="max-h-[320px] overflow-y-auto divide-y divide-slate-100">
                {customers.map((customer) => (
                  <li key={customer.id}>
                    <button
                      type="button"
                      className="w-full px-4 py-3 text-left hover:bg-slate-50 focus:bg-slate-50 focus:outline-none"
                      onClick={() => {
                        onSelectCustomer(customer)
                        onOpenChange(false)
                      }}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-slate-900">{customer.name}</p>
                          <p className="mt-1 text-xs text-slate-500">
                            {customer.customerCode} · {customer.phone}
                          </p>
                        </div>
                        <span className="shrink-0 rounded-md border border-slate-200 px-2 py-1 text-xs text-slate-500">
                          {customer.loyaltyPoints} điểm
                        </span>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
