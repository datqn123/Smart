---
name: fixing-reported-bugs
description: Use when the user reports a bug, sai dữ liệu, câu trả lời sai, crash, or unexpected behavior in this project (especially the ai_python agentic assistant) — including urgent "sửa nhanh", "gấp", "sắp demo" requests
---

# Xử lý bug theo quy trình chuẩn

Quy trình đúc kết từ 4 ca lỗi production (xem `docs/bao-cao-agentic-ai/`).
Đây là skill **rigid**: làm đúng thứ tự, không bỏ bước, kể cả khi user nói "gấp".

**Announce at start:** "Tôi dùng skill fixing-reported-bugs để xử lý bug này theo quy trình chuẩn."

## Quy trình (bắt buộc, đúng thứ tự)

### 1. Tái hiện trên dữ liệu thật — TRƯỚC khi mở file sửa

- Lấy SQL/output **thật sự** hệ thống đã sinh: đọc think log, hoặc chạy lại
  đúng câu hỏi của user qua API. KHÔNG suy từ triệu chứng.
- Chạy query đối chứng trên DB read-only (`DATABASE_URL_RO`, che mật khẩu
  khi hiển thị) để biết kết quả đúng phải là gì.
- Sản phẩm của bước này: cặp (output sai thực tế, output đúng kỳ vọng).

### 2. Chẩn đoán tầng chịu trách nhiệm

Hệ có nhiều tầng: skill.md/schema.md (prompt) → tool code (sql_execute, guard,
executor) → dispatcher → validator → answer_composer → session_manager.
Xác định lỗi sinh ra ở tầng nào bằng bằng chứng từ bước 1, không đoán theo
"lớp bug này thường là...".

Phép thử sai tầng: nếu bản vá khiến lỗi **di chuyển** sang file/tầng khác —
đang vá sai tầng, quay lại bước này.

### 3. Tìm nguyên nhân gốc rễ — không chữa cháy

- Hỏi: "vì sao tầng này CHO PHÉP lỗi xảy ra?", không chỉ "sửa chỗ nào cho hết?".
- Tổng quát hóa: rule phải áp dụng cho cả lớp lỗi (vd: mọi "chủ thể" dữ liệu),
  không hardcode cho một entity/một câu hỏi vừa fail.

### 4. GATE: Bàn với user trước khi sửa — DỪNG TẠI ĐÂY

Trình bày cho user: hiện tượng đã tái hiện, tầng chịu trách nhiệm, nguyên nhân
gốc, phương án sửa + trade-off. **Chờ user đồng ý rồi mới sửa.**
Áp dụng cho mọi bug, kể cả sửa "một dòng" và kể cả khi sắp demo.

### 5. Sửa tại nguồn, deterministic trước LLM

- Sửa tại **nơi sản sinh dữ liệu**, không vá từng nơi tiêu thụ.
- Việc gì đảm bảo được bằng code/guard thì KHÔNG nhờ prompt. Prompt chỉ giữ
  phần thật sự cần suy luận ngôn ngữ.

### 6. Bằng chứng cho mỗi thay đổi

- Thay đổi **code**: TDD — viết test fail trước, rồi implement.
- Thay đổi **prompt** (skill.md/schema.md): kiểm chứng mẫu SQL đích chạy đúng
  trên DB thật TRƯỚC khi đưa vào rule/few-shot. Sau khi sửa, chạy lại đúng câu
  hỏi gốc và câu nghịch đảo (positive case) để chắc không phá happy path.

### 7. Chạy toàn bộ test suite trước khi commit

`cd /d/do_an_tot_nghiep/project/ai_python && python -m pytest` (Bash, POSIX
path, `PYTHONIOENCODING=utf-8`). Toàn bộ suite, không chỉ test mới.

### 8. Commit

Message theo style repo: `fix(<phạm vi>): <mô tả tiếng Việt không dấu>`.

## Bảng biện hộ — nếu bạn đang nghĩ thế này, DỪNG LẠI

| Biện hộ | Thực tế |
|---|---|
| "Sắp demo, skip ceremony, vào sửa prompt luôn" | Quy trình đầy đủ mất ~15 phút. Vá sai tầng rồi gỡ lại tốn hơn nhiều — và demo chết vì fix chưa kiểm chứng. |
| "Lớp bug này hầu như chắc chắn là prompt gap" | "Hầu như chắc" không phải bằng chứng. Các ca production từng bị đoán sai tầng. Tái hiện trước (bước 1). |
| "Log không thấy thì suy từ triệu chứng cũng được" | Suy từ triệu chứng = chữa cháy. Chạy lại câu hỏi để lấy SQL thật — chỉ mất 1 phút. |
| "Sửa nhỏ thôi, không cần bàn với user" | User yêu cầu gate này tường minh. Nhỏ hay lớn đều trình bày trước (bước 4). |
| "Chạy suite sau demo rồi backfill test" | Suite chạy vài chục giây. Commit không qua suite là nợ kỹ thuật tức thì. |
| "Thêm few-shot này chắc đúng, khỏi chạy thử SQL" | Few-shot sai trên DB thật sẽ dạy model sai có hệ thống. Kiểm chứng trước (bước 6). |
| "User đã chỉ sẵn file lỗi rồi, sửa file đó luôn" | File user chỉ là GIẢ THUYẾT, không phải chẩn đoán. Vẫn tái hiện (bước 1) và xác định tầng (bước 2) bằng bằng chứng. |

## Red flags — dấu hiệu đang làm sai

- Mở skill.md/schema.md để sửa khi CHƯA thấy SQL/output thật hệ thống sinh ra.
- Bắt đầu edit file khi user chưa đồng ý phương án (chưa qua gate bước 4).
- Bản vá làm lỗi xuất hiện ở file khác → sai tầng, quay lại bước 2.
- Rule/few-shot mới chứa SQL chưa từng chạy trên DB thật.
- Định commit mà chưa chạy toàn bộ suite.
