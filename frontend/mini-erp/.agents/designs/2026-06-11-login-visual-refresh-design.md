# Login Page Visual Refresh — Design Spec

**Date:** 2026-06-11
**Style:** Enterprise Classic
**Approach:** A — Classic Corporate (tinh chỉnh nhẹ, giữ nguyên cấu trúc)

---

## 1. Goals

- Nâng cấp look & feel trang Login theo hướng Enterprise Classic — chuyên nghiệp, formal, tinh tế
- Giữ nguyên cấu trúc layout hiện tại (centered card), không thay đổi UX flow
- Dễ migrate, minimal breaking changes
- Dùng design tokens có sẵn trong `index.css`

## 2. Files thay đổi

| File | Thay đổi |
|------|---------|
| `src/features/auth/pages/LoginPage.tsx` | Brand area (logo, title, tagline) |
| `src/features/auth/components/LoginForm.tsx` | Card, inputs, button, spacing, remember me, footer |
| `src/index.css` | Không cần thay đổi (dùng token có sẵn) |

---

## 3. LoginPage.tsx — Brand area

| Token | Current | New |
|-------|---------|-----|
| Logo box | `h-12 w-12` (48px) | `h-14 w-14` (56px) |
| Logo shadow | none | `shadow-[0_4px_12px_rgba(15,23,42,0.15)]` |
| Title size | `text-xl font-semibold` | `text-2xl font-bold` |
| Title tracking | inline `-0.02em` | bỏ inline |
| Tagline | `text-xs uppercase tracking-widest font-medium` | `text-sm font-medium` (bỏ uppercase) |
| Page background | `bg-[#f8f9fa]` | `bg-muted` |

Không thay đổi cấu trúc layout: `min-h-screen`, `flex items-center justify-center`, `max-w-lg`.

```tsx
<div className="h-14 w-14 bg-gradient-to-br from-primary to-primary-hover rounded-xl flex items-center justify-center shadow-[0_4px_12px_rgba(15,23,42,0.15)]">
  <span className="text-white font-bold text-2xl">M</span>
</div>
<h1 className="text-2xl font-bold tracking-tight text-foreground">Mini ERP</h1>
<p className="text-sm text-muted-foreground font-medium mt-1">Smart Management</p>
```

---

## 4. LoginForm.tsx — Form card & inputs

### Card

| Token | Current | New |
|-------|---------|-----|
| Shadow | `shadow-[0px_10px_30px_rgba(43,52,55,0.06)]` | `shadow-sm` |
| Border | `border-none` | `border border-border` |
| Title | `text-2xl font-medium` | `text-xl font-semibold` |
| Description | "Hãy nhập thông tin để quản lý doanh nghiệp của bạn" | "Nhập thông tin tài khoản để đăng nhập" |
| Spacing (`space-y`) | `space-y-5` | `space-y-4` |

### Inputs

| Token | Current | New |
|-------|---------|-----|
| Background | `bg-muted border-none` | `bg-white border border-border` |
| Inner shadow | none | `shadow-[inset_0_1px_2px_rgba(0,0,0,0.04)]` |
| Focus style | `focus-visible:shadow-[0_0_0_2px_rgba(100,116,139,0.2)]` | `focus-visible:ring-2 focus-visible:ring-primary/20 focus-visible:border-primary` |
| Height | `h-11` | `h-10` |

### Submit Button

| Token | Current | New |
|-------|---------|-----|
| Background | `bg-gradient-to-br from-primary to-primary-hover` | `bg-primary hover:bg-primary-hover` |
| Height | `h-11` | `h-10` |
| Border radius | `rounded-[0.5rem]` | `rounded-lg` |
| Hover effect | `hover:opacity-95 active:scale-[0.98]` | `hover:bg-primary-hover active:scale-[0.98]` |

### Label

| Token | Current | New |
|-------|---------|-----|
| Font weight | `font-medium` | `font-semibold` |

---

## 5. LoginForm.tsx — New elements

### Remember me (giữa password field và submit button)

```tsx
<div className="flex items-center justify-between">
  <div className="flex items-center space-x-2">
    <Checkbox id="remember" />
    <Label htmlFor="remember" className="text-sm font-medium cursor-pointer">Ghi nhớ đăng nhập</Label>
  </div>
  <button type="button" onClick={() => setOwnerResetOpen(true)}
    className="text-sm text-muted-foreground hover:text-foreground font-medium">
    Quên mật khẩu?
  </button>
</div>
```

- Lưu state vào localStorage (khác với sessionStorage hiện tại)
- Nếu checked: khi login thành công, set `localStorage.setItem("rememberEmail", email)`
- Khi load form: nếu có `rememberEmail` trong localStorage, tự điền vào email field

### Footer

```tsx
<p className="text-xs text-muted-foreground text-center mt-6">
  © 2024 Mini ERP. All rights reserved.
</p>
```

### Password reset link styling

| Token | Current | New |
|-------|---------|-----|
| Styling | `underline-offset-4 hover:text-foreground hover:underline` | `text-muted-foreground hover:text-foreground font-medium` (no underline) |
| Vị trí | Dưới submit button, centered | Trong cùng row với remember me |

---

## 6. Password Reset Dialog

Giữ nguyên hoàn toàn — không thay đổi.

---

## 7. Non-goals

- Không thay đổi API layer (authApi.ts, http.ts)
- Không thay đổi Zustand store (useAuthStore.ts)
- Không thay đổi routing (App.tsx)
- Không thêm social login, OTP, hay tính năng auth mới
- Không thay đổi theme tokens (index.css)

---

## 8. Implementation order

1. `LoginPage.tsx` — brand area
2. `LoginForm.tsx` — card, inputs, button styling
3. `LoginForm.tsx` — remember me + footer
