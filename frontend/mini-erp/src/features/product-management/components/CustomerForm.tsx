import React, { useEffect, useState } from "react"
import { useForm, type FieldPath } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { X, User, Phone, Mail, MapPin, CheckCircle2, UserPlus, Trophy } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"
import { FORM_LABEL_CLASS, FORM_INPUT_CLASS } from "@/lib/data-table-layout"
import { ApiRequestError } from "@/lib/api/http"
import { toast } from "sonner"
import { applyCustomerCreateApiError } from "../api/customersApi"
import type { Customer } from "../types"
import { customerSchema, type CustomerFormData } from "../validation"

/** Báo form: đừng đóng dialog (Task051 hoặc trạng thái chưa sẵn sàng). */
export class CustomerFormSubmitAborted extends Error {
  constructor() {
    super("CustomerFormSubmitAborted")
    this.name = "CustomerFormSubmitAborted"
  }
}

interface CustomerFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  customer?: Customer
  /** Task051 / BR-3 — Staff không gửi `loyaltyPoints` (403); ẩn field khi sửa. */
  canEditLoyaltyPoints?: boolean
  onSubmit: (data: CustomerFormData) => void | Promise<void>
}

export function CustomerForm({
  open,
  onOpenChange,
  customer,
  canEditLoyaltyPoints = true,
  onSubmit,
}: CustomerFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)

  const form = useForm<CustomerFormData>({
    resolver: zodResolver(customerSchema),
    defaultValues: {
      name: "",
      customerCode: "",
      phone: "",
      email: "",
      address: "",
      status: "Active",
    },
  })

  useEffect(() => {
    if (!open) {
      return
    }
    if (customer) {
      form.reset({
        name: customer.name,
        customerCode: customer.customerCode,
        phone: customer.phone,
        email: customer.email || "",
        address: customer.address || "",
        status: customer.status,
        ...(canEditLoyaltyPoints ? { loyaltyPoints: customer.loyaltyPoints } : {}),
      })
    } else {
      form.reset({
        name: "",
        customerCode: `KH${Math.floor(Math.random() * 10000)
          .toString()
          .padStart(5, "0")}`,
        phone: "",
        email: "",
        address: "",
        status: "Active",
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reset theo dialog / khách / quyền
  }, [open, customer, customer?.id, customer?.updatedAt, canEditLoyaltyPoints])

  const handleLocalSubmit = async (data: CustomerFormData) => {
    setIsSubmitting(true)
    form.clearErrors()
    try {
      await onSubmit(data)
      onOpenChange(false)
    } catch (err) {
      if (err instanceof CustomerFormSubmitAborted) {
        return
      }
      if (err instanceof ApiRequestError) {
        const n = applyCustomerCreateApiError(
          (name, e) => {
            form.setError(name as FieldPath<CustomerFormData>, e)
          },
          err,
        )
        if (n === 0) {
          toast.error(err.body?.message ?? err.message)
        }
      } else {
        toast.error(err instanceof Error ? err.message : "Không thể lưu")
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const showLoyaltyField = Boolean(customer) && canEditLoyaltyPoints

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl p-0 overflow-hidden border-slate-200 shadow-2xl rounded-2xl">
        <DialogHeader className="p-8 pb-6 bg-slate-50/50 border-b border-slate-100">
          <div className="flex items-center gap-3 text-slate-400 mb-1">
            <UserPlus size={16} />
            <span className="text-[10px] font-bold uppercase tracking-widest">Hồ sơ khách hàng</span>
          </div>
          <DialogTitle className="text-2xl font-black text-slate-900">
            {customer ? "Cập nhật thông tin khách hàng" : "Thêm mới khách hàng"}
          </DialogTitle>
          <DialogDescription className="text-slate-500">
            Quản lý thông tin liên hệ và hạng thành viên của khách hàng.
            {customer && !canEditLoyaltyPoints ? (
              <span className="block mt-2 text-amber-900/85 text-xs font-medium">
                Vai trò Staff không chỉnh điểm tích lũy trên form (tránh 403 từ server).
              </span>
            ) : null}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={form.handleSubmit(handleLocalSubmit)} className="p-8 space-y-6 bg-white">
          <div className="grid grid-cols-2 gap-x-6 gap-y-5">
            <div className="space-y-2">
              <Label className={FORM_LABEL_CLASS}>Mã khách hàng *</Label>
              <Input
                {...form.register("customerCode")}
                className={cn(FORM_INPUT_CLASS, "font-mono")}
                placeholder="KH00001"
              />
              {form.formState.errors.customerCode && (
                <p className="text-xs text-red-500">{form.formState.errors.customerCode.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label className={FORM_LABEL_CLASS}>Trạng thái</Label>
              <Select
                value={form.watch("status")}
                onValueChange={(val) => {
                  form.setValue("status", val as "Active" | "Inactive")
                }}
              >
                <SelectTrigger className={FORM_INPUT_CLASS}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Active">Đang hoạt động</SelectItem>
                  <SelectItem value="Inactive">Tạm ngưng</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2 col-span-2">
              <Label className={FORM_LABEL_CLASS}>Tên khách hàng *</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-4 w-4" />
                <Input
                  {...form.register("name")}
                  className={cn(FORM_INPUT_CLASS, "pl-10 font-semibold text-slate-900")}
                  placeholder="Nguyễn Văn A"
                />
              </div>
              {form.formState.errors.name && <p className="text-xs text-red-500">{form.formState.errors.name.message}</p>}
            </div>

            <div className="space-y-2">
              <Label className={FORM_LABEL_CLASS}>Số điện thoại *</Label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-4 w-4" />
                <Input
                  {...form.register("phone")}
                  className={cn(FORM_INPUT_CLASS, "pl-10")}
                  placeholder="09xxx..."
                />
              </div>
              {form.formState.errors.phone && (
                <p className="text-xs text-red-500">{form.formState.errors.phone.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label className={FORM_LABEL_CLASS}>Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-4 w-4" />
                <Input
                  {...form.register("email")}
                  className={cn(FORM_INPUT_CLASS, "pl-10")}
                  placeholder="example@mail.com"
                />
              </div>
              {form.formState.errors.email && (
                <p className="text-xs text-red-500">{form.formState.errors.email.message}</p>
              )}
            </div>

            <div className="space-y-2 col-span-2">
              <Label className={FORM_LABEL_CLASS}>Địa chỉ</Label>
              <div className="relative">
                <MapPin className="absolute left-3 top-3 text-slate-400 h-4 w-4" />
                <Input
                  {...form.register("address")}
                  className={cn(FORM_INPUT_CLASS, "h-20 pl-10 flex items-start pt-2")}
                  placeholder="Số nhà, đường, phường/xã..."
                />
              </div>
            </div>

            {showLoyaltyField ? (
              <div className="space-y-2 col-span-2">
                <Label className={FORM_LABEL_CLASS}>Điểm tích lũy</Label>
                <div className="relative max-w-xs">
                  <Trophy className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-4 w-4" />
                  <Input
                    type="number"
                    min={0}
                    step={1}
                    {...form.register("loyaltyPoints", { valueAsNumber: true })}
                    className={cn(FORM_INPUT_CLASS, "pl-10 tabular-nums")}
                  />
                </div>
                {form.formState.errors.loyaltyPoints ? (
                  <p className="text-xs text-red-500">{form.formState.errors.loyaltyPoints.message}</p>
                ) : null}
              </div>
            ) : null}
          </div>
        </form>

        <DialogFooter className="p-8 bg-slate-50 border-t border-slate-100">
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="h-11 px-6 border-slate-300 font-medium text-slate-600"
          >
            <X className="h-4 w-4 mr-2" />
            Hủy bỏ
          </Button>
          <Button
            type="button"
            disabled={isSubmitting}
            onClick={form.handleSubmit(handleLocalSubmit)}
            className="h-11 px-8 bg-slate-900 hover:bg-slate-800 text-white shadow-lg shadow-slate-200"
          >
            <CheckCircle2 className="h-4 w-4 mr-2" />
            Lưu khách hàng
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
