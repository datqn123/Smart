# 2. Bốn ca lỗi thực tế và nguyên nhân gốc

Cả 4 ca đều phát hiện khi chạy thật trên dữ liệu demo (163 sản phẩm Active,
PostgreSQL). Mỗi ca trình bày theo khung: **hiện tượng → chẩn đoán → nguyên
nhân gốc → cách sửa → bài học**.

---

## Ca 1 — Crash: `Object of type datetime is not JSON serializable`

**Hiện tượng.** Câu hỏi nối tiếp làm server crash giữa stream SSE.

**Chẩn đoán.** Postgres trả cột `created_at` kiểu `datetime`; kết quả đi vào
`state["history"]` rồi bị `json.dumps` trong session_manager. Vá lần 1 (thêm
`default=` handler tại session_manager) **thất bại**: crash di chuyển sang
data_validator — vì mọi consumer hạ nguồn (SM history, validator prompt,
composer prompt, HITL snapshot) đều dumps cùng dữ liệu đó.

**Nguyên nhân gốc.** Executor trả giá trị thô của driver DB (datetime,
Decimal, UUID, bytes) trong khi **hợp đồng ngầm** của toàn pipeline là
"kết quả query phải JSON-safe".

**Cách sửa.** Chuẩn hóa **một lần tại nguồn** — hàm `_jsonable()` trong
`app/sql/executor.py`: datetime→ISO, Decimal→float, UUID→str, bytes→hex.
Gỡ bỏ bản vá cục bộ để hành vi đồng nhất.

**Bài học.** *Sửa tại nguồn thay vì vá từng điểm tiêu thụ* — vá hạ nguồn là
whack-a-mole: diệt chỗ này mọc chỗ khác.

---

## Ca 2 — Sai dữ liệu: hỏi "sản phẩm nào đang ế" lại trả về top seller

**Hiện tượng.** Danh sách "doanh số thấp nhất" chứa sản phẩm bán chạy nhất
(636 đơn vị).

**Chẩn đoán.** SQL sinh ra dùng `INNER JOIN orderdetails ... ORDER BY
tong_ban ASC`. DB thật: 163 sản phẩm Active nhưng **chỉ 2 có đơn hàng**.
INNER JOIN loại sạch 161 sản phẩm 0 đơn — chính là hàng ế thật — nên kết quả
chỉ còn 2 dòng, và top seller "lọt" vào danh sách ế vì đứng 2/2.

**Nguyên nhân gốc.** Lỗi thuộc lớp **ngữ nghĩa vắng mặt (absence
semantics)**: đối tượng cần tìm chỉ tồn tại dưới dạng *dòng không có mặt*
trong bảng sự kiện — không INNER JOIN nào lôi ra được. Hai yếu tố cộng
hưởng: (1) toàn bộ few-shot trong skill khi đó đều dùng INNER JOIN, tạo bias
in-context; (2) **không tầng nào bắt được lỗi ngữ nghĩa**: guard chỉ kiểm
cú pháp, validator chỉ nhìn rows trả về — dòng bị join nuốt là vô hình với
validator.

**Cách sửa (2 lớp).**
1. Quy tắc + mẫu LEFT JOIN trong `schema.md` (hướng model sinh đúng từ đầu).
2. **Semantic self-check** trong code: sau khi sinh SQL, một LLM call thứ hai
   tự hỏi "câu hỏi có ngữ nghĩa vắng mặt mà SQL đang INNER JOIN không?" —
   nếu sai thì viết lại; fail-open và SQL viết lại vẫn qua guard read-only.

**Bài học.** Pipeline chỉ validate *hình thức* sẽ để lọt query *sai nghĩa
nhưng đúng cú pháp*; cần một bước phản tư (self-critique) ở đúng tầng sinh SQL.

---

## Ca 3 — Không tìm thấy dữ liệu: "dầu ăn nhập vào bao nhiêu"

**Hiện tượng.** Hệ thống xin user "kiểm tra lại tên sản phẩm" dù câu trước
nó vừa liệt kê "Dầu ăn Neptuna 1L".

**Chẩn đoán.** SQL sinh ra: `WHERE p.name ILIKE '%dau an%'` — **mất dấu**.
Kiểm chứng DB: pattern không dấu khớp 0; pattern có dấu khớp 4 sản phẩm;
extension `unaccent` chưa cài nên không có đường match chéo.

**Nguyên nhân gốc (2 tầng).**
1. *Tầng ngữ cảnh:* hệ thống ĐÃ có tên chính xác (memory lưu nguyên văn câu
   trả lời trước, SM đọc được) nhưng rule `resolved_require` của SM chỉ dạy
   viết lại với câu tham chiếu kiểu đại từ ("còn tháng trước?"); "dầu ăn"
   trông như danh từ tự đủ nghĩa nên SM bỏ qua. Trong khi đó tool chỉ nhận
   `memory_summary` — vốn là None trước lượt thứ 10 — nên sql_execute hoàn
   toàn mù ngữ cảnh và tự bịa pattern.
2. *Tầng so khớp:* model có thói quen phiên âm tiếng Việt không dấu (một
   phần do toàn bộ prompt nội bộ của hệ viết không dấu), còn DB lưu có dấu.

**Cách sửa.** (1) Rule "xác định chủ thể theo ngữ cảnh" tổng quát cho SM:
chủ thể — *bất kỳ đối tượng dữ liệu nào, không giới hạn loại* — đã xuất hiện
trong câu trả lời trước thì `resolved_require` phải dùng tên chính xác; khớp
nhiều chủ thể thì giữ đủ. (2) Rule sql_execute: ILIKE giữ nguyên dấu, lọc
qua bảng master, GROUP BY theo tên.

**Bài học.** Lỗi "không tìm thấy" nhiều khi không phải thiếu dữ liệu mà là
**đứt đường dẫn ngữ cảnh** giữa các thành phần; và quy tắc nên viết theo
khái niệm tổng quát (chủ thể) thay vì liệt kê cứng loại thực thể.

---

## Ca 4 — Lỗi trình bày: mất số thứ tự trong câu trả lời dạng danh sách

**Hiện tượng.** Danh sách đơn hàng hiển thị không đánh số `1. 2. 3.`.

**Nguyên nhân gốc.** skill.md của answer_composer không ràng buộc định dạng
danh sách; few-shot không có ví dụ nhiều dòng được đánh số → model tự chọn
format.

**Cách sửa.** Thêm constraint "rows ≥ 2 phải đánh số, không thay bằng gạch
đầu dòng" + viết lại 2 few-shot có đánh số.

**Bài học.** Với LLM, **few-shot mạnh hơn lời dặn**: muốn format nào thì
ví dụ phải trình diễn đúng format đó.

---

## Nhìn chung

| Ca | Lớp lỗi | Tầng sửa đúng |
|----|---------|----------------|
| 1 | Hợp đồng dữ liệu giữa các tầng | Code (executor — nguồn) |
| 2 | Ngữ nghĩa vắng mặt trong SQL | Code (self-check) + prompt (rule/few-shot) |
| 3 | Đứt ngữ cảnh + so khớp văn bản | Prompt (SM + sql_execute), hướng tới code (grounding) |
| 4 | Định dạng đầu ra | Prompt (few-shot) |

Điểm chung: **chẩn đoán bằng dữ liệu thật** (truy vấn đối chứng trên DB)
trước khi sửa, và mỗi lần sửa đều xác định *tầng* chịu trách nhiệm thay vì
vá tại chỗ biểu hiện lỗi.
