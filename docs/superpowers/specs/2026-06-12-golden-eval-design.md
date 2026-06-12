# Golden Set Eval (tầng rẻ) — Design Spec

**Ngày:** 2026-06-12
**Trạng thái:** đã duyệt thiết kế với user (tầng rẻ, mức B, phương án pytest thuần)
**Vị trí trong lộ trình:** điểm yếu #2 (eval & đo lường) trong three-weakness-roadmap;
làm sau khi structured output nấc 3 hoàn thành (2026-06-11, suite 142 pass).

---

## 1. Bối cảnh & mục tiêu

Quy trình hiện tại là *bug → thêm rule/few-shot vào skill.md*. Sửa prompt là thay
đổi **toàn cục**: rule mới có thể âm thầm phá hành vi cũ, và 142 unit test hiện
tại không phát hiện được vì chúng dùng FakeLLM. Bằng chứng thực tế: 6 few-shot
INNER JOIN từng kéo model đi ngược rule LEFT JOIN (ca "sản phẩm ế").

**Mục tiêu:** bộ eval hồi quy "câu hỏi vàng" chạy với **LLM thật**, kiểm được
bằng máy, chạy trước mỗi lần sửa skill.md/schema.md. Biến quy trình thành:
*bug → eval case vĩnh viễn → sửa prompt → eval xanh → commit*.

## 2. Phạm vi vòng này (đã chốt với user)

- **Tầng rẻ**: dừng ngay sau khi có chuỗi SQL — không chạy DB, không validator,
  không composer. (Tầng đắt — full pipeline + assert answer — làm vòng sau.)
- **Mức B**: đo từ **Session Manager trở đi**, không nhảy cóc. Mỗi case có thể
  kèm lịch sử hội thoại giả lập để kiểm rule "xác định chủ thể theo ngữ cảnh"
  (ca "dầu ăn" — lỗi nằm ở SM, không phải sql_execute).
- **Phương án 1 — pytest thuần**: golden set là YAML, runner là một file test
  parametrize, marker `llm`. Không CLI riêng, không report file (nâng cấp sau
  nếu cần so sánh model).

**Ngoài scope (ghi nhận, làm sau):**
- Tầng đắt (run_session full + DB thật + assert câu trả lời cuối).
- Bộ đếm think-log (tỉ lệ SQL đúng lần đầu, tỉ lệ self-check viết lại, latency).
- Report JSON + script so sánh 2 model (phương án 3).
- Ca lỗi #4 (đánh số danh sách) thuộc composer — chờ tầng đắt.

## 3. Kiến trúc

### 3.1. Cấu trúc file

```
ai_python/tests/eval/
  golden.yaml          # DỮ LIỆU: ~25 câu hỏi + barem chấm bằng máy
  conftest.py          # fixture: LLM thật từ env + FakeExecutor
  test_golden_sql.py   # runner: đọc YAML, parametrize mỗi case thành 1 test
```

Tư tưởng như skill.md: tri thức nằm trong file dữ liệu, code chỉ là máy chạy.
Thêm case mới = thêm YAML, không sửa Python.

### 3.2. Schema một case trong golden.yaml

```yaml
- id: products-e-left-join          # tên case, hiện trong pytest -v
  tags: [absence, products]          # [lớp-lỗi, nghiệp-vụ] — soi ma trận coverage
  history: []                        # lượt chat trước (giả lập); rỗng = câu độc lập
  require: "sản phẩm nào đang ế"     # đề bài
  expect:                            # barem — mọi trường đều optional
    sm_tool: sql_execute             # SM phải chọn tool này
    sm_require_contains: []          # substring phải có trong require SM gửi tool
    sql_contains: ["LEFT JOIN", "COALESCE"]
    sql_not_contains: ["JOIN orderdetails od ON"]
    sql_regex: null                  # regex tùy chọn cho pattern phức tạp
```

Case clarify chỉ có `sm_tool: request_clarification` — không có phần SQL.
Format `history` (`[{user, answer}]`) trùng đúng shape `memory_context["turns"]`
mà `analyze()` nhận (xem `app/memory`), nên runner đưa thẳng vào không cần map.

### 3.3. Runner — chạy gì, dừng ở đâu

```
YAML history ──> memory_context giả ──> analyze() SM THẬT        (1 LLM call)
                                            │ assert sm_tool, sm_require_contains
                                            ▼ (nếu sm_tool == sql_execute)
                          sql_execute.execute() THẬT, executor=FakeExecutor
                          (SqlDraft + SemanticCheck = 2 LLM call)
                                            │
                  FakeExecutor.run(sql) GHI LẠI sql, trả rows giả
                                            │ assert sql_contains/not_contains/regex
                                            ▼ DỪNG
```

- SQL được chấm là SQL **sau semantic self-check và sau `assert_read_only`** —
  đúng chuỗi sẽ chạm DB trong production.
- Runner dựng `ToolState` cho sql_execute theo cùng cách dispatcher làm
  (require lấy từ args của decision SM).
- ~3 LLM call/case × 25 case ≈ 75 call, chạy tuần tự ~5–8 phút.

### 3.4. FakeExecutor

Vật thế thân cho tầng I/O cuối, ~10 dòng, đặt trong `tests/eval/conftest.py`:

```python
class FakeExecutor:
    def __init__(self):
        self.captured_sql: str | None = None

    def run(self, sql, *, row_limit=100):
        self.captured_sql = sql
        return {"columns": ["name", "total"],
                "rows": [{"name": "X", "total": 1}], "row_count": 1}
```

Cùng kỹ thuật dependency-injection mà 142 unit test dùng với FakeLLM — chỉ đảo
chiều: LLM thật, DB giả. **Không sửa dòng code production nào.**

### 3.5. conftest.py của tests/eval

- Fixture `real_llm`: dựng `OpenAILLMClient` từ env (`LLM_API_KEY`,
  `LLM_BASE_URL`, `LLM_MODEL`). Thiếu key → `pytest.skip` toàn bộ với message
  rõ ràng, không fail.
- Đổi model (DeepSeek qua OpenRouter, Ollama local...) = đổi 3 biến env, chạy
  lại cùng lệnh — điều kiện: endpoint hỗ trợ native tool-calling
  (`tool_choice` ép buộc); nếu không, lỗi phải hiện rõ ở case đầu tiên.

## 4. Tích hợp pytest

`pytest.ini` thêm:

```ini
markers =
    llm: goi LLM that — golden set, can LLM_API_KEY
addopts = -q -m "not llm"
```

| Lệnh | Hành vi |
|---|---|
| `pytest` | suite thường (142 test), tự loại golden set, nhanh như cũ |
| `pytest -m llm -v` | chạy golden set (CLI `-m` đè addopts) |
| `pytest -m llm -k dau-an` | chạy 1 case lẻ khi debug |

## 5. Bộ case khởi đầu (~25 câu) — ma trận lớp lỗi × nghiệp vụ

| Lớp lỗi \ Nghiệp vụ | Bán hàng/Đơn | Nhập kho | Sản phẩm | Khách hàng |
|---|---|---|---|---|
| **Absence** (LEFT JOIN) | khách chưa mua tháng này | kho chưa nhập | **sp ế** ★, sp chưa ai mua | khách chưa quay lại |
| **Diacritics/so khớp** | | **dầu ăn** ★ | tìm theo tên có dấu | tên khách có dấu |
| **Chủ thể ngữ cảnh** (history) | follow-up "còn tháng trước?" | **dầu ăn follow-up** ★ | follow-up sp vừa liệt kê | |
| **Aggregate** | doanh thu theo tháng, top-N khách | tổng nhập theo NCC | top bán chạy | |
| **Clarify** (SM hỏi lại) | "cái đó bao nhiêu" | | "xem chi tiết" | |

★ = case vĩnh viễn từ bug production. Ca datetime (bug code) đã có unit test
riêng, không vào golden set.

**Nguyên tắc soạn case:** danh sách câu cụ thể + barem từng câu chốt ở bước
plan; mỗi SQL kỳ vọng phải được **kiểm chứng chạy đúng trên DB thật** trước khi
đưa barem vào YAML (đúng nguyên tắc 4 — mỗi thay đổi đi kèm bằng chứng).

**Bản chất golden set:** lưới chặn hồi quy, không phải chứng minh đúng tuyệt
đối. 25 câu là điểm khởi đầu phủ mỗi ô quan trọng 1–2 câu; bộ lớn dần theo
luật *mỗi bug mới = một case vĩnh viễn mới*. Tags cho phép soi ô nào còn trống.

## 6. Luật sắt & quy trình vận hành

- **Luật sắt** (ghi vào AGENTS.md): không commit thay đổi `skill.md`/`schema.md`
  nếu `pytest -m llm` chưa xanh.
- Vòng đời: sửa prompt → `pytest -m llm` (~5–8 phút) → xanh hết mới commit;
  có case đỏ nghĩa là rule mới phá hành vi cũ.
- Gặp bug production mới: thêm case YAML trước, sửa prompt sau, eval xanh
  rồi mới đóng bug.

## 7. Tiêu chí nghiệm thu

1. `pytest` (suite thường) không chậm đi, không gọi LLM thật — 142 test pass.
2. `pytest -m llm -v` chạy đủ ~25 case với LLM thật (Qwen3.6-27B/FPT) và pass
   toàn bộ tại thời điểm commit (baseline xanh).
3. Thiếu `LLM_API_KEY` → skip sạch với message, không fail.
4. 3 case ★ (sản phẩm ế, dầu ăn độc lập, dầu ăn follow-up) tái hiện đúng
   barem của bug gốc.
5. Luật sắt được ghi vào AGENTS.md.
