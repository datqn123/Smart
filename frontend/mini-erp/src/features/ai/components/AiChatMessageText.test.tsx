import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"

import { AiChatMessageText } from "./AiChatMessageText"

describe("AiChatMessageText", () => {
  it("renders paragraph text intact for Vietnamese words", () => {
    render(<AiChatMessageText text={"Hôm nay bạn cần hỗ trợ gì?"} />)
    expect(screen.getByText("Hôm nay bạn cần hỗ trợ gì?")).toBeInTheDocument()
  })

  it("preserves line breaks in paragraph blocks", () => {
    const text = "Dòng một\nDòng hai"
    render(<AiChatMessageText text={text} />)
    const paragraph = screen.getByText(/Dòng một/).closest("p")
    expect(paragraph).toHaveClass("whitespace-pre-wrap")
    expect(screen.getByText(/Dòng hai/)).toBeInTheDocument()
  })

  it("renders bullet and ordered lists", () => {
    render(
      <AiChatMessageText
        text={"- Mục một\n- Mục hai\n\n1. Bước một\n2. Bước hai"}
      />
    )
    const bullets = screen.getAllByRole("list")[0]
    const ordered = screen.getAllByRole("list")[1]
    expect(bullets).toBeInTheDocument()
    expect(ordered).toBeInTheDocument()
    expect(screen.getByText("Mục một")).toBeInTheDocument()
    expect(screen.getByText("Bước hai")).toBeInTheDocument()
  })

  it("renders inline strong and inline code", () => {
    render(
      <AiChatMessageText
        text={"Bạn hãy kiểm tra **đơn hàng** với mã `SO-001`."}
      />
    )
    const strong = screen.getByText("đơn hàng")
    expect(strong.tagName.toLowerCase()).toBe("strong")
    const code = screen.getByText("SO-001")
    expect(code.tagName.toLowerCase()).toBe("code")
  })

  it("renders fenced code block", () => {
    render(
      <AiChatMessageText
        text={"```sql\nSELECT id FROM customers LIMIT 10;\n```"}
      />
    )
    expect(screen.getByText("sql")).toBeInTheDocument()
    expect(screen.getByText("SELECT id FROM customers LIMIT 10;")).toBeInTheDocument()
  })
})
