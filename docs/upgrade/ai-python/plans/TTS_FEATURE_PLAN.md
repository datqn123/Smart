# TTS (Text-to-Speech) Feature — Implementation Plan

## Goal
Khi AI trả lời bằng văn bản, user có thể nhấn nút "nói" để AI đọc lại câu trả lời bằng giọng tiếng Việt (vi-VN).

## Architecture Decision
- **Phase 1: Frontend Web Speech API** — Dùng `window.speechSynthesis` của browser, không cần sửa backend
- **Giọng đọc**: Tiếng Việt (`vi-VN`) mặc định
- **UI**: Nút `Volume2` icon (lucide-react) ở góc phải mỗi tin nhắn assistant

---

## Phase 1: Frontend TTS Hook

### 1.1 Tạo hook: `useTextToSpeech.ts`
**Vị trí:** `frontend/mini-erp/src/features/ai/hooks/useTextToSpeech.ts`

```typescript
import { useState, useEffect, useCallback, useRef } from "react"

interface UseTextToSpeechReturn {
  speak: (text: string) => void
  stop: () => void
  pause: () => void
  resume: () => void
  isSpeaking: boolean
  isPaused: boolean
}

export function useTextToSpeech(): UseTextToSpeechReturn {
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null)

  useEffect(() => {
    return () => {
      window.speechSynthesis.cancel()
    }
  }, [])

  const speak = useCallback((text: string) => {
    window.speechSynthesis.cancel() // Stop any ongoing speech

    const cleanText = text.replace(/\*\*/g, "").replace(/#{1,6}\s/g, "").replace(/[-*_~`]/g, "")
    if (!cleanText.trim()) return

    const utterance = new SpeechSynthesisUtterance(cleanText)
    utterance.lang = "vi-VN"
    utterance.rate = 1.0
    utterance.pitch = 1.0

    // Try to find a Vietnamese voice
    const voices = window.speechSynthesis.getVoices()
    const viVoice = voices.find(v => v.lang.startsWith("vi"))
    if (viVoice) utterance.voice = viVoice

    utterance.onstart = () => {
      setIsSpeaking(true)
      setIsPaused(false)
    }
    utterance.onend = () => {
      setIsSpeaking(false)
      setIsPaused(false)
    }
    utterance.onerror = () => {
      setIsSpeaking(false)
      setIsPaused(false)
    }

    utteranceRef.current = utterance
    window.speechSynthesis.speak(utterance)
  }, [])

  const stop = useCallback(() => {
    window.speechSynthesis.cancel()
    setIsSpeaking(false)
    setIsPaused(false)
  }, [])

  const pause = useCallback(() => {
    window.speechSynthesis.pause()
    setIsPaused(true)
  }, [])

  const resume = useCallback(() => {
    window.speechSynthesis.resume()
    setIsPaused(false)
  }, [])

  return { speak, stop, pause, resume, isSpeaking, isPaused }
}
```

**Key logic:**
- `speak(text)` — Xóa markdown markers (**, #, -, *, _, ~, `), tạo utterance với `lang: "vi-VN"`, tìm voice tiếng Việt nếu có
- `stop()` — Dừng đọc ngay lập tức
- `pause()` / `resume()` — Tạm dừng / tiếp tục
- Cleanup trên unmount — cancel mọi speech đang chạy

---

## Phase 2: UI Integration

### 2.1 `ChatBotPage.tsx` — Thêm nút speak vào assistant messages

**Vị trí chèn:** Trong message bubble của assistant (dòng 416-441), góc phải trên cùng.

**Thay đổi cụ thể:**

```tsx
// Import thêm icons
import { Bot, Mic, User, Volume2, StopCircle } from "lucide-react"

// Trong component, thêm hook
const { speak, stop, isSpeaking } = useTextToSpeech()

// Track which message is currently speaking
const [speakingMessageId, setSpeakingMessageId] = useState<string | null>(null)

// Handler cho nút speak
const handleSpeak = (msg: ChatMessage) => {
  if (speakingMessageId === msg.id && isSpeaking) {
    stop()
    setSpeakingMessageId(null)
  } else {
    setSpeakingMessageId(msg.id)
    speak(msg.content)
  }
}
```

**UI trong message bubble (dòng ~436-437):**

```tsx
{msg.role === "assistant" && !hasClarify && (
  <div className="flex items-start justify-between gap-2">
    <span className="whitespace-pre-line break-words flex-1">{assistantText}</span>
    {msg.content && !isTyping && (
      <button
        onClick={() => handleSpeak(msg)}
        className="shrink-0 p-1 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-blue-600 transition-colors"
        title={speakingMessageId === msg.id && isSpeaking ? "Dừng đọc" : "Đọc tin nhắn"}
      >
        {speakingMessageId === msg.id && isSpeaking ? (
          <StopCircle className="h-4 w-4" />
        ) : (
          <Volume2 className="h-4 w-4" />
        )}
      </button>
    )}
  </div>
)}
```

**Logic hiển thị:**
- Chỉ hiện trên tin nhắn `role === "assistant"`
- Chỉ hiện khi `msg.content` không rỗng
- Ẩn khi `isTyping === true` (AI đang stream trả lời)
- Icon `Volume2` khi idle, `StopCircle` khi đang đọc
- Hover effect: `text-blue-600`

---

## Phase 3: State Management & Edge Cases

### 3.1 Dừng đọc khi gửi tin nhắn mới
Khi user gửi tin nhắn mới hoặc AI bắt đầu stream, dừng TTS đang chạy:

```tsx
// Trong handleSend, trước khi gọi API
if (speakingMessageId) {
  stop()
  setSpeakingMessageId(null)
}
```

### 3.2 Dừng đọc khi AI bắt đầu stream
Khi nhận `delta` event đầu tiên từ SSE:

```tsx
// Trong useEffect theo dõi isTyping
useEffect(() => {
  if (isTyping && speakingMessageId) {
    stop()
    setSpeakingMessageId(null)
  }
}, [isTyping])
```

### 3.3 Multiple messages
- Chỉ 1 message được đọc tại 1 thời điểm
- Nhấn nút speak trên message khác → dừng message cũ, đọc message mới
- Nhấn nút trên message đang đọc → dừng

### 3.4 Browser compatibility
- Web Speech API hỗ trợ trên Chrome, Edge, Safari, Firefox
- Fallback: Nếu browser không hỗ trợ, ẩn nút speak hoặc hiện toast "Trình duyệt không hỗ trợ đọc văn bản"

```tsx
const isSpeechSupported = typeof window !== "undefined" && "speechSynthesis" in window
```

---

## Phase 4: Polish & UX

### 4.1 Loading state khi đang đọc
Thêm visual feedback khi AI đang đọc:

```tsx
// Pulse animation khi đang speak
<button className={`shrink-0 p-1 rounded-lg transition-colors ${
  speakingMessageId === msg.id && isSpeaking
    ? "bg-blue-100 text-blue-600 animate-pulse"
    : "hover:bg-slate-100 text-slate-400 hover:text-blue-600"
}`}>
```

### 4.2 Auto-scroll khi đang đọc
Nếu câu trả lời dài, auto-scroll để user thấy đoạn đang được đọc (optional).

### 4.3 Keyboard shortcut (optional)
- `Ctrl+Shift+S` — Stop TTS
- `S` — Speak last assistant message (khi focus trong chat)

---

## Files to Create

| File | Purpose |
|------|---------|
| `frontend/mini-erp/src/features/ai/hooks/useTextToSpeech.ts` | Custom hook wrapping Web Speech API |

## Files to Modify

| File | Changes |
|------|---------|
| `frontend/mini-erp/src/features/ai/pages/ChatBotPage.tsx` | Import hook, thêm nút Volume2/StopCircle vào assistant messages, handle speak/stop logic |

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Web Speech API | Không cần backend, miễn phí, latency bằng 0, hoạt động offline |
| Vietnamese voice (`vi-VN`) | App dùng tiếng Việt là chính |
| Clean markdown before speak | SpeechSynthesis không render được markdown, cần strip `**`, `#`, `-`, v.v. |
| Single message at a time | Tránh overlap audio, UX rõ ràng hơn |
| Stop on new message | Tự nhiên — user gửi tin mới thì dừng đọc câu cũ |
| Hide button while typing | Tránh đọc câu chưa hoàn chỉnh |

---

## Browser Support

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome | Full | Google voices chất lượng tốt cho vi-VN |
| Edge | Full | Microsoft voices |
| Safari | Full | Apple voices |
| Firefox | Full | Ít voice options hơn |
| Mobile Chrome | Full | Hoạt động tốt trên iOS/Android |

---

## Testing

### Manual testing checklist
- [ ] Nhấn Volume2 → AI đọc tin nhắn bằng tiếng Việt
- [ ] Nhấn StopCircle → dừng đọc ngay
- [ ] Gửi tin nhắn mới → dừng đọc câu cũ
- [ ] AI đang stream → nút speak ẩn
- [ ] Tin nhắn rỗng → không hiện nút
- [ ] Tin nhắn có markdown → đọc text sạch (không đọc **)
- [ ] Nhấn speak trên message khác → dừng message cũ, đọc message mới
- [ ] Reload page → speech dừng (cleanup)

### Edge cases
- Tin nhắn rất dài (>5000 chars) → SpeechSynthesis có thể bị truncate
- Browser không có voice vi-VN → fallback sang default voice
- User tắt speech trong browser settings → graceful degradation

---

## Phase 2 (Future — Backend TTS)
Nếu cần voice chất lượng cao hơn (giọng tự nhiên hơn):

1. **Backend:** Thêm `POST /api/v1/ai/chat/synthesize` endpoint
2. **Service:** Dùng FPT Cloud TTS API hoặc OpenAI `/v1/audio/speech`
3. **Spring relay:** Forward audio request
4. **Frontend:** Nhận audio blob → play qua `<audio>` element hoặc `AudioContext`
5. **UI:** Giữ nguyên nút Volume2, nhưng thay vì gọi `speechSynthesis` thì fetch audio từ backend
