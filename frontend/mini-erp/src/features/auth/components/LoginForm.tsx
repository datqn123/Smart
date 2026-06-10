import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Loader2, Eye, EyeOff } from "lucide-react"
import { useNavigate } from "react-router-dom"
import { ApiRequestError } from "@/lib/api/http"
import { postLogin, postPasswordResetRequest } from "@/features/auth/api/authApi"
import { useAuthStore, type UserRole } from "@/features/auth/store/useAuthStore"

const loginSchema = z.object({
  email: z
    .string()
    .min(1, { message: "Email là bắt buộc" })
    .email({ message: "Email không hợp lệ" }),
  password: z
    .string()
    .min(6, { message: "Mật khẩu phải có ít nhất 6 ký tự" })
    .refine((s) => s.trim().length > 0, { message: "Mật khẩu là bắt buộc" }),
})

const ownerResetRequestSchema = z.object({
  username: z.string().min(1, { message: "Vui lòng nhập tên đăng nhập" }),
  message: z.string().max(500).optional(),
})

type LoginFormValues = z.infer<typeof loginSchema>
type OwnerResetRequestValues = z.infer<typeof ownerResetRequestSchema>

export function LoginForm() {
  const [isLoading, setIsLoading] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)
  const [ownerResetOpen, setOwnerResetOpen] = useState(false)
  const [ownerResetSubmitting, setOwnerResetSubmitting] = useState(false)
  const [ownerResetSuccess, setOwnerResetSuccess] = useState(false)
  const [ownerResetError, setOwnerResetError] = useState<string | null>(null)
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  })

  const ownerResetForm = useForm<OwnerResetRequestValues>({
    resolver: zodResolver(ownerResetRequestSchema),
    defaultValues: { username: "", message: "" },
  })

  function handleOwnerResetDialogChange(open: boolean) {
    setOwnerResetOpen(open)
    if (!open) {
      setOwnerResetSuccess(false)
      setOwnerResetError(null)
      ownerResetForm.reset()
    }
  }

  async function onSubmit(data: LoginFormValues) {
    setIsLoading(true)
    setSubmitError(null)
    try {
      const result = await postLogin({ email: data.email, password: data.password })
      sessionStorage.setItem("accessToken", result.accessToken)
      sessionStorage.setItem("refreshToken", result.refreshToken)
      sessionStorage.setItem("user", JSON.stringify(result.user))
      useAuthStore.getState().login(
        {
          id: result.user.id,
          fullName: result.user.fullName,
          email: result.user.email,
          username: result.user.username,
          role: result.user.role as UserRole,
        },
        result.accessToken,
      )
      navigate("/dashboard")
    } catch (err) {
      if (err instanceof ApiRequestError && err.status === 400 && err.body.details) {
        const d = err.body.details
        if (d.email) {
          setError("email", { message: d.email })
        }
        if (d.password) {
          setError("password", { message: d.password })
        }
        if (!d.email && !d.password) {
          setSubmitError(err.body.message)
        }
        return
      }
      if (err instanceof ApiRequestError) {
        setSubmitError(err.body.message ?? err.message)
        return
      }
      setSubmitError(err instanceof Error ? err.message : "Đăng nhập thất bại")
    } finally {
      setIsLoading(false)
    }
  }

  async function onOwnerResetSubmit(data: OwnerResetRequestValues) {
    setOwnerResetSubmitting(true)
    setOwnerResetError(null)
    try {
      await postPasswordResetRequest({
        username: data.username.trim(),
        message: data.message?.trim() ? data.message.trim() : undefined,
      })
      setOwnerResetSuccess(true)
    } catch (err) {
      if (err instanceof ApiRequestError && err.status === 400 && err.body.details) {
        const d = err.body.details
        if (d.username) {
          ownerResetForm.setError("username", { message: d.username })
        }
        if (d.message) {
          ownerResetForm.setError("message", { message: d.message })
        }
        if (!d.username && !d.message) {
          setOwnerResetError(err.body.message)
        }
        return
      }
      if (err instanceof ApiRequestError) {
        setOwnerResetError(err.body.message ?? err.message)
        return
      }
      setOwnerResetError(err instanceof Error ? err.message : "Không gửi được yêu cầu. Vui lòng thử lại.")
    } finally {
      setOwnerResetSubmitting(false)
    }
  }

  return (
    <Card className="w-full max-w-md bg-white shadow-sm border border-border rounded-lg lg:rounded-xl">
      <CardHeader className="space-y-1 pb-8">
        <CardTitle className="text-xl font-semibold text-foreground tracking-tight">
          Chào mừng trở lại
        </CardTitle>
        <CardDescription className="text-muted-foreground font-normal leading-relaxed">
          Nhập thông tin tài khoản để đăng nhập
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Email Field */}
          <div className="space-y-2">
            <Label htmlFor="email" className="text-sm font-semibold text-foreground">
              Email
            </Label>
            <Input
              id="email"
              type="email"
              placeholder="ten@vi-du.com"
              {...register("email")}
              className={`h-10 bg-white border border-border shadow-[inset_0_1px_2px_rgba(0,0,0,0.04)] transition-all duration-200 ease-in-out
                focus-visible:ring-2 focus-visible:ring-primary/20 focus-visible:border-primary focus-visible:bg-white focus-visible:shadow-none
                ${errors.email ? "bg-alert-light text-alert" : ""}`}
            />
            {errors.email && (
              <p className="text-xs text-alert mt-1">{errors.email.message}</p>
            )}
          </div>

          {/* Password Field */}
          <div className="space-y-2">
            <Label htmlFor="password" className="text-sm font-semibold text-foreground">
              Mật khẩu
            </Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                {...register("password")}
                className={`h-10 bg-white border border-border shadow-[inset_0_1px_2px_rgba(0,0,0,0.04)] pr-12 transition-all duration-200 ease-in-out
                  focus-visible:ring-2 focus-visible:ring-primary/20 focus-visible:border-primary focus-visible:bg-white focus-visible:shadow-none
                  ${errors.password ? "bg-alert-light text-alert" : ""}`}
              />
              {/* Show/Hide password toggle - 44px touch target */}
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-0 top-0 h-10 w-10 flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors duration-200 ease-in-out"
                aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
              >
                {showPassword ? (
                  <EyeOff className="h-[18px] w-[18px]" />
                ) : (
                  <Eye className="h-[18px] w-[18px]" />
                )}
              </button>
            </div>

            {errors.password && (
              <p className="text-xs text-alert mt-2">{errors.password.message}</p>
            )}
          </div>

          {submitError ? <p className="text-sm text-alert">{submitError}</p> : null}

          {/* Login Button */}
          <Button
            type="submit"
            className="w-full h-10 bg-primary text-white font-medium rounded-lg hover:bg-primary-hover active:scale-[0.98] transition-colors mt-4"
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              "Đăng nhập"
            )}
          </Button>

          <p className="text-center pt-1">
            <button
              type="button"
              onClick={() => setOwnerResetOpen(true)}
              className="text-sm text-muted-foreground hover:text-foreground font-medium"
            >
              Yêu cầu mật khẩu
            </button>
          </p>
        </form>
      </CardContent>

      <Dialog open={ownerResetOpen} onOpenChange={handleOwnerResetDialogChange}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Yêu cầu mật khẩu</DialogTitle>
            <DialogDescription>
              Không có tự khôi phục mật khẩu qua email. <strong>Quên mật khẩu:</strong> nhập tên đăng nhập —
              Owner xử lý xong bạn nhận mật khẩu mới qua email. <strong>Chưa có tài khoản nhân viên:</strong> liên hệ
              Owner trực tiếp hoặc ghi rõ trong ghi chú nếu Owner đã hướng dẫn dùng form này.
            </DialogDescription>
          </DialogHeader>

          {ownerResetSuccess ? (
            <p className="text-sm text-muted-foreground leading-relaxed">
              Nếu tài khoản tồn tại, yêu cầu đã được gửi tới Owner. Bạn sẽ nhận email khi Owner xử lý
              xong.
            </p>
          ) : (
            <form
              id="owner-reset-request-form"
              onSubmit={ownerResetForm.handleSubmit(onOwnerResetSubmit)}
              className="space-y-4"
            >
              {ownerResetError ? <p className="text-sm text-alert">{ownerResetError}</p> : null}
              <div className="space-y-2">
                <Label htmlFor="reset-username">Tên đăng nhập</Label>
                <Input
                  id="reset-username"
                  placeholder="vd: staff01"
                  className="h-11 bg-muted border-none"
                  {...ownerResetForm.register("username")}
                  aria-invalid={!!ownerResetForm.formState.errors.username}
                />
                {ownerResetForm.formState.errors.username && (
                  <p className="text-xs text-alert">
                    {ownerResetForm.formState.errors.username.message}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="reset-message">Ghi chú cho Owner (tuỳ chọn)</Label>
                <Textarea
                  id="reset-message"
                  placeholder="Ví dụ: Em quên mật khẩu, nhờ reset giúp."
                  className="min-h-[88px] bg-muted border-none resize-y"
                  {...ownerResetForm.register("message")}
                  aria-invalid={!!ownerResetForm.formState.errors.message}
                />
                {ownerResetForm.formState.errors.message && (
                  <p className="text-xs text-alert">
                    {ownerResetForm.formState.errors.message.message}
                  </p>
                )}
              </div>
            </form>
          )}

          <DialogFooter>
            {ownerResetSuccess ? (
              <Button type="button" onClick={() => handleOwnerResetDialogChange(false)}>
                Đóng
              </Button>
            ) : (
              <>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => handleOwnerResetDialogChange(false)}
                  disabled={ownerResetSubmitting}
                >
                  Huỷ
                </Button>
                <Button
                  type="submit"
                  form="owner-reset-request-form"
                  disabled={ownerResetSubmitting}
                  className="bg-gradient-to-br from-primary to-primary-hover"
                >
                  {ownerResetSubmitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Đang gửi…
                    </>
                  ) : (
                    "Gửi yêu cầu"
                  )}
                </Button>
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
