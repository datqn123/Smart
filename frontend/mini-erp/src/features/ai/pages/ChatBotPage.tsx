import { useState, useRef, useEffect } from "react"
import { usePageTitle } from "@/context/PageTitleContext"
import {
  Send,
  Mic,
  Bot,
  User,
  Loader2,
  Volume2,
  StopCircle,
  Sparkles,
  Database,
  Table2,
  BarChart2,
  ClipboardList,
  PackagePlus,
  RotateCcw,
  Copy,
  Check,
} from "lucide-react"
import type { AiInteractionMode, ChatMessage } from "../types"
import { Button } from "@/components/ui/button"
import {
  startAiChatPostStream,
  transcribeAudio,
  TranscribeAudioError,
  type AiChatStreamHandle,
} from "../api/aiChatSse"
import {
  convertToWav,
  MAX_RECORDING_MS,
  MIN_PEAK_AMPLITUDE,
  MIN_RECORDING_SEC,
} from "../utils/audioUtils"
import { AiChatChartCard } from "../components/AiChatChartCard"
import { AiChatDraftTableCard } from "../components/AiChatDraftTableCard"
import { AiChatReceiptDraftCard } from "../components/AiChatReceiptDraftCard"
import { AiChatQueryTableCard } from "../components/AiChatQueryTableCard"
import { AiChatClarifyCard } from "../components/AiChatClarifyCard"
import { AiChatMessageText } from "../components/AiChatMessageText"
import type { CatalogDraftTablePayload } from "../api/aiCatalogDraftApi"
import type { DomainClarifyPayload } from "../api/aiDomainClarifyTypes"
import type { InventoryReceiptDraftPayload } from "../api/aiInventoryDraftApi"
import type { QueryTablePayload } from "../api/aiQueryTableTypes"
import { cn } from "@/lib/utils"
import { useTextToSpeech } from "../hooks/useTextToSpeech"

const AI_CHAT_CONVERSATION_ID_KEY = "ai_chat_conversation_id"

const WELCOME_MESSAGE = "Xin chào. Tôi là trợ lý AI Mini ERP — trả lời qua Spring và dịch vụ Python (dữ liệu SQL read-only khi bạn hỏi số liệu). Hãy nhập câu hỏi bằng chữ."

const INTERACTION_MODES: { id: AiInteractionMode; label: string; icon: typeof Sparkles }[] = [
  { id: "auto", label: "Tự động", icon: Sparkles },
  { id: "data_query", label: "Hỏi dữ liệu", icon: Database },
  { id: "data_table", label: "Bảng kết quả", icon: Table2 },
  { id: "chart", label: "Biểu đồ", icon: BarChart2 },
  { id: "catalog_draft", label: "Tạo bảng nhập", icon: ClipboardList },
  { id: "inventory_draft", label: "Phiếu nhập kho", icon: PackagePlus },
]

type ClarifyContinuation = {
  clarifyId?: string
  clarifyKind?: string
  continuationContext?: Record<string, unknown>
  suggestedRewrite?: string
}

function createWelcomeMessage(): ChatMessage {
  return {
    id: "1",
    role: "assistant",
    content: WELCOME_MESSAGE,
    timestamp: new Date().toISOString(),
    type: "text",
  }
}

function ensureConversationId(reset = false) {
  if (reset) {
    window.sessionStorage.removeItem(AI_CHAT_CONVERSATION_ID_KEY)
  } else {
    const fromStorage = window.sessionStorage.getItem(AI_CHAT_CONVERSATION_ID_KEY)
    if (fromStorage && fromStorage.trim().length > 0) return fromStorage
  }
  const cid = crypto.randomUUID()
  window.sessionStorage.setItem(AI_CHAT_CONVERSATION_ID_KEY, cid)
  return cid
}

export function ChatBotPage() {
  const { setTitle } = usePageTitle()
  useEffect(() => { setTitle("Trợ lý ảo AI") }, [setTitle])

  const [messages, setMessages] = useState<ChatMessage[]>([createWelcomeMessage()])
  const [inputValue, setInputValue] = useState("")
  const [interactionMode, setInteractionMode] = useState<AiInteractionMode>("auto")
  const [isTyping, setIsTyping] = useState(false)
  const [speakingMessageId, setSpeakingMessageId] = useState<string | null>(null)
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null)
  const { speak, stop, isSpeaking, isLoading: isTtsLoading, supported: ttsSupported } = useTextToSpeech()
  const [isRecording, setIsRecording] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [progressText, setProgressText] = useState("")
  const [recordingSeconds, setRecordingSeconds] = useState(0)
  const [conversationId, setConversationId] = useState(() => ensureConversationId())
  const chatEndRef = useRef<HTMLDivElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  // Theo dõi người dùng có đang ở gần đáy không — chỉ auto-scroll khi đúng vậy,
  // tránh kéo ngược màn hình khi họ cuộn lên đọc lại trong lúc đang stream.
  const autoScrollRef = useRef(true)
  const streamRef = useRef<AiChatStreamHandle | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const micStreamRef = useRef<MediaStream | null>(null)
  const recordingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const recordingTickRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const copyResetTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const handleMessagesScroll = () => {
    const el = scrollContainerRef.current
    if (!el) return
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
    autoScrollRef.current = distanceFromBottom < 120
  }

  // behavior "auto" (instant) thay vì "smooth": trong lúc stream token, scroll mượt
  // sẽ chồng animation gây layout thrash. Snap tức thời mỗi frame trông vẫn liền mạch.
  const scrollToBottom = () => {
    if (!autoScrollRef.current) return
    chatEndRef.current?.scrollIntoView({ behavior: "auto" })
  }

  useEffect(() => { scrollToBottom() }, [messages])

  useEffect(() => {
    if (isTyping && speakingMessageId) {
      stop()
      setSpeakingMessageId(null)
    }
  }, [isTyping, speakingMessageId, stop])

  const handleSpeak = (msg: ChatMessage) => {
    if (speakingMessageId === msg.id && (isSpeaking || isTtsLoading)) {
      stop()
      setSpeakingMessageId(null)
    } else {
      setSpeakingMessageId(msg.id)
      void speak(msg.content)
    }
  }

  useEffect(() => {
    return () => {
      streamRef.current?.abort()
      streamRef.current = null
      if (recordingTimerRef.current) clearTimeout(recordingTimerRef.current)
      if (recordingTickRef.current) clearInterval(recordingTickRef.current)
      if (copyResetTimerRef.current) clearTimeout(copyResetTimerRef.current)
      mediaRecorderRef.current?.stop()
      micStreamRef.current?.getTracks().forEach((t) => t.stop())
    }
  }, [])

  const startAssistantStream = (
    query: string,
    options?: { autoSpeakOnComplete?: boolean; clarifyContinuation?: ClarifyContinuation | null }
  ) => {
    streamRef.current?.abort()
    streamRef.current = null

    const autoSpeak = options?.autoSpeakOnComplete ?? false
    const clarifyContinuation = options?.clarifyContinuation ?? null
    const assistantId = (Date.now() + 1).toString()
    const assistantMsg: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
      type: "text",
    }

    setMessages(prev => [...prev, assistantMsg])
    setIsTyping(true)
    setProgressText("Đang xử lý...")

    let firstDeltaReceived = false
    let usesDeltaFull = false

    // Gom các token delta vào buffer và chỉ flush 1 lần mỗi animation frame (~60fps).
    // Trước đây mỗi token = 1 setMessages = 1 re-render; với 30-80 token/s đó là
    // 30-80 lần map toàn bộ mảng messages mỗi giây. rAF gộp lại còn tối đa 60 render/s
    // và mỗi render chỉ append 1 lần phần text đã tích luỹ.
    let pendingDelta = ""
    let flushRafId: number | null = null
    const flushPendingDelta = () => {
      flushRafId = null
      if (!pendingDelta) return
      const chunk = pendingDelta
      pendingDelta = ""
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantId ? { ...m, content: `${m.content ?? ""}${chunk}` } : m
        )
      )
    }
    const scheduleFlush = () => {
      if (flushRafId === null) flushRafId = requestAnimationFrame(flushPendingDelta)
    }
    const cancelFlush = () => {
      if (flushRafId !== null) {
        cancelAnimationFrame(flushRafId)
        flushRafId = null
      }
    }

    streamRef.current = startAiChatPostStream({
      query,
      conversationId,
      interactionMode,
      clarifyContinuation,
      onProgress: (text) => {
        setProgressText(text)
      },
      onDelta: (delta) => {
        if (usesDeltaFull) return
        if (!firstDeltaReceived) {
          firstDeltaReceived = true
          setProgressText("")
        }
        pendingDelta += delta
        scheduleFlush()
      },
      onDeltaFull: (text) => {
        usesDeltaFull = true
        // delta_full thay thế toàn bộ nội dung → bỏ mọi delta đang buffer.
        pendingDelta = ""
        cancelFlush()
        if (!firstDeltaReceived) {
          firstDeltaReceived = true
          setProgressText("")
        }
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId ? { ...m, content: text } : m
          )
        )
      },
      onChart: (spec) => {
        setProgressText("")
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId
              ? { ...m, metadata: { ...m.metadata, chartSpec: spec } }
              : m
          )
        )
      },
      onDraft: (payload: CatalogDraftTablePayload) => {
        setProgressText("")
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId
              ? { ...m, metadata: { ...m.metadata, draftTable: payload } }
              : m
          )
        )
      },
      onInventoryDraft: (payload: InventoryReceiptDraftPayload) => {
        setProgressText("")
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId
              ? { ...m, metadata: { ...m.metadata, inventoryDraft: payload } }
              : m
          )
        )
      },
      onDataTable: (payload: QueryTablePayload) => {
        setProgressText("")
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId
              ? { ...m, metadata: { ...m.metadata, queryTable: payload } }
              : m
          )
        )
      },
      onClarify: (payload: DomainClarifyPayload) => {
        setProgressText("")
        const intro = (payload.assistantIntro || "").trim().replace(/\*\*/g, "")
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId
              ? {
                  ...m,
                  content: m.content?.trim() ? m.content : intro,
                  metadata: { ...m.metadata, domainClarify: payload },
                }
              : m
          )
        )
      },
      onDone: () => {
        // Áp nốt phần delta còn trong buffer trước khi kết thúc để không mất token cuối.
        cancelFlush()
        flushPendingDelta()
        setIsTyping(false)
        setProgressText("")
        streamRef.current = null
        if (autoSpeak) {
          setMessages((prev) => {
            const msg = prev.find((m) => m.id === assistantId)
            if (msg?.content?.trim() && ttsSupported) {
              setSpeakingMessageId(assistantId)
              void speak(msg.content)
            }
            return prev
          })
        }
      },
      onError: (message) => {
        cancelFlush()
        pendingDelta = ""
        setIsTyping(false)
        setProgressText("")
        setMessages(prev =>
          prev.map(m => (m.id === assistantId ? { ...m, content: message || "Không thể kết nối trợ lý AI." } : m))
        )
        streamRef.current = null
      },
    })
  }

  const handleSend = (
    text?: string,
    type: "text" | "image" | "voice" = "text",
    metadata?: ChatMessage["metadata"],
    clarifyContinuation?: ClarifyContinuation | null
  ) => {
    const content = (text ?? inputValue).trim()
    if (!content && type === "text") return
    if (!content && type === "voice") return

    if (speakingMessageId) {
      stop()
      setSpeakingMessageId(null)
    }
    setProgressText("")

    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content,
      timestamp: new Date().toISOString(),
      type,
      metadata,
    }

    setMessages((prev) => [...prev, newMessage])
    if (type === "text") setInputValue("")

    const autoSpeakReply = type === "voice"

    if (type === "image") {
      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Phiên bản hiện tại chỉ hỗ trợ chat text.",
        timestamp: new Date().toISOString(),
        type: "text",
      }
      setMessages((prev) => [...prev, assistantMsg])
      return
    }

    startAssistantStream(content, {
      autoSpeakOnComplete: autoSpeakReply,
      clarifyContinuation: clarifyContinuation ?? null,
    })
  }

  const stopRecordingTimers = () => {
    if (recordingTimerRef.current) {
      clearTimeout(recordingTimerRef.current)
      recordingTimerRef.current = null
    }
    if (recordingTickRef.current) {
      clearInterval(recordingTickRef.current)
      recordingTickRef.current = null
    }
  }

  const handleCopyMessage = async (msg: ChatMessage) => {
    const text = msg.content.trim()
    if (!text) return
    await navigator.clipboard.writeText(text)
    setCopiedMessageId(msg.id)
    if (copyResetTimerRef.current) clearTimeout(copyResetTimerRef.current)
    copyResetTimerRef.current = setTimeout(() => {
      setCopiedMessageId((current) => (current === msg.id ? null : current))
    }, 1500)
  }

  const handleClearChat = () => {
    if (!window.confirm("Bắt đầu cuộc hội thoại mới?")) return
    audioChunksRef.current = []
    streamRef.current?.abort()
    streamRef.current = null
    mediaRecorderRef.current?.stop()
    mediaRecorderRef.current = null
    micStreamRef.current?.getTracks().forEach((t) => t.stop())
    micStreamRef.current = null
    stopRecordingTimers()
    if (copyResetTimerRef.current) {
      clearTimeout(copyResetTimerRef.current)
      copyResetTimerRef.current = null
    }
    stop()
    setSpeakingMessageId(null)
    setCopiedMessageId(null)
    setIsTyping(false)
    setIsRecording(false)
    setIsTranscribing(false)
    setProgressText("")
    setRecordingSeconds(0)
    setInputValue("")
    setMessages([createWelcomeMessage()])
    setConversationId(ensureConversationId(true))
  }

  const toggleRecording = async () => {
    if (isTranscribing || isTyping) return

    if (isRecording) {
      mediaRecorderRef.current?.stop()
      setIsRecording(false)
      stopRecordingTimers()
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      micStreamRef.current = stream
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm"
      const recorder = new MediaRecorder(stream, { mimeType })
      audioChunksRef.current = []
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data)
      }
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        micStreamRef.current = null
        stopRecordingTimers()
        setRecordingSeconds(0)
        const chunks = audioChunksRef.current
        audioChunksRef.current = []
        if (chunks.length === 0) return
        setIsTranscribing(true)
        try {
          const webmBlob = new Blob(chunks, { type: mimeType })
          const { wav: wavBlob, durationSec, peak } = await convertToWav(webmBlob)
          if (durationSec < MIN_RECORDING_SEC) {
            throw new TranscribeAudioError(
              "validation",
              "Ghi âm quá ngắn. Hãy giữ nút mic và nói ít nhất 1 giây."
            )
          }
          if (peak < MIN_PEAK_AMPLITUDE) {
            throw new TranscribeAudioError(
              "validation",
              "Không phát hiện giọng nói. Hãy nói rõ hơn, gần microphone hơn."
            )
          }
          const { transcript } = await transcribeAudio(wavBlob, { language: "vi" })
          const voiceUrl = URL.createObjectURL(wavBlob)
          handleSend(transcript, "voice", { voiceUrl })
        } catch (err) {
          const message =
            err instanceof TranscribeAudioError
              ? err.message
              : err instanceof DOMException && err.name === "NotAllowedError"
                ? "Vui lòng cấp quyền truy cập microphone để sử dụng tính năng ghi âm."
                : "Không thể chuyển giọng thành văn bản. Vui lòng thử lại."
          setMessages((prev) => [
            ...prev,
            {
              id: (Date.now() + 1).toString(),
              role: "assistant",
              content: message,
              timestamp: new Date().toISOString(),
              type: "text",
            },
          ])
        } finally {
          setIsTranscribing(false)
        }
      }
      recorder.start()
      mediaRecorderRef.current = recorder
      setIsRecording(true)
      setRecordingSeconds(0)
      recordingTickRef.current = setInterval(() => {
        setRecordingSeconds((s) => s + 1)
      }, 1000)
      recordingTimerRef.current = setTimeout(() => {
        if (mediaRecorderRef.current?.state === "recording") {
          mediaRecorderRef.current.stop()
          setIsRecording(false)
        }
      }, MAX_RECORDING_MS)
    } catch (err) {
      const message =
        err instanceof DOMException && err.name === "NotAllowedError"
          ? "Vui lòng cấp quyền truy cập microphone để sử dụng tính năng ghi âm."
          : "Không thể bắt đầu ghi âm. Vui lòng thử lại."
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content: message,
          timestamp: new Date().toISOString(),
          type: "text",
        },
      ])
    }
  }

  const inputBusy = isTyping || isTranscribing || isRecording
  const lastAssistantId = [...messages].reverse().find((msg) => msg.role === "assistant")?.id ?? null

  return (
    <div className="flex flex-col h-full bg-slate-50 overflow-hidden relative">
      {/* Chat Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-white border-b border-slate-200 z-10 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-2xl flex items-center justify-center bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-200/80">
            <Bot className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900 tracking-tight">Trợ lý Mini ERP</h2>
            <div className="flex items-center gap-1.5 mt-0.5">
              <div className="h-2 w-2 bg-emerald-500 rounded-full animate-pulse" />
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Trực tuyến</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="rounded-full hover:bg-slate-100"
            onClick={handleClearChat}
            title="Cuộc hội thoại mới"
            aria-label="Cuộc hội thoại mới"
          >
            <RotateCcw className="h-5 w-5 text-slate-400" />
          </Button>
        </div>
      </div>

      {/* Messages Area */}
      <div
        ref={scrollContainerRef}
        onScroll={handleMessagesScroll}
        className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 scrollbar-hide"
      >
        {messages.map((msg) => {
          // Ẩn bubble assistant đang stream với content rỗng — typing indicator sẽ hiển thị thay
          if (msg.role === "assistant" && isTyping && !msg.content && !msg.metadata) return null

          const hasChart = msg.role === "assistant" && Boolean(msg.metadata?.chartSpec)
          const hasDraft = msg.role === "assistant" && Boolean(msg.metadata?.draftTable)
          const hasInventoryDraft = msg.role === "assistant" && Boolean(msg.metadata?.inventoryDraft)
          const hasQueryTable = msg.role === "assistant" && Boolean(msg.metadata?.queryTable)
          const hasClarify = msg.role === "assistant" && Boolean(msg.metadata?.domainClarify)
          const hasArtifact =
            hasChart || hasDraft || hasInventoryDraft || hasQueryTable || hasClarify
          const fullBleedArtifact =
            msg.role === "assistant" &&
            (hasDraft || hasInventoryDraft || hasQueryTable || hasChart)
          const isWelcomeMessage = msg.id === "1" && msg.role === "assistant"
          const layoutClass = fullBleedArtifact
            ? "w-full max-w-[min(1100px,100%)]"
            : hasArtifact
              ? "max-w-[96%] sm:max-w-[min(720px,92%)]"
              : "max-w-[85%] sm:max-w-[70%]"
          const canShowAssistantActions =
            msg.role === "assistant" &&
            !isWelcomeMessage &&
            !hasClarify &&
            msg.content.trim().length > 0 &&
            (!isTyping || msg.id !== lastAssistantId)
          return (
          <div key={msg.id} className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`flex gap-3 min-w-0 ${layoutClass} ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
              {!fullBleedArtifact && !isWelcomeMessage ? (
              <div className={`h-8 w-8 rounded-xl flex items-center justify-center shrink-0 shadow-sm ${
                msg.role === "assistant"
                  ? "rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-blue-200"
                  : "bg-gradient-to-br from-slate-600 to-slate-800 text-white"
              }`}>
                {msg.role === "assistant" ? <Bot className="h-5 w-5" /> : <User className="h-5 w-5" />}
              </div>
              ) : null}

              {/* Message Content */}
              <div className="min-w-0 flex-1 space-y-2">
                {isWelcomeMessage ? (
                  <div className="rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-50 to-indigo-50 p-5 shadow-sm">
                    <div className="flex items-start gap-4">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-200/70">
                        <Bot className="h-6 w-6" />
                      </div>
                      <div className="space-y-2">
                        <h3 className="text-base font-semibold text-slate-900">Xin chào! 👋</h3>
                        <p className="text-[15px] leading-relaxed text-slate-600">{msg.content}</p>
                      </div>
                    </div>
                  </div>
                ) : hasClarify ? null : (
                <div className={`px-4 py-3 rounded-2xl text-[15px] leading-relaxed shadow-sm ${
                  msg.role === "user" 
                    ? "rounded-tr-none border border-white/10 bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-md shadow-blue-200/50"
                    : "rounded-tl-none border border-slate-100 border-l-2 border-l-blue-200 bg-white text-slate-700 shadow-sm"
                }`}>
                  {msg.type === "image" && msg.metadata?.imageUrl && (
                    <div className="mb-3 overflow-hidden rounded-xl border border-white/20">
                      <img src={msg.metadata.imageUrl} alt="invoice" className="max-h-60 w-full object-cover" />
                    </div>
                  )}
                  {msg.type === "voice" && (
                     <div className="flex items-center gap-3 mb-2 p-2 bg-white/10 rounded-lg">
                        <Mic className="h-4 w-4" />
                        <div className="flex-1 h-1 bg-white/20 rounded-full">
                           <div className="w-[70%] h-full bg-white rounded-full" />
                        </div>
                        <span className="text-[10px] font-bold uppercase tracking-wider">0:05</span>
                     </div>
                  )}
                  {msg.role === "assistant" && !hasClarify ? (
                    <div className="flex items-start justify-between gap-2">
                      <AiChatMessageText text={msg.content ?? ""} />
                      {canShowAssistantActions ? (
                        <div className="flex shrink-0 items-center gap-1">
                          {ttsSupported ? (
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              onClick={() => handleSpeak(msg)}
                              disabled={isTtsLoading && speakingMessageId !== msg.id}
                              className={cn(
                                "min-h-[44px] min-w-[44px] rounded-lg",
                                speakingMessageId === msg.id && (isSpeaking || isTtsLoading)
                                  ? "bg-blue-100 text-blue-600 animate-pulse"
                                  : "text-slate-400 hover:bg-slate-100 hover:text-blue-600"
                              )}
                              title={
                                speakingMessageId === msg.id && (isSpeaking || isTtsLoading)
                                  ? "Dừng đọc"
                                  : "Đọc tin nhắn"
                              }
                              aria-label={
                                speakingMessageId === msg.id && (isSpeaking || isTtsLoading)
                                  ? "Dừng đọc"
                                  : "Đọc tin nhắn"
                              }
                            >
                              {speakingMessageId === msg.id && isTtsLoading ? (
                                <Loader2 className="h-5 w-5 animate-spin" />
                              ) : speakingMessageId === msg.id && isSpeaking ? (
                                <StopCircle className="h-5 w-5" />
                              ) : (
                                <Volume2 className="h-5 w-5" />
                              )}
                            </Button>
                          ) : null}
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            onClick={() => void handleCopyMessage(msg)}
                            className={cn(
                              "min-h-[44px] min-w-[44px] rounded-lg",
                              copiedMessageId === msg.id
                                ? "bg-emerald-100 text-emerald-600"
                                : "text-slate-400 hover:bg-slate-100 hover:text-emerald-600"
                            )}
                            title={copiedMessageId === msg.id ? "Đã sao chép" : "Sao chép tin nhắn"}
                            aria-label={copiedMessageId === msg.id ? "Đã sao chép" : "Sao chép tin nhắn"}
                          >
                            {copiedMessageId === msg.id ? (
                              <Check className="h-5 w-5" />
                            ) : (
                              <Copy className="h-5 w-5" />
                            )}
                          </Button>
                        </div>
                      ) : null}
                    </div>
                  ) : msg.role === "assistant" && hasClarify ? null : (
                    msg.content
                  )}
                </div>
                )}
                {hasChart ? (
                  <AiChatChartCard spec={msg.metadata!.chartSpec as Record<string, unknown>} />
                ) : null}
                {hasDraft && msg.metadata?.draftTable ? (
                  <AiChatDraftTableCard initial={msg.metadata.draftTable} />
                ) : null}
                {hasInventoryDraft && msg.metadata?.inventoryDraft ? (
                  <AiChatReceiptDraftCard initial={msg.metadata.inventoryDraft} />
                ) : null}
                {hasQueryTable && msg.metadata?.queryTable ? (
                  <AiChatQueryTableCard payload={msg.metadata.queryTable} />
                ) : null}
                {hasClarify && msg.metadata?.domainClarify ? (
                  <AiChatClarifyCard
                    payload={msg.metadata.domainClarify}
                    onPickSuggestion={(text) => {
                      setInputValue(text)
                      handleSend(text, "text", undefined, {
                        clarifyId: msg.metadata?.domainClarify?.clarifyId,
                        clarifyKind: msg.metadata?.domainClarify?.clarifyKind,
                        continuationContext: msg.metadata?.domainClarify?.continuationContext,
                        suggestedRewrite: msg.metadata?.domainClarify?.suggestedRewrite,
                      })
                    }}
                  />
                ) : null}
                {!isWelcomeMessage ? (
                  <div className={`mt-1 text-[11px] text-slate-400 ${msg.role === "user" ? "text-right" : "text-left"}`}>
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        )})}

        {isTyping && (
          <div className="flex justify-start">
            <div className="flex gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-sm shadow-blue-200/70">
                <Bot className="h-5 w-5" />
              </div>
              <div className="rounded-2xl rounded-tl-none border border-slate-100 border-l-2 border-l-blue-200 bg-white px-4 py-3 shadow-sm">
                <div className="flex items-center gap-1.5">
                  <div className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-bounce [animation-delay:-0.3s]" />
                  <div className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-bounce [animation-delay:-0.15s]" />
                  <div className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-bounce" />
                </div>
                {progressText ? (
                  <div className="mt-2 text-[11px] text-slate-500">{progressText}</div>
                ) : null}
              </div>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 md:p-6 bg-white border-t border-slate-200 z-10">
        <div className="max-w-4xl mx-auto flex flex-col gap-3">
           <div className="flex flex-wrap gap-2">
             {INTERACTION_MODES.map((mode) => (
               <button
                 key={mode.id}
                 type="button"
                 disabled={inputBusy}
                 onClick={() => setInteractionMode(mode.id)}
                 className={cn(
                   "inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors",
                   interactionMode === mode.id
                     ? "border-blue-600 bg-blue-600 text-white shadow-sm"
                     : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50"
                 )}
               >
                 <mode.icon className="h-3.5 w-3.5" />
                 {mode.label}
               </button>
             ))}
           </div>
           {isRecording && (
              <div className="flex items-center justify-between px-4 py-2 bg-rose-50 border border-rose-100 rounded-xl animate-pulse">
                <div className="flex items-center gap-3">
                   <div className="h-2 w-2 bg-rose-500 rounded-full shadow-[0_0_8px_rgba(244,63,94,0.6)]" />
                   <span className="text-xs font-bold text-rose-600 uppercase tracking-widest">Đang thu âm...</span>
                </div>
                <span className="text-xs font-mono font-bold text-rose-500">
                  {Math.floor(recordingSeconds / 60)}:{String(recordingSeconds % 60).padStart(2, "0")}
                </span>
              </div>
           )}
           {isTranscribing && (
               <div className="flex items-center gap-3 px-4 py-2 bg-blue-50 border border-blue-100 rounded-xl">
                 <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
                 <span className="text-xs font-bold text-blue-700 uppercase tracking-widest">
                   Đang chuyển giọng thành văn bản...
                 </span>
               </div>
            )}
           {progressText && (
              <div className="flex items-center gap-3 px-4 py-2 bg-amber-50 border border-amber-100 rounded-xl">
                <Loader2 className="h-4 w-4 text-amber-600 animate-spin shrink-0" />
                <span className="text-xs font-semibold text-amber-700">{progressText}</span>
              </div>
           )}
           <div className="flex items-end gap-2 bg-slate-50 border border-slate-200 rounded-2xl p-2 focus-within:ring-1 focus-within:ring-blue-500/20 focus-within:border-blue-400/50 transition-all duration-300">
            <textarea
              className="flex-1 max-h-32 min-h-[40px] bg-transparent border-none focus:ring-0 text-[15px] py-2 px-3 text-slate-700 placeholder:text-slate-400 resize-none leading-relaxed transition-all"
              placeholder="Hỏi trợ lý bằng chữ (ví dụ: thống kê đơn hàng, tồn kho)..."
              rows={1}
              disabled={inputBusy}
              value={inputValue}
              onChange={(e) => {
                setInputValue(e.target.value);
                e.target.style.height = 'inherit';
                e.target.style.height = `${e.target.scrollHeight}px`;
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSend()
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = '40px';
                }
              }}
            />
            
            <div className="flex items-center gap-1.5">
               <Button 
                 variant="ghost" 
                 size="icon" 
                 disabled={inputBusy && !isRecording}
                 className={`h-10 w-10 transition-all rounded-xl ${
                   isRecording
                     ? "bg-rose-100 text-rose-600 animate-pulse"
                     : isTranscribing
                       ? "bg-blue-100 text-blue-600"
                       : "text-slate-400 hover:text-rose-600 hover:bg-rose-50"
                 }`}
                 onClick={toggleRecording}
               >
                 {isTranscribing ? (
                   <Loader2 className="h-5 w-5 animate-spin" />
                 ) : (
                   <Mic className="h-5 w-5" />
                 )}
               </Button>
               <Button 
                 size="icon" 
                 className={`h-10 w-10 shadow-lg transition-all rounded-xl ${
                   inputValue.trim() ? "bg-blue-600 hover:bg-blue-700 text-white shadow-blue-200" : "bg-slate-200 text-slate-400 shadow-none cursor-not-allowed"
                 }`}
                 onClick={() => handleSend()}
                 disabled={!inputValue.trim() || inputBusy}
                 title="Gửi tin nhắn"
                 aria-label="Gửi tin nhắn"
               >
                 <Send className="h-5 w-5" />
               </Button>
            </div>
           </div>
           <p className="text-[10px] text-center text-slate-400 uppercase tracking-widest font-bold">
             Dữ liệu được bảo mật bởi hệ thống AI Mini ERP • © 2026
           </p>
        </div>
      </div>
    </div>
  )
}
