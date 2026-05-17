import { useState, useRef, useEffect } from "react"
import { usePageTitle } from "@/context/PageTitleContext"
import { Send, Image as ImageIcon, Mic, Paperclip, MessageSquare, Bot, User } from "lucide-react"
import type { ChatMessage } from "../types"
import { Button } from "@/components/ui/button"
import { startAiChatPostStream, type AiChatStreamHandle } from "../api/aiChatSse"
import { AiChatChartCard } from "../components/AiChatChartCard"
import { AiChatDraftTableCard } from "../components/AiChatDraftTableCard"
import type { CatalogDraftTablePayload } from "../api/aiCatalogDraftApi"

export function ChatBotPage() {
  const { setTitle } = usePageTitle()
  useEffect(() => { setTitle("Trợ lý ảo AI") }, [setTitle])

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Xin chào. Tôi là trợ lý AI Mini ERP — trả lời qua Spring và dịch vụ Python (dữ liệu SQL read-only khi bạn hỏi số liệu). Hãy nhập câu hỏi bằng chữ.",
      timestamp: new Date().toISOString(),
      type: "text"
    }
  ])
  const [inputValue, setInputValue] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [conversationId] = useState(() => {
    const fromStorage = window.sessionStorage.getItem("ai_chat_conversation_id")
    if (fromStorage && fromStorage.trim().length > 0) return fromStorage
    const cid = crypto.randomUUID()
    window.sessionStorage.setItem("ai_chat_conversation_id", cid)
    return cid
  })
  const chatEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const streamRef = useRef<AiChatStreamHandle | null>(null)

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => { scrollToBottom() }, [messages])

  useEffect(() => {
    return () => {
      streamRef.current?.abort()
      streamRef.current = null
    }
  }, [])

  const appendDeltaSmart = (current: string, delta: string) => {
    if (!current) return delta
    if (!delta) return current
    const last = current.slice(-1)
    const first = delta.slice(0, 1)

    // Punctuation rules: no space before closing punctuations, and no space after opening punctuations.
    const noSpaceBefore = ",.!?:;)]}".includes(first)
    const noSpaceAfter = "([{".includes(last)
    if (noSpaceBefore || noSpaceAfter) return `${current}${delta}`

    const isLetter = (c: string) => /[A-Za-zÀ-ỹ]/.test(c)
    const isDigit = (c: string) => /[0-9]/.test(c)
    const isWordish = (c: string) => isLetter(c) || isDigit(c)

    // Add a space after punctuation when the next chunk starts a word.
    // Example: "Xin chào!" + "Rất vui..." => "Xin chào! Rất vui..."
    const spaceAfterPunct = ",.!?:;".includes(last) && isWordish(first)
    if (spaceAfterPunct) return `${current} ${delta}`

    // Do not insert spaces inside numbers like 2024.
    if (isDigit(last) && isDigit(first)) return `${current}${delta}`

    // Insert space only between word-ish boundaries (e.g. "Hello" + "world", "Năm" + "2024").
    const needsSpace = isWordish(last) && isWordish(first) && !/\s/.test(last) && !/\s/.test(first)
    return needsSpace ? `${current} ${delta}` : `${current}${delta}`
  }

  const handleSend = (text?: string, type: "text" | "image" | "voice" = "text", metadata?: ChatMessage["metadata"]) => {
    const content = text || inputValue
    if (!content && type === "text") return

    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content,
      timestamp: new Date().toISOString(),
      type,
      metadata
    }

    setMessages(prev => [...prev, newMessage])
    if (type === "text") setInputValue("")
    
    if (type !== "text") {
      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Phiên bản hiện tại chỉ hỗ trợ chat text.",
        timestamp: new Date().toISOString(),
        type: "text",
      }
      setMessages(prev => [...prev, assistantMsg])
      return
    }

    streamRef.current?.abort()
    streamRef.current = null

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

    streamRef.current = startAiChatPostStream({
      query: content,
      conversationId,
      onDelta: (delta) => {
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId ? { ...m, content: appendDeltaSmart(m.content ?? "", delta) } : m
          )
        )
      },
      onChart: (spec) => {
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId
              ? { ...m, metadata: { ...m.metadata, chartSpec: spec } }
              : m
          )
        )
      },
      onDraft: (payload: CatalogDraftTablePayload) => {
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId
              ? { ...m, metadata: { ...m.metadata, draftTable: payload } }
              : m
          )
        )
      },
      onDone: () => {
        setIsTyping(false)
        streamRef.current = null
      },
      onError: (message) => {
        setIsTyping(false)
        setMessages(prev =>
          prev.map(m => (m.id === assistantId ? { ...m, content: message || "Không thể kết nối trợ lý AI." } : m))
        )
        streamRef.current = null
      },
    })
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // In a real app, you would upload to server and get URL
      const reader = new FileReader()
      reader.onload = (event) => {
        handleSend("Gửi kèm hóa đơn", "image", { imageUrl: event.target?.result })
      }
      reader.readAsDataURL(file)
    }
  }

  const toggleRecording = () => {
    if (isRecording) {
      setIsRecording(false)
      handleSend("Nhập kho 50 thùng sữa Vinamilk lô A kệ B2", "voice")
    } else {
      setIsRecording(true)
    }
  }

  return (
    <div className="flex flex-col h-full bg-slate-50 overflow-hidden relative">
      {/* Chat Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-white border-b border-slate-200 z-10 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-200">
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
          <Button variant="ghost" size="icon" className="rounded-full hover:bg-slate-100">
            <MessageSquare className="h-5 w-5 text-slate-400" />
          </Button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 scroll-smooth scrollbar-hide">
        {messages.map((msg) => {
          const hasChart = msg.role === "assistant" && Boolean(msg.metadata?.chartSpec)
          const hasDraft = msg.role === "assistant" && Boolean(msg.metadata?.draftTable)
          const wideBubble = hasChart || hasDraft
          const layoutClass = hasDraft
            ? "w-full max-w-[min(960px,100%)]"
            : wideBubble
              ? "max-w-[96%] sm:max-w-[min(640px,88%)]"
              : "max-w-[85%] sm:max-w-[70%]"
          const assistantText = (msg.content ?? "").replace(/\*\*/g, "")
          return (
          <div key={msg.id} className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`flex gap-3 ${layoutClass} ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
              {/* Avatar */}
              <div className={`h-8 w-8 rounded-xl flex items-center justify-center shrink-0 shadow-sm ${
                msg.role === "assistant" ? "bg-blue-600 text-white" : "bg-slate-200 text-slate-600"
              }`}>
                {msg.role === "assistant" ? <Bot className="h-5 w-5" /> : <User className="h-5 w-5" />}
              </div>

              {/* Message Content */}
              <div className="min-w-0 flex-1 space-y-2">
                <div className={`px-4 py-3 rounded-2xl text-[15px] leading-relaxed shadow-sm ${
                  msg.role === "user" 
                    ? "bg-blue-600 text-white rounded-tr-none" 
                    : "bg-white text-slate-700 border border-slate-100 rounded-tl-none"
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
                  {msg.role === "assistant" ? (
                    <span className="whitespace-pre-line break-words">{assistantText}</span>
                  ) : (
                    msg.content
                  )}
                </div>
                {hasChart ? (
                  <AiChatChartCard spec={msg.metadata!.chartSpec as Record<string, unknown>} />
                ) : null}
                {hasDraft && msg.metadata?.draftTable ? (
                  <AiChatDraftTableCard initial={msg.metadata.draftTable} />
                ) : null}
                <div className={`text-[10px] font-bold uppercase tracking-widest text-slate-400 ${msg.role === "user" ? "text-right" : "text-left"}`}>
                  {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          </div>
        )})}

        {isTyping && (
          <div className="flex justify-start">
            <div className="flex gap-3">
              <div className="h-8 w-8 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-sm">
                <Bot className="h-5 w-5" />
              </div>
              <div className="bg-white border border-slate-100 px-4 py-3 rounded-2xl rounded-tl-none shadow-sm flex items-center gap-1.5">
                <div className="h-1.5 w-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                <div className="h-1.5 w-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                <div className="h-1.5 w-1.5 bg-slate-400 rounded-full animate-bounce" />
              </div>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 md:p-6 bg-white border-t border-slate-200 z-10">
        <div className="max-w-4xl mx-auto flex flex-col gap-3">
           {isRecording && (
              <div className="flex items-center justify-between px-4 py-2 bg-rose-50 border border-rose-100 rounded-xl animate-pulse">
                <div className="flex items-center gap-3">
                   <div className="h-2 w-2 bg-rose-500 rounded-full shadow-[0_0_8px_rgba(244,63,94,0.6)]" />
                   <span className="text-xs font-bold text-rose-600 uppercase tracking-widest">Đang thu âm...</span>
                </div>
                <span className="text-xs font-mono font-bold text-rose-500">0:04</span>
              </div>
           )}
           
           <div className="flex items-end gap-2 bg-slate-50 border border-slate-200 rounded-2xl p-2 focus-within:ring-1 focus-within:ring-blue-500/20 focus-within:border-blue-400/50 transition-all duration-300">
            <div className="flex items-center">
               <input 
                 type="file" 
                 accept="image/*" 
                 className="hidden" 
                 ref={fileInputRef}
                 onChange={handleFileUpload}
               />
               <Button 
                 variant="ghost" 
                 size="icon" 
                 className="h-10 w-10 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl"
                 onClick={() => fileInputRef.current?.click()}
               >
                 <ImageIcon className="h-5 w-5" />
               </Button>
               <Button 
                variant="ghost" 
                size="icon" 
                className="h-10 w-10 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl"
               >
                 <Paperclip className="h-5 w-5" />
               </Button>
            </div>
            
            <textarea
              className="flex-1 max-h-32 min-h-[40px] bg-transparent border-none focus:ring-0 text-[15px] py-2 px-3 text-slate-700 placeholder:text-slate-400 resize-none leading-relaxed transition-all"
              placeholder="Hỏi trợ lý bằng chữ (ví dụ: thống kê đơn hàng, tồn kho)..."
              rows={1}
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
                 className={`h-10 w-10 transition-all rounded-xl ${
                   isRecording ? "bg-rose-100 text-rose-600 animate-pulse" : "text-slate-400 hover:text-rose-600 hover:bg-rose-50"
                 }`}
                 onClick={toggleRecording}
               >
                 <Mic className="h-5 w-5" />
               </Button>
               <Button 
                 size="icon" 
                 className={`h-10 w-10 shadow-lg transition-all rounded-xl ${
                   inputValue.trim() ? "bg-blue-600 hover:bg-blue-700 text-white shadow-blue-200" : "bg-slate-200 text-slate-400 shadow-none cursor-not-allowed"
                 }`}
                 onClick={() => handleSend()}
                 disabled={!inputValue.trim()}
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
