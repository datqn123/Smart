import React from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription
} from "@/components/ui/dialog"
import { formatDate } from "../../inventory/utils"
import type { Order, OrderItem } from "../types"
import type { SalesOrderDetailDto } from "../api/salesOrdersApi"
import { ShoppingBag, User, Calendar, Activity, CreditCard, Receipt, MapPin, Package, Trash2, Edit, CheckCircle2, Truck, Timer, XCircle, BarChart3, Tag, Store } from "lucide-react"
import { Button } from "@/components/ui/button"
import { StatusBadge } from "../../inventory/components/StatusBadge"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"

interface OrderDetailDialogProps {
  order: Order | null
  isOpen: boolean
  onClose: () => void
  /** Task058 — mở luồng hủy đơn (dialog lý do / POST cancel). */
  onCancelOrder?: (order: Order) => void
  onEditOrder?: (order: Order) => void
  /** Task102 — chỉ đọc: ẩn hủy/sửa. */
  readOnly?: boolean
  /** Khi truyền: hiển thị dòng hàng từ API (thay mock). */
  detailLines?: OrderItem[]
  /** SRS-020 — DTO đầy đủ để hiển thị shippingAddress, cancelledAt, voucherCode, posShiftRef. */
  detailDto?: SalesOrderDetailDto
}

// Mock items for detail display
const mockOrderItems: OrderItem[] = [
    { id: 1, productId: 101, unitId: 1, productName: "Sơn Mykolor Grand", skuCode: "MK-001", quantity: 5, unitName: "Thùng", unitPrice: 1250000, lineTotal: 6250000 },
    { id: 2, productId: 102, unitId: 2, productName: "Sơn Dulux 5in1", skuCode: "DX-002", quantity: 3, unitName: "Thùng", unitPrice: 1550000, lineTotal: 4650000 },
]

export function OrderDetailDialog({
  order,
  isOpen,
  onClose,
  onCancelOrder,
  onEditOrder,
  readOnly = false,
  detailLines,
  detailDto,
}: OrderDetailDialogProps) {
  if (!order) return null

  const lineItems = detailLines !== undefined ? detailLines : mockOrderItems

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-full sm:max-w-5xl lg:max-w-5xl max-h-[90vh] overflow-y-auto p-0 gap-0 border-slate-200 shadow-2xl rounded-2xl">
        <DialogHeader className="p-8 pb-4 bg-slate-50/50">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
            <div className="text-left">
              <div className="flex items-center gap-3 mb-2">
                <StatusBadge status={order.status} />
                <span className="text-xs font-mono text-slate-400">Order Ref: {order.orderCode}</span>
              </div>
              <DialogTitle className="text-2xl font-black tracking-tight text-slate-900 flex items-center gap-2">
                Đơn hàng {order.type === "Wholesale" ? "Bán buôn" : "Bán lẻ"} 
              </DialogTitle>
              <p className="text-sm text-slate-500 mt-1 flex items-center gap-2">
                <User size={14} /> Khách hàng: <span className="font-bold text-slate-900">{order.customerName}</span>
              </p>
            </div>
            
            <div className="flex items-center gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <div className="text-right border-r pr-4 border-slate-100">
                    <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Thanh toán</p>
                    <p className={cn(
                        "text-sm font-black",
                        order.paymentStatus === "Paid" ? "text-green-600" : "text-amber-500"
                    )}>{{ Paid: "Đã thanh toán", Unpaid: "Chưa thanh toán", Partial: "Một phần" }[order.paymentStatus] ?? order.paymentStatus}</p>
                </div>
                <div className="text-right">
                    <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Tổng thanh toán</p>
                    <p className="text-2xl font-black text-slate-900">{order.finalAmount.toLocaleString()} <span className="text-sm font-normal text-slate-400">đ</span></p>
                </div>
            </div>
          </div>
        </DialogHeader>

        <div className="p-8 pt-6">
          {/* Progress Tracker / Cancelled Banner */}
          {order.status === "Cancelled" ? (
            <div className="flex items-center gap-3 bg-red-50 border border-red-100 rounded-xl p-4 mb-12">
              <XCircle size={20} className="text-red-500 shrink-0" />
              <div>
                <p className="font-semibold text-sm text-red-700">Đơn hàng đã bị huỷ</p>
                {detailDto?.cancelledAt && (
                  <p className="text-xs text-red-500 mt-0.5">
                    Thời điểm huỷ: {formatDate(detailDto.cancelledAt)}
                  </p>
                )}
              </div>
            </div>
          ) : (
            <div className="mb-12 pt-4">
              <div className="flex justify-between relative px-2">
                <div className="absolute top-1/2 left-0 w-full h-1 bg-slate-100 -translate-y-1/2 z-0 rounded-full" />
                <div className={cn("absolute top-1/2 left-0 h-1 bg-slate-900 -translate-y-1/2 z-0 transition-all duration-1000 ease-in-out rounded-full",
                  order.status === "Pending" ? "w-0" :
                  order.status === "Processing" ? "w-1/3" :
                  order.status === "Shipped" ? "w-2/3" : "w-full"
                )} />
                <Step icon={Timer} label="Tiếp nhận" active />
                <Step icon={Activity} label="Xử lý" active={["Processing", "Shipped", "Delivered", "Completed"].includes(order.status)} />
                <Step icon={Truck} label="Giao hàng" active={["Shipped", "Delivered", "Completed"].includes(order.status)} />
                <Step icon={CheckCircle2} label="Hoàn tất" active={["Delivered", "Completed"].includes(order.status)} />
              </div>
            </div>
          )}

          <div className="space-y-10">
            {/* Row 1: Basic Info Grid */}
            <div className="space-y-6">
                <SectionHeader icon={Receipt} title="Thông tin vận hành" />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-7">
                    <div className="space-y-2">
                        <Label className="text-[10px] font-black uppercase tracking-widest text-slate-400 flex items-center gap-2 px-1">
                            <Calendar size={12} /> Ngày lập đơn
                        </Label>
                        <div className="h-14 bg-slate-50 border border-slate-100 rounded-2xl flex items-center px-5 font-bold text-slate-900 shadow-sm">
                            {formatDate(order.date)}
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label className="text-[10px] font-black uppercase tracking-widest text-slate-400 flex items-center gap-2 px-1">
                            <Package size={12} /> Số lượng mặt hàng
                        </Label>
                        <div className="h-14 bg-slate-50 border border-slate-100 rounded-2xl flex items-center px-5 font-bold text-slate-900 shadow-sm">
                            {order.itemsCount} loại sản phẩm trong đơn
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label className="text-[10px] font-black uppercase tracking-widest text-slate-400 flex items-center gap-2 px-1">
                            <MapPin size={12} /> Địa điểm giao hàng
                        </Label>
                        <div className="h-14 bg-slate-50 border border-slate-100 rounded-2xl flex items-center px-5 font-bold text-slate-900 shadow-sm truncate">
                            {detailDto?.shippingAddress?.trim() || "Tại cửa hàng (POS)"}
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label className="text-[10px] font-black uppercase tracking-widest text-slate-400 flex items-center gap-2 px-1">
                            <CreditCard size={12} /> Trạng thái thanh toán
                        </Label>
                        <div className="h-14 bg-slate-50 border border-slate-100 rounded-2xl flex items-center px-5 font-bold text-slate-900 shadow-sm">
                            {{ Paid: "Đã thanh toán", Unpaid: "Chưa thanh toán", Partial: "Thanh toán một phần" }[order.paymentStatus] ?? order.paymentStatus}
                        </div>
                    </div>

                    {detailDto?.voucherCode && (
                      <div className="space-y-2">
                        <Label className="text-[10px] font-black uppercase tracking-widest text-slate-400 flex items-center gap-2 px-1">
                          <Tag size={12} /> Voucher áp dụng
                        </Label>
                        <div className="h-14 bg-slate-50 border border-slate-100 rounded-2xl flex items-center px-5 font-bold text-slate-900 shadow-sm font-mono">
                          {detailDto.voucherCode}
                        </div>
                      </div>
                    )}

                    {detailDto?.posShiftRef && (
                      <div className="space-y-2">
                        <Label className="text-[10px] font-black uppercase tracking-widest text-slate-400 flex items-center gap-2 px-1">
                          <Store size={12} /> Ca POS
                        </Label>
                        <div className="h-14 bg-slate-50 border border-slate-100 rounded-2xl flex items-center px-5 font-bold text-slate-900 shadow-sm font-mono text-sm">
                          {detailDto.posShiftRef}
                        </div>
                      </div>
                    )}
                </div>
            </div>

            <Separator className="bg-slate-100" />

            {/* Row 2: Product List & Summary */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12">
                <div className="space-y-4">
                    <SectionHeader icon={ShoppingBag} title="Chi tiết sản phẩm" />
                    <div className="bg-white border border-slate-100 rounded-2xl overflow-hidden shadow-sm">
                        <table className="w-full text-left text-sm">
                            <thead>
                                <tr className="bg-slate-50/80 border-b border-slate-100">
                                    <th className="p-4 font-black text-slate-500 text-[10px] uppercase tracking-wider">Mặt hàng</th>
                                    <th className="p-4 font-black text-slate-500 text-[10px] uppercase tracking-wider text-right">S.Lượng</th>
                                    <th className="p-4 font-black text-slate-500 text-[10px] uppercase tracking-wider text-right">Thành tiền</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-50">
                                {lineItems.map((item) => (
                                    <tr key={item.id} className="hover:bg-slate-50/50 transition-colors">
                                        <td className="p-4">
                                            <p className="font-bold text-slate-900">{item.productName}</p>
                                            <p className="text-[10px] text-slate-400 font-mono tracking-tighter uppercase">{item.skuCode}</p>
                                        </td>
                                        <td className="p-4 text-right">
                                            <span className="font-bold text-slate-900">{item.quantity}</span>
                                            <span className="text-[10px] text-slate-400 ml-1 font-bold uppercase">{item.unitName}</span>
                                        </td>
                                        <td className="p-4 text-right font-black text-slate-900">
                                            {item.lineTotal.toLocaleString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div className="space-y-4 flex flex-col justify-end">
                    <SectionHeader icon={BarChart3} title="Tổng kết tài chính" />
                    <div className="p-6 bg-slate-900 rounded-3xl text-white shadow-2xl relative overflow-hidden group">
                        <Receipt className="absolute -right-4 -top-4 size-24 text-white/5 rotate-12 group-hover:rotate-0 transition-transform duration-700" />
                        <div className="space-y-4 relative z-10">
                            <div className="flex justify-between items-center opacity-60 text-[10px] uppercase tracking-[0.2em] font-black">
                                <span>Giá trị hàng hóa</span>
                                <span>{order.totalAmount.toLocaleString()} đ</span>
                            </div>
                            <div className="flex justify-between items-center text-red-400 text-[10px] uppercase tracking-[0.2em] font-black">
                                <span>Ưu đãi áp dụng</span>
                                <span>-{order.discountAmount?.toLocaleString() || 0} đ</span>
                            </div>
                            <Separator className="bg-white/10" />
                            <div className="pt-2">
                                <p className="text-[10px] uppercase tracking-[0.2em] font-black opacity-40 mb-1 text-center">Tổng tiền thanh toán</p>
                                <p className="text-4xl font-black text-center tracking-tighter tabular-nums">
                                    {order.finalAmount.toLocaleString()} <span className="text-sm font-normal opacity-40 uppercase tracking-normal">vnd</span>
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
          </div>
        </div>

        <div className="p-6 bg-slate-50 border-t border-slate-200 flex justify-between gap-3">
          {readOnly ? (
            <div className="flex w-full justify-end">
              <Button type="button" variant="outline" onClick={onClose} className="px-6 border-slate-300 min-h-11">
                Đóng
              </Button>
            </div>
          ) : (
            <>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  disabled={!onCancelOrder}
                  onClick={() => onCancelOrder?.(order)}
                  className="min-h-11 text-red-600 border-red-200 hover:bg-red-50 hover:text-red-700"
                >
                  <XCircle size={16} className="mr-2" /> Hủy đơn
                </Button>
              </div>
              <div className="flex gap-3">
                <Button variant="outline" onClick={onClose} className="px-6 border-slate-300">
                  Đóng
                </Button>
                <Button
                  type="button"
                  disabled={!onEditOrder}
                  className="min-h-11 bg-slate-900 hover:bg-slate-800 text-white px-6 shadow-lg shadow-slate-200"
                  onClick={() => {
                    if (!onEditOrder) return
                    onEditOrder(order)
                    onClose()
                  }}
                >
                  <Edit size={16} className="mr-2" /> Chỉnh sửa
                </Button>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function SectionHeader({ icon: Icon, title }: { icon: any, title: string }) {
    return (
        <h3 className="text-xs font-black uppercase tracking-[0.2em] text-slate-900 flex items-center gap-2">
            <Icon size={14} className="text-slate-400" /> {title}
        </h3>
    )
}

function Step({ icon: Icon, label, active }: { icon: any, label: string, active?: boolean }) {
    return (
        <div className="flex flex-col items-center gap-2 relative z-10 group">
            <div className={cn(
                "h-10 w-10 rounded-full flex items-center justify-center border-2 transition-all duration-500",
                active 
                    ? "bg-slate-900 border-slate-900 text-white shadow-[0_0_15px_rgba(15,23,42,0.3)] scale-110" 
                    : "bg-white border-slate-100 text-slate-300"
            )}>
                <Icon size={18} />
            </div>
            <span className={cn(
                "text-[10px] font-bold uppercase tracking-wider",
                active ? "text-slate-900" : "text-slate-300"
            )}>{label}</span>
        </div>
    )
}
