import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import { StatusBadge } from "./StatusBadge"

describe("shared StatusBadge", () => {
  it("renders order pending as cho xu ly with amber styling", () => {
    const { container } = render(<StatusBadge status="Pending" context="order" />)

    expect(screen.getByText("Chờ xử lý")).toBeInTheDocument()
    expect(container.firstChild).toHaveClass("bg-amber-100")
    expect(container.firstChild).toHaveClass("text-amber-700")
    expect(container.firstChild).toHaveClass("border-amber-200")
  })

  it("renders warehouse pending as cho duyet", () => {
    render(<StatusBadge status="Pending" context="warehouse" />)

    expect(screen.getByText("Chờ duyệt")).toBeInTheDocument()
  })

  it("renders inactive as ngung", () => {
    render(<StatusBadge status="Inactive" />)

    expect(screen.getByText("Ngừng")).toBeInTheDocument()
  })

  it("renders debt active mapping as con no with border", () => {
    const { container } = render(<StatusBadge status="Active_debt" />)

    expect(screen.getByText("Còn nợ")).toBeInTheDocument()
    expect(container.firstChild).toHaveClass("border-amber-200")
  })

  it("renders dispatch partial shortage warning with rose styling", () => {
    const { container } = render(<StatusBadge status="Partial" shortageWarning />)

    expect(screen.getByText("Thiếu hàng cần xử lý")).toBeInTheDocument()
    expect(container.firstChild).toHaveClass("bg-rose-100")
    expect(container.firstChild).toHaveClass("text-rose-600")
  })
})
