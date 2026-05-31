# Kế hoạch: Hệ thống Quy tắc Tự tiến hóa (Self-Evolving Rules System)

## 1. Mục tiêu
Tự động hóa việc thu thập kiến thức từ các lần sửa bug của Agent để cập nhật vào bộ quy tắc dự án, nhằm ngăn chặn lỗi lặp lại và nâng cao chất lượng code một cách bền vững.

## 2. Các thành phần chính

### A. Tệp lưu trữ kiến thức: `RULES_BUG_FIX.md`
Đây là nơi lưu trữ các bài học kinh nghiệm.
- **Cấu trúc mỗi entry:**
  - **ID:** `BF-XXX` (Bug Fix)
  - **Symptom:** Mô tả hiện tượng lỗi.
  - **Root Cause:** Nguyên nhân gốc rễ (Kỹ thuật/Quy trình).
  - **Prevention Rule:** Quy tắc mới để tránh lỗi này.
  - **Example:** Code mẫu (Bad vs. Good).

### B. Bộ lọc chất lượng (The Learning Filter)
Để tránh làm "loãng" bộ quy tắc, Agent chỉ cập nhật khi bug đáp ứng:
- **Tính lặp lại:** Có khả năng xảy ra ở các module khác.
- **Tính đặc thù:** Liên quan đến Tech Stack (Tailwind v4, TanStack Query v5, Shadcn).
- **Tính nghiêm trọng:** Lỗi logic nghiệp vụ hoặc lỗ hổng bảo mật.

## 3. Quy trình thực hiện (Workflow)

### Bước 1: Thu thập (Agent DEVELOPER)
- Sau khi fix bug thành công, Agent DEV phải điền mục **RCA (Root Cause Analysis)** vào file Task tương ứng (ví dụ `TASKS/TaskXXX.md`).
- Nội dung bao gồm: *Lỗi gì? Tại sao? Làm sao để không bị lại?*

### Bước 2: Sàng lọc & Cập nhật (Agent DOC_SYNC)
- Agent DOC_SYNC sẽ chạy định kỳ hoặc sau mỗi PR.
- Nhiệm vụ: Đọc các mục RCA trong các Task đã `Completed`.
- Đánh giá dựa trên **Bộ lọc chất lượng**.
- Nếu đạt, tự động format và chèn vào `RULES_BUG_FIX.md`.
- Nếu bug cực kỳ quan trọng (Blocker), đề xuất cập nhật vào `RULES.md`.

### Bước 3: Áp dụng (Tất cả Agent)
- Cập nhật `RULES.md` để ép buộc mọi Agent mới khi bắt đầu làm việc phải đọc cả `RULES.md` và `RULES_BUG_FIX.md`.

## 4. Danh sách công việc (Todo List)

1. [ ] Khởi tạo file `RULES_BUG_FIX.md` với template chuẩn.
2. [ ] Cập nhật `AGENTS/DEVELOPER_AGENT_INSTRUCTIONS.md`: Thêm yêu cầu viết RCA sau khi fix bug.
3. [ ] Cập nhật `AGENTS/DOC_SYNC_AGENT_INSTRUCTIONS.md`: Thêm logic "Knowledge Harvesting" (Thu hoạch kiến thức).
4. [ ] Cập nhật `RULES.md`: Thêm mục "Compliance with Bug-Fix Rules".
5. [ ] Thực hiện một "Test Run" với một bug giả định để kiểm tra quy trình.
