---
name: tech-spec-ai-chat-ui-upgrade
description: Tech Spec / Coding Handoff cho SRS-022 — nâng cấp giao diện ChatBotPage
metadata:
  type: project
---

# Tech Spec 001 — AI Chat UI Upgrade (SRS-022)

## 1. Tổng quan

**File duy nhất cần sửa:** `frontend/mini-erp/src/features/ai/pages/ChatBotPage.tsx`

Không tạo file mới, không sửa bất kỳ file nào khác. Mọi thay đổi là UI/UX thuần tuý — logic SSE, hooks, artifact cards, types giữ nguyên.

---

## 2. Import changes

### 2.1 Thêm icons vào import lucide-react hiện có

```tsx
// Thay dòng import lucide hiện tại:
import {
  Send, Mic, MessageSquare, Bot, User, Loader2,
  Volume2, StopCircle,
  // --- THÊM MỚI ---
  Sparkles, Database, Table2, BarChart2, ClipboardList, PackagePlus,
  RotateCcw, Copy, Check,
} from "lucide-react"
```

> Xoá `Image as ImageIcon` và `Paperclip` khỏi import (R-06).

---

## 3. State changes

### 3.1 Thêm state mới

```tsx
// Thêm sau dòng khai báo speakingMessageId:
const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null)
```

### 3.2 Thay đổi conversationId state → dùng useState có setter

Hiện tại `conversationId` là `const [conversationId] = useState(...)` — không có setter. Cần đổi để hỗ trợ reset (R-08):

```tsx
const [conversationId, setConversationId] = useState(() => {
  const fromStorage = window.sessionStorage.getItem("ai_chat_conversation_id")
  if (fromStorage && fromStorage.trim().length > 0) return fromStorage
  const cid = crypto.randomUUID()
  window.sessionStorage.setItem("ai_chat_conversation_id", cid)
  return cid
})
```

---

## 4. Constants changes

### 4.1 INTERACTION_MODES — thêm trường icon

```tsx
const INTERACTION_MODES: { id: AiInteractionMode; label: string; icon: React.ReactNode }[] = [
  { id: "auto",            label: "Tự động",       icon: <Sparkles className="h-3.5 w-3.5" /> },
  { id: "data_query",      label: "Hỏi dữ liệu",   icon: <Database className="h-3.5 w-3.5" /> },
  { id: "data_table",      label: "Bảng kết quả",  icon: <Table2 className="h-3.5 w-3.5" /> },
  { id: "chart",           label: "Biểu đồ",       icon: <BarChart2 className="h-3.5 w-3.5" /> },
  { id: "catalog_draft",   label: "Tạo bảng nhập", icon: <ClipboardList className="h-3.5 w-3.5" /> },
  { id: "inventory_draft", label: "Phiếu nhập kho",icon: <PackagePlus className="h-3.5 w-3.5" /> },
]
```

### 4.2 WELCOME_MESSAGE constant

Tách welcome message ra constant để dễ reset:

```tsx
const WELCOME_MESSAGE: ChatMessage = {
  id: "1",
  role: "assistant",
  content: "Xin chào. Tôi là trợ lý AI Mini ERP — trả lời qua Spring và dịch vụ Python (dữ liệu SQL read-only khi bạn hỏi số liệu). Hãy nhập câu hỏi bằng chữ.",
  timestamp: new Date().toISOString(),
  type: "text",
}
```

Đổi `useState<ChatMessage[]>([{ id: "1", ... }])` → `useState<ChatMessage[]>([WELCOME_MESSAGE])`

---

## 5. Handler mới

### 5.1 handleClearChat

```tsx
const handleClearChat = () => {
  if (!window.confirm("Bắt đầu cuộc hội thoại mới? Lịch sử chat hiện tại sẽ bị xoá.")) return
  streamRef.current?.abort()
  streamRef.current = null
  stop()
  setSpeakingMessageId(null)
  setIsTyping(false)
  setProgressText("")
  const newCid = crypto.randomUUID()
  window.sessionStorage.setItem("ai_chat_conversation_id", newCid)
  setConversationId(newCid)
  setMessages([{ ...WELCOME_MESSAGE, timestamp: new Date().toISOString() }])
}
```

### 5.2 handleCopy

```tsx
const handleCopy = (msg: ChatMessage) => {
  void navigator.clipboard.writeText(msg.content).then(() => {
    setCopiedMessageId(msg.id)
    setTimeout(() => setCopiedMessageId(null), 1500)
  })
}
```

---

## 6. JSX changes (chi tiết từng vùng)

### 6.1 Header — thêm nút Clear Chat

Tìm `<div className="flex items-center gap-2">` bên phải header (chứa nút MessageSquare hiện tại), thêm nút Clear:

```tsx
<div className="flex items-center gap-2">
  <Button
    variant="ghost"
    size="icon"
    className="rounded-full hover:bg-slate-100"
    onClick={handleClearChat}
    title="Cuộc hội thoại mới"
  >
    <RotateCcw className="h-5 w-5 text-slate-400" />
  </Button>
  <Button variant="ghost" size="icon" className="rounded-full hover:bg-slate-100">
    <MessageSquare className="h-5 w-5 text-slate-400" />
  </Button>
</div>
```

### 6.2 Avatar — gradient

**Bot avatar** (2 chỗ: message list + typing indicator):
```tsx
// Cũ:
"bg-blue-600 text-white"
// Mới:
"bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-sm shadow-blue-200"
```

**User avatar:**
```tsx
// Cũ:
"bg-slate-200 text-slate-600"
// Mới:
"bg-gradient-to-br from-slate-600 to-slate-800 text-white"
```

### 6.3 Welcome message — card đặc biệt (R-09)

Trong `messages.map`, thêm điều kiện trước khi render bubble bình thường:

```tsx
// Ngay sau guard "ẩn bubble content rỗng đang stream":
if (msg.id === "1") {
  return (
    <div key={msg.id} className="flex justify-start w-full">
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100 rounded-2xl p-5 max-w-[85%] sm:max-w-[70%]">
        <div className="flex items-center gap-3 mb-3">
          <div className="h-10 w-10 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-md shadow-blue-200 shrink-0">
            <Bot className="h-6 w-6 text-white" />
          </div>
          <div>
            <p className="font-bold text-slate-800 text-base">Xin chào! 👋</p>
            <p className="text-xs text-slate-500">Trợ lý Mini ERP</p>
          </div>
        </div>
        <p className="text-[15px] leading-relaxed text-slate-600">{msg.content}</p>
      </div>
    </div>
  )
}
```

### 6.4 User bubble — gradient (R-02)

```tsx
// Cũ:
"bg-blue-600 text-white border border-slate-100 rounded-tl-none"
// Mới:
"bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-md shadow-blue-200/50 rounded-tr-none"
```

### 6.5 Assistant bubble — accent border (R-03)

```tsx
// Cũ:
"bg-white text-slate-700 border border-slate-100 rounded-tl-none"
// Mới:
"bg-white text-slate-700 border border-slate-100 border-l-2 border-l-blue-200 rounded-tl-none shadow-sm"
```

> **Lưu ý:** Tailwind không merge hai class `border` và `border-l-2` tốt — dùng `border border-slate-100 [border-left:2px_solid_theme(colors.blue.200)]` hoặc dùng inline style `style={{ borderLeftColor: '#bfdbfe', borderLeftWidth: 2 }}` nếu cần.

### 6.6 Copy button trong assistant message (R-07)

Trong khối render nút TTS (`Volume2`), thêm nút Copy ngay trước:

```tsx
{ttsSupported && msg.content.trim() && !isTyping ? (
  <div className="flex items-center gap-1 shrink-0">
    {/* Copy button */}
    <Button
      type="button"
      variant="ghost"
      size="icon"
      onClick={() => handleCopy(msg)}
      className="min-h-[44px] min-w-[44px] rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700"
      title="Sao chép"
    >
      {copiedMessageId === msg.id
        ? <Check className="h-4 w-4 text-emerald-500" />
        : <Copy className="h-4 w-4" />
      }
    </Button>
    {/* TTS button — giữ nguyên */}
    <Button ... />
  </div>
) : null}
```

> Nếu `ttsSupported` là false, copy button vẫn nên hiển thị. Tách điều kiện:

```tsx
{/* Copy — luôn hiện khi message done */}
{msg.content.trim() && (!isTyping) ? (
  <Button ... onClick={() => handleCopy(msg)} ...>
    {copiedMessageId === msg.id ? <Check .../> : <Copy .../>}
  </Button>
) : null}
{/* TTS — chỉ hiện khi supported */}
{ttsSupported && msg.content.trim() && !isTyping ? (
  <Button ... onClick={() => handleSpeak(msg)} .../>
) : null}
```

### 6.7 Typing indicator — màu sắc (R-04)

```tsx
// Cũ:
<div className="h-1.5 w-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
<div className="h-1.5 w-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
<div className="h-1.5 w-1.5 bg-slate-400 rounded-full animate-bounce" />

// Mới:
<div className="h-2 w-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
<div className="h-2 w-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
<div className="h-2 w-2 bg-violet-400 rounded-full animate-bounce" />
```

Thêm `progressText` ngay dưới 3 chấm (trong cùng bubble):

```tsx
<div className="bg-white border border-slate-100 border-l-2 border-l-blue-200 px-4 py-3 rounded-2xl rounded-tl-none shadow-sm flex flex-col gap-2">
  <div className="flex items-center gap-1.5">
    <div className="h-2 w-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
    <div className="h-2 w-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
    <div className="h-2 w-2 bg-violet-400 rounded-full animate-bounce" />
  </div>
  {progressText ? (
    <span className="text-[11px] text-slate-400">{progressText}</span>
  ) : null}
</div>
```

> Đồng thời **xoá** banner `progressText` riêng ở input area (khối `{progressText && (...)}` hiện tại).

### 6.8 Mode pills — thêm icon (R-05)

```tsx
// Cũ:
{mode.label}

// Mới:
<span className="flex items-center gap-1.5">
  {mode.icon}
  {mode.label}
</span>
```

### 6.9 Xoá Image + Paperclip buttons (R-06)

Xoá toàn bộ khối:

```tsx
// XOÁ:
<input type="file" accept="image/*" className="hidden" ref={fileInputRef} onChange={handleFileUpload} />
<Button variant="ghost" size="icon" ... onClick={() => fileInputRef.current?.click()}>
  <ImageIcon className="h-5 w-5" />
</Button>
<Button variant="ghost" size="icon" ...>
  <Paperclip className="h-5 w-5" />
</Button>
```

Xoá cả `fileInputRef` ref, `handleFileUpload` handler, và `Image as ImageIcon` + `Paperclip` import.

### 6.10 Timestamp — gọn hơn (R-10)

```tsx
// Cũ:
"text-[10px] font-bold uppercase tracking-widest text-slate-400"
// Mới:
"text-[11px] text-slate-400 mt-1"
```

---

## 7. Cleanup sau khi xoá Image/Paperclip

Xoá các phần sau vì không còn dùng:
- `fileInputRef` (`useRef<HTMLInputElement>`)
- `handleFileUpload` function
- Block xử lý `type === "image"` trong `handleSend` **giữ lại** (vì user vẫn có thể nhận ảnh về lý thuyết — chỉ ẩn UI upload)

---

## 8. Thứ tự triển khai đề xuất

1. Cập nhật imports (thêm icons, bỏ ImageIcon/Paperclip)
2. Thêm `WELCOME_MESSAGE` constant
3. Đổi `useState` messages dùng constant
4. Đổi `conversationId` sang có setter
5. Thêm state `copiedMessageId`
6. Thêm `handleClearChat`, `handleCopy`
7. Sửa `INTERACTION_MODES` thêm icon
8. Xoá `fileInputRef`, `handleFileUpload`
9. Sửa Header JSX (nút Clear)
10. Sửa avatar classes (2 chỗ trong message list + typing indicator)
11. Thêm welcome message card (guard `msg.id === "1"`)
12. Sửa user bubble class
13. Sửa assistant bubble class
14. Sửa typing indicator (màu + progressText)
15. Xoá progressText banner ở input area
16. Thêm copy button trong assistant message
17. Sửa mode pills JSX (thêm icon)
18. Xoá Image/Paperclip buttons khỏi input toolbar
19. Sửa timestamp class

---

## 9. Rủi ro & Lưu ý

| Rủi ro | Mitigation |
|---|---|
| Tailwind không merge `border` + `border-l-2` | Dùng inline style hoặc `[border-left-width:2px]` arbitrary |
| `window.confirm` bị chặn trong một số browser embedded | Acceptable — đây là internal tool |
| Copy API không hoạt động trên HTTP (non-HTTPS) | Wrap trong `try/catch`, silent fail |
| Reset `conversationId` trong `handleClearChat` nhưng `interactionMode` vẫn giữ — có thể gây confusion | Thêm `setInteractionMode("auto")` trong `handleClearChat` |

**Superpowers:** writing-plans (exact, bite-sized, testable slices)
**CodeGraph:** status + context (SRS-022)
