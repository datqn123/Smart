# RCA — Task002: chat trả về có khoảng trắng giữa từ ("R ất", "Th ân", "Ph ổ")

> Role: AI_BUG_INVESTIGATOR (ad-hoc, parallel session theo `ai_python/AGENTS/WORKFLOW_RULE.md` §1).
> Verdict: **bug nằm NGOÀI scope `ai_python`** — đóng Task002 ở phía `ai_python` mà không sửa code Python.
> Owner action đã thực hiện cùng phiên: patch frontend (xem §6).

---

## 1. Triệu chứng

UI chat hiển thị câu trả lời gemma-4 bị tách giữa âm tiết, ví dụ:

```
Xin chào! R ất vui được gặp bạn. Mình có thể giúp gì cho bạn hôm nay?
```

Lẽ ra: `Rất vui...`. Tương tự xảy ra với `Th ân`, `Ph ổ`, ... (mọi từ Việt mà tokenizer tách diacritic).

## 2. Phạm vi điều tra

| Thành phần | Đường dẫn | Kết luận |
| --- | --- | --- |
| Model upstream | FPT MKP gemma-4-31B-it | Sạch. Stream sub-word đúng SSE spec. |
| `ai_python` SSE serializer | `ai_python/app/core/sse.py` | Sạch cho case "Rất". (1 minor follow-up — xem §7.) |
| `ai_python` chat router | `ai_python/app/api/routers/chat.py` | Sạch. |
| BE relay | `backend/smart-erp/.../AiChatRelayController.java` | Sạch. Pass-through từng `data:`. |
| FE chat page | `frontend/mini-erp/src/features/ai/pages/ChatBotPage.tsx` | **Bug ở đây.** |

## 3. Reproduce

Cmd:

```powershell
curl.exe -N "http://localhost:9000/v1/chat/stream?q=Cho%20t%C3%B4i%20m%E1%BB%99t%20l%E1%BB%9Di%20ch%C3%A0o%20ng%E1%BA%AFn"
```

Raw SSE từ `ai_python` cho thấy mọi `event: delta` đều có **đúng 1 dòng `data:`** với nội dung sạch (terminal log lưu tại `c:\Users\Admin\.cursor\projects\d-do-an-tot-nghiep-project\terminals\12.txt`). Ví dụ chuỗi đại diện:

```
event: delta
data: T

event: delta
data: ù

event: delta
data: y

event: delta
data:  vào
```

Ghép tuần tự ⇒ `Tùy vào` (đúng). Như vậy upstream sạch.

## 4. Root cause

`ChatBotPage.tsx` định nghĩa hàm `appendDeltaSmart` chèn space khi ký tự cuối của text hiện có và ký tự đầu của delta mới đều "wordish" (chữ/số):

```tsx
const needsSpace = isWordish(last) && isWordish(first) && !/\s/.test(last) && !/\s/.test(first)
return needsSpace ? `${current} ${delta}` : `${current}${delta}`
```

Giả định ngầm: mỗi delta = 1 từ. Sai với gemma-4 stream sub-word — model tách "Rất" thành ` R` rồi `ất`:

| Bước | current | delta | last → first | Output sau bước |
| --- | --- | --- | --- | --- |
| n | `Xin chào!` | ` R` | `!` → ` ` | `Xin chào! R` |
| n+1 | `Xin chào! R` | `ất` | `R` → `ấ` | **`Xin chào! R ất`** |

Logic đúng phải là: tin tưởng model đã tự đặt leading-space khi cần (ví dụ ` vào`, ` đối`, ` tượng` trong terminal log) → FE chỉ concat thô.

## 5. Tại sao `ai_python` không sửa

Theo workflow §4 (Bất biến) + §6 (quan hệ FE/BE): scope task `ai_python` chỉ chạm `ai_python/`. Bug ở `frontend/mini-erp/`, fix bằng cách sửa Python sẽ tạo workaround ngược chuẩn (vd: BE chèn marker bytes để FE tự tách lại) — không hợp lý.

## 6. Owner action (đã thực hiện cùng phiên)

Patch FE — file `frontend/mini-erp/src/features/ai/pages/ChatBotPage.tsx`:

1. Xoá hàm `appendDeltaSmart`.
2. Trong callback `onDelta` của `openAiChatStream`, đổi `appendDeltaSmart(m.content ?? "", delta)` → `(m.content ?? "") + delta`.

Verify: lint clean. Cần test runtime: gọi UI, prompt câu chào → kỳ vọng `Rất vui...` không còn space giữa.

## 7. Follow-up trong scope `ai_python` (Minor)

Khi delta chứa nhiều newline (`"\n\n"` — paragraph break trong markdown), `sse_event` dùng `str.splitlines()` nên emit:

```
event: delta
data:
data:

```

Theo SSE spec, client gộp 2 dòng `data:` rỗng thành **1** newline → mất 1 newline so với input. Có thể quan sát ở terminal `12.txt:71-74`. Đề xuất:

- Đổi `data.splitlines()` → `data.split("\n")` trong `ai_python/app/core/sse.py` (đúng spec SSE; chỉ tách `\n`, không tách Unicode line separators).
- Tạo `Task<XXX>-followup.md` riêng nếu muốn track theo workflow §3 (severity `Minor`).

## 8. Gate exit (Task002 phía ai_python)

| Gate | Trạng thái |
| --- | --- |
| `G-AI-PLAN` | Skipped (bug investigation, dùng AI_BUG_INVESTIGATOR ad-hoc thay AI_PLANNER). |
| `G-AI-BA` … `G-AI-DS` | Skipped — bug ngoài scope. |
| `G-AI-OR` | **PASS** với verdict: out-of-scope, redirect FE patch. |

Budget used: ≤ 5 / 20 (chỉ tool-call điều tra). Không tạo branch `feature/ai-task002`.

## 9. Tham chiếu

- Workflow: `ai_python/AGENTS/WORKFLOW_RULE.md` §1, §3.1, §4, §6.
- Bug investigator role: `ai_python/AGENTS/AI_BUG_INVESTIGATOR_AGENT_INSTRUCTIONS.md`.
- Terminal raw SSE: `c:\Users\Admin\.cursor\projects\d-do-an-tot-nghiep-project\terminals\12.txt`.
- BE relay (sạch): `backend/smart-erp/src/main/java/com/example/smart_erp/ai/controller/AiChatRelayController.java`.
- FE consumer (đã fix): `frontend/mini-erp/src/features/ai/pages/ChatBotPage.tsx`.
