# 4. "Mỗi lần bug lại mở rộng skill file" — có phải cách làm chuẩn?

Câu hỏi đặt ra trong quá trình phát triển: *cứ gặp bug là thêm rule/few-shot
vào skill.md — cách này có bền không, và Anthropic (Claude) hay OpenAI
(Codex) có làm vậy không?*

## 4.1. Họ cũng vá prompt — nhiều là đằng khác

- System prompt của các sản phẩm như Claude Code, Cursor, GitHub Copilot
  chứa hàng chục quy tắc hành vi cụ thể ("KHÔNG được làm X khi Y") — phần
  lớn là "vết sẹo" của lỗi thực tế, đúng như cách skill.md của đồ án tích
  lũy rule qua từng bug. Anthropic công bố system prompt công khai nên điều
  này kiểm chứng được.
- Cơ chế **Agent Skills** của Anthropic (2025) chuẩn hóa đúng mô hình này:
  tri thức tác vụ đặt trong file `SKILL.md` (hướng dẫn + ví dụ), nạp theo
  nhu cầu. Kiến trúc skill.md/schema.md đọc-lại-mỗi-lần-gọi của đồ án tương
  đồng về tư tưởng.

**Kết luận trung thực: hướng đi không sai.** Nhưng các lab lớn có 3 lớp đỡ
khiến việc tích lũy rule bền vững — và đây là khoảng cách thật sự.

## 4.2. Ba lớp đỡ của công nghiệp

### (1) Eval suite — mỗi bug kết thúc bằng một test case, không phải một rule

Quy trình chuẩn: bug → thêm ca vào **bộ eval hồi quy** (câu hỏi → tiêu chí
pass kiểm được bằng máy) → sửa prompt/code → chạy lại toàn bộ eval. Nhờ đó:

- biết rule mới có phá hành vi cũ không (prompt thay đổi là thay đổi
  *toàn cục*, không như sửa một hàm);
- đo được rule nào thực sự có tác dụng để cắt tỉa định kỳ.

Thiếu eval, việc mở rộng skill file đúng nghĩa là whack-a-mole có rủi ro
hồi quy âm thầm. Đây là hạng mục đề xuất ưu tiên 1 của đồ án (tài liệu 6).

### (2) Kiến trúc trước, prompt sau

Quy tắc ngầm: *cái gì làm được bằng code deterministic thì không nhờ LLM
nhớ*. Ví dụ trong công nghiệp: structured outputs/constrained decoding thay
cho "hãy trả đúng JSON"; hệ text-to-SQL nghiêm túc **ground thực thể bằng
truy vấn DB** (lấy tên chính xác đưa vào prompt) thay vì dặn "giữ nguyên
dấu". Đồ án đã đi đúng hướng này ở `_jsonable()`, guard SQL, semantic
self-check; bước tiếp theo là entity grounding bằng code (tài liệu 5).

### (3) Đẩy lỗi lặp lại vào model

Lab lớn sở hữu model: lớp lỗi tái diễn được đưa vào dữ liệu huấn luyện /
RLHF, nên system prompt của họ không phình vô hạn — model thế hệ sau "nuốt"
bớt rule. Đồ án dùng Qwen cố định, không fine-tune → **một phần đáng kể
rule trong skill.md tồn tại để bù năng lực model**. Hệ quả thực tiễn: nâng
model cho vai trò sinh SQL là đòn bẩy lớn nhất nếu chất lượng còn là vấn đề,
và có thể gỡ được nhiều rule sau khi nâng.

## 4.3. Khi nào prompt "quá tải" và thuốc của họ

Dấu hiệu cần để ý khi skill file phình:

1. Model bỏ sót rule nằm giữa file (hiệu ứng *lost-in-the-middle*).
2. Hai rule mâu thuẫn nhau ở ngữ cảnh hẹp.
3. **Few-shot cũ kéo hành vi ngược rule mới** — đồ án đã gặp đúng ca này:
   6 few-shot đều INNER JOIN tạo bias khiến rule chữ nghĩa không đủ sức kéo
   lại (ca "sản phẩm ế").

Thuốc tương ứng: gộp rule vụn thành **nguyên tắc tổng quát** (đồ án đã làm
với rule "xác định chủ thể theo ngữ cảnh" — viết theo khái niệm chủ thể,
không liệt kê cứng sản phẩm/khách/đơn); cân bằng few-shot theo lớp bài
toán; theo dõi ngân sách token (skill + schema của sql_execute hiện ~vài
nghìn token — còn xa vùng nguy hiểm).

## 4.4. Bảng đối chiếu

| Tiêu chí | Lab lớn | Đồ án hiện tại |
|---|---|---|
| Rule/few-shot trong file prompt | Có, quy mô lớn | Có (skill.md, schema.md, hot-reload) |
| Eval hồi quy cho prompt | Bắt buộc | **Chưa có** — đề xuất ưu tiên 1 |
| Guardrail deterministic | Mặc định | Có (guard SQL, RO transaction, jsonable, self-check) |
| Grounding thực thể bằng DB | Phổ biến trong text-to-SQL | Mới ở mức rule prompt; kế hoạch chuyển sang code |
| Đẩy lỗi vào model (fine-tune/RLHF) | Có | Không khả thi — bù bằng rule + chọn model |
| Observability/trace | Chuẩn hóa | Thinking log (`think` logger) |
