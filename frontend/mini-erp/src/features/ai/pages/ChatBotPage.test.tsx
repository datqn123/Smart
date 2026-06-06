import type { ReactElement } from "react"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"

import { PageTitleProvider } from "@/context/PageTitleContext"
import { ChatBotPage } from "./ChatBotPage"

const mockStartAiChatPostStream = vi.fn()
const mockSpeak = vi.fn(async () => {})
const mockStop = vi.fn()
const mockClipboardWriteText = vi.fn(async () => {})

vi.mock("../api/aiChatSse", () => ({
  startAiChatPostStream: mockStartAiChatPostStream,
  transcribeAudio: vi.fn(),
  TranscribeAudioError: class TranscribeAudioError extends Error {
    code: string
    constructor(code: string, message: string) {
      super(message)
      this.code = code
    }
  },
}))

vi.mock("../hooks/useTextToSpeech", () => ({
  useTextToSpeech: () => ({
    speak: mockSpeak,
    stop: mockStop,
    isSpeaking: false,
    isLoading: false,
    supported: true,
  }),
}))

vi.mock("../components/AiChatChartCard", () => ({
  AiChatChartCard: () => <div data-testid="ai-chart-card" />,
}))

vi.mock("../components/AiChatDraftTableCard", () => ({
  AiChatDraftTableCard: () => <div data-testid="ai-draft-card" />,
}))

vi.mock("../components/AiChatReceiptDraftCard", () => ({
  AiChatReceiptDraftCard: () => <div data-testid="ai-receipt-card" />,
}))

vi.mock("../components/AiChatQueryTableCard", () => ({
  AiChatQueryTableCard: () => <div data-testid="ai-query-card" />,
}))

vi.mock("../components/AiChatClarifyCard", () => ({
  AiChatClarifyCard: () => <div data-testid="ai-clarify-card" />,
}))

function renderWithProviders(ui: ReactElement) {
  return render(<PageTitleProvider>{ui}</PageTitleProvider>)
}

describe("ChatBotPage", () => {
  beforeEach(() => {
    mockStartAiChatPostStream.mockReset()
    mockStartAiChatPostStream.mockReturnValue({ abort: vi.fn() })
    mockSpeak.mockClear()
    mockStop.mockClear()
    mockClipboardWriteText.mockClear()
    vi.restoreAllMocks()
    window.sessionStorage.clear()
    vi.spyOn(window.navigator, "clipboard", "get").mockReturnValue({
      writeText: mockClipboardWriteText,
    } as unknown as Clipboard)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("renders the welcome card and hides legacy upload actions", () => {
    renderWithProviders(<ChatBotPage />)

    expect(screen.getByText("Xin chào! 👋")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Cuộc hội thoại mới" })).toBeInTheDocument()
    expect(screen.queryByLabelText("Sao chép tin nhắn")).not.toBeInTheDocument()
    expect(screen.queryByRole("button", { name: /image/i })).not.toBeInTheDocument()
    expect(screen.queryByRole("button", { name: /paperclip/i })).not.toBeInTheDocument()
  })

  it("streams an assistant reply and copies the completed content", async () => {
    renderWithProviders(<ChatBotPage />)

    fireEvent.change(screen.getByPlaceholderText(/Hỏi trợ lý bằng chữ/i), {
      target: { value: "Cho tôi biết doanh thu hôm nay" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Gửi tin nhắn" }))

    const streamArgs = mockStartAiChatPostStream.mock.calls[0]?.[0]
    expect(streamArgs?.conversationId).toBeTruthy()
    streamArgs.onDeltaFull("Doanh thu hôm nay là 12 triệu.")
    streamArgs.onDone()

    expect(await screen.findByText("Doanh thu hôm nay là 12 triệu.")).toBeInTheDocument()

    const copyButton = await screen.findByRole("button", { name: "Sao chép tin nhắn" })
    fireEvent.click(copyButton)

    await waitFor(() => {
      expect(mockClipboardWriteText).toHaveBeenCalledWith("Doanh thu hôm nay là 12 triệu.")
    })
    expect(screen.getByRole("button", { name: "Đã sao chép" })).toBeInTheDocument()
  })

  it("clears the chat and regenerates the conversation id", async () => {
    window.sessionStorage.setItem("ai_chat_conversation_id", "conv-old")
    const randomSpy = vi
      .spyOn(globalThis.crypto, "randomUUID")
      .mockReturnValue("conv-new-0000-0000-0000-000000000000")
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true)

    renderWithProviders(<ChatBotPage />)

    fireEvent.change(screen.getByPlaceholderText(/Hỏi trợ lý bằng chữ/i), {
      target: { value: "Tạo cuộc hội thoại thử" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Gửi tin nhắn" }))

    const streamArgs = mockStartAiChatPostStream.mock.calls[0]?.[0]
    streamArgs.onDeltaFull("Đây là phản hồi tạm.")
    streamArgs.onDone()

    expect(await screen.findByText("Đây là phản hồi tạm.")).toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: "Cuộc hội thoại mới" }))

    expect(confirmSpy).toHaveBeenCalled()
    expect(window.sessionStorage.getItem("ai_chat_conversation_id")).toBe("conv-new-0000-0000-0000-000000000000")
    expect(randomSpy).toHaveBeenCalledTimes(1)
    expect(screen.getByText("Xin chào! 👋")).toBeInTheDocument()
    expect(screen.queryByText("Đây là phản hồi tạm.")).not.toBeInTheDocument()
  })
})
