import { useState } from "react"
import { Trash2, Plus, Minus, User, CreditCard, Receipt, Loader2 } from "lucide-react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { useOrderStore } from "../store/useOrderStore"
import { Separator } from "@/components/ui/separator"
import { Input } from "@/components/ui/input"
import { toast } from "sonner"
import { ApiRequestError } from "@/lib/api/http"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  buildRetailCheckoutBody,
  postRetailCheckout,
  RETAIL_SALES_HISTORY_LIST_QUERY_KEY,
  SALES_ORDER_LIST_QUERY_KEY,
} from "../api/salesOrdersApi"
import { POS_PRODUCTS_SEARCH_QUERY_KEY } from "../api/posProductsApi"
import { CustomerSearchDialog } from "./CustomerSearchDialog"
import { ReceiptDialog } from "./ReceiptDialog"
import type { CustomerListItemDto } from "@/features/product-management/api/customersApi"
import type { SalesOrderDetailDto } from "../api/salesOrdersApi"

function numMoney(v: number | string): number {
  const n = typeof v === "number" ? v : Number(v)
  return Number.isFinite(n) ? n : 0
}

function checkoutErrorToast(e: unknown) {
  if (e instanceof ApiRequestError) {
    const msg = e.body?.message ?? e.message
    if (e.status === 409) {
      toast.error(msg, {
        description: "Dữ liệu thanh toán đã thay đổi. Kiểm tra lại giỏ hàng rồi thử thanh toán lại.",
      })
      return
    }
    const d = e.body?.details
    if (d && typeof d === "object") {
      const parts = Object.entries(d).map(([k, v]) => `${k}: ${v}`)
      if (parts.length > 0) {
        toast.error(msg, { description: parts.join(" · ") })
        return
      }
    }
    toast.error(msg)
    return
  }
  toast.error(e instanceof Error ? e.message : "Thanh toán thất bại.")
}

export function POSCartPanel() {
  const queryClient = useQueryClient()
  const {
    cart,
    removeItem,
    updateQuantity,
    getTotal,
    getFinalTotal,
    customerName,
    discount,
    notes,
    clearCart,
    setCustomer,
    setDiscount,
    setNotes,
  } = useOrderStore()
  const [customerDialogOpen, setCustomerDialogOpen] = useState(false)
  const [cashOpen, setCashOpen] = useState(false)
  const [cashReceivedInput, setCashReceivedInput] = useState("")
  const [partialDialogOpen, setPartialDialogOpen] = useState(false)
  const [partialReceivedInput, setPartialReceivedInput] = useState("")
  const [receiptOpen, setReceiptOpen] = useState(false)
  const [receiptOrder, setReceiptOrder] = useState<SalesOrderDetailDto | null>(null)
  const [receiptCashReceived, setReceiptCashReceived] = useState<number | undefined>()
  const [receiptPartialReceived, setReceiptPartialReceived] = useState<number | undefined>()

  const checkoutMutation = useMutation({
    mutationFn: (intent: {
      paymentStatus: "Paid" | "Unpaid" | "Partial"
      cashReceived?: number
      partialReceived?: number
    }) => {
      const snap = useOrderStore.getState()
      const body = buildRetailCheckoutBody({
        cart: snap.cart.map((i) => ({
          productId: i.productId,
          unitId: i.unitId,
          quantity: i.quantity,
          unitPrice: i.unitPrice,
        })),
        customerId: snap.customerId,
        discount: snap.discount,
        voucherCode: null,
        paymentStatus: intent.paymentStatus,
        notes: snap.notes,
      })
      return postRetailCheckout(body)
    },
    onSuccess: (data, intent) => {
      setReceiptOrder(data)
      setReceiptCashReceived(intent.cashReceived)
      setReceiptPartialReceived(intent.partialReceived)
      setReceiptOpen(true)
      clearCart()
      setCashOpen(false)
      setCashReceivedInput("")
      setPartialDialogOpen(false)
      setPartialReceivedInput("")
      void queryClient.invalidateQueries({ queryKey: [...SALES_ORDER_LIST_QUERY_KEY] })
      void queryClient.invalidateQueries({ queryKey: [...RETAIL_SALES_HISTORY_LIST_QUERY_KEY] })
      void queryClient.invalidateQueries({ queryKey: [...POS_PRODUCTS_SEARCH_QUERY_KEY] })
      toast.success(`Thanh toán thành công — ${data.orderCode}`)
    },
    onError: checkoutErrorToast,
  })

  const runCheckout = (
    paymentStatus: "Paid" | "Unpaid" | "Partial",
    meta?: { cashReceived?: number; partialReceived?: number },
  ) => {
    if (cart.length === 0) {
      toast.error("Giỏ hàng trống")
      return
    }
    checkoutMutation.mutate({ paymentStatus, ...meta })
  }

  const handleSelectCustomer = (customer: CustomerListItemDto) => {
    setCustomer(customer.id, customer.name)
    toast.success(`Đã chọn ${customer.name}`)
  }

  const handleSelectWalkInCustomer = () => {
    setCustomer(null, "Khách lẻ")
    toast.success("Đã chọn Khách lẻ")
  }

  const handleOpenCashCalculator = () => {
    if (cart.length === 0) {
      toast.error("Giỏ hàng trống")
      return
    }
    setCashOpen((current) => !current)
  }

  const handleDiscountChange = (raw: string) => {
    const amount = numMoney(raw.replace(/[^\d]/g, ""))
    setDiscount(Math.min(amount, getTotal()))
  }

  const handleOpenPartialDialog = () => {
    if (cart.length === 0) {
      toast.error("Giỏ hàng trống")
      return
    }
    setPartialDialogOpen(true)
  }

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(val)

  const pending = checkoutMutation.isPending
  const checkoutPaymentStatus = checkoutMutation.variables?.paymentStatus
  const displayTotal = getFinalTotal()
  const cashReceived = numMoney(cashReceivedInput.replace(/[^\d]/g, ""))
  const cashChange = Math.max(0, cashReceived - displayTotal)
  const cashMissing = Math.max(0, displayTotal - cashReceived)
  const canConfirmCash = !pending && cart.length > 0 && cashReceived >= displayTotal
  const partialReceived = numMoney(partialReceivedInput.replace(/[^\d]/g, ""))
  const partialRemaining = Math.max(0, displayTotal - partialReceived)
  const canConfirmPartial = !pending && cart.length > 0 && partialReceived > 0 && partialReceived < displayTotal

  return (
    <>
      <CustomerSearchDialog
        open={customerDialogOpen}
        onOpenChange={setCustomerDialogOpen}
        onSelectCustomer={handleSelectCustomer}
        onSelectWalkIn={handleSelectWalkInCustomer}
      />
      <ReceiptDialog
        open={receiptOpen}
        onOpenChange={setReceiptOpen}
        order={receiptOrder}
        cashReceived={receiptCashReceived}
        partialReceived={receiptPartialReceived}
        onNewOrder={() => setReceiptOpen(false)}
      />
      <Dialog open={partialDialogOpen} onOpenChange={setPartialDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Trả trước một phần</DialogTitle>
            <DialogDescription>Ghi nhận số tiền đã nhận và lưu đơn ở trạng thái thanh toán một phần.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="rounded-lg bg-slate-50 p-3 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Tổng đơn</span>
                <span className="font-bold text-slate-900">{formatCurrency(displayTotal)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Còn lại</span>
                <span className="font-bold text-slate-900">{formatCurrency(partialRemaining)}</span>
              </div>
            </div>
            <div className="space-y-1.5">
              <label htmlFor="pos-partial-received" className="text-sm font-semibold text-slate-700">
                Đã nhận
              </label>
              <Input
                id="pos-partial-received"
                inputMode="numeric"
                value={partialReceivedInput}
                disabled={pending}
                onChange={(e) => setPartialReceivedInput(e.target.value)}
                placeholder="Nhập số tiền trả trước"
                className="h-10 border-slate-200 focus-visible:ring-1 focus-visible:ring-slate-400"
              />
              {partialReceived >= displayTotal && partialReceived > 0 ? (
                <p className="text-xs text-amber-700">Số tiền đã nhận bằng hoặc vượt tổng đơn, hãy dùng thanh toán tiền mặt.</p>
              ) : null}
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" disabled={pending} onClick={() => setPartialDialogOpen(false)}>
                Hủy
              </Button>
              <Button
                type="button"
                className="bg-slate-900 text-white hover:bg-slate-800"
                disabled={!canConfirmPartial}
                onClick={() => runCheckout("Partial", { partialReceived })}
              >
                {pending && checkoutPaymentStatus === "Partial" ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                Xác nhận
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
      <div className="flex flex-col h-full bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-3 py-2 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-full bg-white border border-slate-200 flex items-center justify-center shadow-sm shrink-0">
              <User className="h-3.5 w-3.5 text-slate-600" />
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-slate-400 leading-none tracking-wider">Khách hàng</p>
              <p className="text-sm font-semibold text-slate-900 mt-0.5">{customerName}</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            type="button"
            className="text-slate-500 text-xs font-medium hover:text-slate-900 h-7 px-2"
            onClick={() => setCustomerDialogOpen(true)}
          >
            Thay đổi
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {cart.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-2">
            <Receipt className="h-10 w-10 opacity-10" />
            <p className="text-sm">Giỏ hàng đang trống</p>
          </div>
        ) : (
          cart.map((item) => (
            <div key={`${item.productId}-${item.unitId}`} className="group relative">
              <div className="flex justify-between items-start">
                <div className="flex-1 min-w-0 pr-5">
                  <h4 className="text-sm font-semibold text-slate-900 line-clamp-1 leading-tight">{item.productName}</h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {item.skuCode}
                    {item.unitName ? ` · ${item.unitName}` : ""}
                  </p>
                </div>
                <button
                  type="button"
                  disabled={pending}
                  onClick={() => removeItem(item.productId, item.unitId)}
                  className="p-1 text-slate-300 hover:text-red-500 transition-colors bg-slate-50 rounded-md disabled:opacity-50"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
              <div className="mt-1.5 flex items-center justify-between">
                <div className="flex items-center border border-slate-200 rounded-md overflow-hidden h-7 bg-white shadow-sm">
                  <button
                    type="button"
                    disabled={pending}
                    onClick={() => updateQuantity(item.productId, item.unitId, item.quantity - 1)}
                    className="px-2 hover:bg-slate-50 text-slate-600 transition-colors disabled:opacity-50"
                  >
                    <Minus className="h-3 w-3" />
                  </button>
                  <div className="w-8 text-center text-sm font-bold text-slate-900 border-x border-slate-200">
                    {item.quantity}
                  </div>
                  <button
                    type="button"
                    disabled={pending}
                    onClick={() => updateQuantity(item.productId, item.unitId, item.quantity + 1)}
                    className="px-2 hover:bg-slate-50 text-slate-600 transition-colors disabled:opacity-50"
                  >
                    <Plus className="h-3 w-3" />
                  </button>
                </div>
                <span className="text-sm font-bold text-slate-900">{formatCurrency(item.lineTotal)}</span>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="px-3 py-2 bg-slate-50 border-t border-slate-100 space-y-1.5">
        <div className="grid grid-cols-1 gap-1.5">
          <div className="space-y-1">
            <label htmlFor="pos-manual-discount" className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
              Giảm giá đơn
            </label>
            <Input
              id="pos-manual-discount"
              inputMode="numeric"
              value={discount > 0 ? String(discount) : ""}
              disabled={pending}
              onChange={(e) => handleDiscountChange(e.target.value)}
              placeholder="Nhập số tiền giảm"
              className="h-8 bg-white border-slate-200 text-xs focus-visible:ring-1 focus-visible:ring-slate-400"
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="pos-order-notes" className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
              Ghi chú
            </label>
            <textarea
              id="pos-order-notes"
              value={notes}
              disabled={pending}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Ghi chú đơn hàng..."
              rows={2}
              className="min-h-12 w-full resize-none rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-900 outline-none transition-colors placeholder:text-slate-400 focus:border-slate-400 focus:ring-1 focus:ring-slate-400 disabled:opacity-50"
            />
          </div>
        </div>
      </div>

      <div className="px-3 pt-2 pb-2 bg-slate-900 text-white shadow-[0_-10px_20px_rgba(0,0,0,0.1)] shrink-0">
        <div className="space-y-1">
          <div className="flex justify-between text-slate-400 text-xs font-medium">
            <span>Tạm tính ({cart.length} món)</span>
            <span>{formatCurrency(getTotal())}</span>
          </div>
          {discount > 0 && (
            <div className="flex justify-between text-amber-200 text-xs font-medium">
              <span>Giảm giá</span>
              <span>-{formatCurrency(discount)}</span>
            </div>
          )}
          <Separator className="bg-slate-800 my-0.5" />
          <div className="flex justify-between items-baseline gap-2">
            <span className="text-xs font-bold text-slate-400 shrink-0">Tổng cộng</span>
            <span className="text-lg sm:text-xl font-black tracking-tight text-white text-right inline-flex items-center justify-end gap-1.5 min-w-0">
              <span className="tabular-nums break-all">{formatCurrency(displayTotal)}</span>
            </span>
          </div>
        </div>

        {cashOpen && (
          <div className="mt-2 rounded-lg border border-slate-700 bg-slate-800/70 p-2.5 space-y-2">
            <div className="flex items-center justify-between gap-3 text-xs">
              <span className="text-slate-300">Cần thanh toán</span>
              <span className="font-bold text-white tabular-nums">{formatCurrency(displayTotal)}</span>
            </div>
            <div className="space-y-1">
              <label htmlFor="pos-cash-received" className="text-xs font-semibold text-slate-300">
                Khách đưa
              </label>
              <Input
                id="pos-cash-received"
                inputMode="numeric"
                value={cashReceivedInput}
                disabled={pending}
                onChange={(e) => setCashReceivedInput(e.target.value)}
                placeholder="Nhập số tiền khách đưa"
                className="h-8 border-slate-600 bg-white text-slate-900 text-sm focus-visible:ring-1 focus-visible:ring-slate-300"
              />
            </div>
            <div className="flex items-center justify-between gap-3 text-xs">
              <span className="text-slate-300">{cashMissing > 0 ? "Còn thiếu" : "Tiền thừa"}</span>
              <span className={cashMissing > 0 ? "font-bold text-amber-200" : "font-bold text-emerald-200"}>
                {formatCurrency(cashMissing > 0 ? cashMissing : cashChange)}
              </span>
            </div>
            <Button
              type="button"
              disabled={!canConfirmCash}
              className="h-8 w-full bg-white text-slate-900 hover:bg-slate-100 font-bold text-sm"
              onClick={() => runCheckout("Paid", { cashReceived })}
            >
              {pending && checkoutPaymentStatus === "Paid" ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin text-slate-900" />
              ) : null}
              Xác nhận tiền mặt
            </Button>
          </div>
        )}

        <div className="grid grid-cols-2 gap-2 mt-2">
          <Button
            type="button"
            variant="outline"
            disabled={pending || cart.length === 0}
            className="bg-transparent border-slate-700 text-white hover:bg-slate-800 h-9 px-2 text-xs inline-flex items-center justify-center gap-1.5"
            onClick={() => runCheckout("Unpaid")}
          >
            {pending && checkoutPaymentStatus === "Unpaid" ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin shrink-0" />
            ) : (
              <CreditCard className="h-3.5 w-3.5 shrink-0" />
            )}
            <span className="text-center leading-tight">Thẻ/Chuyển khoản</span>
          </Button>
          <Button
            type="button"
            disabled={pending || cart.length === 0}
            className="bg-white text-slate-900 hover:bg-slate-100 h-9 px-2 text-xs font-bold uppercase tracking-wide inline-flex items-center justify-center gap-1.5"
            onClick={handleOpenCashCalculator}
          >
            {pending && checkoutPaymentStatus === "Paid" ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin shrink-0 text-slate-900" />
            ) : null}
            Tiền mặt
          </Button>
        </div>
        <Button
          type="button"
          variant="outline"
          disabled={pending || cart.length === 0}
          className="mt-2 h-9 w-full border-slate-700 bg-transparent text-white hover:bg-slate-800"
          onClick={handleOpenPartialDialog}
        >
          {pending && checkoutPaymentStatus === "Partial" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
          Trả trước một phần
        </Button>
      </div>
      </div>
    </>
  )
}
