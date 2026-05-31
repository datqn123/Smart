import { useEffect, useState } from "react"
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle,
} from "@/components/ui/dialog"
import type { Employee } from "../types"
import { User, Shield, Mail, Phone, Calendar, Activity, BadgeCheck, Lock, type LucideIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { ApiRequestError } from "@/lib/api/http"
import { getUserById, type UserDetailData } from "../api/usersApi"
import {
  FORM_LABEL_CLASS,
} from "@/lib/data-table-layout"

interface EmployeeDetailDialogProps {
  employee: Employee | null;
  isOpen: boolean;
  onClose: () => void;
}

export function EmployeeDetailDialog({ employee, isOpen, onClose }: EmployeeDetailDialogProps) {
  const [loading, setLoading] = useState(false)
  const [detail, setDetail] = useState<UserDetailData | null>(null)

  useEffect(() => {
    if (!isOpen || !employee) {
      setDetail(null)
      setLoading(false)
      return
    }
    let cancelled = false
    void (async () => {
      setLoading(true)
      try {
        const data = await getUserById(employee.id)
        if (!cancelled) setDetail(data)
      } catch (e) {
        if (e instanceof ApiRequestError) {
          // RBAC self-view (OQ-1): Staff có thể bị 403 khi xem người khác
          // Chỉ toast 1 câu ngắn theo message để UI không crash
          // (không phân nhánh theo error code vì backend đã chuẩn hoá message)
          console.warn("getUserById failed", e.status, e.body?.error)
        }
        if (!cancelled) setDetail(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [isOpen, employee])

  const username = detail?.username ?? null
  const lastLogin = detail?.lastLogin ?? null

  if (!employee) return null;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-full sm:max-w-3xl lg:max-w-3xl p-0 overflow-hidden border-slate-200 shadow-2xl rounded-2xl">
        <DialogHeader className="p-8 pb-4 bg-slate-50/50">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-6">
                <div className="h-20 w-20 rounded-2xl bg-slate-900 flex items-center justify-center text-white text-3xl font-black shadow-xl">
                    {employee.fullName.charAt(0)}
                </div>
                <div className="text-left">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={cn(
                      "px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-widest border",
                      employee.status === "Active" ? "bg-green-50 text-green-700 border-green-100" : "bg-slate-100 text-slate-500 border-slate-200"
                    )}>
                      {employee.status === "Active" ? "Active" : "Inactive"}
                    </span>
                    <span className="text-xs font-mono text-slate-400">ID: {employee.employeeCode}</span>
                  </div>
                  <DialogTitle className="text-2xl font-black tracking-tight text-slate-900 flex items-center gap-2">
                    {employee.fullName}
                  </DialogTitle>
                  <p className="text-sm font-bold text-slate-500 mt-1 flex items-center gap-2">
                    <Shield size={14} className="text-blue-500" /> Vai trò: <span className="text-slate-900">{employee.role}</span>
                  </p>
                  {loading && (
                    <p className="text-xs text-slate-400 mt-2">Đang tải chi tiết…</p>
                  )}
                </div>
            </div>
            
            <div className="flex items-center gap-2">
                 <Button variant="outline" className="h-10 border-slate-200">
                    <Lock size={14} className="mr-2" /> Đổi mật khẩu
                 </Button>
            </div>
          </div>
        </DialogHeader>

        <div className="p-8 pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                <div className="space-y-6">
                    <div>
                        <h3 className={cn(FORM_LABEL_CLASS, "mb-4")}>
                            <User size={14} className="inline mr-1" /> Thông tin liên hệ
                        </h3>
                        <div className="space-y-4">
                            <InfoCard icon={Mail} label="Địa chỉ Email" value={employee.email} />
                            <InfoCard icon={Phone} label="Số điện thoại" value={employee.phone} />
                            <InfoCard icon={Calendar} label="Ngày gia nhập" value={new Date(employee.joinedDate).toLocaleDateString('vi-VN')} />
                            {username && <InfoCard icon={User} label="Tên đăng nhập" value={username} />}
                        </div>
                    </div>
                </div>

                <div className="space-y-6">
                     <div>
                        <h3 className={cn(FORM_LABEL_CLASS, "mb-4")}>
                            <Activity size={14} className="inline mr-1" /> Hoạt động hệ thống
                        </h3>
                        <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 space-y-4">
                             <div className="flex items-center justify-between">
                                <span className="text-xs text-slate-500">Trạng thái đăng nhập</span>
                                <span className="flex items-center gap-1.5 text-xs font-bold text-green-600">
                                    <div className="h-1.5 w-1.5 rounded-full bg-green-600 animate-pulse" /> Trực tuyến
                                </span>
                             </div>
                             <div className="flex items-center justify-between">
                                <span className="text-xs text-slate-500">Lần cuối hoạt động</span>
                                <span className="text-xs font-bold text-slate-900">
                                  {lastLogin ? new Date(lastLogin).toLocaleString("vi-VN") : "—"}
                                </span>
                             </div>
                             <div className="flex items-center justify-between">
                                <span className="text-xs text-slate-500">Tổng số thao tác</span>
                                <span className="text-xs font-bold text-slate-900">1,240</span>
                             </div>
                        </div>
                    </div>
                </div>
          </div>

          <div className="p-4 bg-slate-900 rounded-2xl text-white flex items-center justify-between shadow-xl">
               <div className="flex items-center gap-3">
                    <BadgeCheck className="text-blue-400" />
                    <div>
                        <p className="text-xs font-bold uppercase tracking-widest opacity-60">Xác thực tài khoản</p>
                        <p className="text-sm font-bold text-white">Đã định danh (Identity Verified)</p>
                    </div>
               </div>
               <Button className="bg-white/10 hover:bg-white/20 text-white text-xs border-0 h-8">
                  Xem nhật ký
               </Button>
          </div>
        </div>

        <div className="p-6 bg-slate-50 border-t border-slate-200 flex justify-end gap-3">
           <Button variant="outline" onClick={onClose} className="px-6 border-slate-300">Đóng</Button>
           <Button className="bg-slate-900 hover:bg-slate-800 text-white px-6 shadow-lg shadow-slate-200">
             Chỉnh sửa hồ sơ
           </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function InfoCard({ icon: Icon, label, value }: { icon: LucideIcon, label: string, value: string }) {
    return (
        <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-slate-100 flex items-center justify-center text-slate-500 border border-slate-200">
                <Icon size={16} />
            </div>
            <div>
                <p className={cn(FORM_LABEL_CLASS, "leading-none mb-1")}>{label}</p>
                <p className="text-sm font-bold text-slate-900 leading-none">{value}</p>
            </div>
        </div>
    )
}
