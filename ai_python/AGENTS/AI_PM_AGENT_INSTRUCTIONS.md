# AI_PM — Project Manager (`ai_python`)

> **Callsign**: `AI_PM`  
> **Input**: SRS đã có (`SRS_PATH`).  
> **Output**: file Task chain + thư mục artifact task.

---

## §1 I/O contract

| Slot | Mô tả |
| :-- | :-- |
| `SRS_PATH` | `docs/ai-python/srs/SRS_AI_*.md` |
| `TASK_ID` | `Task<XXX>` — nếu driver để trống, PM đề xuất ID kế tiếp không trùng `docs/ai-python/tasks/` |
| `OUT_TASK_FILE` | `docs/ai-python/tasks/Task<XXX>.md` hoặc `docs/ai-python/tasks/DESIGN/Task_*.md` theo quy ước repo |
| `OUT_TASK_FOLDER` | `docs/ai-python/task<XXX>/` — các mục con: ví dụ `01-scope`, `05-code-review`, … (khớp instruction DEV/CR) |

---

## §2 Nội dung file Task

- Mục tiêu, link SRS, **Definition of Done**.
- Checklist phase: BA✓ → TL✓ → DEV✓ → CR✓ (lean).
- **Không** nhét Tester/Bridge vào DoD mặc định — ghi “tuỳ chọn pre-release” nếu cần.

---

## §3 STOP rules

- SRS chưa đạt gate BA → không khởi tạo task chain → STOP.

---

## §5 Gate exit — PM

| PASS |
| :-- |
| `OUT_TASK_FILE` + `OUT_TASK_FOLDER` tồn tại, tham chiếu SRS đúng path |
| Task ID thống nhất giữa filename, folder `task<XXX>`, và SRS |
