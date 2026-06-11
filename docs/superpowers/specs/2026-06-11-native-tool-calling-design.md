# Native Tool-Calling cho Structured Output (nấc 3) — Design Spec

**Ngày:** 2026-06-11
**Trạng thái:** Đã duyệt (hướng A)
**Phạm vi:** ai_python — 4 điểm JSON-trong-văn chuyển sang native tool-calling

---

## 1. Bối cảnh & mục tiêu

Hệ hiện "xin" JSON bằng prompt rồi parse văn xuôi (strip backtick, `raw[raw.find("{"):]`,
bounded reparse). Đây là nấc yếu nhất của structured output — model thường
(Qwen3.6-27B) thỉnh thoảng trả JSON hỏng, mỗi điểm gọi phải tự vá.

**Probe thực tế trên FPT Cloud (2026-06-11) — căn cứ quyết định:**

| Probe | Kết quả |
|---|---|
| `tools` + `tool_choice=auto` | ✅ trả `tool_calls`, args đúng schema (finish_reason=`tool_calls`) |
| `tool_choice` ép buộc 1 function | ✅ hoạt động — không bao giờ trả văn xuôi |
| `response_format=json_object` | ✅ hoạt động (chỉ dùng làm escape hatch, không wire) |
| `guided_json` (vLLM extra_body) | ❌ server lờ đi, trả văn thường — KHÔNG dùng được |

Phát hiện phụ từ probe: với `tool_choice=auto`, model **bịa tool_name**
(`get_monthly_revenue`) → schema phải có `enum` cho `tool_name`.

**Mục tiêu:** loại bỏ toàn bộ parse-văn-xuôi; mọi output có cấu trúc đi qua
tool-calling + pydantic validate tại biên; hành vi fallback từng điểm GIỮ NGUYÊN.

## 2. Phạm vi

**4 điểm chuyển đổi:**
1. SM decision — `session_manager.analyze()`
2. Verdict — `data_validator.execute()`
3. Sinh SQL — `sql_execute.execute()` (`{"sql": ...}`)
4. Semantic self-check — `sql_execute._semantic_check()` (`{"ok": ...}`)

**Ngoài phạm vi:** `answer_composer` (văn tự do — giữ `complete()`); đường memory
(input-side, không đổi); guided_json/json_object (không wire).

## 3. Thiết kế

### 3.1. `complete_structured()` — một method duy nhất trên LLMClient

File: `app/config/llm_client.py`

```python
class StructuredOutputError(Exception):
    """Sau 2 attempt van khong co args hop le theo output_model."""

def complete_structured(self, *, system: str, user: str,
                        output_model: type[BaseModel],
                        schema_patch: dict | None = None,
                        role: str = "default",
                        temperature: float | None = None) -> BaseModel:
```

Hành vi:
- Sinh schema: `output_model.model_json_schema()`; nếu có `schema_patch`
  (dict path→value, vd `{"properties.tool_name.enum": [...]}`) thì áp vào schema
  trước khi gửi.
- Gọi `chat.completions.create` với `tools=[{type: function, function:
  {name: "respond", description: <docstring model>, parameters: <schema>}}]`
  + **`tool_choice={"type":"function","function":{"name":"respond"}}` (ép buộc)**
  + `extra_body={"chat_template_kwargs": {"enable_thinking": False}}` (giữ như
  `complete()` hiện tại) + `max_tokens` nếu cấu hình.
- Parse: `message.tool_calls[0].function.arguments` →
  `output_model.model_validate_json(args)`.
- Retry đúng 1 lần khi: không có `tool_calls`, args không phải JSON, hoặc
  `ValidationError` — attempt 2 nối thêm `[Loi attempt truoc: <err>]` vào user.
- Hết 2 attempt → raise `StructuredOutputError(last_err)`.
- Log + think giữ phong cách hiện tại (role, elapsed, args preview ≤300 chars).

`LLMClient` Protocol thêm chữ ký `complete_structured`. `complete()` giữ nguyên
cho answer_composer.

### 3.2. Bốn output model

```python
# session_manager/__init__.py — Decision ĐÃ CÓ, giữ nguyên field + validator
# (validator is_registered giữ làm lưới 2)

# data_validator/__init__.py
class ValidatorVerdict(BaseModel):
    """Ket luan du lieu co du/dung de tra loi raw_require khong."""
    verdict: Literal["pass", "fail"]
    reason: str

# sql_execute/__init__.py
class SqlDraft(BaseModel):
    """Cau SQL SELECT read-only tra loi raw_require."""
    sql: str

class SemanticCheck(BaseModel):
    """Ket qua tu kiem tra ngu nghia JOIN cua SQL vua sinh."""
    ok: bool
    sql: str | None = None      # SQL viet lai khi ok=false
    reason: str | None = None
```

### 3.3. Enum động cho `Decision.tool_name`

Tại `analyze()`: `schema_patch={"properties.tool_name.enum":
list(DISPATCHABLE) }` (import từ registry). Model không thể sinh tool ngoài
danh sách ngay từ lúc decode. Vì `tool_name` nullable (action `finish`/
`request_clarification`), pydantic v2 sinh `anyOf: [{type: string}, {type: null}]`
— **quyết định: patch enum vào nhánh string của anyOf** (`anyOf[0].enum = [...]`).
Nếu server từ chối shape này, hạ xuống phương án dự phòng đã ghi ở mục 5:
enum phẳng + chấp nhận model điền tool_name thừa khi finish (pydantic validator
hiện có bỏ qua tool_name cho action không cần tool).

### 3.4. Call sites — trước/sau

| Điểm | Trước | Sau |
|---|---|---|
| SM | `complete()` + `_coerce_json` + vòng reparse 2 lần thủ công | `complete_structured(output_model=Decision, schema_patch=enum, role="sm")` trong try/except |
| validator | `complete()` + strip ``` + json.loads | `complete_structured(output_model=ValidatorVerdict)` |
| sinh SQL | `complete()` + `_parse_sql` | `complete_structured(output_model=SqlDraft)` |
| semantic check | `complete()` + `_coerce_json` | `complete_structured(output_model=SemanticCheck)` |

`_coerce_json` (2 bản — SM và sql_execute) và `_parse_sql` XÓA.

### 3.5. Fallback khi `StructuredOutputError` — hành vi GIỮ NGUYÊN

| Điểm | Hành vi (như hiện tại) |
|---|---|
| SM | `Decision(action="finish", reasoning=..., message="Xin loi...")` |
| validator | `{"verdict": None, "reason": "LLM output khong hop le..."}` → self_validate fail → SM retry |
| sinh SQL | `{"sql": "", ..., "error": "LLM output khong hop le: ..."}` → SM quyết |
| semantic check | fail-open: giữ SQL gốc, đi tiếp |

Bất biến an toàn không đổi: mọi SQL (kể cả bản semantic check viết lại) vẫn qua
`assert_read_only` trước executor; validator vẫn là cổng bắt buộc trước composer.

## 4. Test strategy

- **FakeLLM** (`tests/conftest.py`) thêm `complete_structured(...)`: pop từ
  `structured_queue` (list[dict] hoặc by_role dict), `model_validate(payload)`,
  ghi `structured_calls` để assert prompt/skill/schema_patch. Script dict sai
  schema → FakeLLM cũng raise ValidationError như thật (test fallback).
- **Test mới `test_llm_client.py`:** mock SDK trả `tool_calls` → parse đúng;
  args hỏng attempt 1 + đúng attempt 2 → retry hoạt động; hỏng cả 2 →
  `StructuredOutputError`; assert request có `tool_choice` ép buộc +
  `enable_thinking: False`; schema_patch áp enum đúng chỗ.
- **Migrate test 4 điểm:** script JSON-string → script dict. Hành vi assert giữ
  nguyên (kể cả các test fallback/malformed — đổi cách giả lập lỗi sang dict
  sai schema).
- **Toàn suite** (hiện 128) phải xanh; mục tiêu sau migrate: số test ≥ hiện tại.
- **Smoke test thật (manual, không vào suite):** 1 câu hỏi e2e qua API với LLM
  thật để xác nhận hành vi trên FPT Cloud — chạy trước khi commit cuối.

## 5. Rủi ro & đối sách

| Rủi ro | Đối sách |
|---|---|
| FC của Qwen/FPT là template-based, args thỉnh thoảng hỏng | Retry 1 lần + pydantic tại biên + fallback từng điểm giữ nguyên |
| Schema pydantic v2 cho field nullable sinh `anyOf` — patch enum sai chỗ | Test chốt shape schema; nếu phức tạp, đơn giản hóa: enum = DISPATCHABLE + chấp nhận model điền tool_name thừa khi finish (validator bỏ qua) |
| `enable_thinking: False` + tools tương tác lạ trên server | Probe đã chạy chính tổ hợp này — OK; smoke test thật trước commit cuối |
| Latency thay đổi | Đo qua log elapsed có sẵn; kỳ vọng tương đương (cùng 1 call) |
