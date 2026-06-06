import { ReceiptText } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Separator } from "@/components/ui/separator"
import type { SalesOrderDetailDto } from "../api/salesOrdersApi"

type ReceiptDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  order: SalesOrderDetailDto | null
  cashReceived?: number
  partialReceived?: number
  onNewOrder: () => void
}

function numMoney(value: number | string | null | undefined): number {
  const n = typeof value === "number" ? value : Number(value)
  return Number.isFinite(n) ? n : 0
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value)
}

function paymentStatusLabel(status: string) {
  if (status === "Paid") return "Đã thanh toán"
  if (status === "Partial") return "Trả trước một phần"
  return "Ghi nhận nợ"
}

export function ReceiptDialog({
  open,
  onOpenChange,
  order,
  cashReceived,
  partialReceived,
  onNewOrder,
}: ReceiptDialogProps) {
  const finalAmount = numMoney(order?.finalAmount)
  const totalAmount = numMoney(order?.totalAmount)
  const discountAmount = numMoney(order?.discountAmount)
  const cashChange = cashReceived != null ? Math.max(0, cashReceived - finalAmount) : null
  const partialRemaining = partialReceived != null ? Math.max(0, finalAmount - partialReceived) : null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg p-0 gap-0">
        <DialogHeader className="px-5 pt-5 pb-4 border-b border-slate-200">
          <div className="flex items-start gap-3 pr-6">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-900 text-white">
              <ReceiptText className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <DialogTitle>Thanh toán thành công</DialogTitle>
              <DialogDescription className="mt-1">
                {order?.orderCode ? `Mã đơn: ${order.orderCode}` : "Đơn bán lẻ đã được ghi nhận."}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="max-h-[70vh] overflow-y-auto px-5 py-4">
          {order ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-xs font-semibold uppercase text-slate-400">Khách hàng</p>
                  <p className="mt-1 font-semibold text-slate-900">{order.customerName}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs font-semibold uppercase text-slate-400">Thanh toán</p>
                  <p className="mt-1 font-semibold text-slate-900">{paymentStatusLabel(order.paymentStatus)}</p>
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                {order.lines.map((line) => (
                  <div key={line.id} className="flex items-start justify-between gap-3 text-sm">
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-slate-900">{line.productName}</p>
                      <p className="mt-0.5 text-xs text-slate-500">
                        {line.quantity} x {line.unitName} · {formatCurrency(numMoney(line.unitPrice))}
                      </p>
                    </div>
                    <span className="shrink-0 font-semibold text-slate-900">
                      {formatCurrency(numMoney(line.lineTotal))}
                    </span>
                  </div>
                ))}
              </div>

              <Separator />

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">Tạm tính</span>
                  <span className="font-semibold text-slate-900">{formatCurrency(totalAmount)}</span>
                </div>
                {discountAmount > 0 && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Giảm giá</span>
                    <span className="font-semibold text-slate-900">-{formatCurrency(discountAmount)}</span>
                  </div>
                )}
                {order.voucherCode && (
                  <div className="flex justify-between gap-3">
                    <span className="text-slate-500">Voucher</span>
                    <span className="truncate font-semibold text-slate-900">{order.voucherCode}</span>
                  </div>
                )}
                <div className="flex justify-between text-base">
                  <span className="font-bold text-slate-900">Tổng cộng</span>
                  <span className="font-black text-slate-900">{formatCurrency(finalAmount)}</span>
                </div>
                {cashReceived != null && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Khách đưa</span>
                      <span className="font-semibold text-slate-900">{formatCurrency(cashReceived)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Tiền thừa</span>
                      <span className="font-semibold text-slate-900">{formatCurrency(cashChange ?? 0)}</span>
                    </div>
                  </>
                )}
                {partialReceived != null && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Đã nhận</span>
                      <span className="font-semibold text-slate-900">{formatCurrency(partialReceived)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Còn lại</span>
                      <span className="font-semibold text-slate-900">{formatCurrency(partialRemaining ?? 0)}</span>
                    </div>
                  </>
                )}
              </div>

              {order.notes?.trim() ? (
                <>
                  <Separator />
                  <div className="rounded-lg bg-slate-50 p-3 text-sm text-slate-600">
                    <p className="mb-1 text-xs font-semibold uppercase text-slate-400">Ghi chú</p>
                    {order.notes}
                  </div>
                </>
              ) : null}
            </div>
          ) : (
            <p className="py-8 text-center text-sm text-slate-500">Không có dữ liệu hóa đơn.</p>
          )}
        </div>

        <div className="flex flex-col-reverse gap-2 border-t border-slate-200 px-5 py-4 sm:flex-row sm:justify-end">
          <Button type="button" variant="outline" disabled>
            In hóa đơn
          </Button>
          <Button type="button" className="bg-slate-900 text-white hover:bg-slate-800" onClick={onNewOrder}>
            Đơn mới
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
