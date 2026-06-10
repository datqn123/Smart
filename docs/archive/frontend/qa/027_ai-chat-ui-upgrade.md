---
name: qa-ai-chat-ui-upgrade
description: QA Spec / Test Plan cho SRS-022 — nâng cấp giao diện ChatBotPage
metadata:
  type: project
---

# QA Spec 027 — AI Chat UI Upgrade (SRS-022)

## 1. Phạm vi kiểm thử

**File target:** `frontend/mini-erp/src/features/ai/pages/ChatBotPage.tsx`

Tất cả test case tập trung vào thay đổi UI/UX. Không có thay đổi logic → không cần test unit cho stream/SSE/TTS.

---

## 2. Test Cases

### TC-01: Avatar gradient — Bot

| | |
|---|---|
| **Pre-condition** | Trang chat đang mở |
| **Steps** | 1. Quan sát avatar bot ở header và trong message list |
| **Expected** | Avatar bot có gradient xanh (blue → indigo), có shadow nhẹ màu blue, góc bo `rounded-2xl` |
| **AC** | AC-01 |

---

### TC-02: Avatar gradient — User

| | |
|---|---|
| **Pre-condition** | Đã gửi ít nhất 1 tin nhắn |
| **Steps** | 1. Quan sát avatar user bên phải message |
| **Expected** | Avatar user có gradient slate đậm (slate-600 → slate-800), text trắng, không còn bg-slate-200 |
| **AC** | AC-01 |

---

### TC-03: User bubble gradient

| | |
|---|---|
| **Pre-condition** | Đã gửi ít nhất 1 tin nhắn |
| **Steps** | 1. Quan sát bubble tin nhắn của user |
| **Expected** | Bubble có gradient `from-blue-500 to-indigo-600`, có shadow nhẹ màu blue, góc `rounded-tr-none` |
| **AC** | AC-02 |

---

### TC-04: Assistant bubble accent border

| | |
|---|---|
| **Pre-condition** | Nhận được ít nhất 1 phản hồi từ assistant |
| **Steps** | 1. Quan sát bubble phản hồi assistant |
| **Expected** | Bubble có đường kẻ trái màu blue (`border-l-2`), nền trắng, shadow nhẹ |
| **AC** | AC-03 |

---

### TC-05: Typing indicator — màu sắc

| | |
|---|---|
| **Pre-condition** | Gửi một câu hỏi, chờ phản hồi |
| **Steps** | 1. Quan sát typing indicator trong khi chờ |
| **Expected** | 3 chấm bounce có màu blue/indigo/violet tương ứng, không còn slate-400 |
| **AC** | AC-04 |

---

### TC-06: Typing indicator — progressText hiển thị trong bubble

| | |
|---|---|
| **Pre-condition** | Backend trả về progress event trước khi có delta |
| **Steps** | 1. Gửi câu hỏi phức tạp, quan sát typing bubble |
| **Expected** | Text "Đang xử lý..." hoặc progress text xuất hiện bên dưới 3 chấm trong cùng bubble, KHÔNG có banner vàng riêng ở input area |
| **AC** | AC-04 |

---

### TC-07: Mode pills — icon

| | |
|---|---|
| **Pre-condition** | Trang chat đang mở |
| **Steps** | 1. Quan sát 6 mode pills ở input area |
| **Expected** | Mỗi pill có icon nhỏ bên trái label: Sparkles (Tự động), Database (Hỏi dữ liệu), Table2 (Bảng kết quả), BarChart2 (Biểu đồ), ClipboardList (Tạo bảng nhập), PackagePlus (Phiếu nhập kho) |
| **AC** | AC-05 |

---

### TC-08: Mode pills — active state

| | |
|---|---|
| **Pre-condition** | Trang chat đang mở |
| **Steps** | 1. Click lần lượt từng mode pill |
| **Expected** | Pill được chọn có nền blue-600 text trắng; các pill còn lại nền trắng/slate |
| **AC** | AC-05 |

---

### TC-09: Không còn nút Image + Paperclip

| | |
|---|---|
| **Pre-condition** | Trang chat đang mở |
| **Steps** | 1. Quan sát input toolbar (bên trái textarea) |
| **Expected** | Không có nút upload ảnh (ImageIcon), không có nút đính kèm (Paperclip). Chỉ còn Mic và Send |
| **AC** | AC-06 |

---

### TC-10: Copy button — hiển thị

| | |
|---|---|
| **Pre-condition** | Nhận được phản hồi hoàn chỉnh từ assistant (không đang stream) |
| **Steps** | 1. Quan sát vùng góc trên phải của bubble assistant |
| **Expected** | Có icon Copy bên cạnh nút TTS (Volume2) |
| **AC** | AC-07 |

---

### TC-11: Copy button — chức năng

| | |
|---|---|
| **Pre-condition** | Nhận được phản hồi hoàn chỉnh |
| **Steps** | 1. Click nút Copy trên một assistant message 2. Quan sát icon 3. Paste vào ô khác |
| **Expected** | Icon đổi thành Check màu emerald trong 1.5s rồi trở về Copy. Nội dung paste = nội dung message |
| **AC** | AC-07 |

---

### TC-12: Copy button — không hiển thị khi đang stream

| | |
|---|---|
| **Pre-condition** | Vừa gửi tin nhắn, assistant đang trả lời |
| **Steps** | 1. Quan sát bubble đang được stream |
| **Expected** | Không có nút Copy trên message đang stream |
| **AC** | AC-07 |

---

### TC-13: Clear chat button — hiển thị

| | |
|---|---|
| **Pre-condition** | Trang chat đang mở |
| **Steps** | 1. Quan sát header góc phải |
| **Expected** | Có nút RotateCcw với tooltip "Cuộc hội thoại mới" |
| **AC** | AC-08 |

---

### TC-14: Clear chat — cancel

| | |
|---|---|
| **Pre-condition** | Có ít nhất 1 tin nhắn đã gửi |
| **Steps** | 1. Click nút Clear 2. Click Cancel trong confirm dialog |
| **Expected** | Dialog đóng, conversation không thay đổi, messages vẫn còn |
| **AC** | AC-08 |

---

### TC-15: Clear chat — confirm

| | |
|---|---|
| **Pre-condition** | Có ít nhất 3 tin nhắn |
| **Steps** | 1. Click nút Clear 2. Click OK trong confirm dialog |
| **Expected** | Messages reset về welcome card duy nhất. interactionMode về "auto". Session storage có conversation ID mới |
| **AC** | AC-08 |

---

### TC-16: Clear chat — abort stream

| | |
|---|---|
| **Pre-condition** | Đang có stream chạy (đã gửi tin, đang chờ reply) |
| **Steps** | 1. Click nút Clear 2. Confirm OK |
| **Expected** | Stream bị abort (không còn delta đến), chat reset về welcome |
| **AC** | AC-08 |

---

### TC-17: Welcome message — card riêng

| | |
|---|---|
| **Pre-condition** | Trang chat vừa mở (hoặc sau khi clear) |
| **Steps** | 1. Quan sát message đầu tiên |
| **Expected** | Hiển thị card gradient blue-50→indigo-50 với icon Bot lớn, title "Xin chào! 👋", text chào mừng. KHÔNG có timestamp, KHÔNG có nút Copy/TTS |
| **AC** | AC-09 |

---

### TC-18: Welcome message — không phải bubble thường

| | |
|---|---|
| **Pre-condition** | Trang chat vừa mở |
| **Steps** | 1. So sánh welcome message với các assistant message thông thường |
| **Expected** | Welcome message không có `rounded-tl-none`, không có avatar nhỏ bên trái như messages thông thường |
| **AC** | AC-09 |

---

### TC-19: Timestamp — format

| | |
|---|---|
| **Pre-condition** | Có ít nhất 1 message user và 1 message assistant |
| **Steps** | 1. Quan sát timestamp bên dưới mỗi message |
| **Expected** | Timestamp hiển thị giờ:phút, không in hoa, không tracking-widest. Font nhỏ gọn `text-[11px]` |
| **AC** | AC-10 |

---

### TC-20: Regression — gửi và nhận tin nhắn text

| | |
|---|---|
| **Steps** | 1. Gõ câu hỏi 2. Nhấn Enter hoặc Send 3. Chờ phản hồi |
| **Expected** | Message user thêm vào list, stream phản hồi đúng, nội dung hiển thị markdown đúng qua AiChatMessageText |
| **AC** | AC-11 |

---

### TC-21: Regression — TTS

| | |
|---|---|
| **Pre-condition** | Browser hỗ trợ TTS |
| **Steps** | 1. Nhận phản hồi 2. Click nút Volume2 |
| **Expected** | Text được đọc, icon đổi sang StopCircle, click lại thì dừng |
| **AC** | AC-11 |

---

### TC-22: Regression — Voice recording

| | |
|---|---|
| **Steps** | 1. Click nút Mic 2. Nói 3. Click lại để dừng |
| **Expected** | Recording indicator (rose) hiển thị trong khi ghi, transcribing indicator (blue) sau khi dừng, message voice được gửi |
| **AC** | AC-11 |

---

### TC-23: Regression — Artifact cards

| | |
|---|---|
| **Steps** | 1. Chọn mode "Biểu đồ" 2. Hỏi câu tạo chart 3. Nhận phản hồi |
| **Expected** | `AiChatChartCard` render đúng bên dưới bubble assistant. Không bị ảnh hưởng bởi thay đổi bubble styles |
| **AC** | AC-11 |

---

### TC-24: Regression — Typing indicator ẩn đúng

| | |
|---|---|
| **Steps** | 1. Gửi tin nhắn 2. Quan sát trong khi chờ 3. Quan sát sau khi nhận phản hồi |
| **Expected** | Typing indicator chỉ hiện khi `isTyping = true`, ẩn ngay khi stream done. Không có 2 bot icon cùng lúc |
| **AC** | AC-11 |

---

## 3. Test không cần thiết (OUT OF SCOPE)

- Unit test cho `AiChatMessageText` — không thay đổi
- Unit test cho `useTextToSpeech` — không thay đổi  
- API/SSE integration test — không thay đổi
- Test các artifact card components — không thay đổi

---

## 4. Test environment

- Browser: Chrome latest (clipboard API, TTS, MediaRecorder)
- Không cần mock — có thể test UI thay đổi ngay với dev server

---

## 5. Pass/Fail Criteria

- **Pass:** TC-01 đến TC-24 đều pass
- **Blocking:** TC-20, TC-21, TC-22, TC-23, TC-24 (regression) — fail bất kỳ = block merge
- **Non-blocking:** TC-19 (timestamp) — cosmetic, có thể accept với note

**Superpowers:** TDD (define expected failing tests before coding)
**CodeGraph:** status + context (SRS-022)
