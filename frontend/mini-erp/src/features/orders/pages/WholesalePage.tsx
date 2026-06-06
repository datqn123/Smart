import { useEffect, useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { usePageTitle } from "@/context/PageTitleContext"
import type { Order, OrderItem } from "../types"
import { OrderToolbar } from "../components/OrderToolbar"
import { OrderTable } from "../components/OrderTable"
import { OrderDetailDialog } from "../components/OrderDetailDialog"
import { Button } from "@/components/ui/button"
import { DATA_TABLE_SCROLL_CLASS, DATA_TABLE_SHELL_CLASS } from "@/lib/data-table-layout"
import { useRetailSalesHistoryListQuery } from "../hooks/useRetailSalesHistoryListQuery"
import {
  getRetailHistoryListSortLabel,
  getSalesOrderDetail,
  mapSalesOrderDetailLineDtoToOrderItem,
  type RetailHistoryListSort,
} from "../api/salesOrdersApi"

export function WholesalePage() {
  const { setTitle } = usePageTitle()
  const {
    orders,
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
    sortWhitelist,
    statusFilter,
    setStatusFilter,
    paymentStatusFilter,
    setPaymentStatusFilter,
    isListPending,
    isListFetching,
    isListError,
    total,
    totalPages,
  } = useRetailSalesHistoryListQuery()

  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState(false)

  useEffect(() => {
    setTitle("Lịch sử hóa đơn")
  }, [setTitle])

  const detailQuery = useQuery({
    queryKey: ["sales-orders", "detail", selectedOrder?.id],
    queryFn: () => getSalesOrderDetail(selectedOrder!.id),
    enabled: isDetailOpen && selectedOrder != null,
  })

  const detailLines: OrderItem[] | undefined = useMemo(() => {
    if (!isDetailOpen || !selectedOrder) return undefined
    if (detailQuery.isPending || detailQuery.isFetching) return []
    if (!detailQuery.data?.lines) return []
    return detailQuery.data.lines.map(mapSalesOrderDetailLineDtoToOrderItem)
  }, [isDetailOpen, selectedOrder, detailQuery.isPending, detailQuery.isFetching, detailQuery.data])

  const handleView = (item: Order) => {
    setSelectedOrder(item)
    setIsDetailOpen(true)
  }

  return (
    <div className="p-4 md:p-6 lg:p-8 flex flex-col h-full min-h-0 gap-4 md:gap-5 overflow-hidden">
      <div className="shrink-0">
        <h1 className="text-xl md:text-2xl font-semibold text-slate-900 tracking-tight">
          Lịch sử hóa đơn
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Tra cứu hóa đơn đã phát sinh và xem chi tiết giao dịch.
        </p>
      </div>

      <div className={DATA_TABLE_SHELL_CLASS}>
        {isListPending ? (
          <div className="p-8 text-center text-slate-500 flex-1" role="status">
            Đang tải lịch sử hóa đơn...
          </div>
        ) : isListError ? (
          <div className="p-8 text-center text-red-600 flex-1" role="alert">
            Không tải được lịch sử hóa đơn.
          </div>
        ) : (
          <>
            <OrderToolbar
              variant="retailHistory"
              searchStr={search}
              onSearch={setSearch}
              statusFilter={statusFilter}
              onStatusChange={() => {}}
              selectedIds={[]}
              onAction={() => {}}
              dateFrom={dateFrom}
              dateTo={dateTo}
              onDateFromChange={setDateFrom}
              onDateToChange={setDateTo}
              onStatusFilterChange={setStatusFilter}
              paymentStatusFilter={paymentStatusFilter}
              onPaymentStatusFilterChange={setPaymentStatusFilter}
              sort={sort}
              onSortChange={(v) => setSort(v as RetailHistoryListSort)}
              sortWhitelist={sortWhitelist}
              getSortLabel={getRetailHistoryListSortLabel}
            />

            <div className={DATA_TABLE_SCROLL_CLASS}>
              <OrderTable
                data={orders}
                selectedIds={[]}
                onSelect={() => {}}
                onSelectAll={() => {}}
                onView={handleView}
                showCheckbox={false}
                hideTypeBadge
              />
            </div>
            <div className="flex items-center justify-between flex-wrap gap-2 px-3 py-2 border-t border-slate-200 bg-slate-50/80 text-sm text-slate-600 min-h-11 shrink-0">
              <span className="tabular-nums">Đang hiển thị {orders.length} / {total} hóa đơn</span>
              <div className="flex items-center gap-2">
                <span className="text-slate-500 tabular-nums">
                  Trang {page}/{totalPages}
                  {isListFetching ? " · Đang cập nhật..." : ""}
                </span>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={page <= 1 || isListPending}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Trước
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages || isListPending}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Sau
                </Button>
              </div>
            </div>
          </>
        )}
      </div>

      <OrderDetailDialog
        order={selectedOrder}
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        readOnly
        detailLines={detailLines}
        detailDto={detailQuery.data ?? undefined}
      />
    </div>
  )
}
