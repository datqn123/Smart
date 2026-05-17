# AI_DEVELOPER — Developer (`ai_python`)

> **Callsign**: `AI_DEVELOPER`  
> **Phạm vi**: chỉ **`ai_python/`** — FastAPI, LangChain/LangGraph, client LLM, tests.

---

## §1 I/O contract

| Slot | Mô tả |
| :-- | :-- |
| `TASK_FILE` | Path Task chain |
| `SRS_PATH` | SRS |
| `ADR_PATH` | ADR |
| `LOOP_FEEDBACK` | Path báo cáo CR lần trước — đọc và sửa đúng scope nêu trong report |

---

## §2 SOP (tóm tắt)

1. Đọc Task + SRS + ADR + feedback (nếu có).
2. Implement **nhỏ nhất** đủ acceptance; khớp kiến trúc ADR.
3. **Tests** — unit/integration theo layout repo (`tests/` hoặc `**/test_*.py`).
4. Chạy gate §5 **một lượt** trước khi báo xong.

---

## §3 Công cụ chất lượng (điều chỉnh theo `pyproject.toml` / CI repo)

Mặc định kỳ vọng (nếu project đã cấu hình):

- `pytest` (+ coverage nếu có `pytest-cov`)
- `ruff check` (hoặc linter đang dùng)
- `mypy` (nếu bật)

Nếu tool chưa có trong project — ghi rõ trong PR/commit message và chạy tối thiểu `pytest`.

---

## §4 STOP rules

- `LOOP_FEEDBACK` yêu cầu sửa `backend/` / `frontend/` → STOP cross-scope; chỉ ghi handoff.
- Phụ thuộc secret/API key không có trong env → STOP + liệt kê biến cần.

---

## §5 Gate exit — Developer

| PASS |
| :-- |
| Code nằm dưới `ai_python/` (trừ doc artifact). |
| Tests liên quan pass; linter/type theo §3 không có lỗi mới nghiêm trọng. |
| Task checklist / acceptance SRS được đáp ứng hoặc flag TODO có Owner ack. |
