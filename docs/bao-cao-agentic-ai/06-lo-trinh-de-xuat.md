# 6. Lộ trình đề xuất

Sắp theo tỉ lệ lợi ích/chi phí cho giai đoạn tiếp theo của đồ án.

## Ưu tiên 1 — Bộ eval "câu hỏi vàng" (chi phí thấp, lợi ích lớn nhất)

Chuyển quy trình từ *bug → rule* sang *bug → eval case → rule → eval xanh*:

- File khai báo ~15–20 câu hỏi đã từng lỗi + tiêu chí pass kiểm bằng máy:

```yaml
- require: "sản phẩm nào đang ế"
  sql_must_contain: ["LEFT JOIN", "COALESCE"]
  sql_must_not_contain: ["JOIN orderdetails od ON"]   # dạng INNER trần
- require: "dầu ăn nhập vào bao nhiêu"
  sql_must_match: "ILIKE '%dầu ăn%'"                  # còn dấu
  answer_must_not_contain: ["kiểm tra lại tên"]
```

- Chạy như pytest, đánh dấu `@pytest.mark.llm` (gọi LLM thật) tách khỏi
  suite nhanh; chạy trước mỗi lần sửa skill file.
- Giá trị: phát hiện hồi quy prompt — thứ mà 128 unit test hiện tại không
  thể thấy.

## Ưu tiên 2 — Entity grounding bằng code (tài liệu 5)

Bước retrieval top-k lên bảng master trước khi sinh SQL; tiêm danh sách ứng
viên vào prompt. Kèm theo: `CREATE EXTENSION pg_trgm` + GIN index cho cột
tên (cần quyền superuser một lần).

## Ưu tiên 3 — Policy cho kết quả rỗng (`rows = 0`)

Hiện `rows=0` → validator fail → hỏi lại user, trong khi "0" thường là
**câu trả lời** ("chưa có phiếu nhập nào"). Đề xuất verdict ba trạng thái:

| Verdict | Nghĩa | Hành xử của SM |
|---|---|---|
| `pass` | Dữ liệu đủ và đúng | Soạn trả lời |
| `empty` | Query hợp lệ, sự kiện = 0 | Kiểm tra chủ thể tồn tại trong master: có → trả lời "chưa có..."; không → clarify |
| `fail` | Dữ liệu không khớp yêu cầu | Retry / clarify như hiện tại |

## Ưu tiên 4 — Cài `unaccent` + nâng cấp so khớp

Chống ca user gõ tiếng Việt không dấu ("dau an nhap bao nhieu"):
`unaccent(p.name) ILIKE unaccent('%...%')`. Một lệnh `CREATE EXTENSION`,
cần superuser.

## Ưu tiên 5 — Cân nhắc nâng model cho vai trò sinh SQL

Nhiều rule trong skill file tồn tại để bù năng lực model (tài liệu 4, mục
4.2.3). Nếu ngân sách cho phép, dùng model mạnh hơn riêng cho role SQL và
đo lại bằng bộ eval (ưu tiên 1) — kỳ vọng gỡ được một phần rule và giảm
tỉ lệ self-check phải viết lại.

## Việc duy trì định kỳ

- Soát skill file mỗi khi vượt ~1.5–2k token/file: gộp rule vụn thành
  nguyên tắc tổng quát, cân few-shot theo lớp bài toán.
- Theo dõi thinking log để phát hiện hành vi lệch sớm thay vì đợi user báo.
