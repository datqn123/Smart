---
name: activity-diagram
description: Triệu Agent Activity Diagram (Mermaid) — luồng nghiệp vụ hoặc từ code; output một khối mermaid theo ACTIVITY_DIAGRAM_AGENT_INSTRUCTIONS.md.
---

# /activity-diagram — Agent vẽ activity diagram (Mermaid)

Đọc và tuân thủ **[`frontend/AGENTS/ACTIVITY_DIAGRAM_AGENT_INSTRUCTIONS.md`](../frontend/AGENTS/ACTIVITY_DIAGRAM_AGENT_INSTRUCTIONS.md)**.

## Tham số (từ tin nhắn user)

- **Nguồn**: mô tả luồng tự do **hoặc** `@file` / đường dẫn code **hoặc** trích đoạn tài liệu.
- **Ngôn ngữ nhãn** (tùy chọn): `Lang=VN` | `Lang=EN`.
- **Hướng** (tùy chọn): `Dir=TD` (mặc định) | `Dir=LR`.
- **Bố cục chặt** (tùy chọn): `Tight=1` → giảm `nodeSpacing` / `rankSpacing` trong `%%{init}%%`.

## Việc phải làm

1. Nếu có `@file` / path: **đọc tối thiểu** (hàm, nhánh, return) — không mở rộng ngoài phạm vi luồng cần vẽ.
2. Xuất **một** khối ` ```mermaid ` … ` ``` ` đầy đủ theo §3–§5 của file hướng dẫn.
3. Tối đa **5 gạch** giải thích ánh xạ bước ↔ code (chỉ khi Owner gửi code hoặc yêu cầu).

## Việc không làm

- Không dùng `@{ shape: … }` làm mặc định (trừ khi user nói rõ và chấp nhận rủi ro viewer).
- Không viết dài dòng trước/sau khối mermaid.
