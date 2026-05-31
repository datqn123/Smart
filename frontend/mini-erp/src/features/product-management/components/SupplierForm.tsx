import React, { useState } from "react"
import { useForm, type FieldPath } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { Building2, Phone, Mail, MapPin, CheckCircle2, CreditCard, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogFooter,
  DialogDescription 
} from "@/components/ui/dialog"
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"
import { FORM_LABEL_CLASS, FORM_INPUT_CLASS } from "@/lib/data-table-layout"
import { ApiRequestError } from "@/lib/api/http"
import { toast } from "sonner"
import type { Supplier } from "../types"
import { supplierSchema, type SupplierFormData } from "../validation"

/** Báo cho form: đừng đóng dialog (Task045 trở lên mới nối PATCH). */
export class SupplierFormSubmitAborted extends Error {
  constructor() {
    super("SupplierFormSubmitAborted")
    this.name = "SupplierFormSubmitAborted"
  }
}

const SUPPLIER_ERROR_FIELDS: FieldPath<SupplierFormData>[] = [
  "supplierCode",
  "name",
  "contactPerson",
  "phone",
  "email",
  "address",
  "taxCode",
  "status",
]

function applyApiDetailsToForm(
  setError: (name: FieldPath<SupplierFormData>, error: { message: string }) => void,
  e: ApiRequestError,
): number {
  const d = e.body?.details
  if (!d || typeof d !== "object") {
    return 0
  }
  let n = 0
  for (const key of SUPPLIER_ERROR_FIELDS) {
    const v = d[key as string]
    if (v != null && String(v).length > 0) {
      setError(key, { message: String(v) })
      n += 1
    }
  }
  return n
}

interface SupplierFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  supplier?: Supplier
  onSubmit: (data: SupplierFormData) => void | Promise<void>
}

export function SupplierForm({ open, onOpenChange, supplier, onSubmit }: SupplierFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)

  const form = useForm<SupplierFormData>({
    resolver: zodResolver(supplierSchema),
    defaultValues: supplier ? {
      name: supplier.name,
      supplierCode: supplier.supplierCode,
      contactPerson: supplier.contactPerson || "",
      phone: supplier.phone,
      email: supplier.email || "",
      address: supplier.address || "",
      taxCode: supplier.taxCode || "",
      status: supplier.status,
    } : {
      name: "",
      supplierCode: `NCC${Math.floor(Math.random() * 10000).toString().padStart(4, '0')}`,
      contactPerson: "",
      phone: "",
      email: "",
      address: "",
      taxCode: "",
      status: "Active",
    }
  })

  const { errors } = form.formState

  const handleLocalSubmit = async (data: SupplierFormData) => {
    setIsSubmitting(true)
    form.clearErrors()
    try {
      await onSubmit(data)
      onOpenChange(false)
    } catch (err) {
      if (err instanceof SupplierFormSubmitAborted) {
        return
      }
      if (err instanceof ApiRequestError) {
        const n = applyApiDetailsToForm(form.setError, err)
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

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[90dvh] w-full max-w-2xl flex-col gap-0 overflow-hidden border-slate-200 p-0 shadow-2xl rounded-2xl">
        <DialogHeader className="shrink-0 p-8 pb-6 bg-slate-50/50 border-b border-slate-100">
          <div className="flex items-center gap-3 text-slate-400 mb-1">
            <Building2 size={16} />
            <span className="text-[10px] font-bold uppercase tracking-widest">Hồ sơ nhà cung cấp</span>
          </div>
          <DialogTitle className="text-2xl font-black text-slate-900">
            {supplier ? "Cập nhật nhà cung cấp" : "Thêm mới nhà cung cấp"}
          </DialogTitle>
          <DialogDescription className="text-slate-500">
            Quản lý thông tin pháp nhân và đầu mối liên hệ của đối tác.
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={form.handleSubmit(handleLocalSubmit)}
          className="min-h-0 flex-1 space-y-6 overflow-y-auto bg-white p-8"
        >
          <div className="grid grid-cols-2 gap-x-6 gap-y-5">
             <div className="space-y-2">
                <Label className={FORM_LABEL_CLASS}>Mã nhà cung cấp *</Label>
                <Input
                  {...form.register("supplierCode")}
                  className={cn(FORM_INPUT_CLASS, "font-mono", errors.supplierCode && "border-red-300")}
                  placeholder="NCC0001"
                />
                {errors.supplierCode?.message ? (
                  <p className="text-sm text-red-600">{errors.supplierCode.message}</p>
                ) : null}
             </div>

             <div className="space-y-2">
                <Label className={FORM_LABEL_CLASS}>Trạng thái</Label>
                <Select 
                  defaultValue={form.getValues("status")}
                  onValueChange={(val) => form.setValue("status", val as "Active" | "Inactive")}
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
                <Label className={FORM_LABEL_CLASS}>Tên nhà cung cấp *</Label>
                <div className="relative">
                    <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-4 w-4" />
                    <Input
                      {...form.register("name")}
                      className={cn(FORM_INPUT_CLASS, "pl-10 font-semibold text-slate-900", errors.name && "border-red-300")}
                    />
                </div>
                {errors.name?.message ? <p className="text-sm text-red-600">{errors.name.message}</p> : null}
             </div>

             <div className="space-y-2">
                <Label className={FORM_LABEL_CLASS}>Người liên hệ *</Label>
                <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-4 w-4" />
                    <Input
                      {...form.register("contactPerson")}
                      className={cn(FORM_INPUT_CLASS, "pl-10", errors.contactPerson && "border-red-300")}
                    />
                </div>
                {errors.contactPerson?.message ? (
                  <p className="text-sm text-red-600">{errors.contactPerson.message}</p>
                ) : null}
             </div>

             <div className="space-y-2">
                <Label className={FORM_LABEL_CLASS}>Mã số thuế</Label>
                <div className="relative">
                    <CreditCard className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-4 w-4" />
                    <Input 
                        {...form.register("taxCode")} 
                        className={cn(FORM_INPUT_CLASS, "pl-10")}
                    />
                </div>
             </div>

             <div className="space-y-2">
                <Label className={FORM_LABEL_CLASS}>Số điện thoại *</Label>
                <div className="relative">
                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-4 w-4" />
                    <Input 
                        {...form.register("phone")} 
                        className={cn(FORM_INPUT_CLASS, "pl-10")}
                    />
                </div>
             </div>

             <div className="space-y-2">
                <Label className={FORM_LABEL_CLASS}>Email</Label>
                <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-4 w-4" />
                    <Input
                      {...form.register("email")}
                      className={cn(FORM_INPUT_CLASS, "pl-10", errors.email && "border-red-300")}
                    />
                </div>
                {errors.email?.message ? <p className="text-sm text-red-600">{errors.email.message}</p> : null}
             </div>

             <div className="space-y-2 col-span-2">
                <Label className={FORM_LABEL_CLASS}>Địa chỉ</Label>
                <div className="relative">
                    <MapPin className="absolute left-3 top-3 text-slate-400 h-4 w-4" />
                    <Input 
                        {...form.register("address")} 
                        className={cn(FORM_INPUT_CLASS, "h-20 pl-10 flex items-start pt-2")}
                    />
                </div>
             </div>
          </div>
        </form>

        <DialogFooter className="shrink-0 border-t border-slate-100 bg-slate-50 p-8">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)} className="h-11 px-6 border-slate-300 font-medium text-slate-600">
            Hủy bỏ
          </Button>
          <Button type="submit" disabled={isSubmitting} onClick={form.handleSubmit(handleLocalSubmit)} className="h-11 px-8 bg-slate-900 hover:bg-slate-800 text-white shadow-lg shadow-slate-200">
            <CheckCircle2 className="h-4 w-4 mr-2" />
            Lưu nhà cung cấp
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
