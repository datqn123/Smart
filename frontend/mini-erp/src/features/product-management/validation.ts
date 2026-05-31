import { z } from "zod"

export const PHONE_FORMAT_MESSAGE = "Số điện thoại không đúng định dạng"
const PHONE_REGEX = /^0\d{9}$/

export const customerSchema = z.object({
  name: z.string().min(1, "Vui lòng nhập tên khách hàng").max(255),
  customerCode: z.string().min(1, "Vui lòng nhập mã khách hàng").max(50),
  phone: z
    .string()
    .min(1, "Vui lòng nhập số điện thoại")
    .regex(PHONE_REGEX, PHONE_FORMAT_MESSAGE),
  email: z.string().email("Email không hợp lệ").optional().or(z.literal("")),
  address: z.string().optional(),
  status: z.enum(["Active", "Inactive"]),
  loyaltyPoints: z.coerce.number().int().min(0).optional(),
})

export type CustomerFormData = z.infer<typeof customerSchema>

export const supplierSchema = z.object({
  name: z.string().min(1, "Vui lòng nhập tên nhà cung cấp"),
  supplierCode: z.string().min(1, "Vui lòng nhập mã nhà cung cấp"),
  contactPerson: z.string().min(1, "Vui lòng nhập người liên hệ"),
  phone: z
    .string()
    .min(1, "Vui lòng nhập số điện thoại")
    .regex(PHONE_REGEX, PHONE_FORMAT_MESSAGE),
  email: z.string().email("Email không hợp lệ").optional().or(z.literal("")),
  address: z.string().optional(),
  taxCode: z
    .string()
    .regex(/^\d{10}$/, "Mã số thuế phải là 10 số")
    .optional()
    .or(z.literal("")),
  status: z.enum(["Active", "Inactive"]),
})

export type SupplierFormData = z.infer<typeof supplierSchema>

export function validateCustomerForm(data: CustomerFormData): string[] {
  const result = customerSchema.safeParse(data)
  return result.success ? [] : result.error.issues.map((issue) => issue.message)
}

export function validateSupplierForm(data: SupplierFormData): string[] {
  const result = supplierSchema.safeParse(data)
  return result.success ? [] : result.error.issues.map((issue) => issue.message)
}
