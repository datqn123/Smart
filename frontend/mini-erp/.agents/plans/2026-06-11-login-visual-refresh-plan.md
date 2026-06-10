# Login Page Visual Refresh — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh the Login page visual design to Enterprise Classic style — professional, clean, with subtle shadow, border, and refined typography.

**Architecture:** Update CSS classes in two existing files (LoginPage.tsx, LoginForm.tsx). Add "Remember me" checkbox with localStorage persistence. No API or routing changes.

**Tech Stack:** React 19, TypeScript, Tailwind CSS v4, shadcn/ui (Checkbox, Label, Input, Button, Card), react-hook-form, vitest, @testing-library/react

---

### Task 1: LoginPage.tsx — Brand area refresh

**Files:**
- Modify: `src/features/auth/pages/LoginPage.tsx`

- [ ] **Step 1.1: Update LoginPage.tsx brand area**

Replace the brand section (lines 19-31) with updated sizes, shadow, and styling:

```tsx
import { useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { LoginForm } from "../components/LoginForm"
import { hasResumeSessionInSessionStorage } from "@/features/auth/lib/clientSessionResume"

export function LoginPage() {
  const navigate = useNavigate()

  useEffect(() => {
    if (hasResumeSessionInSessionStorage()) {
      navigate("/dashboard", { replace: true })
    }
  }, [navigate])

  return (
    <main className="min-h-screen w-full flex items-center justify-center bg-muted p-4 sm:p-6 antialiased">
      <div className="w-full flex flex-col items-center max-w-lg">
        {/* Logo / Brand Header */}
        <div className="mb-10 flex flex-col items-center space-y-3">
          <div className="h-14 w-14 bg-gradient-to-br from-primary to-primary-hover rounded-xl flex items-center justify-center shadow-[0_4px_12px_rgba(15,23,42,0.15)]">
            <span className="text-white font-bold text-2xl">M</span>
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Mini ERP
            </h1>
            <p className="text-sm text-muted-foreground font-medium mt-1">
              Smart Management
            </p>
          </div>
        </div>
        
        {/* Login Form Component */}
        <LoginForm />
      </div>
    </main>
  )
}
```

Changes made:
- `bg-[#f8f9fa]` → `bg-muted` (use design token)
- Logo box: `h-12 w-12` → `h-14 w-14`, added `shadow-[0_4px_12px_rgba(15,23,42,0.15)]`
- Title: `text-xl font-semibold` → `text-2xl font-bold`, removed inline `letterSpacing`
- Tagline: `text-xs uppercase tracking-widest font-medium` → `text-sm text-muted-foreground font-medium` (removed uppercase)

- [ ] **Step 1.2: Verify TypeScript compiles**

Run: `npx tsc --noEmit`
Expected: No errors

- [ ] **Step 1.3: Commit**

```bash
git add src/features/auth/pages/LoginPage.tsx
git commit -m "refactor(login): refresh brand area — larger logo, bold title, token bg"
```

---

### Task 2: LoginForm.tsx — Card, inputs, button styling

**Files:**
- Modify: `src/features/auth/components/LoginForm.tsx`

- [ ] **Step 2.1: Update Card, inputs, and button styling**

Replace the entire `LoginForm.tsx` with updated styling. The logic (form submission, error handling, password toggle, dialog) stays identical — only CSS classes change:

```tsx
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
```

Key changes:
- Card: `shadow-sm border border-border` (was `shadow-[0px_10px_30px...] border-none`)
- CardTitle: `text-xl font-semibold` (was `text-2xl font-medium`)
- CardDescription: "Nhập thông tin tài khoản để đăng nhập"
- Inputs: `bg-white border border-border shadow-[inset_0_1px_2px...] h-10`
- Input focus: `focus-visible:ring-2 focus-visible:ring-primary/20 focus-visible:border-primary`
- Labels: `font-semibold` (was `font-medium`)
- Button: `bg-primary hover:bg-primary-hover rounded-lg h-10` (removed gradient)
- Spacing: `space-y-4` (was `space-y-5`)
- Password toggle button: `h-10 w-10` (was `h-11 w-11`)

- [ ] **Step 2.2: Verify TypeScript compiles**

Run: `npx tsc --noEmit`
Expected: No errors

- [ ] **Step 2.3: Commit**

```bash
git add src/features/auth/components/LoginForm.tsx
git commit -m "refactor(login): refresh form card, inputs, button — enterprise classic style"
```

---

### Task 3: LoginForm.tsx — Remember me + Footer

**Files:**
- Modify: `src/features/auth/components/LoginForm.tsx`
- Create: `src/features/auth/components/LoginForm.test.tsx`

- [ ] **Step 3.1: Add Checkbox import and remember me logic**

Add `Checkbox` to imports and add `useEffect` for loading remembered email, plus state for the checkbox:

```tsx
import { useState, useEffect } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
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
```

- [ ] **Step 3.2: Add remember me state and useEffect**

Inside the `LoginForm` function, after the existing `useState` declarations (after line 56), add:

```tsx
  const [rememberMe, setRememberMe] = useState(false)

  // Load remembered email on mount — set checkbox if email was remembered
  useEffect(() => {
    const remembered = localStorage.getItem("rememberEmail")
    if (remembered) {
      setRememberMe(true)
    }
  }, [])
```

- [ ] **Step 3.3: Update useForm defaultValues and add remember me handling**

Change the `useForm` call to include `defaultValues` with remembered email:

```tsx
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: localStorage.getItem("rememberEmail") || "",
      password: "",
    },
  })
```

In the `onSubmit` function, after successful login (after `navigate("/dashboard")` line), add:

```tsx
      if (rememberMe) {
        localStorage.setItem("rememberEmail", data.email)
      } else {
        localStorage.removeItem("rememberEmail")
      }
```

The full `onSubmit` function now looks like:

```tsx
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
      if (rememberMe) {
        localStorage.setItem("rememberEmail", data.email)
      } else {
        localStorage.removeItem("rememberEmail")
      }
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
```

- [ ] **Step 3.4: Add Remember me row and Footer**

Replace the section between the password field error and the submit button. Currently it's:

```tsx
          {submitError ? <p className="text-sm text-alert">{submitError}</p> : null}

          {/* [A] Login Button ... */}
          <Button ...>
```

Replace with:

```tsx
          {submitError ? <p className="text-sm text-alert">{submitError}</p> : null}

          {/* Remember me + Forgot password */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="remember"
                checked={rememberMe}
                onCheckedChange={(checked) => setRememberMe(checked as boolean)}
              />
              <Label
                htmlFor="remember"
                className="text-sm font-medium cursor-pointer"
              >
                Ghi nhớ đăng nhập
              </Label>
            </div>
            <button
              type="button"
              onClick={() => setOwnerResetOpen(true)}
              className="text-sm text-muted-foreground hover:text-foreground font-medium"
            >
              Quên mật khẩu?
            </button>
          </div>

          {/* Login Button */}
          <Button
            type="submit"
            className="w-full h-10 bg-primary text-white font-medium rounded-lg hover:bg-primary-hover active:scale-[0.98] transition-colors"
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              "Đăng nhập"
            )}
          </Button>
```

Remove the old password reset link (the `<p className="text-center pt-1">` block with "Yêu cầu mật khẩu").

- [ ] **Step 3.5: Add footer after Card closing tag**

After the `</Card>` closing tag in the return statement, add the footer. But since `LoginForm` only returns the Card, we need to add the footer inside the Card at the bottom, or modify `LoginPage.tsx` to include the footer.

The cleaner approach: add the footer in `LoginPage.tsx` below the `<LoginForm />` component.

Modify `LoginPage.tsx` to add footer after the LoginForm:

```tsx
        {/* Login Form Component */}
        <LoginForm />

        {/* Footer */}
        <p className="text-xs text-muted-foreground text-center mt-6">
          © 2024 Mini ERP. All rights reserved.
        </p>
      </div>
    </main>
  )
}
```

- [ ] **Step 3.6: Write tests for LoginForm**

Create `src/features/auth/components/LoginForm.test.tsx`:

```tsx
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router-dom"
import { LoginForm } from "./LoginForm"

// Mock the auth API
vi.mock("@/features/auth/api/authApi", () => ({
  postLogin: vi.fn(),
  postPasswordResetRequest: vi.fn(),
}))

// Mock the auth store
vi.mock("@/features/auth/store/useAuthStore", () => ({
  useAuthStore: {
    getState: () => ({
      login: vi.fn(),
    }),
  },
}))

// Mock the navigate
const mockNavigate = vi.fn()
vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>()
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

function renderLoginForm() {
  return render(
    <MemoryRouter>
      <LoginForm />
    </MemoryRouter>
  )
}

describe("LoginForm visual refresh", () => {
  beforeEach(() => {
    localStorage.clear()
    mockNavigate.mockClear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it("renders with brand title and description", () => {
    renderLoginForm()
    expect(screen.getByText("Chào mừng trở lại")).toBeInTheDocument()
    expect(screen.getByText("Nhập thông tin tài khoản để đăng nhập")).toBeInTheDocument()
  })

  it("renders email and password fields", () => {
    renderLoginForm()
    expect(screen.getByLabelText("Email")).toBeInTheDocument()
    expect(screen.getByLabelText("Mật khẩu")).toBeInTheDocument()
  })

  it("renders remember me checkbox", () => {
    renderLoginForm()
    expect(screen.getByLabelText("Ghi nhớ đăng nhập")).toBeInTheDocument()
  })

  it("renders forgot password link", () => {
    renderLoginForm()
    expect(screen.getByText("Quên mật khẩu?")).toBeInTheDocument()
  })

  it("renders submit button with correct text", () => {
    renderLoginForm()
    expect(screen.getByRole("button", { name: "Đăng nhập" })).toBeInTheDocument()
  })

  it("pre-fills email from localStorage rememberEmail", () => {
    localStorage.setItem("rememberEmail", "test@example.com")
    renderLoginForm()
    const emailInput = screen.getByLabelText("Email") as HTMLInputElement
    expect(emailInput.value).toBe("test@example.com")
  })

  it("shows password reset dialog when clicking Quên mật khẩu?", async () => {
    const user = userEvent.setup()
    renderLoginForm()
    await user.click(screen.getByText("Quên mật khẩu?"))
    expect(screen.getByText("Yêu cầu mật khẩu")).toBeInTheDocument()
  })
})
```

- [ ] **Step 3.7: Run tests**

Run: `npx vitest run src/features/auth/components/LoginForm.test.tsx`
Expected: All 7 tests pass

- [ ] **Step 3.8: Verify TypeScript compiles**

Run: `npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3.9: Commit**

```bash
git add src/features/auth/pages/LoginPage.tsx src/features/auth/components/LoginForm.tsx src/features/auth/components/LoginForm.test.tsx
git commit -m "feat(login): add remember me with localStorage + footer + tests"
```

---

### Task 4: Final verification & dev server check

**Files:**
- No file changes

- [ ] **Step 4.1: Run all tests**

Run: `npx vitest run`
Expected: All tests pass (including new LoginForm tests)

- [ ] **Step 4.2: Start dev server and verify visual**

Run: `npm run dev`
Open: `http://localhost:3000/login`

Verify:
- Logo is 56x56 with subtle shadow
- Title is bold, 24px
- Tagline is not uppercase, 14px
- Card has border and subtle shadow
- Inputs have white background, border, inner shadow
- Submit button is solid dark (no gradient)
- Remember me checkbox appears between password and submit
- "Quên mật khẩu?" is inline with remember me
- Footer appears below card

- [ ] **Step 4.3: Test remember me flow manually**

1. Enter email, check "Ghi nhớ đăng nhập", login (with valid credentials)
2. Logout, go back to login
3. Verify email is pre-filled from localStorage
