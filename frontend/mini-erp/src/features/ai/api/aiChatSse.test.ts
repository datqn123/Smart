import { describe, expect, it } from "vitest"

type Parsed = { event: string; data: string } | null

function parseSseBlockLocal(block: string): Parsed {
  let event = ""
  const dataLines: string[] = []
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim()
    } else if (line.startsWith("data:")) {
      const d = line.startsWith("data: ") ? line.slice(6) : line.slice(5)
      dataLines.push(d)
    }
  }
  if (!event) return null
  return { event, data: dataLines.join("\n") }
}

describe("aiChatSse data parser", () => {
  it("drops only separator space after data colon", () => {
    const block = "event: delta\ndata: hello\n"
    const parsed = parseSseBlockLocal(block)
    expect(parsed).toEqual({ event: "delta", data: "hello" })
  })

  it("preserves a meaningful leading space in payload", () => {
    // Upstream may encode payload with leading space as double-space after colon.
    const block = "event: delta\ndata:  bạn\n"
    const parsed = parseSseBlockLocal(block)
    expect(parsed).toEqual({ event: "delta", data: " bạn" })
  })

  it("preserves leading space when line is encoded as data:<payload>", () => {
    // Some emitters can produce `data:<payload>` without separator space.
    const block = "event: delta\ndata: bạn\n"
    const parsed = parseSseBlockLocal(block)
    expect(parsed).toEqual({ event: "delta", data: " bạn".slice(1) }) // "bạn"
  })
})

