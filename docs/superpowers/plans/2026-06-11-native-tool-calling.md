# Native Tool-Calling (nấc 3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Chuyển toàn bộ 5 điểm JSON-trong-văn của ai_python sang native tool-calling (SM chọn hành động bằng tools thật + `tool_choice="required"`; 4 điểm extraction dùng forced-function), xóa sạch hệ cũ với nghiệm thu grep-zero.

**Architecture:** Registry là nguồn chân lý duy nhất (`ToolSpec{description, args_model, kind}` → `render_api_tools()`). SM đọc `tool_calls[0]` → validate args bằng pydantic → map sang `Decision` nội bộ (orchestrator/dispatcher/HITL giữ nguyên luật; bỏ action `replan` + field `forward_data`). `complete_structured()` ép 1 function "respond" cho SqlDraft/SemanticCheck/ValidatorVerdict/ComposerAnswer. `complete()` text chỉ còn memory compact.

**Tech Stack:** openai SDK (FPT Cloud, Qwen3.6-27B), pydantic v2, LangGraph subgraph hiện có, pytest + FakeLLM v2.

**Spec:** `docs/superpowers/specs/2026-06-11-native-tool-calling-design.md`

---

## Thứ tự task (bắt buộc)

```
Task 1 llm_client (tool_select + structured)
Task 2 registry (args models + REGISTRY + render_api_tools, xóa catalog)
Task 3 conftest FakeLLM v2
Task 4 data_validator  ─┐
Task 5 answer_composer ─┼─ độc lập nhau, sau Task 3
Task 6 sql_execute     ─┘
Task 7 session_manager + orchestrator (atomic — Decision đổi shape) + migrate test SM/orchestrator/e2e
Task 8 skill.md × 4 (xóa Output schema, SM viết lại luật chọn tool)
Task 9 Grep-zero + full suite + smoke test thật + commit cuối
```

Mỗi task: test fail trước → code → test pass → **chạy full suite** → commit riêng.
Lệnh suite: `cd ai_python && .venv\Scripts\python -m pytest -q` (Windows) hoặc Bash `cd /d/do_an_tot_nghiep/project/ai_python && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q`.

---

## Task 1: llm_client — `complete_tool_select` + `complete_structured`

**Files:**
- Modify: `ai_python/app/config/llm_client.py`
- Test: `ai_python/tests/test_llm_client.py` (thêm test, giữ test cũ)

- [ ] **Step 1: Viết test fail** — thêm vào cuối `tests/test_llm_client.py`:

```python
import json
import pytest
from pydantic import BaseModel
from typing import Literal
from unittest.mock import MagicMock
from app.config.llm_client import (OpenAILLMClient, StructuredOutputError,
                                   ToolCallError)


class _Verdict(BaseModel):
    """Ket luan kiem dinh."""
    verdict: Literal["pass", "fail"]
    reason: str


def _sdk_returning(tool_calls_list):
    """Moi phan tu = list tool_calls (hoac None) cho 1 lan create()."""
    sdk = MagicMock()
    resps = []
    for tcs in tool_calls_list:
        msg = MagicMock()
        msg.tool_calls = tcs
        msg.content = ""
        resps.append(MagicMock(choices=[MagicMock(message=msg)]))
    sdk.chat.completions.create.side_effect = resps
    return sdk


def _tc(name, args: dict):
    tc = MagicMock()
    tc.function.name = name
    tc.function.arguments = json.dumps(args, ensure_ascii=False)
    return tc


def test_complete_structured_parses_valid_args():
    sdk = _sdk_returning([[_tc("respond", {"verdict": "pass", "reason": "ok"})]])
    c = OpenAILLMClient(sdk=sdk, model="m", temperature=0.0)
    out = c.complete_structured(system="S", user="U", output_model=_Verdict)
    assert out.verdict == "pass" and out.reason == "ok"
    kwargs = sdk.chat.completions.create.call_args.kwargs
    assert kwargs["tool_choice"] == {"type": "function",
                                     "function": {"name": "respond"}}
    assert kwargs["tools"][0]["function"]["name"] == "respond"
    assert kwargs["tools"][0]["function"]["parameters"]["properties"]["verdict"]


def test_complete_structured_retries_once_then_succeeds():
    sdk = _sdk_returning([[_tc("respond", {"verdict": "maybe", "reason": "x"})],
                          [_tc("respond", {"verdict": "fail", "reason": "thieu"})]])
    c = OpenAILLMClient(sdk=sdk, model="m", temperature=0.0)
    out = c.complete_structured(system="S", user="U", output_model=_Verdict)
    assert out.verdict == "fail"
    assert sdk.chat.completions.create.call_count == 2
    # attempt 2 phai mang thong bao loi attempt 1
    u2 = sdk.chat.completions.create.call_args.kwargs["messages"][1]["content"]
    assert "[Loi attempt truoc" in u2


def test_complete_structured_raises_after_two_failures():
    # ca 2 attempt deu tra args sai schema
    sdk = _sdk_returning([[_tc("respond", {"verdict": "maybe", "reason": "x"})],
                          [_tc("respond", {"verdict": "no", "reason": "y"})]])
    c = OpenAILLMClient(sdk=sdk, model="m", temperature=0.0)
    with pytest.raises(StructuredOutputError):
        c.complete_structured(system="S", user="U", output_model=_Verdict)


def test_complete_structured_no_toolcall_counts_as_failure():
    sdk = _sdk_returning([None, [_tc("respond", {"verdict": "pass", "reason": "r"})]])
    c = OpenAILLMClient(sdk=sdk, model="m", temperature=0.0)
    out = c.complete_structured(system="S", user="U", output_model=_Verdict)
    assert out.verdict == "pass"
    assert sdk.chat.completions.create.call_count == 2


def test_complete_tool_select_returns_name_and_args():
    sdk = _sdk_returning([[_tc("sql_execute", {"reasoning": "r", "require": "q"})]])
    c = OpenAILLMClient(sdk=sdk, model="m", temperature=0.0)
    tools = [{"type": "function", "function": {"name": "sql_execute",
              "description": "d", "parameters": {"type": "object"}}}]
    name, args = c.complete_tool_select(system="S", user="U", tools=tools)
    assert name == "sql_execute"
    assert json.loads(args)["require"] == "q"
    kwargs = sdk.chat.completions.create.call_args.kwargs
    assert kwargs["tool_choice"] == "required"
    assert kwargs["tools"] is tools


def test_complete_tool_select_raises_when_no_toolcall():
    sdk = _sdk_returning([None])
    c = OpenAILLMClient(sdk=sdk, model="m", temperature=0.0)
    with pytest.raises(ToolCallError):
        c.complete_tool_select(system="S", user="U", tools=[])


def test_tool_calls_carry_disable_thinking_extra_body():
    sdk = _sdk_returning([[_tc("respond", {"verdict": "pass", "reason": "r"})]])
    c = OpenAILLMClient(sdk=sdk, model="m", temperature=0.0, disable_thinking=True)
    c.complete_structured(system="S", user="U", output_model=_Verdict)
    kwargs = sdk.chat.completions.create.call_args.kwargs
    assert kwargs["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}
```

(LƯU Ý cho executor: test thứ 3 ở trên có 2 dòng `sdk = _sdk_returning(...)` thừa do nháp —
chỉ giữ dòng cuối cùng "ca 2 attempt deu args sai schema". Viết bản sạch.)

- [ ] **Step 2: Run → fail**

Run: `pytest tests/test_llm_client.py -v`
Expected: FAIL — `ImportError: cannot import name 'StructuredOutputError'`.

- [ ] **Step 3: Implement** — thêm vào `app/config/llm_client.py` (sau class `OpenAILLMClient.complete`, trong cùng class):

```python
# đầu file thêm:
from pydantic import BaseModel, ValidationError


class ToolCallError(Exception):
    """Model khong tra tool_calls trong response."""


class StructuredOutputError(Exception):
    """Sau 2 attempt van khong co args hop le theo output_model."""
```

Trong class `OpenAILLMClient` thêm 3 method:

```python
    def _tool_request(self, *, system: str, user: str, tools: list[dict],
                      tool_choice, role: str, temperature: float | None):
        temp = self.temperature if temperature is None else temperature
        log.debug("LLM tool-call role=%s model=%s tools=%d", role, self.model, len(tools))
        extra: dict = {}
        if self.max_tokens:
            extra["max_tokens"] = self.max_tokens
        if self.disable_thinking:
            extra["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}
        t0 = time.perf_counter()
        resp = self._sdk.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            tools=tools, tool_choice=tool_choice, temperature=temp, **extra)
        msg = resp.choices[0].message
        log.info("LLM tool-call done role=%s elapsed=%.2fs has_tool_calls=%s",
                 role, time.perf_counter() - t0, bool(msg.tool_calls))
        return msg

    def complete_tool_select(self, *, system: str, user: str, tools: list[dict],
                             role: str = "default",
                             temperature: float | None = None) -> tuple[str, str]:
        """1 call voi tool_choice='required'. Tra (tool_name, args_json_str).
        Khong co tool_calls -> ToolCallError (caller tu retry vi can args_model
        theo ten tool de validate)."""
        msg = self._tool_request(system=system, user=user, tools=tools,
                                 tool_choice="required", role=role,
                                 temperature=temperature)
        if not msg.tool_calls:
            raise ToolCallError("model khong goi tool nao (tool_calls rong)")
        fn = msg.tool_calls[0].function
        log.debug("LLM tool-select -> %s args=%.300s", fn.name, fn.arguments)
        return fn.name, fn.arguments

    def complete_structured(self, *, system: str, user: str,
                            output_model: type[BaseModel], role: str = "default",
                            temperature: float | None = None) -> BaseModel:
        """Forced-function extraction: ep model dien dung schema output_model.
        Retry 1 lan; het -> StructuredOutputError."""
        tools = [{"type": "function", "function": {
            "name": "respond",
            "description": (output_model.__doc__ or "").strip(),
            "parameters": output_model.model_json_schema()}}]
        choice = {"type": "function", "function": {"name": "respond"}}
        u = user
        last_err: Exception | None = None
        for attempt in range(2):
            try:
                msg = self._tool_request(system=system, user=u, tools=tools,
                                         tool_choice=choice, role=role,
                                         temperature=temperature)
                if not msg.tool_calls:
                    raise ToolCallError("khong co tool_calls")
                return output_model.model_validate_json(
                    msg.tool_calls[0].function.arguments)
            except (ToolCallError, ValidationError, ValueError) as exc:
                last_err = exc
                log.warning("structured attempt=%d model=%s err=%s",
                            attempt + 1, output_model.__name__, exc)
                u = user + f"\n\n[Loi attempt truoc: {exc}. Dien dung schema.]"
        raise StructuredOutputError(str(last_err))
```

- [ ] **Step 4: Run → pass**: `pytest tests/test_llm_client.py -v` → PASS (test cũ + mới).
- [ ] **Step 5: Full suite → 128+ pass. Commit:**

```bash
git add ai_python/app/config/llm_client.py ai_python/tests/test_llm_client.py
git commit -m "feat(llm): complete_tool_select (required) + complete_structured (forced function)" -- ai_python/app/config/llm_client.py ai_python/tests/test_llm_client.py
```

---

## Task 2: Registry — args models + REGISTRY + render_api_tools (xóa catalog)

**Files:**
- Create: `ai_python/app/registry/args.py`
- Modify: `ai_python/app/registry/registry.py` (xóa `DISPATCHABLE`, `is_registered`, `render_tool_catalog`)
- Modify: `ai_python/app/graph/dispatcher.py:4,40` (`is_registered` → `is_dispatchable`)
- Modify: `ai_python/app/tools/session_manager/__init__.py:8` (import tạm `is_dispatchable` thay `is_registered`; phần còn lại đổi ở Task 7)
- Test: `ai_python/tests/test_registry.py` (viết lại các test catalog)

- [ ] **Step 1: Viết test fail** — thay nội dung `tests/test_registry.py`:

```python
import pytest
from app.registry.registry import (TOOL_NAMES, REGISTRY, load_skill,
                                    render_api_tools, get_args_model,
                                    is_dispatchable)
from app.registry.args import SqlExecuteArgs, FinishArgs


def test_tool_names_unchanged():  # fact-registry-static (load_skill dirs)
    assert set(TOOL_NAMES) == {
        "sql_execute", "data_validator", "answer_composer", "session_manager"}


def test_registry_has_5_api_tools_3_dispatch_2_control():
    assert set(REGISTRY) == {"sql_execute", "data_validator", "answer_composer",
                             "finish", "request_clarification"}
    kinds = {n: s.kind for n, s in REGISTRY.items()}
    assert kinds["sql_execute"] == "dispatch"
    assert kinds["finish"] == "control"
    assert kinds["request_clarification"] == "control"


def test_is_dispatchable():
    assert is_dispatchable("sql_execute")
    assert not is_dispatchable("finish")          # control: SM-level, khong dispatch
    assert not is_dispatchable("rm_rf_database")


def test_render_api_tools_openai_format():
    tools = render_api_tools()
    assert len(tools) == 5
    by_name = {t["function"]["name"]: t for t in tools}
    assert by_name["sql_execute"]["type"] == "function"
    params = by_name["sql_execute"]["function"]["parameters"]
    assert "require" in params["properties"]
    assert "reasoning" in params["properties"]
    assert by_name["finish"]["function"]["parameters"]["properties"]["message"]
    assert by_name["sql_execute"]["function"]["description"]


def test_get_args_model():
    assert get_args_model("sql_execute") is SqlExecuteArgs
    assert get_args_model("finish") is FinishArgs
    with pytest.raises(KeyError):
        get_args_model("nope")


def test_load_skill_reads_md_fresh_each_call():
    first = load_skill("sql_execute")
    assert isinstance(first, str) and len(first) > 0


def test_load_skill_unknown_raises():
    with pytest.raises(KeyError):
        load_skill("nope")
```

- [ ] **Step 2: Run → fail** (`ImportError`).
- [ ] **Step 3: Tạo `app/registry/args.py`:**

```python
from __future__ import annotations
from pydantic import BaseModel


class CommonArgs(BaseModel):
    reasoning: str                          # vi sao chon buoc nay
    resolved_require: str | None = None     # cau hoi noi tiep da viet lai tu-du-nghia


class SqlExecuteArgs(CommonArgs):
    """Sinh SQL read-only tu yeu cau va chay tren DB de lay du lieu."""
    require: str                            # yeu cau du lieu da lam ro/viet lai


class ValidatorArgs(CommonArgs):
    """Kiem tra data vua lay co du/dung de tra loi yeu cau khong."""


class ComposerArgs(CommonArgs):
    """Soan cau tra loi cuoi cho user tu data da duoc kiem dinh."""


class FinishArgs(CommonArgs):
    """Ket thuc phien voi message cuoi cho user."""
    message: str


class ClarifyArgs(CommonArgs):
    """Hoi lai user khi yeu cau mo ho/thieu thong tin."""
    message: str
```

- [ ] **Step 4: Viết lại `app/registry/registry.py`** (giữ `TOOL_NAMES` + `load_skill` concat schema.md; xóa `DISPATCHABLE`/`is_registered`/`render_tool_catalog`):

```python
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from pydantic import BaseModel
from app.registry.args import (ClarifyArgs, ComposerArgs, FinishArgs,
                               SqlExecuteArgs, ValidatorArgs)

_TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"

# Thu muc tool co skill.md (load_skill). session_manager khong phai API tool.
TOOL_NAMES = ("session_manager", "sql_execute", "data_validator", "answer_composer")


@dataclass(frozen=True)
class ToolSpec:
    """Nguon chan ly duy nhat cho 1 tool: mo ta cho LLM + schema args + loai."""
    description: str
    args_model: type[BaseModel]
    kind: str  # "dispatch" (co subgraph) | "control" (SM-level)


REGISTRY: dict[str, ToolSpec] = {
    "sql_execute": ToolSpec(
        "Sinh SQL read-only tu yeu cau va chay tren DB de lay du lieu ERP.",
        SqlExecuteArgs, kind="dispatch"),
    "data_validator": ToolSpec(
        "Kiem tra data vua lay co du/dung de tra loi yeu cau khong. "
        "BAT BUOC chay va pass truoc answer_composer.",
        ValidatorArgs, kind="dispatch"),
    "answer_composer": ToolSpec(
        "Soan cau tra loi cuoi cho user (lich su, du thong tin, co 'Gợi ý:'). "
        "Chi goi sau khi data_validator pass.",
        ComposerArgs, kind="dispatch"),
    "finish": ToolSpec(
        "Ket thuc phien va gui message cuoi (chao hoi/ngoai pham vi/da co answer).",
        FinishArgs, kind="control"),
    "request_clarification": ToolSpec(
        "Hoi lai user khi yeu cau mo ho, thieu thong tin de truy van.",
        ClarifyArgs, kind="control"),
}


def is_dispatchable(tool_name: str) -> bool:
    spec = REGISTRY.get(tool_name)
    return spec is not None and spec.kind == "dispatch"


def get_args_model(tool_name: str) -> type[BaseModel]:
    return REGISTRY[tool_name].args_model     # KeyError neu tool la


def render_api_tools() -> list[dict]:
    """OpenAI tools format tu REGISTRY — nguon duy nhat SM nhin thay."""
    return [{"type": "function",
             "function": {"name": name, "description": spec.description,
                          "parameters": spec.args_model.model_json_schema()}}
            for name, spec in REGISTRY.items()]


def load_skill(tool_name: str) -> str:
    """Doc skill.md MOI LAN goi (khong cache) — nen tang cho reload-on-retry.
    Neu co schema.md cung thu muc, tu dong concat vao sau skill.md."""
    if tool_name not in TOOL_NAMES:
        raise KeyError(f"unknown tool: {tool_name}")
    tool_dir = _TOOLS_DIR / tool_name
    content = (tool_dir / "skill.md").read_text(encoding="utf-8")
    schema_path = tool_dir / "schema.md"
    if schema_path.exists():
        content = content + "\n\n" + schema_path.read_text(encoding="utf-8")
    return content
```

- [ ] **Step 5: Cập nhật 2 importer của `is_registered`:**
  - `app/graph/dispatcher.py` dòng 4: `from app.registry.registry import is_dispatchable`; dòng 40: `if not is_dispatchable(tool_name):`
  - `app/tools/session_manager/__init__.py` dòng 8: đổi `render_tool_catalog, is_registered` → `is_dispatchable`; dòng 28: `if not v or not is_dispatchable(v):`; dòng 74: xóa `catalog=render_tool_catalog(),` và bỏ `{catalog}` khỏi `_PROMPT` (dòng 33-35) — `_PROMPT` tạm thời còn câu "Tra ve DUY NHAT JSON theo Output schema." (xóa hẳn ở Task 7).

- [ ] **Step 6: Run → pass** `pytest tests/test_registry.py tests/test_session_manager.py tests/test_dispatcher.py -v`.
- [ ] **Step 7: Full suite → pass. Commit:**

```bash
git add -A ai_python/app/registry ai_python/app/graph/dispatcher.py ai_python/app/tools/session_manager/__init__.py ai_python/tests/test_registry.py
git commit -m "feat(registry): ToolSpec + REGISTRY 5 tool + render_api_tools — xoa catalog/is_registered"
```

---

## Task 3: FakeLLM v2 (conftest)

**Files:**
- Modify: `ai_python/tests/conftest.py`

- [ ] **Step 1: Thêm vào class `FakeLLM`** (giữ `complete`/`scripted`/`by_role` nguyên — memory compact còn dùng):

```python
    # __init__ thêm 2 queue + 2 log:
    def __init__(self, scripted=None, by_role=None, structured=None,
                 tool_selects=None):
        self.scripted = list(scripted or [])
        self.by_role = {k: list(v) for k, v in (by_role or {}).items()}
        self.structured = list(structured or [])      # dict | Exception
        self.tool_selects = list(tool_selects or [])  # (name, args_dict) | Exception
        self.calls = []
        self.structured_calls = []
        self.tool_select_calls = []

    def complete_structured(self, *, system, user, output_model,
                            role="default", temperature=None):
        self.structured_calls.append({"role": role, "system": system,
                                      "user": user,
                                      "model": output_model.__name__})
        if not self.structured:
            raise AssertionError(
                f"FakeLLM het kich ban structured cho {output_model.__name__}")
        item = self.structured.pop(0)
        if isinstance(item, Exception):
            raise item
        return output_model.model_validate(item)

    def complete_tool_select(self, *, system, user, tools,
                             role="default", temperature=None):
        self.tool_select_calls.append({
            "role": role, "system": system, "user": user,
            "tools": [t["function"]["name"] for t in tools]})
        if not self.tool_selects:
            raise AssertionError("FakeLLM het kich ban tool_selects")
        item = self.tool_selects.pop(0)
        if isinstance(item, Exception):
            raise item
        name, args = item
        return name, json.dumps(args, ensure_ascii=False)
```

- [ ] **Step 2: Full suite → vẫn pass (chỉ thêm method). Commit:**

```bash
git add ai_python/tests/conftest.py
git commit -m "test(conftest): FakeLLM v2 — structured queue + tool_selects queue"
```

---

## Task 4: data_validator → complete_structured

**Files:**
- Modify: `ai_python/app/tools/data_validator/__init__.py`
- Test: `ai_python/tests/test_tool_data_validator.py` (migrate)

- [ ] **Step 1: Migrate test** — trong `test_tool_data_validator.py`: thay mọi LLM giả trả JSON-string bằng `FakeLLM(structured=[{...}])` từ conftest. Pattern:
  - pass case: `FakeLLM(structured=[{"verdict": "pass", "reason": "du"}])`
  - fail case: `FakeLLM(structured=[{"verdict": "fail", "reason": "lech"}])`
  - malformed case (cũ: LLM trả văn xuôi): thay bằng `from app.config.llm_client import StructuredOutputError` + `FakeLLM(structured=[StructuredOutputError("2 attempts failed")])` — assert vẫn là `out["verdict"] is None` và `self_validate` fail.
  - assert prompt: dùng `llm.structured_calls[0]["user"]` thay `llm.calls/seen`.
- [ ] **Step 2: Run → fail** (execute còn gọi `llm.complete`).
- [ ] **Step 3: Viết lại `execute` trong `data_validator/__init__.py`:**

```python
from __future__ import annotations
import json
import logging
from typing import Literal
from pydantic import BaseModel
from app.config.llm_client import StructuredOutputError
from app.graph.state import ToolState
from app.harness.think_log import think
from app.tools import memory_block

log = logging.getLogger(__name__)


class ValidatorVerdict(BaseModel):
    """Ket luan du lieu co du va dung de tra loi raw_require khong."""
    verdict: Literal["pass", "fail"]
    reason: str


_PROMPT = ("{skill}\n\n--- KIEM DINH ---\nraw_require: {raw_require}\n"
           "data: {data}\n{memory}")


def execute(state: ToolState, *, llm, **_) -> dict:
    data = state["upstream_data"]
    n_rows = len(data.get("rows", [])) if isinstance(data, dict) else 0
    think("data_validator", 'soi ket qua (%d dong) xem co du va dung de tra loi "%.100s" khong',
          n_rows, state["raw_require"])
    user = _PROMPT.format(skill=state["skill"], raw_require=state["raw_require"],
                          data=json.dumps(data, ensure_ascii=False)[:4000],
                          memory=memory_block(state))
    try:
        v = llm.complete_structured(system=state["skill"], user=user,
                                    output_model=ValidatorVerdict)
    except StructuredOutputError as exc:
        log.warning("data_validator structured output failed: %s", exc)
        think("data_validator", "-> khong doc duoc ket luan tu LLM, bao loi de SM thu lai")
        return {"verdict": None, "reason": f"LLM output khong hop le: {exc}"}
    log.info("data_validator verdict=%s reason=%.120s", v.verdict, v.reason)
    if v.verdict == "pass":
        think("data_validator", "-> dat: %s", v.reason or "du lieu du de tra loi")
    else:
        think("data_validator", "-> KHONG dat: %s", v.reason)
    return {"verdict": v.verdict, "reason": v.reason}
```

(`self_validate` giữ nguyên.)

- [ ] **Step 4: Run → pass. Full suite → pass. Commit:**

```bash
git add ai_python/app/tools/data_validator/__init__.py ai_python/tests/test_tool_data_validator.py
git commit -m "feat(validator): verdict qua complete_structured — xoa parse JSON van xuoi"
```

---

## Task 5: answer_composer → complete_structured

**Files:**
- Modify: `ai_python/app/tools/answer_composer/__init__.py`
- Test: `ai_python/tests/test_tool_answer_composer.py` (migrate cùng pattern Task 4)

- [ ] **Step 1: Migrate test** — `FakeLLM(structured=[{"answer": "...\nGợi ý: ..."}])`; malformed case → `StructuredOutputError` scripted, assert `out["answer"] == ""` + `self_validate` fail.
- [ ] **Step 2: Run → fail.**
- [ ] **Step 3: Viết lại `execute`:**

```python
from __future__ import annotations
import json
import logging
from pydantic import BaseModel
from app.config.llm_client import StructuredOutputError
from app.graph.state import ToolState
from app.harness.think_log import think
from app.tools import memory_block

log = logging.getLogger(__name__)


class ComposerAnswer(BaseModel):
    """Cau tra loi cuoi cho user, ket thuc bang dong bat dau 'Gợi ý:'."""
    answer: str


_PROMPT = ("{skill}\n\n--- SOAN TRA LOI ---\nraw_require: {raw_require}\n"
           "data: {data}\n{memory}\nKet thuc answer bang dong bat dau 'Gợi ý:'.")


def execute(state: ToolState, *, llm, **_) -> dict:
    think("answer_composer", 'du lieu da duoc duyet, soan cau tra loi tieng Viet cho "%.100s"',
          state["raw_require"])
    user = _PROMPT.format(skill=state["skill"], raw_require=state["raw_require"],
                          data=json.dumps(state["upstream_data"], ensure_ascii=False)[:4000],
                          memory=memory_block(state))
    try:
        out = llm.complete_structured(system=state["skill"], user=user,
                                      output_model=ComposerAnswer)
        answer = out.answer.strip()
    except StructuredOutputError as exc:
        log.warning("answer_composer structured output failed: %s", exc)
        answer = ""
    if not answer:
        think("answer_composer", "-> LLM tra answer rong/khong doc duoc, de SM thu lai")
    else:
        think("answer_composer", "-> soan xong cau tra loi %d ky tu", len(answer))
        if "gợi ý:" not in answer.lower():
            log.warning("answer_composer missing 'Gợi ý:' marker — self_validate will fail")
    return {"answer": answer}
```

- [ ] **Step 4: Run → pass. Full suite. Commit:**

```bash
git add ai_python/app/tools/answer_composer/__init__.py ai_python/tests/test_tool_answer_composer.py
git commit -m "feat(composer): answer qua complete_structured — xoa parse JSON van xuoi"
```

---

## Task 6: sql_execute → SqlDraft + SemanticCheck

**Files:**
- Modify: `ai_python/app/tools/sql_execute/__init__.py`
- Test: `ai_python/tests/test_tool_sql_execute.py` (migrate)

- [ ] **Step 1: Migrate test** — thay `_LLM`/`_SeqLLM`/`_BadJsonLLM` bằng `FakeLLM(structured=[...])`; queue tuần tự = [SqlDraft dict, SemanticCheck dict]:
  - happy: `FakeLLM(structured=[{"sql": "SELECT ..."}, {"ok": True}])`
  - rewrite: `FakeLLM(structured=[{"sql": _INNER}, {"ok": False, "sql": _LEFT, "reason": "..."}])`; assert `executed == [_LEFT]`, check `llm.structured_calls[1]["user"]` chứa `_INNER`
  - fail-open: `FakeLLM(structured=[{"sql": "SELECT ..."}, StructuredOutputError("x")])` → giữ SQL gốc
  - draft hỏng: `FakeLLM(structured=[StructuredOutputError("x")])` → `error` không None, executor không chạm
  - guard sau rewrite: `[{"sql": "SELECT 1"}, {"ok": False, "sql": "DELETE FROM products"}]` → error, executed rỗng
  - memory block asserts → `structured_calls[0]["user"]`
- [ ] **Step 2: Run → fail.**
- [ ] **Step 3: Viết lại phần LLM của `sql_execute/__init__.py`** — xóa `_coerce_json`, `_parse_sql`, sửa `_PROMPT`/`_CHECK_PROMPT` bỏ chỉ dẫn JSON:

```python
# imports thêm:
from pydantic import BaseModel
from app.config.llm_client import StructuredOutputError


class SqlDraft(BaseModel):
    """Cau SQL SELECT read-only tra loi raw_require."""
    sql: str


class SemanticCheck(BaseModel):
    """Ket qua tu kiem tra ngu nghia JOIN cua SQL vua sinh.
    ok=false thi sql = ban viet lai."""
    ok: bool
    sql: str | None = None
    reason: str | None = None


_PROMPT = ("{skill}\n\n--- YEU CAU ---\nraw_require: {raw_require}\n"
           "upstream_data: {upstream}\n{memory}")

_CHECK_PROMPT = (
    "Ban vua sinh cau SQL duoi day cho yeu cau cua user. Tu kiem tra NGU NGHIA JOIN "
    "truoc khi chay:\n"
    "1. Cau hoi co hoi ve doi tuong KHONG CO / CHUA TUNG CO du lieu su kien khong? "
    "(dau hieu: 'chua', 'khong co', 'chua tung', 'e', 'ban cham', 'it nhat', 'thap nhat', "
    "'chua duoc dung', 'khong ban duoc')\n"
    "2. Neu CO ma SQL dang INNER JOIN sang bang su kien (orderdetails, salesorders, "
    "stockreceipts...) thi cac dong 0-su-kien — chinh la doi tuong user hoi — bi loai mat. "
    "SQL SAI. Viet lai: FROM bang chu the, LEFT JOIN bang su kien, "
    "COALESCE(SUM(...), 0) / COUNT(x.id).\n"
    "3. Neu cau hoi khong thuoc loai do, hoac SQL da dung ngu nghia, tra ok=true.\n\n"
    "raw_require: {raw_require}\nsql: {sql}")
```

`_semantic_check` mới (giữ fail-open + think):

```python
def _semantic_check(*, llm, skill: str, raw_require: str, sql: str) -> str:
    think("sql_execute", "tu kiem tra lai SQL vua sinh: cau hoi co ngu nghia "
          "vang mat (chua/khong co/e) ma minh lo dung INNER JOIN khong?")
    user = _CHECK_PROMPT.format(raw_require=raw_require, sql=sql)
    try:
        verdict = llm.complete_structured(system=skill, user=user,
                                          output_model=SemanticCheck)
        if verdict.ok is False and (verdict.sql or "").strip():
            fixed = verdict.sql.strip()
            log.info("sql_execute semantic check REWROTE sql reason=%.150s\n  cu : %.200s\n  moi: %.200s",
                     verdict.reason, sql, fixed)
            think("sql_execute", "-> phat hien SQL sai ngu nghia: %s. Viet lai: %.200s",
                  verdict.reason, fixed)
            return fixed
        log.debug("sql_execute semantic check ok")
        think("sql_execute", "-> SQL on, khong can sua")
    except Exception as exc:
        log.warning("sql_execute semantic check fail-open: %s", exc)
        think("sql_execute", "-> buoc tu kiem tra gap loi (%s), giu SQL goc va di tiep", exc)
    return sql
```

Trong `execute`, thay khối sinh SQL:

```python
    try:
        draft = llm.complete_structured(system=state["skill"], user=user,
                                        output_model=SqlDraft)
        sql = draft.sql
    except StructuredOutputError as exc:
        log.warning("sql_execute structured draft failed: %s", exc)
        think("sql_execute", "-> LLM tra output khong doc duoc, bao loi de SM quyet dinh thu lai")
        return {"sql": "", "columns": [], "rows": [],
                "error": f"LLM output khong hop le: {exc}"}
```

(phần guard/executor/`self_validate` giữ nguyên.)

- [ ] **Step 4: Run → pass. Full suite. Commit:**

```bash
git add ai_python/app/tools/sql_execute/__init__.py ai_python/tests/test_tool_sql_execute.py
git commit -m "feat(sql): SqlDraft + SemanticCheck qua complete_structured — xoa _coerce_json/_parse_sql"
```

---

## Task 7: session_manager + orchestrator (ATOMIC) + migrate test

**Files:**
- Modify: `ai_python/app/tools/session_manager/__init__.py` (viết lại)
- Modify: `ai_python/app/graph/orchestrator.py` (bỏ replan branch + forward_data)
- Test: `ai_python/tests/test_session_manager.py` (viết lại), `tests/test_orchestrator.py`, `tests/test_e2e_happy_path.py`, `tests/test_e2e_memory.py` (migrate)

- [ ] **Step 1: Viết lại `test_session_manager.py`:**

```python
import pytest
from app.config.llm_client import ToolCallError
from app.tools.session_manager import Decision, analyze
from app.graph.state import new_session_state
from tests.conftest import FakeLLM


def _st(require="R", history=None):
    st = new_session_state(raw_require=require, thread_id="t")
    if history:
        st["history"] = history
    return st


def test_toolcall_sql_execute_maps_to_call_tool(monkeypatch):
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "SM-SKILL")
    llm = FakeLLM(tool_selects=[("sql_execute",
                                 {"reasoning": "can data",
                                  "require": "doanh thu thang 6/2026"})])
    d = analyze(_st("doanh thu thang nay"), llm=llm)
    assert d.action == "call_tool" and d.tool_name == "sql_execute"
    assert d.resolved_require == "doanh thu thang 6/2026"
    assert llm.tool_select_calls[0]["role"] == "sm"
    # SM nhin thay du 5 API tools tu registry
    assert set(llm.tool_select_calls[0]["tools"]) == {
        "sql_execute", "data_validator", "answer_composer",
        "finish", "request_clarification"}


def test_same_tool_after_invalid_becomes_retry(monkeypatch):
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "S")
    hist = [{"action": "call_tool", "tool": "sql_execute", "valid": False,
             "output": {"error": "loi DB"}}]
    llm = FakeLLM(tool_selects=[("sql_execute", {"reasoning": "thu lai",
                                                 "require": "R"})])
    d = analyze(_st(history=hist), llm=llm)
    assert d.action == "retry_tool" and d.tool_name == "sql_execute"


def test_finish_maps_message(monkeypatch):
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "S")
    llm = FakeLLM(tool_selects=[("finish", {"reasoning": "chao hoi",
                                            "message": "Chao ban!"})])
    d = analyze(_st("chao ban"), llm=llm)
    assert d.action == "finish" and d.message == "Chao ban!"


def test_clarify_maps_message(monkeypatch):
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "S")
    llm = FakeLLM(tool_selects=[("request_clarification",
                                 {"reasoning": "mo ho", "message": "Thang nao?"})])
    d = analyze(_st("cai do?"), llm=llm)
    assert d.action == "request_clarification" and d.message == "Thang nao?"


def test_unknown_tool_then_valid_uses_retry_attempt(monkeypatch):
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "S")
    llm = FakeLLM(tool_selects=[
        ("rm_rf_database", {"reasoning": "bia"}),                 # attempt 1 hong
        ("finish", {"reasoning": "ok", "message": "xong"})])      # attempt 2
    d = analyze(_st(), llm=llm)
    assert d.action == "finish"
    assert len(llm.tool_select_calls) == 2
    assert "[Loi attempt truoc" in llm.tool_select_calls[1]["user"]


def test_bad_args_two_attempts_falls_back_finish(monkeypatch):
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "S")
    llm = FakeLLM(tool_selects=[("finish", {"reasoning": "thieu message"}),
                                ("sql_execute", {"reasoning": "thieu require"})])
    d = analyze(_st(), llm=llm)
    assert d.action == "finish"
    assert "Xin loi" in (d.message or "")


def test_toolcall_error_falls_back(monkeypatch):
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "S")
    llm = FakeLLM(tool_selects=[ToolCallError("no tool"), ToolCallError("no tool")])
    d = analyze(_st(), llm=llm)
    assert d.action == "finish"


def test_analyze_reloads_skill_each_call(monkeypatch):  # fact-sm-reanalyze
    loads = []
    monkeypatch.setattr("app.tools.session_manager.load_skill",
                        lambda name: loads.append(name) or "SM-SKILL")
    llm = FakeLLM(tool_selects=[("finish", {"reasoning": "x", "message": "ok"}),
                                ("finish", {"reasoning": "x", "message": "ok"})])
    st = _st()
    analyze(st, llm=llm)
    analyze(st, llm=llm)
    assert loads == ["session_manager", "session_manager"]


def test_analyze_injects_memory_blocks(monkeypatch):
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "SM-SKILL")
    llm = FakeLLM(tool_selects=[("finish", {"reasoning": "x", "message": "ok"})])
    mem = {"summary": "User xem doanh thu thang 5/2026",
           "turns": [{"user": "doanh thu thang 5?", "answer": "15 trieu"}]}
    analyze(_st("con thang truoc thi sao?"), llm=llm, memory_context=mem)
    user = llm.tool_select_calls[0]["user"]
    assert "[Tom tat hoi thoai cu]: User xem doanh thu thang 5/2026" in user
    assert "[Cac luot gan nhat]:" in user


def test_analyze_no_memory_blocks_when_absent(monkeypatch):
    monkeypatch.setattr("app.tools.session_manager.load_skill", lambda n: "SM-SKILL")
    llm = FakeLLM(tool_selects=[("finish", {"reasoning": "x", "message": "ok"})])
    analyze(_st("doanh thu quy 1"), llm=llm)
    assert "[Tom tat hoi thoai cu]" not in llm.tool_select_calls[0]["user"]


def test_decision_rejects_unregistered_tool():  # luoi 2 giu nguyen
    with pytest.raises(Exception):
        Decision.model_validate({"action": "call_tool", "tool_name": "rm_rf",
                                 "reasoning": "r"})
```

- [ ] **Step 2: Run → fail.**
- [ ] **Step 3: Viết lại `app/tools/session_manager/__init__.py`:**

```python
from __future__ import annotations
import json
import logging
from typing import Literal
from pydantic import BaseModel, ValidationError, field_validator
from app.config.llm_client import ToolCallError
from app.graph.state import SessionState
from app.harness.think_log import think
from app.registry.args import CommonArgs
from app.registry.registry import get_args_model, is_dispatchable, load_skill, render_api_tools

log = logging.getLogger(__name__)

Action = Literal["call_tool", "retry_tool", "request_clarification", "finish"]


class Decision(BaseModel):
    """Ngon ngu noi bo orchestrator — dung tu tool_call cua SM, khong con la
    format output LLM."""
    action: Action
    tool_name: str | None = None
    reasoning: str
    message: str | None = None
    resolved_require: str | None = None

    @field_validator("tool_name")
    @classmethod
    def _tool_dispatchable(cls, v, info):
        if info.data.get("action") in ("call_tool", "retry_tool"):
            if not v or not is_dispatchable(v):
                raise ValueError(f"tool_name khong hop le/khong dispatch duoc: {v!r}")
        return v


_PROMPT = ("{skill}\n\n{memory}raw_require: {raw_require}\n"
           "history: {history}\nlast_result: {last}\n\n"
           "Chon va goi DUNG 1 tool cho buoc tiep theo.")


def _memory_blocks(memory_context) -> str:
    """SM la noi duy nhat thay du cac luot verbatim (spec) — tool chi nhan summary."""
    if not memory_context:
        return ""
    parts = []
    if memory_context.get("summary"):
        parts.append(f"[Tom tat hoi thoai cu]: {memory_context['summary']}")
    if memory_context.get("turns"):
        parts.append("[Cac luot gan nhat]: "
                     + json.dumps(memory_context["turns"], ensure_ascii=False)[:6000])
    return "\n".join(parts) + "\n" if parts else ""


def _derive_action(state: SessionState, tool_name: str) -> str:
    """Goi lai cung tool ngay sau ket qua KHONG dat = retry (model khong con
    phai tu khai 'retry_tool')."""
    hist = state["history"]
    if hist and hist[-1].get("tool") == tool_name and hist[-1].get("valid") is False:
        return "retry_tool"
    return "call_tool"


def _to_decision(name: str, args: CommonArgs, state: SessionState) -> Decision:
    if name == "finish":
        return Decision(action="finish", reasoning=args.reasoning,
                        message=args.message, resolved_require=args.resolved_require)
    if name == "request_clarification":
        return Decision(action="request_clarification", reasoning=args.reasoning,
                        message=args.message, resolved_require=args.resolved_require)
    resolved = args.resolved_require or getattr(args, "require", None)
    return Decision(action=_derive_action(state, name), tool_name=name,
                    reasoning=args.reasoning, resolved_require=resolved)


def analyze(state: SessionState, *, llm, memory_context: dict | None = None) -> Decision:
    """SM doc LAI skill.md moi lan phan tich (fact-sm-reanalyze), chon hanh dong
    bang native tool-calling (tool_choice=required), role 'sm'."""
    skill = load_skill("session_manager")
    last = state["history"][-1] if state["history"] else None
    log.debug("SM analyze step=%d history_len=%d raw_require=%.100s",
              state["step_count"], len(state["history"]), state["raw_require"])
    if last:
        think("SM", 'doc lai tinh hinh: yeu cau "%.100s", da qua %d buoc, '
              "buoc gan nhat: %s%s",
              state["raw_require"], len(state["history"]),
              last.get("tool") or last.get("action"),
              "" if last.get("valid", True) else " (KHONG dat)")
    else:
        think("SM", 'nhan yeu cau moi: "%.100s" — chua co buoc nao, '
              "bat dau phan tich xem can tool gi", state["raw_require"])
    user = _PROMPT.format(skill=skill, memory=_memory_blocks(memory_context),
                          raw_require=state["raw_require"],
                          history=json.dumps(state["history"], ensure_ascii=False)[:4000],
                          last=json.dumps(last, ensure_ascii=False))
    tools = render_api_tools()
    last_err = None
    for attempt in range(2):
        try:
            name, raw_args = llm.complete_tool_select(system=skill, user=user,
                                                      tools=tools, role="sm")
            args = get_args_model(name).model_validate_json(raw_args)
        except (ToolCallError, KeyError, ValidationError, ValueError) as exc:
            last_err = exc
            log.warning("SM tool-select failed attempt=%d err=%s", attempt + 1, exc)
            user += (f"\n\n[Loi attempt truoc: {exc}. Goi dung 1 tool trong "
                     "danh sach voi args dung schema.]")
            continue
        decision = _to_decision(name, args, state)
        log.info("SM decision action=%s tool=%s reasoning=%.120s",
                 decision.action, decision.tool_name, decision.reasoning)
        think("SM", "suy nghi: %s", decision.reasoning)
        if decision.resolved_require:
            think("SM", 'hieu lai yeu cau thanh: "%.150s"', decision.resolved_require)
        if decision.action in ("call_tool", "retry_tool"):
            think("SM", "-> quyet dinh: %s %s",
                  "goi tool" if decision.action == "call_tool" else "thu lai tool",
                  decision.tool_name)
        elif decision.action == "request_clarification":
            think("SM", '-> quyet dinh: can hoi lai user — "%.150s"', decision.message)
        else:
            think("SM", "-> quyet dinh: %s", decision.action)
        return decision
    log.error("SM falling back to finish after 2 attempts last_err=%s", last_err)
    think("SM", "-> bo cuoc: 2 lan khong doc duoc quyet dinh tu LLM, ket thuc an toan")
    return Decision(action="finish", reasoning=f"SM decision loi: {last_err}",
                    message="Xin loi, he thong chua xu ly duoc yeu cau luc nay.")
```

- [ ] **Step 4: Sửa `orchestrator.py`:**
  - Xóa block `if action == "replan":` (dòng 90-95).
  - `_build_upstream(state, forward_data)` → `_build_upstream(state)`: xóa tham số + 3 dòng overlay `src`; cập nhật call site (dòng 115) thành `upstream = _build_upstream(state)`; cập nhật docstring (merge tất cả tool_results, key sau đè key trước — không còn "from").
- [ ] **Step 5: Migrate `test_orchestrator.py`:** xóa `ScriptLLM`, dùng `FakeLLM(tool_selects=[...])`. Mapping từng test:
  - happy path: `[("sql_execute", {"reasoning": "r", "require": "liet ke khach hang"}), ("data_validator", {"reasoning": "r"}), ("answer_composer", {"reasoning": "r"}), ("finish", {"reasoning": "done", "message": ""})]`
  - clarify: `[..., ("request_clarification", {"reasoning": "fail", "message": "Khoang thoi gian nao?"})]`
  - budget: `[("sql_execute", {"reasoning": "loop", "require": "x"})] * 20`
  - resume: tương tự happy bỏ bước sql.
  - `test_build_upstream_overlay_keeps_rows_from_other_tools` + `test_build_upstream_named_source_wins_on_conflict`: viết lại thành 1 test `_build_upstream(state)` merge tất cả (rows + verdict cùng có mặt); xóa test "named source wins".
  - `test_dispatch_uses_resolved_require_and_memory_summary`: đổi decision sang `("sql_execute", {"reasoning": "r", "require": "doanh thu thang 4/2026"})` và fake_dispatch key `sql_execute`; assert `captured["raw_require"] == "doanh thu thang 4/2026"`.
  - 2 test done/resume raw_require: scripted `("finish", {"reasoning": "x", "message": "..."})`.
- [ ] **Step 6: Migrate `test_e2e_happy_path.py`:** xóa `RoutingLLM`; dùng MỘT FakeLLM cho cả SM + tool:

```python
llm = FakeLLM(
    tool_selects=[("sql_execute", {"reasoning": "lay data", "require": "liet ke 5 khach hang moi nhat"}),
                  ("data_validator", {"reasoning": "validate"}),
                  ("answer_composer", {"reasoning": "soan"}),
                  ("finish", {"reasoning": "xong", "message": ""})],
    structured=[{"sql": "SELECT id, name FROM customers LIMIT 5"},
                {"ok": True},
                {"verdict": "pass", "reason": "du data"},
                {"answer": "Day la 5 khach hang.\nGợi ý: xem don hang?"}])
```

  (import `from tests.conftest import FakeLLM`; assertions giữ nguyên.)
- [ ] **Step 7: Migrate `test_e2e_memory.py`** cùng pattern Step 6 (đọc file, thay LLM giả decision-JSON bằng tool_selects + structured queue; assertions memory giữ nguyên).
- [ ] **Step 8: Run → pass:** `pytest tests/test_session_manager.py tests/test_orchestrator.py tests/test_e2e_happy_path.py tests/test_e2e_memory.py -v`
- [ ] **Step 9: Full suite → pass. Commit:**

```bash
git add -A ai_python/app/tools/session_manager/__init__.py ai_python/app/graph/orchestrator.py ai_python/tests/
git commit -m "feat(sm): decision = native tool_call (required) — xoa replan/forward_data/JSON parse"
```

---

## Task 8: skill.md × 4 — xóa "Output schema", SM viết lại luật chọn tool

**Files:**
- Modify: `ai_python/app/tools/session_manager/skill.md` (viết lại các mục Role/Nhiệm vụ/Constraints/Output/Few-shot)
- Modify: `ai_python/app/tools/sql_execute/skill.md`, `data_validator/skill.md`, `answer_composer/skill.md` (xóa mục `## Output schema`)

- [ ] **Step 1: SM skill.md** — giữ nguyên Input contract + toàn bộ 2 khối rule "resolved_require"/"XÁC ĐỊNH CHỦ THỂ THEO NGỮ CẢNH" (chỉ đổi chữ "điền `resolved_require`" thành "điền tham số `resolved_require`/`require` của tool"); thay các mục còn lại:

```markdown
## Role
Bạn là Session Manager (planner-evaluator). Bạn KHÔNG tự thực thi nghiệp vụ —
mỗi bước bạn GỌI ĐÚNG 1 TOOL trong danh sách tools được cấp (function calling).

## Nhiệm vụ
- Phân tích `raw_require`, lịch sử các bước, kết quả tool gần nhất.
- Mỗi lượt gọi đúng 1 tool: sql_execute / data_validator / answer_composer /
  finish / request_clarification. Luôn điền `reasoning` ngắn gọn.

## Constraints / Rules
- TRƯỚC TIÊN phân loại `raw_require`:
  - Chào hỏi / small talk → gọi `finish` NGAY với `message` thân thiện.
  - Câu hỏi NGOÀI phạm vi dữ liệu ERP → gọi `finish` NGAY với `message` từ chối
    lịch sự, nói rõ chỉ hỗ trợ dữ liệu ERP (doanh thu, đơn hàng, khách, tồn kho...).
  - Chỉ gọi `sql_execute` khi THẬT SỰ cần dữ liệu từ DB ERP; điền `require` =
    yêu cầu dữ liệu đã làm rõ (viết lại tự-đủ-nghĩa nếu là câu nối tiếp).
- `data_validator` PHẢI chạy và pass TRƯỚC khi gọi `answer_composer`.
- Kết quả tool gần nhất KHÔNG đạt (valid=false, lỗi DB) → gọi LẠI chính tool đó
  (hệ thống tự đếm retry; đừng lặp quá 2 lần cùng một lỗi).
- validator trả "fail" → gọi `request_clarification` hỏi lại user.
- Đã có answer hợp lệ từ answer_composer → gọi `finish`.
(+ giữ nguyên 2 khối rule resolved_require & CHỦ THỂ như bản cũ)

## Few-shot (tình huống → tool + args)
- "chào bạn" → finish(message="Chào bạn! Tôi là trợ lý dữ liệu ERP...", reasoning="chào hỏi")
- "thời tiết hôm nay?" → finish(message="Xin lỗi, tôi chỉ hỗ trợ dữ liệu ERP...", reasoning="ngoài phạm vi")
- Mới bắt đầu, cần data → sql_execute(require=<câu hỏi đã làm rõ>, reasoning="cần lấy data")
- Có rows, chưa validate → data_validator(reasoning="bắt buộc validate trước khi soạn")
- validator pass → answer_composer(reasoning="soạn trả lời từ data")
- validator fail → request_clarification(message="Bạn nói rõ khoảng thời gian?", reasoning="data không khớp")
- `[Cac luot gan nhat]` có "doanh thu tháng 5/2026 = 15 triệu", hỏi "còn tháng trước?" →
  sql_execute(require="doanh thu tháng 4/2026", reasoning="câu nối tiếp")
(+ giữ 2 ví dụ chủ thể "Dầu ăn Neptuna/Simply" cũ, đổi format JSON → dạng gọi tool như trên)
```
- [ ] **Step 2: 3 tool skill.md** — xóa mục `## Output schema` (sql_execute:~56, data_validator:~54, answer_composer:~26) và mọi câu "trả về JSON"; thay bằng 1 dòng: `## Output\nOutput trả qua structured channel (function calling) — tập trung vào đúng nghiệp vụ ở trên.` Giữ nguyên toàn bộ rule nghiệp vụ + few-shot SQL.
- [ ] **Step 3: Full suite → pass** (skill.md là data; test SM đã stub load_skill).
- [ ] **Step 4: Smoke nhanh skill mới với LLM thật** (không vào suite): chạy script Bash gọi `analyze()` với llm thật cho 2 câu: "chào bạn" (mong finish) và "sản phẩm nào đang ế" (mong sql_execute + require). In decision, che key.
- [ ] **Step 5: Commit:**

```bash
git add ai_python/app/tools/*/skill.md
git commit -m "docs(skill): SM chon tool qua function calling — xoa Output schema JSON o 4 skill"
```

---

## Task 9: Nghiệm thu grep-zero + suite + smoke E2E thật

- [ ] **Step 1: Grep-zero (PHẢI 0 hit):**

```bash
cd /d/do_an_tot_nghiep/project/ai_python
grep -rn "_coerce_json\|_parse_sql\|render_tool_catalog\|is_registered" app/ tests/   # = 0
grep -rn "Tra ve JSON\|Tra ve DUY NHAT JSON\|Output schema" app/                      # = 0
grep -rn 'startswith("```' app/                                                       # = 0
grep -rn "json.loads" app/ --include="*.py"   # chỉ: llm_client.py? (không — model_validate_json), hitl.py (snapshot)
grep -rn "llm.complete(" app/                 # chỉ: memory compact
```

  Nếu lệnh nào ra hit ngoài allowlist → quay lại task tương ứng xóa nốt.
- [ ] **Step 2: Full suite:** `pytest -q` → toàn bộ pass (mục tiêu ≥ 128).
- [ ] **Step 3: Smoke E2E thật:** chạy API local (hoặc script run_session với llm thật + executor thật DATABASE_URL_RO), hỏi "liệt kê 5 khách hàng mua nhiều nhất" → answer có dữ liệu + "Gợi ý:"; hỏi "sản phẩm nào đang ế" → SQL có LEFT JOIN. Ghi elapsed các LLM call từ log so với trước.
- [ ] **Step 4: Commit cuối + cập nhật plan checkboxes:**

```bash
git add docs/superpowers/plans/2026-06-11-native-tool-calling.md
git commit -m "docs(plan): native tool-calling hoan tat — grep-zero pass, suite xanh, smoke that OK"
```
