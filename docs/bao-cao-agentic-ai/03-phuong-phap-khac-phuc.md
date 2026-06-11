# 3. Phương pháp khắc phục: phân tầng trách nhiệm code — prompt

## Nguyên tắc 1: Sửa tại nguồn (fix-at-source)

Khi một lỗi có thể xuất hiện ở nhiều điểm tiêu thụ, sửa tại **nơi sản sinh
dữ liệu** thay vì vá từng nơi dùng. Ca datetime (tài liệu 2, ca 1) là minh
họa: 1 hàm `_jsonable()` tại executor thay cho 4+ bản vá `json.dumps(...,
default=...)` rải rác. Tiêu chí nhận biết: nếu bản vá thứ nhất khiến lỗi
"di chuyển" sang file khác — đang vá sai tầng.

## Nguyên tắc 2: Việc gì deterministic được thì không nhờ LLM

Phân công trách nhiệm trong hệ:

| Loại đảm bảo | Cơ chế | Vì sao không dùng prompt |
|---|---|---|
| Chỉ cho phép SELECT | Guard sqlparse + transaction READ ONLY + role DB | An toàn không được phép xác suất |
| Kết quả JSON-safe | `_jsonable()` trong executor | Quy tắc cố định, không cần "suy luận" |
| Validator phải chạy trước composer | Dispatcher chặn cứng | Ràng buộc thứ tự là logic chương trình |
| Bound retry / bound parse | Vòng lặp đếm trong orchestrator | LLM không tự đếm tin cậy được |

Prompt (skill.md) chỉ giữ phần **thật sự cần suy luận ngôn ngữ**: hiểu ý
định, chọn bảng/join, soạn văn.

## Nguyên tắc 3: Self-check ở tầng sinh — bắt lỗi mà validator không thể thấy

Validator chỉ nhìn *kết quả trả về*; những dòng bị query loại nhầm là vô
hình với nó. Vì vậy lớp lỗi "ngữ nghĩa vắng mặt" được chặn bằng một LLM call
phản tư ngay sau khi sinh SQL, trước khi thực thi:

```
sinh SQL ──> semantic self-check ──> guard read-only ──> executor
                  │ phát hiện sai: viết lại LEFT JOIN
                  │ check lỗi: fail-open, giữ SQL gốc
```

Thiết kế đáng chú ý: **fail-open** (bước kiểm tra không bao giờ làm hỏng
happy path) và **mọi SQL — kể cả bản viết lại — vẫn đi qua guard** (self-check
không phải là cửa hậu an toàn). Đánh đổi: +1 LLM call/câu hỏi.

## Nguyên tắc 4: Mỗi thay đổi prompt đi kèm bằng chứng

Quy trình áp dụng cho cả 4 ca lỗi:

1. **Tái hiện** trên dữ liệu thật (query đối chứng vào DB read-only).
2. Với thay đổi code: **viết test fail trước** (TDD), rồi implement
   (ví dụ: `test_executor_returns_json_safe_values`,
   4 test cho semantic self-check).
3. Với thay đổi prompt: kiểm chứng mẫu SQL đích chạy đúng trên DB thật
   trước khi đưa vào few-shot.
4. Chạy lại toàn bộ suite (hiện 128 tests) trước khi commit.

## Nguyên tắc 5: Quan sát được (observability) trước khi tối ưu

Logger `think` tường thuật pipeline như dòng suy nghĩ:

```
think [SM] nhan yeu cau moi: "san pham nao dang e" — bat dau phan tich...
think [SM] suy nghi: can truy van DB de biet san pham ban cham
think [SM] -> quyet dinh: goi tool sql_execute
think [sql_execute] SQL nhap: SELECT ... JOIN orderdetails ...
think [sql_execute] tu kiem tra lai SQL vua sinh: ... INNER JOIN khong?
think [sql_execute] -> phat hien SQL sai ngu nghia: ... Viet lai: LEFT JOIN
```

Giá trị: (1) chẩn đoán lỗi production nhanh — cả 4 ca lỗi đều được truy từ
log; (2) minh bạch hành vi agent khi demo; (3) là tiền đề cho bước eval
tự động (so khớp trace với kỳ vọng).
