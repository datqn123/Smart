# 5. Entity grounding và bài toán quy mô: bảng master hàng triệu bản ghi thì sao?

## 5.1. Grounding là gì và vì sao cần

**Entity grounding** = trước khi sinh SQL, xác định *chính xác* các bản ghi
master mà user đang nhắc tới ("dầu ăn" → `Dầu ăn Neptuna 1L`, `Dầu ăn Simply
1L`, ...) rồi đưa danh sách đó vào prompt. Model khi ấy **chép** tên có sẵn
thay vì **đoán** tên — loại bỏ cả lớp lỗi mất dấu/sai chính tả/bịa tên.

```
câu hỏi ──> [retrieval] tìm ứng viên trong bảng master ──> top-k ứng viên
                                                                │
            SQL chính xác  <── [LLM sinh SQL + danh sách ứng viên trong prompt]
```

## 5.2. Trả lời thẳng câu hỏi quy mô

**Hiểu nhầm cần gỡ: grounding KHÔNG phải "tải bảng vào prompt".** Nó là một
truy vấn **có lọc + có chặn trên (top-k)**:

```sql
SELECT id, name FROM products
WHERE name ILIKE '%dầu ăn%'
ORDER BY <độ liên quan> LIMIT 20;
```

Hai đại lượng cần tách bạch:

| Đại lượng | Phụ thuộc kích thước bảng? | Giải pháp |
|---|---|---|
| **Kích thước prompt** | **KHÔNG** — luôn ≤ k ứng viên (k ≈ 10–20, vài trăm token) | LIMIT k cố định |
| **Thời gian tìm ứng viên** | CÓ — `ILIKE '%...%'` trên bảng triệu dòng = full scan (giây) | Đánh index chuyên dụng (dưới) |

Tức là với 10 triệu sản phẩm, prompt vẫn chỉ nhận tối đa 20 dòng; vấn đề
duy nhất là làm sao *tìm* 20 dòng đó nhanh — và đây là bài toán search kinh
điển đã có lời giải theo từng nấc.

## 5.3. Thang giải pháp theo quy mô

### Nấc 1 — Trigram index (đến ~chục triệu dòng, ngay trong Postgres)

```sql
CREATE EXTENSION pg_trgm;
CREATE INDEX idx_products_name_trgm ON products USING gin (name gin_trgm_ops);
```

`ILIKE '%dầu ăn%'` từ full-scan (hàng giây) xuống index-scan (mili-giây).
`pg_trgm` còn cho **similarity search** (`name % 'dau an neptuna'`) — chịu
được sai chính tả nhẹ. Kết hợp `unaccent` thì chịu được cả gõ không dấu.
Đây là nấc đủ dùng cho tuyệt đại đa số hệ ERP thực tế.

### Nấc 2 — Full-text search (khớp theo từ, có xếp hạng)

`tsvector` + GIN index: khớp theo từ/từ gốc thay vì chuỗi con, có
`ts_rank` để xếp hạng ứng viên trước khi cắt top-k. Phù hợp khi tên dài,
nhiều từ, cần "khớp 2/3 từ cũng được".

### Nấc 3 — Search engine chuyên dụng (Elasticsearch/Meilisearch/Typesense)

Khi cần: chịu lỗi chính tả mạnh, đồng nghĩa, gợi ý khi-đang-gõ, hàng trăm
triệu bản ghi, hoặc tách tải khỏi DB giao dịch. Mô hình: sync bảng master
sang search engine; retrieval hỏi engine, SQL vẫn chạy trên Postgres bằng
`id IN (...)` lấy từ kết quả retrieval.

### Nấc 4 — Vector/embedding search (khớp NGỮ NGHĨA)

Khi user gọi bằng khái niệm chứ không phải tên: "nước ngọt có ga" → Coca,
Pepsi (tên không chứa chữ nào của câu hỏi). Embed tên sản phẩm vào pgvector
/ FAISS, tìm k-NN theo vector câu hỏi. Đây chính là kiến trúc **RAG**
(Retrieval-Augmented Generation) — và là điểm mấu chốt để báo cáo: *grounding
top-k chính là RAG thu nhỏ; các hệ LLM lớn KHÔNG BAO GIỜ đưa cả kho dữ liệu
vào prompt, họ đưa kết quả retrieval đã chặn trên.*

## 5.4. Xử lý các tình huống biên (mọi nấc đều cần)

| Tình huống | Hành xử đúng |
|---|---|
| 0 ứng viên khớp chính xác | Hạ dần độ chặt: bỏ dấu → similarity → vẫn 0 thì **mới** hỏi lại user ("không tìm thấy X, ý bạn là...?") |
| Quá nhiều ứng viên (> k) | Lấy top-k theo độ liên quan + nói rõ trong câu trả lời "hiển thị 20/1.234 kết quả khớp"; hoặc hỏi user thu hẹp |
| 1–k ứng viên | Trường hợp đẹp: tiêm cả danh sách, SQL `IN (...)` hoặc GROUP BY theo tên |

Lưu ý ráp với ca lỗi số 3 (tài liệu 2): khi user hỏi nối tiếp về chủ thể đã
xuất hiện trong câu trả lời trước, **ngữ cảnh hội thoại là nguồn grounding
rẻ nhất** (0 query) — SM viết lại câu hỏi với tên chính xác. Retrieval lên
bảng master chỉ cần thiết khi ngữ cảnh không có sẵn.

## 5.5. Chi phí tổng thể của grounding cho đồ án

- +1 query SELECT có index: **mili-giây**, không đáng kể so với 1 LLM call
  (hàng giây).
- +vài trăm token prompt (k = 10–20 ứng viên).
- Đổi lại: xóa lớp lỗi mất dấu/bịa tên ở gốc, giảm phụ thuộc vào rule
  "dặn dò" trong skill file — đúng tinh thần "kiến trúc trước, prompt sau"
  (tài liệu 4).
