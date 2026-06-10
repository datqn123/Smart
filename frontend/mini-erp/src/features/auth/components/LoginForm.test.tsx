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
