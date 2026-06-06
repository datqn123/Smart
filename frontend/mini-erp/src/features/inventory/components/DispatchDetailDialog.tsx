import React from "react"
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle,
  DialogDescription 
} from "@/components/ui/dialog"
import { formatDate } from "../utils"
import type { StockDispatch } from "../types"
import type { StockDispatchDetailResponse } from "../api/dispatchApi"
import { StatusBadge } from "./StatusBadge"
import { Package, Calendar, User, Truck, MapPin, ClipboardList, CheckCircle2, XCircle, Printer, Boxes, Timer, Activity, UserCircle, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { cn } from "@/lib/utils"

interface DispatchDetailDialogProps {
  dispatch: StockDispatch | null;
  isOpen: boolean;
  onClose: () => void;
  canApprove?: boolean;
  /** Admin — duyệt phiếu có stockdispatch_lines (Pending/Partial → chờ xuất). */
  canApproveStockLines?: boolean;
  onApproveStockDispatch?: () => void;
  approveStockDispatchPending?: boolean;
  /** Chi tiết REST (dòng thủ công, xóa mềm, thiếu hàng). */
  detailFromApi?: StockDispatchDetailResponse | null;
  detailLoading?: boolean;
}

export function DispatchDetailDialog({
  dispatch,
  isOpen,
  onClose,
  canApprove = false,
  canApproveStockLines = false,
  onApproveStockDispatch,
  approveStockDispatchPending = false,
  detailFromApi,
  detailLoading,
}: DispatchDetailDialogProps) {
  if (!dispatch) return null;

  const manualLines = detailFromApi?.lines && detailFromApi.lines.length > 0 ? detailFromApi.lines : null;
  const pickTotal = Math.max(manualLines?.length ?? dispatch.items.length, 1);
  const pickDone = manualLines
    ? manualLines.filter((l) => !l.shortageLine && l.quantity <= l.availableQuantity).length
    : dispatch.items.filter((i) => i.isFullyDispatched).length;

  const handleComplete = () => alert(`Đã hoàn tất xuất kho phiếu ${dispatch.dispatchCode}`);
  const handleCancel = () => alert(`Đã hủy phiếu ${dispatch.dispatchCode}`);

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-full sm:max-w-5xl lg:max-w-5xl max-h-[90vh] overflow-y-auto p-0 gap-0 border-slate-200 shadow-2xl rounded-2xl">
        <DialogHeader className="p-8 pb-4 bg-slate-50/50">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
            <div className="text-left">
              <div className="flex items-center gap-3 mb-2">
                <StatusBadge status={dispatch.status} type="dispatch" shortageWarning={dispatch.shortageWarning} />
                <span className="text-xs font-mono text-slate-400">Inventory ID: #{dispatch.id}</span>
              </div>
              <DialogTitle className="text-2xl font-black tracking-tight text-slate-900 flex items-center gap-2">
                Phiếu xuất kho <span className="text-slate-400 font-medium">#{dispatch.dispatchCode}</span>
              </DialogTitle>
              <p className="text-sm text-slate-500 mt-1 flex items-center gap-2 font-medium">
                <UserCircle size={14} className="text-slate-300" /> Khách hàng: <span className="font-bold text-slate-900">{dispatch.customerName}</span>
              </p>
            </div>
            
            <div className="flex items-center gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <div className="text-right border-r pr-4 border-slate-100">
                    <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Mã đơn hàng</p>
                    <p className="text-sm font-black text-slate-900">{dispatch.orderCode}</p>
                </div>
                <div className="text-right">
                    <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Số lượng hàng</p>
                    <p className="text-2xl font-black text-slate-900">
                      {dispatch.lineCount ?? dispatch.items.length}{" "}
                      <span className="text-[10px] text-slate-400">SKU</span>
                    </p>
                </div>
            </div>
          </div>
        </DialogHeader>

        <div className="p-8 pt-6">
          {detailLoading && <p className="text-xs text-slate-500 mb-4">Đang tải chi tiết phiếu…</p>}
          {detailFromApi?.deleteReason ? (
            <div className="mb-4 rounded-lg border border-red-200 bg-red-50 text-red-900 text-sm p-3">
              <p className="font-semibold">Phiếu đã xóa mềm</p>
              {detailFromApi.deletedByUserName ? (
                <p className="text-xs mt-1 text-red-800">Người xóa: {detailFromApi.deletedByUserName}</p>
              ) : null}
              <p className="mt-2 whitespace-pre-wrap text-red-950">{detailFromApi.deleteReason}</p>
            </div>
          ) : null}
          {detailFromApi?.shortageWarning && !detailFromApi?.deleteReason ? (
            <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 text-amber-950 text-sm p-3">
              Cảnh báo thiếu hàng
            </div>
          ) : null}
          {/* Status Progress Flow: Pending → WaitingDispatch → Delivering → Delivered */}
          {dispatch.status !== "Cancelled" && (
            <div className="mb-10 pt-2">
              <div className="flex justify-between relative">
                <div className="absolute top-5 left-0 w-full h-0.5 bg-slate-100 z-0" />
                <div className={cn(
                  "absolute top-5 left-0 h-0.5 bg-slate-900 z-0 transition-all duration-700",
                  dispatch.status === "Pending" ? "w-0" :
                  dispatch.status === "WaitingDispatch" ? "w-1/3" :
                  dispatch.status === "Delivering" || dispatch.status === "Partial" ? "w-2/3" :
                  "w-full",
                )} />
                <Step
                  icon={Clock}
                  label="Chờ duyệt"
                  active={dispatch.status === "Pending"}
                  done={["WaitingDispatch", "Delivering", "Partial", "Delivered", "Full"].includes(dispatch.status)}
                />
                <Step
                  icon={Timer}
                  label="Chờ xuất kho"
                  active={dispatch.status === "WaitingDispatch"}
                  done={["Delivering", "Partial", "Delivered", "Full"].includes(dispatch.status)}
                />
                <Step
                  icon={Activity}
                  label="Đang giao"
                  active={dispatch.status === "Delivering" || dispatch.status === "Partial"}
                  done={["Delivered", "Full"].includes(dispatch.status)}
                />
                <Step
                  icon={CheckCircle2}
                  label="Đã giao"
                  active={dispatch.status === "Delivered" || dispatch.status === "Full"}
                  done={false}
                />
              </div>
            </div>
          )}
          {dispatch.status === "Cancelled" && (
            <div className="mb-6 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <XCircle className="h-4 w-4 shrink-0" />
              <span className="font-medium">Phiếu xuất đã bị hủy</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-10 mb-8">
            <div className="space-y-6">
                <SectionHeader icon={ClipboardList} title="Chi tiết điều phối" />
                <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                        <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-1">Ngày xuất dự kiến</p>
                        <p className="text-sm font-bold text-slate-900">{formatDate(dispatch.dispatchDate)}</p>
                    </div>
                    <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                        <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-1">Kho xuất hàng</p>
                        <p className="text-sm font-bold text-slate-900">Kho Trung Tâm</p>
                    </div>
                </div>

                <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-sm space-y-3">
                    <InfoLine icon={Truck} label="Hình thức" value="Giao hàng tận nơi" />
                    <InfoLine icon={User} label="Nhân viên phụ trách" value={dispatch.userName} />
                </div>

                {dispatch.notes && (
                    <div className="p-4 bg-slate-50 border border-slate-100 rounded-xl">
                        <p className="text-[10px] text-slate-400 font-black uppercase tracking-widest mb-2 flex items-center gap-1.5">
                            <ClipboardList size={12} /> Chỉ dẫn Picking
                        </p>
                        <p className="text-sm text-slate-700 italic leading-relaxed">"{dispatch.notes}"</p>
                    </div>
                )}
            </div>

            <div className="space-y-4">
                <SectionHeader icon={Boxes} title="Picking List / Phiếu soạn hàng" />
                <div className="bg-white border border-slate-100 rounded-2xl overflow-hidden shadow-sm">
                    <Table>
                        <TableHeader className="bg-slate-50/50">
                            <TableRow className="hover:bg-transparent border-0">
                                <TableHead className="font-bold text-slate-400 text-[10px] uppercase tracking-wider h-10">Sản phẩm / Vị trí</TableHead>
                                <TableHead className="font-bold text-slate-400 text-[10px] uppercase tracking-wider h-10 text-right">SL Đặt</TableHead>
                                <TableHead className="font-bold text-slate-400 text-[10px] uppercase tracking-wider h-10 text-right">Thực xuất</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {manualLines
                              ? manualLines.map((row) => (
                                  <TableRow key={row.lineId} className="hover:bg-slate-50/30 transition-colors border-slate-50">
                                    <TableCell className="py-3">
                                      <p className="font-bold text-slate-900">{row.productName}</p>
                                      <p className="text-[10px] text-slate-500 font-medium bg-slate-100 px-1.5 py-0.5 rounded-md inline-block mt-1">
                                        {row.warehouseCode} — {row.shelfCode}
                                      </p>
                                      {row.shortageLine ? (
                                        <p className="text-[10px] text-amber-700 font-bold mt-1">Thiếu hàng</p>
                                      ) : null}
                                    </TableCell>
                                    <TableCell className="py-3 text-right">
                                      <span className="text-xs text-slate-400">Tồn {row.availableQuantity}</span>
                                    </TableCell>
                                    <TableCell className="py-3 text-right">
                                      <span className={cn("font-black text-slate-900", row.shortageLine && "text-amber-600")}>
                                        {row.quantity}
                                      </span>
                                    </TableCell>
                                  </TableRow>
                                ))
                              : dispatch.items.map((item) => (
                                  <TableRow key={item.id} className="hover:bg-slate-50/30 transition-colors border-slate-50">
                                    <TableCell className="py-3">
                                      <p className="font-bold text-slate-900">{item.productName}</p>
                                      <p className="text-[10px] text-slate-500 font-medium bg-slate-100 px-1.5 py-0.5 rounded-md inline-block mt-1">
                                        {item.warehouseLocation} - {item.shelfCode}
                                      </p>
                                    </TableCell>
                                    <TableCell className="py-3 text-right">
                                      <span className="text-xs text-slate-400">{item.orderedQty} {item.unitName}</span>
                                    </TableCell>
                                    <TableCell className="py-3 text-right">
                                      <span className={cn(
                                        "font-black text-slate-900",
                                        item.dispatchQty < item.orderedQty && "text-amber-600",
                                      )}>
                                        {item.dispatchQty}
                                      </span>
                                      <span className="text-[10px] text-slate-400 ml-1">{item.unitName}</span>
                                    </TableCell>
                                  </TableRow>
                                ))}
                        </TableBody>
                    </Table>
                </div>

                <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex items-center justify-between">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Tình trạng soạn hàng</p>
                    <div className="flex items-center gap-2">
                         <div className="h-2 w-24 bg-slate-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-slate-900 transition-all duration-1000"
                              style={{ width: `${(pickDone / pickTotal) * 100}%` }}
                            />
                         </div>
                         <span className="text-[10px] font-black text-slate-900">
                           {pickDone}/{pickTotal}
                         </span>
                    </div>
                </div>
            </div>
          </div>
        </div>

        <div className="p-6 bg-slate-50 border-t border-slate-200 flex flex-col sm:flex-row justify-between items-center gap-4">
           <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" className="h-10 border-slate-300 bg-white shadow-sm">
                <Printer size={16} className="mr-2" /> In Picking List
              </Button>
           </div>
           
           <div className="flex gap-3 ml-auto">
              <Button variant="outline" onClick={onClose} className="border-slate-300 h-10 px-6">Đóng</Button>
              {canApproveStockLines &&
                onApproveStockDispatch &&
                detailFromApi &&
                (detailFromApi.status === "Pending" || detailFromApi.status === "Partial") &&
                detailFromApi.stockLinesFulfillment &&
                !detailFromApi.shortageWarning &&
                !detailFromApi.deleteReason && (
                  <Button
                    type="button"
                    className="bg-emerald-700 hover:bg-emerald-800 text-white h-10 px-6"
                    disabled={approveStockDispatchPending}
                    onClick={onApproveStockDispatch}
                  >
                    <CheckCircle2 className="w-4 h-4 mr-2" /> Duyệt phiếu (chờ xuất)
                  </Button>
                )}
              {canApprove &&
                !detailFromApi?.manualDispatch &&
                !detailFromApi?.stockLinesFulfillment &&
                (dispatch.status === "Pending" || dispatch.status === "Partial") && (
                <>
                  <Button variant="outline" className="border-red-200 text-red-600 hover:bg-red-50 h-10 px-6" onClick={handleCancel}>
                    <XCircle className="w-4 h-4 mr-2" /> Hủy phiếu
                  </Button>
                  <Button className="bg-slate-900 hover:bg-slate-800 text-white h-10 px-8 shadow-xl shadow-slate-200" onClick={handleComplete}>
                    <CheckCircle2 className="w-4 h-4 mr-2" /> Hoàn tất xuất kho
                  </Button>
                </>
              )}
           </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function SectionHeader({ icon: Icon, title }: { icon: any, title: string }) {
    return (
        <h3 className="text-[11px] font-black uppercase tracking-[0.3em] text-slate-900 flex items-center gap-2 mb-4">
            <div className="p-1.5 bg-slate-100 rounded-lg"><Icon size={14} className="text-slate-900" /></div> {title}
        </h3>
    )
}

function InfoLine({ icon: Icon, label, value }: { icon: any, label: string, value: string }) {
    return (
        <div className="flex items-center justify-between border-b border-slate-50 pb-2 last:border-0 last:pb-0">
            <div className="flex items-center gap-2 text-slate-400">
                <Icon size={14} />
                <span className="text-xs font-bold uppercase tracking-widest">{label}</span>
            </div>
            <span className="text-sm font-bold text-slate-900">{value}</span>
        </div>
    )
}

function Step({ icon: Icon, label, active, done }: { icon: React.ElementType, label: string, active?: boolean, done?: boolean }) {
    return (
        <div className="flex flex-col items-center gap-2 relative z-10">
            <div className={cn(
                "h-10 w-10 rounded-xl flex items-center justify-center border-2 transition-all duration-500",
                active
                    ? "bg-slate-900 border-slate-900 text-white shadow-[0_8px_16px_rgba(15,23,42,0.2)] scale-110"
                    : done
                      ? "bg-green-600 border-green-600 text-white"
                      : "bg-white border-slate-100 text-slate-300"
            )}>
                {done ? <CheckCircle2 size={18} /> : <Icon size={18} />}
            </div>
            <span className={cn(
                "text-[10px] font-black uppercase tracking-widest whitespace-nowrap",
                active ? "text-slate-900" : done ? "text-green-700" : "text-slate-300"
            )}>{label}</span>
        </div>
    )
}
