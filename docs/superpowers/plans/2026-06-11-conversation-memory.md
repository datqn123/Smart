# Conversation Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agentic AI nhớ hội thoại theo `thread_id` — giữ 10 lượt gần nhất verbatim, compact phần cũ thành rolling summary bằng LLM, inject vào SM (kèm query rewriting `resolved_require`) và summary xuống mọi tool.

**Architecture:** `ConversationMemory` in-memory singleton (module-level, KHÔNG tạo trong `get_deps()`). Read path: `api/app.py` lấy `get_context(thread_id)` → `run_session(memory_context=...)` → SM prompt nhận summary + turns; dispatch dùng `decision.resolved_require or raw_require` + truyền `memory_summary` xuống ToolState → prompt tool. Write path: `stream()` capture event `answer`, sau `done` → `append_turn`; quá window → `asyncio.create_task(compact)` fire-and-forget.

**Tech Stack:** Python 3.11+, FastAPI, LangGraph, pytest. LLM compact dùng role `default` (Qwen), output plain text (không JSON).

**Spec:** `docs/superpowers/specs/2026-06-11-conversation-memory-design.md`

**Chạy test:** luôn từ thư mục `ai_python`: `cd ai_python && python -m pytest tests/<file> -v`

## File map

| File | Hành động | Trách nhiệm |
|---|---|---|
| `ai_python/app/config/settings.py` | Modify | thêm `memory_window_turns`, `memory_summary_max_chars` |
| `ai_python/app/memory/__init__.py` | Rewrite | `ThreadMemory`, `ConversationMemory`, `get_memory()` singleton |
| `ai_python/app/memory/compact_prompt.md` | Create | prompt LLM compact (plain text output) |
| `ai_python/app/graph/state.py` | Modify | `ToolState.memory_summary` + param `new_tool_state` |
| `ai_python/app/graph/dispatcher.py` | Modify | nhận/truyền `memory_summary` vào payload |
| `ai_python/app/tools/__init__.py` | Modify | helper `memory_block(state)` dùng chung 3 tool |
| `ai_python/app/tools/{sql_execute,data_validator,answer_composer}/__init__.py` | Modify | thêm `{memory}` vào `_PROMPT` |
| `ai_python/app/tools/{sql_execute,data_validator,answer_composer}/skill.md` | Modify | hướng dẫn dùng `[Boi canh hoi thoai truoc]` |
| `ai_python/app/tools/session_manager/__init__.py` | Modify | `Decision.resolved_require`, `analyze(memory_context=...)` |
| `ai_python/app/tools/session_manager/skill.md` | Modify | quy tắc điền `resolved_require` + few-shot |
| `ai_python/app/graph/orchestrator.py` | Modify | `memory_context` param, resolved dispatch, done event kèm `raw_require`, restore `raw_require` từ snapshot |
| `ai_python/app/api/app.py` | Modify | `Deps.memory`, read path, write path + fire-and-forget compact |
| `ai_python/tests/test_memory.py` | Create | unit ConversationMemory |
| `ai_python/tests/test_e2e_memory.py` | Create | 2 request cùng thread |
| `ai_python/tests/{test_config_settings,test_graph_state,test_dispatcher,test_session_manager,test_orchestrator,test_api_sse}.py` | Modify | test mới cho từng thay đổi |

---

### Task 1: Settings memory

**Files:**
- Modify: `ai_python/app/config/settings.py`
- Test: `ai_python/tests/test_config_settings.py`

- [ ] **Step 1: Viết test fail** — thêm vào cuối `tests/test_config_settings.py` (theo pattern monkeypatch env sẵn có của file; nếu file đã có fixture set env bắt buộc thì tái dùng):

```python
def test_memory_settings_defaults(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://x")
    monkeypatch.setenv("LLM_API_KEY", "k")
    monkeypatch.setenv("DATABASE_URL_RO", "postgresql://x")
    s = Settings(_env_file=None)
    assert s.memory_window_turns == 10
    assert s.memory_summary_max_chars == 2000
```

- [ ] **Step 2: Chạy fail** — `cd ai_python && python -m pytest tests/test_config_settings.py -v` → FAIL (`AttributeError`/validation).

- [ ] **Step 3: Implement** — trong `settings.py`, thêm sau block `# --- Harness / budget ---` (sau `hitl_checkpoint_db`):

```python
    # --- Conversation memory ---
    memory_window_turns: int = 10
    memory_summary_max_chars: int = 2000
```

- [ ] **Step 4: Chạy pass** — `cd ai_python && python -m pytest tests/test_config_settings.py -v` → PASS.

- [ ] **Step 5: Commit** — `git add ai_python/app/config/settings.py ai_python/tests/test_config_settings.py && git commit -m "feat(memory): settings memory_window_turns + memory_summary_max_chars"`

---

### Task 2: ConversationMemory — data ops (chưa compact)

**Files:**
- Rewrite: `ai_python/app/memory/__init__.py` (hiện là docstring placeholder "DEFERRED")
- Test: `ai_python/tests/test_memory.py` (create)

- [ ] **Step 1: Viết test fail** — tạo `tests/test_memory.py`:

```python
from app.memory import ConversationMemory


def test_append_turn_and_get_context():
    m = ConversationMemory(window=10)
    m.append_turn("t1", "cau hoi 1", "tra loi 1")
    ctx = m.get_context("t1")
    assert ctx["turns"] == [{"user": "cau hoi 1", "answer": "tra loi 1"}]
    assert ctx["summary"] is None


def test_get_context_unknown_thread_is_empty():
    m = ConversationMemory(window=10)
    assert m.get_context("nope") == {"turns": [], "summary": None}


def test_get_context_does_not_leak_reference():
    m = ConversationMemory(window=10)
    m.append_turn("t1", "u", "a")
    ctx = m.get_context("t1")
    ctx["turns"].append({"user": "x", "answer": "y"})
    ctx["turns"][0]["user"] = "sua doi"
    assert m.get_context("t1")["turns"] == [{"user": "u", "answer": "a"}]


def test_threads_isolated():
    m = ConversationMemory(window=10)
    m.append_turn("t1", "u1", "a1")
    m.append_turn("t2", "u2", "a2")
    assert m.get_context("t1")["turns"][0]["user"] == "u1"
    assert m.get_context("t2")["turns"][0]["user"] == "u2"


def test_needs_compact_only_above_window():
    m = ConversationMemory(window=2)
    m.append_turn("t1", "u1", "a1")
    m.append_turn("t1", "u2", "a2")
    assert m.needs_compact("t1") is False
    m.append_turn("t1", "u3", "a3")
    assert m.needs_compact("t1") is True


def test_needs_compact_unknown_thread_false():
    m = ConversationMemory(window=2)
    assert m.needs_compact("nope") is False
```

- [ ] **Step 2: Chạy fail** — `cd ai_python && python -m pytest tests/test_memory.py -v` → FAIL (`ImportError: ConversationMemory`).

- [ ] **Step 3: Implement** — thay toàn bộ `app/memory/__init__.py`:

```python
"""Conversation memory theo thread_id (in-memory — chap nhan mat khi restart).

Giu `window` luot (user -> answer) verbatim; qua window thi compact() gop
phan cu vao rolling summary bang LLM (prompt: compact_prompt.md).

Singleton module-level qua get_memory() — KHONG tao trong get_deps() vi
FastAPI Depends chay moi request se reset store (PendingStore song duoc vi
backed boi SQLite).
"""
from __future__ import annotations
import asyncio
import copy
import logging
from typing import TypedDict

log = logging.getLogger(__name__)


class ThreadMemory(TypedDict):
    turns: list[dict]      # [{"user": str, "answer": str}]
    summary: str | None    # rolling summary, None khi chua compact


class ConversationMemory:
    def __init__(self, *, window: int = 10, summary_max_chars: int = 2000):
        self._window = window
        self._summary_max_chars = summary_max_chars
        self._store: dict[str, ThreadMemory] = {}
        self._lock = asyncio.Lock()  # chi guard compact-vs-compact (Task 3)

    def get_context(self, thread_id: str) -> ThreadMemory:
        mem = self._store.get(thread_id)
        if mem is None:
            return ThreadMemory(turns=[], summary=None)
        return ThreadMemory(turns=copy.deepcopy(mem["turns"]), summary=mem["summary"])

    def append_turn(self, thread_id: str, user: str, answer: str) -> None:
        # Sync, khong await -> atomic tren event loop don, khong can lock.
        mem = self._store.setdefault(thread_id, ThreadMemory(turns=[], summary=None))
        mem["turns"].append({"user": user, "answer": answer})

    def needs_compact(self, thread_id: str) -> bool:
        mem = self._store.get(thread_id)
        return mem is not None and len(mem["turns"]) > self._window
```

- [ ] **Step 4: Chạy pass** — `cd ai_python && python -m pytest tests/test_memory.py -v` → PASS (6 test).

- [ ] **Step 5: Commit** — `git add ai_python/app/memory/__init__.py ai_python/tests/test_memory.py && git commit -m "feat(memory): ConversationMemory in-memory store (append/get_context/needs_compact)"`

---

### Task 3: compact() + compact_prompt.md + get_memory()

**Files:**
- Modify: `ai_python/app/memory/__init__.py`
- Create: `ai_python/app/memory/compact_prompt.md`
- Test: `ai_python/tests/test_memory.py`

- [ ] **Step 1: Viết test fail** — thêm vào `tests/test_memory.py`:

```python
import asyncio


class _CompactLLM:
    def __init__(self, reply="Tom tat moi.", fail=False):
        self.reply, self.fail, self.calls = reply, fail, []

    def complete(self, *, system, user, role="default", temperature=None):
        self.calls.append({"system": system, "user": user, "role": role})
        if self.fail:
            raise RuntimeError("LLM down")
        return self.reply


def test_compact_merges_overflow_and_keeps_window():
    m = ConversationMemory(window=2)
    for i in range(4):
        m.append_turn("t1", f"cauhoi{i}", f"traloi{i}")
    llm = _CompactLLM(reply="  Tom tat moi.  ")
    asyncio.run(m.compact("t1", llm=llm))
    ctx = m.get_context("t1")
    assert ctx["summary"] == "Tom tat moi."          # strip
    assert ctx["turns"] == [{"user": "cauhoi2", "answer": "traloi2"},
                            {"user": "cauhoi3", "answer": "traloi3"}]
    call = llm.calls[0]
    assert call["role"] == "default"
    assert "(chua co)" in call["user"]                # summary cu rong
    assert "cauhoi0" in call["user"] and "cauhoi1" in call["user"]  # overflow vao prompt
    assert "cauhoi3" not in call["user"]              # luot trong window KHONG gop


def test_compact_second_round_merges_old_summary():
    m = ConversationMemory(window=1)
    m.append_turn("t1", "u0", "a0")
    m.append_turn("t1", "u1", "a1")
    asyncio.run(m.compact("t1", llm=_CompactLLM(reply="S1")))
    m.append_turn("t1", "u2", "a2")
    llm = _CompactLLM(reply="S2")
    asyncio.run(m.compact("t1", llm=llm))
    assert "S1" in llm.calls[0]["user"]               # summary cu di vao prompt merge
    assert m.get_context("t1")["summary"] == "S2"


def test_compact_llm_error_degrades_keeps_summary_still_drops():
    m = ConversationMemory(window=1)
    m.append_turn("t1", "u0", "a0")
    m.append_turn("t1", "u1", "a1")
    asyncio.run(m.compact("t1", llm=_CompactLLM(reply="S1")))
    m.append_turn("t1", "u2", "a2")
    asyncio.run(m.compact("t1", llm=_CompactLLM(fail=True)))  # khong duoc raise
    ctx = m.get_context("t1")
    assert ctx["summary"] == "S1"                                # giu summary cu
    assert ctx["turns"] == [{"user": "u2", "answer": "a2"}]      # van drop luot tran


def test_compact_truncates_to_summary_max_chars():
    m = ConversationMemory(window=1, summary_max_chars=10)
    m.append_turn("t1", "u0", "a0")
    m.append_turn("t1", "u1", "a1")
    asyncio.run(m.compact("t1", llm=_CompactLLM(reply="x" * 50)))
    assert len(m.get_context("t1")["summary"]) == 10


def test_compact_noop_within_window():
    m = ConversationMemory(window=10)
    m.append_turn("t1", "u", "a")
    llm = _CompactLLM()
    asyncio.run(m.compact("t1", llm=llm))
    assert llm.calls == []
```

- [ ] **Step 2: Chạy fail** — `cd ai_python && python -m pytest tests/test_memory.py -v` → FAIL (`AttributeError: compact`).

- [ ] **Step 3: Tạo `app/memory/compact_prompt.md`** (nội dung đã chốt trong spec — plain text output):

```markdown
<!-- ai_python/app/memory/compact_prompt.md -->
# Compact: tóm tắt hội thoại cũ

## Role
Bạn là người ghi chép hội thoại của trợ lý dữ liệu ERP. Gộp `[Summary cu]` và
`[Cac luot can gop]` thành MỘT bản tóm tắt mới bằng tiếng Việt.

## Phải GIỮ (ưu tiên từ trên xuống)
1. Chủ đề user đang phân tích — đang xem báo cáo gì, về đối tượng nào
   (doanh thu, tồn kho, công nợ, khách hàng, đơn hàng...).
2. Tham số đã chốt — khoảng thời gian, bộ lọc, kênh bán, chi nhánh...
   (để câu hỏi nối tiếp như "còn tháng trước?" hiểu được).
3. Số liệu kết quả chính trong câu trả lời — ví dụ
   "doanh thu tháng 5/2026 = 15.000.000đ" (phục vụ câu hỏi so sánh nối tiếp).
4. Việc còn dang dở — yêu cầu chưa được trả lời trọn vẹn, câu hỏi làm rõ còn treo.

## Phải BỎ
- Chào hỏi, đưa đẩy, câu chữ trình bày.
- Bảng dữ liệu chi tiết / danh sách dòng dài — chỉ giữ con số tổng hợp
  và nhận xét chính.
- Chi tiết kỹ thuật: tên cột, câu SQL, tên tool.

## Quy tắc
- Summary cũ được NÉN TIẾP (thông tin càng cũ càng gọn); các lượt mới gộp vào
  được giữ chi tiết hơn.
- KHÔNG bịa thông tin không có trong input.
- Kết quả ≤ 1500 ký tự.
- Trả về DUY NHẤT đoạn văn tóm tắt (plain text tiếng Việt).
  KHÔNG JSON, KHÔNG markdown heading, KHÔNG lời giải thích thêm.

## Ví dụ

Input:
[Summary cu]:
(chua co)
[Cac luot can gop]:
[{"user": "doanh thu tháng 5/2026 bao nhiêu?", "answer": "Doanh thu tháng 5/2026 là 15.000.000đ. Gợi ý: xem theo kênh bán?"}]

Output:
User đang xem doanh thu. Đã trả lời: doanh thu tháng 5/2026 = 15.000.000đ. Chưa xem chi tiết theo kênh bán.

Input:
[Summary cu]:
User đang xem doanh thu. Đã trả lời: doanh thu tháng 5/2026 = 15.000.000đ.
[Cac luot can gop]:
[{"user": "còn tháng 4 thì sao?", "answer": "Doanh thu tháng 4/2026 là 12.000.000đ, thấp hơn tháng 5."}]

Output:
User đang so sánh doanh thu các tháng: tháng 5/2026 = 15.000.000đ, tháng 4/2026 = 12.000.000đ (tháng 5 cao hơn).
```

- [ ] **Step 4: Implement compact** — trong `app/memory/__init__.py` thêm import `json`, `Path` và:

```python
import json
from pathlib import Path

_PROMPT_PATH = Path(__file__).parent / "compact_prompt.md"


def load_compact_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")
```

và method trong `ConversationMemory`:

```python
    async def compact(self, thread_id: str, *, llm) -> None:
        """Gop cac luot tran ngoai window vao rolling summary (1 LLM call).

        Degrade an toan: LLM loi -> giu summary cu, VAN drop luot tran,
        khong raise (duoc goi fire-and-forget tu api/app.py)."""
        async with self._lock:
            mem = self._store.get(thread_id)
            if mem is None or len(mem["turns"]) <= self._window:
                return
            overflow = list(mem["turns"][:-self._window])
            prompt = load_compact_prompt()
            user = (f"[Summary cu]:\n{mem['summary'] or '(chua co)'}\n\n"
                    f"[Cac luot can gop]:\n{json.dumps(overflow, ensure_ascii=False)}")
            try:
                # llm.complete la sync (openai SDK) -> to_thread de khong block loop
                new_summary = await asyncio.to_thread(
                    llm.complete, system=prompt, user=user, role="default")
                mem["summary"] = new_summary.strip()[:self._summary_max_chars]
                log.info("memory compact thread=%s dropped=%d summary_len=%d",
                         thread_id, len(overflow), len(mem["summary"]))
            except Exception as exc:
                log.warning("memory compact failed thread=%s: %s — giu summary cu",
                            thread_id, exc)
            # Drop theo len(overflow) da chot truoc LLM call — luot append
            # trong luc LLM dang chay van duoc giu nguyen.
            mem["turns"] = mem["turns"][len(overflow):]
```

và singleton cuối file:

```python
from app.config.settings import get_settings

_memory: ConversationMemory | None = None


def get_memory() -> ConversationMemory:
    global _memory
    if _memory is None:
        s = get_settings()
        _memory = ConversationMemory(window=s.memory_window_turns,
                                     summary_max_chars=s.memory_summary_max_chars)
    return _memory
```

(Đặt import `get_settings` trong thân `get_memory()` nếu import vòng/top-level gây lỗi env khi test — `Settings` đòi `LLM_BASE_URL` v.v. chỉ khi instantiate, import thì an toàn.)

- [ ] **Step 5: Chạy pass** — `cd ai_python && python -m pytest tests/test_memory.py -v` → PASS (11 test).

- [ ] **Step 6: Commit** — `git add ai_python/app/memory/ ai_python/tests/test_memory.py && git commit -m "feat(memory): LLM rolling-summary compact + compact_prompt.md + get_memory singleton"`

---

### Task 4: ToolState.memory_summary + dispatcher

**Files:**
- Modify: `ai_python/app/graph/state.py`
- Modify: `ai_python/app/graph/dispatcher.py`
- Test: `ai_python/tests/test_graph_state.py`, `ai_python/tests/test_dispatcher.py`

- [ ] **Step 1: Viết test fail** — thêm vào `tests/test_graph_state.py`:

```python
def test_new_tool_state_memory_summary_default_none():
    st = new_tool_state(tool_name="x", raw_require="r")
    assert st["memory_summary"] is None


def test_new_tool_state_memory_summary_set():
    st = new_tool_state(tool_name="x", raw_require="r", memory_summary="tom tat")
    assert st["memory_summary"] == "tom tat"
```

thêm vào `tests/test_dispatcher.py` (theo pattern import sẵn có của file):

```python
def test_dispatch_passes_memory_summary_into_payload(monkeypatch):
    captured = {}

    def fake_invoke(tool_name, payload, *, llm, deps):
        captured.update(payload)
        return {"output": {}, "valid": True, "validation_error": None}

    monkeypatch.setattr("app.graph.dispatcher._invoke_subgraph", fake_invoke)
    dispatch("sql_execute", raw_require="r", upstream_data={}, llm=None, deps={},
             memory_summary="tom tat")
    assert captured["memory_summary"] == "tom tat"


def test_dispatch_memory_summary_default_none(monkeypatch):
    captured = {}

    def fake_invoke(tool_name, payload, *, llm, deps):
        captured.update(payload)
        return {"output": {}, "valid": True, "validation_error": None}

    monkeypatch.setattr("app.graph.dispatcher._invoke_subgraph", fake_invoke)
    dispatch("sql_execute", raw_require="r", upstream_data={}, llm=None, deps={})
    assert captured["memory_summary"] is None
```

- [ ] **Step 2: Chạy fail** — `cd ai_python && python -m pytest tests/test_graph_state.py tests/test_dispatcher.py -v` → FAIL.

- [ ] **Step 3: Implement `state.py`** — `ToolState` thêm field sau `upstream_data`:

```python
    memory_summary: str | None       # summary hoi thoai cu (None = khong co)
```

`new_tool_state` thành:

```python
def new_tool_state(*, tool_name: str, raw_require: str,
                   upstream_data: dict | None = None,
                   memory_summary: str | None = None) -> ToolState:
    return ToolState(tool_name=tool_name, raw_require=raw_require,
                     upstream_data=upstream_data or {},
                     memory_summary=memory_summary, skill="", output=None,
                     valid=False, validation_error=None, attempt=0)
```

- [ ] **Step 4: Implement `dispatcher.py`** — `_invoke_subgraph` đổi dòng tạo state:

```python
    state = new_tool_state(tool_name=tool_name, raw_require=payload["raw_require"],
                           upstream_data=payload["upstream_data"],
                           memory_summary=payload.get("memory_summary"))
```

`dispatch` thêm param + payload:

```python
def dispatch(tool_name: str, *, raw_require: str, upstream_data: dict[str, Any],
             llm, deps: dict, validator_passed: bool = True,
             memory_summary: str | None = None) -> dict:
```

```python
    payload = {"raw_require": raw_require, "upstream_data": upstream_data,
               "memory_summary": memory_summary}
```

- [ ] **Step 5: Chạy pass** — `cd ai_python && python -m pytest tests/test_graph_state.py tests/test_dispatcher.py tests/test_subgraph.py -v` → PASS.

- [ ] **Step 6: Commit** — `git add ai_python/app/graph/state.py ai_python/app/graph/dispatcher.py ai_python/tests/test_graph_state.py ai_python/tests/test_dispatcher.py && git commit -m "feat(memory): memory_summary chay qua dispatcher -> ToolState"`

---

### Task 5: memory_block helper + prompt 3 tool + skill.md

**Files:**
- Modify: `ai_python/app/tools/__init__.py` (hiện rỗng)
- Modify: `ai_python/app/tools/sql_execute/__init__.py`, `ai_python/app/tools/data_validator/__init__.py`, `ai_python/app/tools/answer_composer/__init__.py`
- Modify: `ai_python/app/tools/sql_execute/skill.md`, `ai_python/app/tools/data_validator/skill.md`, `ai_python/app/tools/answer_composer/skill.md`
- Test: `ai_python/tests/test_tool_sql_execute.py`, `ai_python/tests/test_tool_data_validator.py`, `ai_python/tests/test_tool_answer_composer.py`

- [ ] **Step 1: Viết test fail** — thêm vào `tests/test_tool_sql_execute.py` (dùng fixture `stub_sql` sẵn có; nếu fake LLM sẵn có của file không ghi prompt thì dùng `_RecLLM` dưới đây):

```python
class _RecLLM:
    def __init__(self, reply):
        self.reply, self.seen = reply, []

    def complete(self, *, system, user, role="default", temperature=None):
        self.seen.append(user)
        return self.reply


def test_prompt_has_memory_block_when_summary(stub_sql):
    llm = _RecLLM(json.dumps({"sql": "SELECT 1"}))
    st = new_tool_state(tool_name="sql_execute", raw_require="con thang truoc?",
                        memory_summary="User dang xem doanh thu thang 5/2026")
    st["skill"] = "SKILL"
    execute(st, llm=llm, executor=stub_sql)
    assert "[Boi canh hoi thoai truoc]: User dang xem doanh thu thang 5/2026" in llm.seen[0]


def test_prompt_no_memory_block_when_none(stub_sql):
    llm = _RecLLM(json.dumps({"sql": "SELECT 1"}))
    st = new_tool_state(tool_name="sql_execute", raw_require="x")
    st["skill"] = "SKILL"
    execute(st, llm=llm, executor=stub_sql)
    assert "[Boi canh hoi thoai truoc]" not in llm.seen[0]
```

Tương tự thêm vào `tests/test_tool_data_validator.py` (reply `json.dumps({"verdict": "pass", "reason": "ok"})`, gọi `execute(st, llm=llm)`) và `tests/test_tool_answer_composer.py` (reply `json.dumps({"answer": "X.\nGợi ý: tiep?"})`, gọi `execute(st, llm=llm)`) — cùng 2 assert có/không khối bối cảnh.

- [ ] **Step 2: Chạy fail** — `cd ai_python && python -m pytest tests/test_tool_sql_execute.py tests/test_tool_data_validator.py tests/test_tool_answer_composer.py -v` → FAIL (thiếu khối trong prompt).

- [ ] **Step 3: Implement helper** — `app/tools/__init__.py`:

```python
from __future__ import annotations


def memory_block(state) -> str:
    """Khoi boi canh hoi thoai cho prompt tool. Rong khi khong co summary —
    chi summary ngan xuong tool, KHONG nhet 10 luot verbatim (spec)."""
    summary = state.get("memory_summary")
    if not summary:
        return ""
    return f"[Boi canh hoi thoai truoc]: {summary}\n"
```

- [ ] **Step 4: Sửa 3 tool** — mỗi tool import `from app.tools import memory_block`, thêm `{memory}` vào `_PROMPT` và `memory=memory_block(state)` vào `.format(...)`:

`sql_execute/__init__.py`:

```python
_PROMPT = ("{skill}\n\n--- YEU CAU ---\nraw_require: {raw_require}\n"
           "upstream_data: {upstream}\n{memory}\nTra ve JSON {{\"sql\": \"...\"}}.")
```

```python
    user = _PROMPT.format(skill=state["skill"], raw_require=state["raw_require"],
                          upstream=json.dumps(state["upstream_data"], ensure_ascii=False),
                          memory=memory_block(state))
```

`data_validator/__init__.py`:

```python
_PROMPT = ("{skill}\n\n--- KIEM DINH ---\nraw_require: {raw_require}\n"
           "data: {data}\n{memory}\nTra ve JSON {{\"verdict\":\"pass|fail\",\"reason\":\"...\"}}.")
```

```python
    user = _PROMPT.format(skill=state["skill"], raw_require=state["raw_require"],
                          data=json.dumps(data, ensure_ascii=False)[:4000],
                          memory=memory_block(state))
```

`answer_composer/__init__.py`:

```python
_PROMPT = ("{skill}\n\n--- SOAN TRA LOI ---\nraw_require: {raw_require}\n"
           "data: {data}\n{memory}\nTra ve JSON {{\"answer\":\"...\"}}, "
           "ket thuc bang dong bat dau 'Gợi ý:'.")
```

```python
    user = _PROMPT.format(skill=state["skill"], raw_require=state["raw_require"],
                          data=json.dumps(state["upstream_data"], ensure_ascii=False)[:4000],
                          memory=memory_block(state))
```

- [ ] **Step 5: Cập nhật 3 skill.md** — thêm vào cuối mục `## Input contract` của cả 3 file dòng:

```markdown
- `[Boi canh hoi thoai truoc]: str` — (optional) tóm tắt hội thoại cũ. Khi
  `raw_require` tham chiếu ngữ cảnh trước ("còn tháng trước?", "khách đó",
  "so với lúc nãy"), dùng bối cảnh này để hiểu đúng ý; nếu mâu thuẫn,
  ưu tiên `raw_require` hiện tại.
```

- [ ] **Step 6: Chạy pass** — `cd ai_python && python -m pytest tests/test_tool_sql_execute.py tests/test_tool_data_validator.py tests/test_tool_answer_composer.py -v` → PASS.

- [ ] **Step 7: Commit** — `git add ai_python/app/tools/ ai_python/tests/test_tool_*.py && git commit -m "feat(memory): memory_block helper + khoi boi canh trong prompt 3 tool + skill.md"`

---

### Task 6: Session Manager — resolved_require + memory blocks

**Files:**
- Modify: `ai_python/app/tools/session_manager/__init__.py`
- Modify: `ai_python/app/tools/session_manager/skill.md`
- Test: `ai_python/tests/test_session_manager.py`

- [ ] **Step 1: Viết test fail** — thêm vào `tests/test_session_manager.py` (theo pattern fake LLM sẵn có của file; dưới đây dùng fake tự ghi calls):

```python
class _MemLLM:
    def __init__(self, reply):
        self.reply, self.calls = reply, []

    def complete(self, *, system, user, role="default", temperature=None):
        self.calls.append({"system": system, "user": user, "role": role})
        return self.reply


def test_analyze_injects_memory_blocks():
    llm = _MemLLM(json.dumps({"action": "finish", "reasoning": "x", "message": "ok"}))
    state = new_session_state(raw_require="con thang truoc thi sao?", thread_id="t")
    mem = {"summary": "User xem doanh thu thang 5/2026",
           "turns": [{"user": "doanh thu thang 5?", "answer": "15 trieu"}]}
    analyze(state, llm=llm, memory_context=mem)
    user = llm.calls[0]["user"]
    assert "[Tom tat hoi thoai cu]: User xem doanh thu thang 5/2026" in user
    assert "[Cac luot gan nhat]:" in user
    assert "doanh thu thang 5?" in user


def test_analyze_no_memory_blocks_when_absent():
    llm = _MemLLM(json.dumps({"action": "finish", "reasoning": "x", "message": "ok"}))
    state = new_session_state(raw_require="doanh thu quy 1", thread_id="t")
    analyze(state, llm=llm)            # khong truyen memory_context
    user = llm.calls[0]["user"]
    assert "[Tom tat hoi thoai cu]" not in user
    assert "[Cac luot gan nhat]" not in user


def test_decision_parses_resolved_require():
    llm = _MemLLM(json.dumps({
        "action": "call_tool", "tool_name": "sql_execute", "forward_data": {},
        "reasoning": "noi tiep", "message": None,
        "resolved_require": "doanh thu thang 4/2026"}))
    state = new_session_state(raw_require="con thang truoc thi sao?", thread_id="t")
    d = analyze(state, llm=llm)
    assert d.resolved_require == "doanh thu thang 4/2026"


def test_decision_resolved_require_default_none():
    llm = _MemLLM(json.dumps({"action": "finish", "reasoning": "x", "message": "ok"}))
    d = analyze(new_session_state(raw_require="x", thread_id="t"), llm=llm)
    assert d.resolved_require is None
```

- [ ] **Step 2: Chạy fail** — `cd ai_python && python -m pytest tests/test_session_manager.py -v` → FAIL.

- [ ] **Step 3: Implement** — trong `session_manager/__init__.py`:

`Decision` thêm field cuối:

```python
    resolved_require: str | None = None   # SM viet lai cau hoi noi tiep tu-du-nghia
```

`_PROMPT` thành:

```python
_PROMPT = ("{skill}\n\n{catalog}\n\n{memory}raw_require: {raw_require}\n"
           "history: {history}\nlast_result: {last}\n\n"
           "Tra ve DUY NHAT JSON theo Output schema.")
```

thêm helper:

```python
def _memory_blocks(memory_context) -> str:
    """SM la noi duy nhat thay du 10 luot verbatim (spec) — tool chi nhan summary."""
    if not memory_context:
        return ""
    parts = []
    if memory_context.get("summary"):
        parts.append(f"[Tom tat hoi thoai cu]: {memory_context['summary']}")
    if memory_context.get("turns"):
        parts.append("[Cac luot gan nhat]: "
                     + json.dumps(memory_context["turns"], ensure_ascii=False)[:6000])
    return "\n".join(parts) + "\n" if parts else ""
```

`analyze` signature + format:

```python
def analyze(state: SessionState, *, llm, memory_context: dict | None = None) -> Decision:
```

```python
    user = _PROMPT.format(skill=skill, catalog=render_tool_catalog(),
                          memory=_memory_blocks(memory_context),
                          raw_require=state["raw_require"],
                          history=json.dumps(state["history"], ensure_ascii=False)[:4000],
                          last=json.dumps(last, ensure_ascii=False))
```

- [ ] **Step 4: Cập nhật `session_manager/skill.md`:**

Mục `## Input contract` thêm:

```markdown
- `[Tom tat hoi thoai cu]: str` — (optional) rolling summary các lượt cũ.
- `[Cac luot gan nhat]: list` — (optional) các lượt (user → answer) gần nhất.
```

Mục `## Constraints / Rules` thêm bullet:

```markdown
- Khi `raw_require` tham chiếu hội thoại cũ (vd "còn tháng trước?", "thế còn X?",
  "so với lúc nãy", đại từ thiếu ngữ cảnh) → PHẢI điền `resolved_require` = câu
  hỏi viết lại TỰ-ĐỦ-NGHĨA dựa trên `[Tom tat hoi thoai cu]` / `[Cac luot gan nhat]`.
  Nếu `raw_require` đã tự đủ nghĩa → `resolved_require: null`.
```

Mục `## Output schema` đổi ví dụ JSON thành:

```json
{"action":"call_tool","tool_name":"sql_execute","forward_data":{},"reasoning":"...","message":null,"resolved_require":null}
```

và thêm chú thích:

```markdown
- `resolved_require`: câu hỏi đã viết lại tự-đủ-nghĩa (chỉ khi raw_require
  tham chiếu hội thoại cũ; ngược lại để null).
```

Mục `## Few-shot examples` thêm:

```markdown
- `[Cac luot gan nhat]` có "doanh thu tháng 5/2026 = 15 triệu", raw_require="còn tháng trước thì sao?" → `{"action":"call_tool","tool_name":"sql_execute","forward_data":{},"reasoning":"Câu nối tiếp — tháng trước của tháng 5/2026 là tháng 4/2026","message":null,"resolved_require":"doanh thu tháng 4/2026"}`
```

- [ ] **Step 5: Chạy pass** — `cd ai_python && python -m pytest tests/test_session_manager.py -v` → PASS.

- [ ] **Step 6: Commit** — `git add ai_python/app/tools/session_manager/ ai_python/tests/test_session_manager.py && git commit -m "feat(memory): SM nhan memory_context + viet lai cau hoi noi tiep (resolved_require)"`

---

### Task 7: Orchestrator — memory_context, resolved dispatch, done kèm raw_require

**Files:**
- Modify: `ai_python/app/graph/orchestrator.py`
- Test: `ai_python/tests/test_orchestrator.py`

- [ ] **Step 1: Viết test fail** — thêm vào `tests/test_orchestrator.py` (tái dùng `_SM`, `_collect`, cách chạy async sẵn có của file):

```python
def test_dispatch_uses_resolved_require_and_memory_summary(monkeypatch):
    captured = {}

    def fake_dispatch(tool, *, raw_require, upstream_data, llm, deps,
                      validator_passed=True, memory_summary=None):
        captured["raw_require"] = raw_require
        captured["memory_summary"] = memory_summary
        return {"output": {"verdict": "pass", "reason": "ok"},
                "valid": True, "validation_error": None}

    monkeypatch.setattr("app.graph.orchestrator.dispatch", fake_dispatch)
    sm = _SM([json.dumps({"action": "call_tool", "tool_name": "data_validator",
                          "forward_data": {}, "reasoning": "r", "message": None,
                          "resolved_require": "doanh thu thang 4/2026"}),
              json.dumps({"action": "finish", "forward_data": {},
                          "reasoning": "xong", "message": "ok"})])
    ctx = TurnContext(raw_require="con thang truoc?", user_id="u", thread_id="t")
    mem = {"summary": "dang xem doanh thu thang 5/2026", "turns": []}
    asyncio.run(_collect(run_session(ctx, llm_sm=sm, llm_tool=None, deps={},
                                     memory_context=mem)))
    assert captured["raw_require"] == "doanh thu thang 4/2026"
    assert captured["memory_summary"] == "dang xem doanh thu thang 5/2026"


def test_done_event_contains_raw_require():
    sm = _SM([json.dumps({"action": "finish", "forward_data": {},
                          "reasoning": "x", "message": "tra loi"})])
    ctx = TurnContext(raw_require="cau hoi goc", user_id="u", thread_id="t")
    events = asyncio.run(_collect(run_session(ctx, llm_sm=sm, llm_tool=None, deps={})))
    done = [e for e in events if e["type"] == "done"][0]
    assert done["data"]["raw_require"] == "cau hoi goc"


def test_resume_restores_raw_require_from_snapshot():
    sm = _SM([json.dumps({"action": "finish", "forward_data": {},
                          "reasoning": "x", "message": "ok"})])
    ctx = TurnContext(raw_require="thang 4", user_id="u", thread_id="t",
                      clarification_response="thang 4")
    snap = {"raw_require": "doanh thu", "tool_results": {}, "history": [],
            "retry_counts": {}}
    events = asyncio.run(_collect(run_session(ctx, llm_sm=sm, llm_tool=None, deps={},
                                              resume_snapshot=snap)))
    done = [e for e in events if e["type"] == "done"][0]
    assert done["data"]["raw_require"].startswith("doanh thu")
    assert "[Bo sung tu user]: thang 4" in done["data"]["raw_require"]
```

- [ ] **Step 2: Chạy fail** — `cd ai_python && python -m pytest tests/test_orchestrator.py -v` → FAIL.

- [ ] **Step 3: Implement `orchestrator.py`:**

Signature:

```python
async def run_session(ctx: TurnContext, *, llm_sm, llm_tool, deps: dict,
                      max_steps: int = 6, retry_cap: int = 2,
                      resume_snapshot: dict | None = None,
                      pending_store=None,
                      memory_context: dict | None = None
                      ) -> AsyncGenerator[dict, None]:
```

Trong block `if resume_snapshot is not None:` thêm (TRƯỚC dòng append clarification):

```python
        # Khoi phuc cau hoi goc — ctx.raw_require luc resume chi la cau tra loi
        # clarify; memory write path can luot gop "cau goc + bo sung" (spec).
        state["raw_require"] = resume_snapshot.get("raw_require") or state["raw_require"]
```

Gọi SM:

```python
        decision = analyze(state, llm=llm_sm, memory_context=memory_context)
```

Dispatch (thay block hiện tại):

```python
        require = decision.resolved_require or state["raw_require"]
        if decision.resolved_require:
            log.info("[%s] resolved_require: %.120s", ctx.thread_id, decision.resolved_require)
        upstream = _build_upstream(state, decision.forward_data)
        log.info("[%s] step=%d dispatch tool=%s", ctx.thread_id, state["step_count"], tool)
        yield _event("tool_call", {"tool_name": tool, "reasoning": decision.reasoning})
        try:
            result = dispatch(tool, raw_require=require, upstream_data=upstream,
                              llm=llm_tool, deps=deps, validator_passed=validator_passed,
                              memory_summary=(memory_context or {}).get("summary"))
```

Done event:

```python
        yield _event("done", {"thread_id": ctx.thread_id,
                              "raw_require": state["raw_require"]})
```

- [ ] **Step 4: Chạy pass** — `cd ai_python && python -m pytest tests/test_orchestrator.py tests/test_hitl.py tests/test_e2e_happy_path.py -v` → PASS (test cũ không vỡ).

- [ ] **Step 5: Commit** — `git add ai_python/app/graph/orchestrator.py ai_python/tests/test_orchestrator.py && git commit -m "feat(memory): orchestrator nhan memory_context, dispatch resolved_require, done kem raw_require"`

---

### Task 8: API write path — Deps.memory + append sau done + fire-and-forget compact

**Files:**
- Modify: `ai_python/app/api/app.py`
- Test: `ai_python/tests/test_api_sse.py`

- [ ] **Step 1: Viết test fail** — trong `tests/test_api_sse.py`: thêm import `from app.memory import ConversationMemory`; trong `_FakeDeps.__init__` thêm `self.memory = ConversationMemory(window=10)`; thêm test:

```python
def _client_with_deps(monkeypatch, fake_run_session):
    monkeypatch.setattr("app.api.app.run_session", fake_run_session)
    app = create_app()
    deps = _FakeDeps()
    app.dependency_overrides[get_deps] = lambda: deps
    return TestClient(app), deps


def test_chat_writes_memory_after_done(monkeypatch):
    async def fake_run_session(ctx, **kw):
        yield {"type": "answer", "data": {"text": "Doanh thu la 100."}}
        yield {"type": "done", "data": {"thread_id": ctx.thread_id,
                                        "raw_require": ctx.raw_require}}
    client, deps = _client_with_deps(monkeypatch, fake_run_session)
    client.post(CHAT_URL,
                json={"message": "doanh thu", "metadata": {"thread_id": "t-mem"}},
                headers={"Authorization": f"Bearer {_token()}"})
    assert deps.memory.get_context("t-mem")["turns"] == [
        {"user": "doanh thu", "answer": "Doanh thu la 100."}]


def test_chat_clarify_does_not_write_memory(monkeypatch):
    async def fake_run_session(ctx, **kw):
        yield {"type": "clarify", "data": {"message": "thang nao?",
                                           "thread_id": ctx.thread_id}}
    client, deps = _client_with_deps(monkeypatch, fake_run_session)
    client.post(CHAT_URL,
                json={"message": "doanh thu", "metadata": {"thread_id": "t-mem2"}},
                headers={"Authorization": f"Bearer {_token()}"})
    assert deps.memory.get_context("t-mem2")["turns"] == []


def test_chat_passes_memory_context_to_run_session(monkeypatch):
    seen = {}

    async def fake_run_session(ctx, **kw):
        seen["memory_context"] = kw.get("memory_context")
        yield {"type": "done", "data": {"thread_id": ctx.thread_id,
                                        "raw_require": ctx.raw_require}}
    client, deps = _client_with_deps(monkeypatch, fake_run_session)
    deps.memory.append_turn("t-mem3", "cau 1", "tra loi 1")
    client.post(CHAT_URL,
                json={"message": "cau 2", "metadata": {"thread_id": "t-mem3"}},
                headers={"Authorization": f"Bearer {_token()}"})
    assert seen["memory_context"]["turns"][0]["user"] == "cau 1"
```

- [ ] **Step 2: Chạy fail** — `cd ai_python && python -m pytest tests/test_api_sse.py -v` → FAIL.

- [ ] **Step 3: Implement `api/app.py`:**

Imports thêm:

```python
import asyncio
from app.memory import ConversationMemory, get_memory
```

Module-level (gần `log = ...`):

```python
# Giu ref task compact fire-and-forget — tranh bi GC giua chung.
_bg_tasks: set[asyncio.Task] = set()
```

`Deps` thêm field cuối: `memory: ConversationMemory`. `get_deps()` thêm `memory=get_memory()` (singleton module-level — sống qua các request, khác executor/llm tạo mới mỗi lần).

Trong handler `chat`, sau khi `thread_id` chốt xong (sau block clarify override):

```python
        memory_context = deps.memory.get_context(thread_id)
```

`stream()` thay bằng:

```python
        async def stream():
            answer_text = ""
            done_require: str | None = None
            try:
                async for event in run_session(
                        ctx, llm_sm=deps.llm_sm, llm_tool=deps.llm_tool, deps=deps.deps,
                        max_steps=deps.max_steps, retry_cap=deps.retry_cap,
                        resume_snapshot=resume_snapshot, pending_store=deps.pending_store,
                        memory_context=memory_context):
                    if event["type"] == "answer":
                        answer_text = event["data"].get("text", "")
                    elif event["type"] == "done":
                        done_require = event["data"].get("raw_require") or ctx.raw_require
                    sse = _to_frontend_sse(event, thread_id=ctx.thread_id)
                    if sse:
                        log.debug("SSE emit event=%s", event["type"])
                        yield sse
                # Chi ghi khi phien ket thuc co answer (sau done) — clarify/
                # aborted/error KHONG ghi (spec write path).
                if done_require is not None and answer_text:
                    deps.memory.append_turn(ctx.thread_id, done_require, answer_text)
                    if deps.memory.needs_compact(ctx.thread_id):
                        # fire-and-forget: user khong phai cho them 1 LLM call
                        task = asyncio.create_task(
                            deps.memory.compact(ctx.thread_id, llm=deps.llm_tool))
                        _bg_tasks.add(task)
                        task.add_done_callback(_bg_tasks.discard)
            except Exception as exc:
                log.error("stream error thread=%s: %s", ctx.thread_id, exc, exc_info=True)
                yield _to_frontend_sse({"type": "error", "data": {"message": "Lỗi hệ thống."}},
                                       thread_id=ctx.thread_id) or ""
```

- [ ] **Step 4: Chạy pass** — `cd ai_python && python -m pytest tests/test_api_sse.py -v` → PASS (cả 3 test cũ).

- [ ] **Step 5: Commit** — `git add ai_python/app/api/app.py ai_python/tests/test_api_sse.py && git commit -m "feat(memory): api read path (get_context) + write path (append sau done, compact fire-and-forget)"`

---

### Task 9: E2E — 2 request cùng thread

**Files:**
- Create: `ai_python/tests/test_e2e_memory.py`

- [ ] **Step 1: Viết test** — tạo `tests/test_e2e_memory.py` (run_session THẬT, chỉ fake LLM + executor):

```python
import json
import time
import jwt
from fastapi.testclient import TestClient
from app.api.app import create_app, get_deps
from app.memory import ConversationMemory

SECRET = "test-secret"
CHAT_URL = "/api/v1/ai/chat/stream"


def _token():
    return jwt.encode({"sub": "user-1", "exp": int(time.time()) + 60},
                      SECRET, algorithm="HS256")


# Moi request: SM goi 3 lan (sql -> validator -> composer; sau composer valid
# orchestrator tu finish khong goi SM nua).
_SM_SCRIPT = [
    {"action": "call_tool", "tool_name": "sql_execute", "forward_data": {},
     "reasoning": "can data", "message": None},
    {"action": "call_tool", "tool_name": "data_validator",
     "forward_data": {"from": "sql_execute"}, "reasoning": "validate", "message": None},
    {"action": "call_tool", "tool_name": "answer_composer",
     "forward_data": {"from": "sql_execute"}, "reasoning": "soan", "message": None},
]


class _LLM:
    def __init__(self):
        self._sm = [json.dumps(d) for d in _SM_SCRIPT]
        self.sm_prompts = []

    def complete(self, *, system, user, role="default", temperature=None):
        if role == "sm":
            self.sm_prompts.append(user)
            return self._sm.pop(0)
        if "Skill: sql_execute" in system:
            return json.dumps({"sql": "SELECT SUM(final_amount) AS doanh_thu FROM orders"})
        if "Skill: data_validator" in system:
            return json.dumps({"verdict": "pass", "reason": "du data"})
        if "Skill: answer_composer" in system:
            return json.dumps({"answer": "Doanh thu thang 5/2026 la 15 trieu.\nGợi ý: xem theo kenh?"})
        raise AssertionError(f"LLM call khong mong doi: {system[:80]}")


class _StubExecutor:
    def run(self, sql, row_limit=100):
        return {"columns": ["doanh_thu"], "rows": [[15000000]]}


class _Deps:
    def __init__(self, llm, memory):
        self.llm_sm = llm
        self.llm_tool = llm
        self.deps = {"executor": _StubExecutor(), "row_limit": 100}
        self.max_steps = 6
        self.retry_cap = 2
        self.jwt_secret = SECRET
        self.jwt_issuer = ""
        self.jwt_audience = ""
        self.dev_bypass = False
        self.pending_store = None
        self.memory = memory


def test_two_requests_same_thread_share_memory():
    memory = ConversationMemory(window=10)
    app = create_app()
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token()}"}

    # --- Request 1 ---
    llm1 = _LLM()
    app.dependency_overrides[get_deps] = lambda: _Deps(llm1, memory)
    r1 = client.post(CHAT_URL,
                     json={"message": "doanh thu thang 5/2026",
                           "metadata": {"thread_id": "t-e2e"}},
                     headers=headers)
    assert r1.status_code == 200
    assert "Doanh thu thang 5/2026 la 15 trieu" in r1.text
    # request 1 KHONG co memory cu
    assert all("[Cac luot gan nhat]" not in p for p in llm1.sm_prompts)
    # sau done: ghi dung 1 luot
    ctxm = memory.get_context("t-e2e")
    assert len(ctxm["turns"]) == 1
    assert ctxm["turns"][0]["user"] == "doanh thu thang 5/2026"
    assert "15 trieu" in ctxm["turns"][0]["answer"]

    # --- Request 2: cau noi tiep, cung thread ---
    llm2 = _LLM()
    app.dependency_overrides[get_deps] = lambda: _Deps(llm2, memory)
    r2 = client.post(CHAT_URL,
                     json={"message": "con thang truoc thi sao?",
                           "metadata": {"thread_id": "t-e2e"}},
                     headers=headers)
    assert r2.status_code == 200
    # SM cua request 2 thay lich su luot 1
    assert any("[Cac luot gan nhat]" in p for p in llm2.sm_prompts)
    assert any("doanh thu thang 5/2026" in p for p in llm2.sm_prompts)
    # sau request 2: 2 luot trong memory
    assert len(memory.get_context("t-e2e")["turns"]) == 2


def test_other_thread_does_not_see_memory():
    memory = ConversationMemory(window=10)
    memory.append_turn("t-khac", "cau cu", "tra loi cu")
    app = create_app()
    client = TestClient(app)
    llm = _LLM()
    app.dependency_overrides[get_deps] = lambda: _Deps(llm, memory)
    r = client.post(CHAT_URL,
                    json={"message": "doanh thu thang 5/2026",
                          "metadata": {"thread_id": "t-moi"}},
                    headers={"Authorization": f"Bearer {_token()}"})
    assert r.status_code == 200
    assert all("cau cu" not in p for p in llm.sm_prompts)
```

- [ ] **Step 2: Chạy** — `cd ai_python && python -m pytest tests/test_e2e_memory.py -v` → PASS (các task trước đã implement đủ; nếu FAIL → debug theo message, KHÔNG sửa test trừ khi test sai giả định).

- [ ] **Step 3: Chạy toàn bộ suite** — `cd ai_python && python -m pytest tests/ -v` → tất cả PASS.

- [ ] **Step 4: Commit** — `git add ai_python/tests/test_e2e_memory.py && git commit -m "test(memory): e2e 2 request cung thread — SM thay lich su, thread khac co lap"`

---

## Self-review notes (đã chạy)

- **Spec coverage:** storage in-memory + singleton (T2/T3/T8), compaction LLM + degrade + prompt file (T3), SM inject + resolved_require + skill.md (T6), 2 kênh xuống tool (T4/T5/T7), write path + clarify-không-ghi + resume-lượt-gộp (T7/T8), config (T1), toàn bộ mục Testing của spec (T2–T9).
- **Resume lượt gộp:** cần restore `raw_require` từ snapshot trong orchestrator (T7 Step 3) — hiện code chưa restore, nếu thiếu thì memory ghi sai câu hỏi gốc.
- **`answer_text` rỗng:** chỉ append khi có answer thật (`done_require is not None and answer_text`) — done-không-answer không ghi rác.
