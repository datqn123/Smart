# 1. Kiến trúc hệ thống Agentic AI

## Tổng quan pipeline

Trợ lý AI nhận câu hỏi tiếng Việt về dữ liệu ERP (doanh thu, tồn kho, đơn
hàng...) và trả lời dựa trên truy vấn read-only vào PostgreSQL. Hệ được tổ
chức theo mô hình **planner–executor**:

```
User ──> FastAPI /chat (SSE) ──> Orchestrator (vòng lặp tối đa 6 bước)
                                      │
                              Session Manager (SM)
                       "bộ não" — quyết định bước kế tiếp
                                      │
              ┌───────────┬───────────┼─────────────────┐
        sql_execute  data_validator  answer_composer  (HITL clarify)
        sinh + chạy   thẩm định       soạn trả lời      hỏi lại user
        SELECT        kết quả         tiếng Việt        khi bí
```

## Vai trò từng thành phần

| Thành phần | Nhiệm vụ | Cơ chế an toàn |
|---|---|---|
| **Session Manager** | Phân tích yêu cầu + lịch sử, chọn action: `call_tool / retry_tool / replan / request_clarification / finish` | Bound 2 lần parse JSON; fallback finish an toàn |
| **sql_execute** | Dịch câu hỏi → 1 câu `SELECT`, thực thi | Guard sqlparse chặn non-SELECT; transaction READ ONLY; semantic self-check |
| **data_validator** | Thẩm định kết quả có đủ/đúng để trả lời không | Chặn answer_composer chạy khi chưa pass |
| **answer_composer** | Soạn câu trả lời tiếng Việt + gợi ý bước tiếp | self_validate bắt buộc có marker "Gợi ý:" |
| **Conversation Memory** | Lưu các lượt (user → answer) theo thread; quá 10 lượt thì gộp vào rolling summary bằng LLM | SM thấy nguyên văn các lượt gần nhất; tool chỉ nhận summary |
| **HITL (Human-in-the-loop)** | Tạm dừng phiên, lưu snapshot SQLite, chờ user làm rõ rồi chạy tiếp | Snapshot khôi phục đúng câu hỏi gốc |

## Đặc điểm thiết kế quan trọng

1. **Tri thức nằm trong file, không nằm trong code.** Mỗi tool có `skill.md`
   (vai trò, ràng buộc, few-shot); sql_execute có thêm `schema.md` (toàn bộ
   schema DB + quy tắc cốt lõi + mẫu join). File được **đọc lại mỗi lần
   gọi** — sửa prompt có hiệu lực ngay, không cần restart.
2. **Một model dùng chung (Qwen)** cho mọi vai trò; role `sm` chỉ hạ
   temperature. Đây là ràng buộc chi phí của đồ án và là yếu tố giải thích
   nhiều quy tắc "dặn dò" trong skill file (xem tài liệu 4).
3. **Phòng thủ nhiều lớp cho SQL**: guard cú pháp chặn non-SELECT TRƯỚC khi
   chạm DB → kết nối mở transaction READ ONLY → role DB chỉ có quyền đọc.
4. **Thinking log**: logger riêng tên `think` tường thuật dòng suy nghĩ của
   từng agent (`[SM] suy nghi: ... -> quyet dinh: ...`) giúp quan sát và
   chẩn đoán hành vi — tương tự trace của các agent framework.
