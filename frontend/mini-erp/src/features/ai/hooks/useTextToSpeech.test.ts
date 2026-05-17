import { describe, expect, it } from "vitest"
import { stripMarkdownForSpeech } from "./useTextToSpeech"

describe("stripMarkdownForSpeech", () => {
  it("removes bold and heading markers", () => {
    expect(stripMarkdownForSpeech("**Xin chào** và # Tiêu đề")).toBe("Xin chào và Tiêu đề")
  })

  it("unwraps inline code and links", () => {
    expect(stripMarkdownForSpeech("Dùng `mã` và [link](https://x.com)")).toBe("Dùng mã và link")
  })

  it("preserves hyphens in numbers", () => {
    expect(stripMarkdownForSpeech("Doanh thu 2024-2025 là 1.000.000")).toBe(
      "Doanh thu 2024-2025 là 1.000.000"
    )
  })
})
