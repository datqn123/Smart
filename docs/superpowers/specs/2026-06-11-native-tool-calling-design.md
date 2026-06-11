# Native Tool-Calling (nấc 3) — Design Spec v2

**Ngày:** 2026-06-11
**Trạng thái:** v2 — kiến trúc đích, KHÔNG bước đệm (thay thế v1 "respond giả")
**Nguyên tắc do user chốt:** không để sót hệ cũ — mọi vết tích JSON-trong-văn bị xóa, có tiêu chí nghiệm thu grep-zero.

---

## 1. Bối cảnh & căn cứ probe

Hệ hiện "xin" JSON bằng prompt rồi parse văn xuôi tại **5 điểm** (không phải 4 —
grep phát hiện answer_composer cũng parse JSON). Bài học quá khứ user nêu:
đập LangGraph sang v2 nhưng giữ code cũ → trì trệ. Vòng này đi thẳng kiến trúc
đích: **registry là nguồn chân lý duy nhất cho tool**, SM chọn hành động bằng
native tool-calling thật.

**Probe FPT Cloud / Qwen3.6-27B (2026-06-11):**

| Probe | Kết quả |
|---|---|
| 1 function + `tool_choice` ép buộc | ✅ luôn trả `tool_calls`, args đúng schema |
| 5 tool thật + `tool_choice="required"` | ✅ chọn đúng tool theo ngữ cảnh (đầu phiên→sql_execute, sau sql→data_validator, câu mơ hồ→request_clarification), kèm reasoning |
| `response_format=json_object` | ✅ (escape hatch, không wire) |
| `guided_json` (vLLM) | ❌ server lờ — loại |
| `tool_choice=auto` | ✅ nhưng không dùng cho SM (required chắc hơn) |

Phát hiện từ probe: với `auto` + schema không enum, model có thể bịa tool_name
→ SM dùng `required` + danh sách tools là toàn bộ ràng buộc.

## 2. Kiến trúc đích

### 2.1. Registry — nguồn chân lý duy nhất (`app/registry/registry.py`)

```python
@dataclass(frozen=True)
class ToolSpec:
    description: str                 # mô tả cho LLM (nguồn duy nhất, bỏ catalog text)
    args_model: type[BaseModel]      # schema args LLM phải điền
    kind: str                        # "dispatch" (có subgraph) | "control" (SM-level)

REGISTRY: dict[str, ToolSpec] = {
    "sql_execute":           ToolSpec(..., SqlExecuteArgs,  kind="dispatch"),
    "data_validator":        ToolSpec(..., ValidatorArgs,   kind="dispatch"),
    "answer_composer":       ToolSpec(..., ComposerArgs,    kind="dispatch"),
    "finish":                ToolSpec(..., FinishArgs,      kind="control"),
    "request_clarification": ToolSpec(..., ClarifyArgs,     kind="control"),
}

def render_api_tools() -> list[dict]:   # OpenAI tools format từ REGISTRY
def get_args_model(name) -> type[BaseModel]
def is_dispatchable(name) -> bool
```

Args models (đặt tại `registry/args.py` để tránh import vòng):

```python
class CommonArgs(BaseModel):
    reasoning: str                          # vì sao chọn bước này
    resolved_require: str | None = None     # câu hỏi nối tiếp đã viết lại (memory)

class SqlExecuteArgs(CommonArgs):
    require: str                            # yêu cầu dữ liệu đã làm rõ

class ValidatorArgs(CommonArgs): ...
class ComposerArgs(CommonArgs): ...

class FinishArgs(CommonArgs):
    message: str

class ClarifyArgs(CommonArgs):
    message: str
```

Registry quản lý cả ba: danh sách tool, schema args cho LLM, mapping dispatch.
`render_tool_catalog()` (bảng text trong prompt) **XÓA** — mô tả tool chỉ còn
một nguồn trong `tools=[...]`.

### 2.2. SM decision = tool_call thật (`tools/session_manager/__init__.py`)

- Gọi LLM với `tools=render_api_tools()`, **`tool_choice="required"`**,
  `temperature` role "sm", `enable_thinking: False`.
- Đọc `tool_calls[0]`: `name` + `arguments` → validate bằng
  `get_args_model(name).model_validate_json(args)`.
- Map sang `Decision` — **Decision đổi vai: từ format output LLM thành ngôn ngữ
  nội bộ của orchestrator** (giữ orchestrator/dispatcher/HITL/SSE nguyên vẹn vì
  budget/retry-cap/validator-gate là luật harness, không phải legacy):
  - tool dispatch + chưa từng fail → `call_tool`
  - tool dispatch lặp lại sau kết quả invalid → `retry_tool` (derive, không
    còn là lựa chọn của model)
  - `finish` / `request_clarification` → action tương ứng, message từ args
  - action `replan` chết — model tự đổi hướng bằng cách gọi tool khác
- Retry 1 lần khi: không có tool_calls / args không parse được / ValidationError
  (nối `[Loi attempt truoc: <err>]` vào user message). Hết 2 attempt →
  Decision finish an toàn (hành vi fallback như hiện tại).
- `skill.md` của SM viết lại: bỏ "## Output schema (CHỈ trả JSON này...)",
  thay bằng luật chọn tool (thứ tự bắt buộc, khi nào clarify, cách điền
  resolved_require). Phần nhận diện chủ thể/ngữ cảnh GIỮ NGUYÊN.

### 2.3. Bốn điểm extraction dùng `complete_structured()` (`config/llm_client.py`)

Forced-function extraction là kiến trúc cuối cho bài "trích xuất có cấu trúc"
(khác bài "chọn hành động" của SM) — không phải bước đệm. Một method:

```python
def complete_structured(self, *, system, user, output_model: type[BaseModel],
                        role="default", temperature=None) -> BaseModel:
    # tools=[function "respond" từ output_model.model_json_schema()]
    # tool_choice ép buộc; parse arguments → model_validate_json
    # retry 1 lần; hết → raise StructuredOutputError
```

| Điểm | Output model | Fallback khi StructuredOutputError (GIỮ hành vi hiện tại) |
|---|---|---|
| sql_execute sinh SQL | `SqlDraft{sql: str}` | trả `error` → SM quyết |
| sql_execute semantic check | `SemanticCheck{ok, sql?, reason?}` | fail-open, giữ SQL gốc |
| data_validator verdict | `ValidatorVerdict{verdict: Literal["pass","fail"], reason}` | `verdict=None` → self_validate fail → SM retry |
| answer_composer | `ComposerAnswer{answer: str}` | trả `error` → SM quyết (như hành vi malformed hiện tại) |

`complete()` (text tự do) chỉ còn MỘT người dùng hợp pháp: memory compact
(rolling summary). Mọi chỗ khác gọi `complete()` là vi phạm.

SM dùng `complete_tool_select(...)` (method riêng nhận `tools` list +
`tool_choice="required"`, trả `(name, args_json)`) — cùng lớp llm_client,
dùng chung code parse tool_calls với `complete_structured`.

### 2.4. Bất biến an toàn — không đổi

- Mọi SQL (kể cả semantic check viết lại) qua `assert_read_only` trước executor.
- Validator vẫn là cổng bắt buộc trước composer (dispatcher chặn cứng).
- Budget `harness_max_steps`, retry cap, HITL pause/resume, SSE contract
  (nested "harness"), memory đường input — nguyên vẹn.

## 3. CHECKLIST XÓA HỆ CŨ (nghiệm thu bằng grep, không hứa miệng)

Inventory đầy đủ từ grep 2026-06-11:

| # | Vết tích | File | Xử lý |
|---|---|---|---|
| 1 | `_coerce_json` + reparse loop + `_PROMPT` "Tra ve DUY NHAT JSON theo Output schema" | `tools/session_manager/__init__.py` | XÓA, thay bằng tool_select |
| 2 | `_coerce_json`, `_parse_sql`, prompt "Tra ve JSON {sql}", `_CHECK_PROMPT` "Tra ve DUY NHAT JSON mot dong" | `tools/sql_execute/__init__.py` | XÓA, thay complete_structured |
| 3 | strip-backtick + `json.loads` + prompt "Tra ve JSON {verdict...}" | `tools/data_validator/__init__.py` | XÓA, thay complete_structured |
| 4 | strip-backtick + `json.loads` + prompt "Tra ve JSON {answer...}" | `tools/answer_composer/__init__.py` | XÓA, thay complete_structured |
| 5 | `render_tool_catalog()` | `registry/registry.py` + import ở SM + `tests/test_registry.py` | XÓA, thay render_api_tools |
| 6 | "## Output schema" (4 file) | `tools/*/skill.md` | Viết lại: bỏ chỉ dẫn trả JSON, giữ luật nghiệp vụ |
| 7 | Test script JSON-string cho complete() | `tests/test_session_manager.py`, `test_tool_*.py`, `test_orchestrator.py`, `test_e2e_*.py` | Migrate sang structured/tool_select fakes |

**Tiêu chí nghiệm thu (chạy sau khi implement, phải = 0 hit):**

```bash
# trong ai_python/, loại trừ .venv:
grep -rn "_coerce_json\|_parse_sql\|render_tool_catalog" app/ tests/        # = 0
grep -rn "Tra ve JSON\|Tra ve DUY NHAT JSON\|Output schema" app/            # = 0 (kể cả skill.md)
grep -rn 'startswith("```' app/                                             # = 0
grep -rn "json.loads" app/ --include="*.py"                                 # chỉ còn: llm_client.py (parse tool args), hitl.py (snapshot — không phải LLM output)
grep -rn "llm.complete(" app/                                               # chỉ còn: memory compact
```

Bộ grep này đưa vào plan như một verification step bắt buộc trước commit cuối.

## 4. Test strategy

- **FakeLLM** thay bằng 2 mặt: `complete_structured` (pop dict từ queue →
  `model_validate` — dict sai schema raise như thật) và `complete_tool_select`
  (pop `(tool_name, args_dict)` từ queue). `complete` chỉ còn cho memory compact.
- **Test mới llm_client:** mock SDK trả tool_calls → parse đúng; args hỏng
  attempt 1, đúng attempt 2 → retry; hỏng cả 2 → StructuredOutputError;
  request có `tool_choice` đúng dạng + `enable_thinking: False`;
  `render_api_tools` sinh đúng OpenAI format từ REGISTRY.
- **Test SM:** tool_call `sql_execute` → Decision call_tool; lặp tool sau
  invalid → retry_tool; vượt retry cap → orchestrator xử như cũ; `finish`/
  `request_clarification` → action + message; no-tool-call 2 lần → finish an toàn.
- **Migrate test 4 tool + orchestrator + e2e:** hành vi assert giữ nguyên.
- Toàn suite xanh (mục tiêu ≥ 128 hiện tại); **smoke test LLM thật** 1 câu e2e
  trước commit cuối.

## 5. Rủi ro & đối sách

| Rủi ro | Đối sách |
|---|---|
| FC template-based, args thỉnh thoảng hỏng | retry 1 lần + pydantic tại biên + fallback từng điểm giữ nguyên |
| Model gọi tool ngoài danh sách (dù required) | `get_args_model` raise KeyError → đếm như attempt hỏng → retry → finish an toàn |
| Scope to (5 điểm + registry + skill.md + test migrate) | Plan chia task nhỏ TDD, mỗi task một commit, suite xanh từng bước |
| skill.md SM viết lại làm lệch hành vi chọn tool | Probe P1–P3 làm chuẩn; smoke test thật + golden questions (vòng eval P1 sắp tới) |
| `required` không stream được reasoning text | Không ảnh hưởng — SSE hiện chỉ phát event theo bước, không stream token |
