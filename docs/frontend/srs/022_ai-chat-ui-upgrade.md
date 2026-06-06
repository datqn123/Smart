---
name: srs-ai-chat-ui-upgrade
description: SRS nâng cấp giao diện chat trợ lý ảo AI — ChatBotPage
metadata:
  type: project
---

# SRS-022 — Nâng cấp giao diện Chat Trợ lý ảo AI

## 1. Bối cảnh & Mục tiêu

**File chính:** `frontend/mini-erp/src/features/ai/pages/ChatBotPage.tsx`

Giao diện chat hiện tại hoạt động đúng nhưng trải nghiệm thị giác còn đơn giản:
- Avatar bot/user là icon đơn sắc không có chiều sâu
- Bubble user message màu blue flat, không có gradient
- Typing indicator 3 chấm nhạt, khó nhận biết
- Mode pills chỉ có text, không có icon gợi nhớ chức năng
- Không có nút copy nội dung assistant
- Không có nút xoá / bắt đầu cuộc hội thoại mới
- Timestamp quá nhỏ, khó đọc
- Welcome message là text thuần — không có visual cue rõ ràng
- Placeholder artifacts (Image, Paperclip) không hoạt động nhưng vẫn hiển thị gây nhầm lẫn

**Mục tiêu:** Nâng cấp thị giác, UX, và tính năng nhỏ mà **không thay đổi logic stream/SSE, types, API**.

---

## 2. Phạm vi thay đổi

### 2.1 Ngoài phạm vi (KHÔNG chạm vào)
- Logic stream SSE (`startAiChatPostStream`, `streamRef`)
- `useTextToSpeech` hook
- Tất cả artifact cards: `AiChatChartCard`, `AiChatDraftTableCard`, `AiChatReceiptDraftCard`, `AiChatQueryTableCard`, `AiChatClarifyCard`
- `AiChatMessageText` (markdown renderer)
- `types.ts`, `aiChatSse.ts`, audio utils
- Backend / API

### 2.2 Trong phạm vi
Tất cả thay đổi nằm trong `ChatBotPage.tsx`:

| Khu vực | Thay đổi |
|---|---|
| Header | Avatar gradient, nút Clear Chat |
| Bot/User avatar | Gradient + shadow thay vì flat color |
| User bubble | Gradient xanh thay vì blue-600 flat |
| Assistant bubble | Subtle bg + left border accent |
| Typing indicator | Animation sống động hơn, có màu |
| Mode pills | Thêm icon cho từng mode |
| Input toolbar | Ẩn Image + Paperclip (chưa dùng được) |
| Copy button | Nút copy nội dung assistant message |
| Clear chat | Nút reset conversation |
| Welcome message | Card đặc biệt thay vì bubble thường |
| Timestamp | Rõ ràng hơn, align với bubble |

---

## 3. Yêu cầu chi tiết

### R-01: Avatar nâng cấp
- **Bot avatar:** gradient `from-blue-500 to-indigo-600`, shadow `shadow-blue-200`, `rounded-2xl`
- **User avatar:** gradient `from-slate-600 to-slate-800`, `rounded-xl`
- Kích thước giữ nguyên `h-8 w-8`

### R-02: User message bubble — gradient
- Thay `bg-blue-600` → `bg-gradient-to-br from-blue-500 to-indigo-600`
- Giữ `text-white rounded-tr-none`
- Thêm `shadow-md shadow-blue-200/50`

### R-03: Assistant message bubble — accent border
- Thêm `border-l-2 border-l-blue-200` bên trái
- Background: `bg-white` giữ nguyên
- Thêm `shadow-sm`

### R-04: Typing indicator — cải thiện animation
- 3 chấm đổi màu: chấm 1 = `bg-blue-400`, chấm 2 = `bg-indigo-400`, chấm 3 = `bg-violet-400`
- Thêm progress text nhỏ bên dưới nếu `progressText` có giá trị (hiện text đang xử lý ngay trong typing bubble thay vì banner riêng ở input area)

### R-05: Mode pills — thêm icon
Mỗi mode có icon lucide-react tương ứng:

| Mode | Icon | Label |
|---|---|---|
| auto | `Sparkles` | Tự động |
| data_query | `Database` | Hỏi dữ liệu |
| data_table | `Table2` | Bảng kết quả |
| chart | `BarChart2` | Biểu đồ |
| catalog_draft | `ClipboardList` | Tạo bảng nhập |
| inventory_draft | `PackagePlus` | Phiếu nhập kho |

### R-06: Ẩn Image + Paperclip button
- Xoá hoặc ẩn 2 nút `ImageIcon` và `Paperclip` trong input toolbar
- Lý do: chưa có backend xử lý, gây nhầm lẫn người dùng

### R-07: Copy button trên assistant message
- Thêm nút copy (`Copy` icon từ lucide) ngay cạnh nút TTS (`Volume2`)
- Click → copy `msg.content` vào clipboard, hiển thị `Check` icon trong 1.5s rồi trở lại `Copy`
- Chỉ hiện khi message đã `done` (không phải đang stream: `!isTyping || msg.id !== lastAssistantId`)

### R-08: Clear chat button ở header
- Thêm nút `RotateCcw` (hoặc `Trash2`) ở góc phải header
- Click → `confirm` dialog đơn giản (native `window.confirm`) → reset `messages` về welcome message gốc, clear `sessionStorage` conversation id, tạo UUID mới
- Tooltip: "Cuộc hội thoại mới"

### R-09: Welcome message — card đặc biệt
- Message đầu tiên (`id === "1"`) render khác: không dùng bubble bình thường
- Dùng card có gradient nhẹ `bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100 rounded-2xl p-5`
- Hiển thị icon Bot lớn hơn (`h-10 w-10`), title "Xin chào! 👋", và text chào mừng
- Không có timestamp, không có TTS button

### R-10: Timestamp rõ hơn
- Đổi class timestamp từ `text-[10px] font-bold uppercase tracking-widest text-slate-400` → `text-[11px] text-slate-400 mt-1`
- Bỏ `uppercase tracking-widest`

---

## 4. Acceptance Criteria

| ID | Criteria |
|---|---|
| AC-01 | Avatar bot có gradient blue→indigo, avatar user có gradient slate |
| AC-02 | User bubble có gradient, không còn flat blue-600 |
| AC-03 | Assistant bubble có border-l-2 blue accent |
| AC-04 | 3 chấm typing có màu blue/indigo/violet |
| AC-05 | Mode pills có icon tương ứng, hiển thị đúng label |
| AC-06 | Không còn nút Image và Paperclip trong input |
| AC-07 | Nút copy xuất hiện trên assistant message, hoạt động đúng |
| AC-08 | Nút clear chat ở header, click → reset conversation |
| AC-09 | Welcome message render dạng card riêng, không phải bubble |
| AC-10 | Timestamp nhỏ gọn, không uppercase |
| AC-11 | Không có regression: stream, TTS, recording, artifacts vẫn hoạt động bình thường |

---

## 5. Ghi chú kỹ thuật

- Tất cả thay đổi trong 1 file duy nhất: `ChatBotPage.tsx`
- Import thêm icons: `Sparkles, Database, Table2, BarChart2, ClipboardList, PackagePlus, RotateCcw, Copy, Check`
- State thêm: `copiedMessageId: string | null` (cho R-07), reset conversation id bằng cách gọi `window.sessionStorage.removeItem` + re-generate UUID
- Không tạo component mới, giữ tất cả inline trong file

---

## 6. File liên quan

| File | Vai trò |
|---|---|
| `features/ai/pages/ChatBotPage.tsx` | **Target duy nhất** |
| `features/ai/types.ts` | Đọc tham khảo, không sửa |
| `features/ai/components/AiChatMessageText.tsx` | Đọc tham khảo, không sửa |
| `features/ai/api/aiChatSse.ts` | Đọc tham khảo, không sửa |

**Superpowers:** brainstorming (requirements discovery)
**CodeGraph:** status + context
