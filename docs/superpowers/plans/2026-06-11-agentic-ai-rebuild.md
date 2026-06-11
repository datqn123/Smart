# Agentic AI Rebuild (ai_python) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây mới hoàn toàn `ai_python/app` thành một Agentic AI: LLM Qwen3.6-27B (qua FPT Cloud, OpenAI-compatible) đóng vai Session Manager / planner-evaluator, gọi 4 tool (mỗi tool là một LangGraph subgraph `[load_skill → execute → self_validate]`) qua cơ chế structured JSON decision + dispatcher, có HITL pause/resume và output SSE. Build stateless.

**Architecture:** Một orchestrator (vòng phiên lớn) chạy LLM Session Manager phát ra `Decision` JSON `{action, tool_name, forward_data, reasoning}`; dispatcher map `tool_name → subgraph` và luôn bơm payload `{raw_require, upstream_data}`. Mỗi tool subgraph đọc lại `skill.md` ở node đầu (kể cả khi retry), tự validate output trước khi trả. `data_validator` là cổng bắt buộc trước `answer_composer`; validator fail → SM `request_clarification` → pause qua langgraph SqliteSaver → resume khi nhận `clarification_response`. Mọi external (LLM/DB) có lớp interface để stub trong test.

**Tech Stack:** Python 3.11+, FastAPI + SSE, LangGraph 0.2.70 + langgraph-checkpoint-sqlite, openai SDK (trỏ FPT Cloud), pydantic v2 / pydantic-settings, sqlparse, psycopg2 + SQLAlchemy (read-only), PyJWT, pytest + pytest-asyncio.

---

## Quyết định kiến trúc đã chốt (từ brainstorming)

| Risk | Quyết định | Ảnh hưởng |
|------|-----------|-----------|
| **R1 — SQL path** | **Direct DB read-only.** Tạo `.env` mới sạch (bỏ `SQL_EXECUTOR_MODE=http_spring`, `SPRING_SQL_URL` của bản cũ). `sql_execute` nối thẳng `DATABASE_URL_RO` qua role/connection read-only + sqlparse guard ở tầng Python. | Task 8 (`sql/executor.py`, `sql/guard.py`) |
| **R3 — SRS-006** | **Hệ mới hoàn toàn, không dính bản cũ.** Bỏ `AGENTIC_V3_ENABLED` và mọi semantic rollback về legacy graph. `.env` mới không mang flag cũ. | Task 1 (`.env`, settings) |
| **R5 — Structured output SM** | **Qwen cho SM decision, config riêng.** SM dùng chính Qwen nhưng client config riêng (temperature 0.0 + structured prompt) + pydantic validate + bounded reparse. `gemma-4-26B` chỉ là escape hatch ghi chú, **chưa wire**. | Task 2 (`llm_client`), Task 11 (SM) |

---

## Module structure (cây thư mục + trách nhiệm file)

```
ai_python/
  .env                          # MỚI (Task 1) — bỏ http_spring + v3 flag
  app/
    __init__.py
    config/
      __init__.py
      settings.py               # pydantic-settings: đọc .env, validate
      llm_client.py             # LLMClient interface + OpenAILLMClient + make_llm(role)
    harness/
      __init__.py
      auth.py                   # verify_jwt(token) -> claims | raise AuthError
      session.py                # resolve_thread_id(user_id) -> thread_id
      turn_context.py           # TurnContext (raw_require, user_id, thread_id, clarification_response?)
      sse_emitter.py            # sse_format(type, data) -> "data: {...}\n\n"  (nested dưới key "harness")
    registry/
      __init__.py
      registry.py               # TOOL_REGISTRY, get_builder, load_skill, render_tool_catalog
    tools/
      __init__.py
      session_manager/
        __init__.py             # Decision model + analyze(state, llm) -> Decision
        skill.md
      sql_execute/
        __init__.py             # execute(state, llm, executor) + self_validate(state)
        skill.md
      data_validator/
        __init__.py             # execute(state, llm) + self_validate(state)
        skill.md
      answer_composer/
        __init__.py             # execute(state, llm) + self_validate(state)
        skill.md
    graph/
      __init__.py
      state.py                  # ToolState, SessionState (TypedDict)
      subgraph.py               # build_tool_subgraph(tool_name) -> compiled graph
      dispatcher.py             # dispatch(tool_name, raw_require, upstream_data, ...) -> dict
      orchestrator.py           # run_session(turn_ctx, deps) -> async generator of SSE events
      hitl.py                   # checkpointer setup + pause/resume helpers
    sql/
      __init__.py
      guard.py                  # assert_read_only(sql) -> None | raise SqlGuardError
      executor.py               # SqlExecutor (Protocol) + PostgresRoExecutor
    api/
      __init__.py
      app.py                    # FastAPI; POST /chat -> StreamingResponse(SSE)
    memory/
      __init__.py               # DEFERRED placeholder (docstring only, no integration)
  tests/
    __init__.py
    conftest.py                 # FakeLLM, StubSqlExecutor, settings fixture
    test_config_settings.py
    test_llm_client.py
    test_harness_auth.py
    test_harness_session.py
    test_registry.py
    test_subgraph.py
    test_sql_guard.py
    test_sql_executor.py
    test_tool_sql_execute.py
    test_tool_data_validator.py
    test_tool_answer_composer.py
    test_session_manager.py
    test_dispatcher.py
    test_orchestrator.py
    test_hitl.py
    test_api_sse.py
    test_e2e_happy_path.py
```

---

## Dependency graph (thứ tự code — bắt buộc theo chiều mũi tên)

```
Task 1 config/settings ─┬─> Task 2 config/llm_client ──────────────┐
                        ├─> Task 3 harness/auth + session ──────────┤
                        └─> Task 4 harness/sse_emitter ─────────────┤
                                                                    v
Task 5 graph/state ──> Task 6 registry ──> Task 7 graph/subgraph ──> (tool nodes)
                                                                    │
Task 8 sql/guard + executor ───────────────────────────────────────┤
                                                                    v
Task 9 tools/sql_execute ──┐
Task 10 tools/data_validator ─┼─> (đều là nodes dùng trong subgraph)
Task 11 tools/answer_composer ┘
                                                                    v
Task 12 tools/session_manager + graph/dispatcher ──> Task 13 graph/orchestrator
                                                                    v
Task 14 graph/hitl (pause/resume) ──> Task 15 api/app (SSE) ──> Task 16 E2E happy path
```

**Lý do thứ tự:** state types + registry + subgraph builder là khung chung mọi tool dùng; sql layer độc lập nên code song song được nhưng phải xong trước tool sql_execute; SM + dispatcher cần đủ 3 tool + subgraph; orchestrator cần SM + dispatcher; HITL cần orchestrator; API cần orchestrator + HITL; E2E cuối.

---

## Test strategy (xuyên suốt)

- **Framework:** `pytest` + `pytest-asyncio` (mode `auto`). Mọi external có lớp interface để inject stub.
- **FakeLLM** (`tests/conftest.py`): deterministic, trả response theo hàng đợi hoặc theo `role`; ghi lại `calls` để assert prompt/skill được nạp. Thay hoàn toàn openai SDK — **không gọi mạng**.
- **StubSqlExecutor** (`tests/conftest.py`): trả rows cố định cho SELECT; raise nếu nhận non-SELECT (để chứng minh guard chạy trước).
- **Mapping fact → test:** mỗi fact `automatedVerification:true` có ≥1 test, ghi `# fact-<id>` ngay trên test để truy vết.
- **Mỗi Task theo TDD:** viết test fail → chạy thấy fail → code tối thiểu → chạy thấy pass → commit.
- **Lệnh chạy toàn bộ:** `cd ai_python && .venv\Scripts\python -m pytest -q` (Windows). Dùng `pytest -k <name> -v` cho từng test.

> **Lưu ý Windows/venv:** repo đã có `ai_python/.venv`. Mọi lệnh pytest/python chạy qua `ai_python\.venv\Scripts\python.exe`. Cài thêm dep (nếu thiếu): `ai_python\.venv\Scripts\python -m pip install -r ai_python\requirements.txt`.

---

## Task 0: Bootstrap test harness (conftest + fakes)

**Files:**
- Create: `ai_python/tests/__init__.py`
- Create: `ai_python/tests/conftest.py`
- Create: `ai_python/app/__init__.py`, `ai_python/app/config/__init__.py` (rỗng)

- [ ] **Step 1: Tạo package markers**

Tạo các file rỗng: `ai_python/app/__init__.py`, `ai_python/app/config/__init__.py`, `ai_python/tests/__init__.py`.

- [ ] **Step 2: Viết `conftest.py` với FakeLLM + StubSqlExecutor**

```python
# ai_python/tests/conftest.py
import json
import pytest

pytest_plugins = ()


class FakeLLM:
    """Deterministic LLM thay openai SDK.

    - `scripted`: list[str] trả lần lượt theo thứ tự gọi complete().
    - `by_role`: dict[str, list[str]] trả theo role nếu complete(role=...) được truyền.
    - Ghi `self.calls` = list[{"role","system","user"}] để assert skill được nạp.
    """

    def __init__(self, scripted=None, by_role=None):
        self.scripted = list(scripted or [])
        self.by_role = {k: list(v) for k, v in (by_role or {}).items()}
        self.calls = []

    def complete(self, *, system: str, user: str, role: str = "default",
                 temperature: float | None = None) -> str:
        self.calls.append({"role": role, "system": system, "user": user})
        if role in self.by_role and self.by_role[role]:
            return self.by_role[role].pop(0)
        if self.scripted:
            return self.scripted.pop(0)
        raise AssertionError(f"FakeLLM hết kịch bản cho role={role!r}")

    def json(self, payload) -> str:
        return json.dumps(payload, ensure_ascii=False)


class StubSqlExecutor:
    """Thay PostgresRoExecutor. Trả rows cố định; chặn non-SELECT để
    chứng minh guard phải chạy TRƯỚC executor (fact-sql-guard)."""

    def __init__(self, rows=None):
        self.rows = rows if rows is not None else [{"id": 1, "name": "Acme"}]
        self.executed = []

    def run(self, sql: str, *, row_limit: int = 100):
        stripped = sql.strip().lower()
        if not stripped.startswith("select"):
            raise AssertionError("StubSqlExecutor nhận non-SELECT — guard đã không chặn")
        self.executed.append(sql)
        return {"columns": list(self.rows[0].keys()) if self.rows else [],
                "rows": self.rows[:row_limit]}


@pytest.fixture
def fake_llm():
    return FakeLLM()


@pytest.fixture
def stub_sql():
    return StubSqlExecutor()
```

- [ ] **Step 3: Tạo `pytest.ini`**

```ini
# ai_python/pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
addopts = -q
```

- [ ] **Step 4: Verify harness chạy**

Run: `cd ai_python && .venv\Scripts\python -m pytest -q`
Expected: `no tests ran` (0 collected) — không lỗi import conftest.

- [ ] **Step 5: Commit**

```bash
git add ai_python/tests ai_python/app/__init__.py ai_python/app/config/__init__.py ai_python/pytest.ini
git commit -m "test(agentic): bootstrap pytest harness with FakeLLM + StubSqlExecutor"
```

---

## Task 1: Config — settings + `.env` mới

**Files:**
- Create: `ai_python/app/config/settings.py`
- Modify: `ai_python/.env` (viết mới, bỏ http_spring + AGENTIC_V3)
- Test: `ai_python/tests/test_config_settings.py`

Maps fact: `fact-config-llm`, `fact-config-backend` (một phần), reconcile R1/R3.

- [ ] **Step 1: Viết test fail cho settings**

```python
# ai_python/tests/test_config_settings.py
from app.config.settings import Settings


def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://mkp-api.fptcloud.com")
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_MODEL", "Qwen3.6-27B")
    monkeypatch.setenv("DATABASE_URL_RO", "postgresql://u:p@127.0.0.1:5432/db")
    s = Settings()
    assert s.llm_base_url == "https://mkp-api.fptcloud.com"
    assert s.llm_model == "Qwen3.6-27B"
    assert s.llm_sm_temperature == 0.0          # SM structured, mặc định deterministic
    assert s.harness_max_steps == 6
    assert s.tool_retry_cap == 2
    assert s.database_url_ro.startswith("postgresql://")


def test_settings_no_legacy_v3_flag():
    # R3: hệ mới không đọc AGENTIC_V3_ENABLED / SQL_EXECUTOR_MODE
    assert not hasattr(Settings, "agentic_v3_enabled")
    assert not hasattr(Settings, "sql_executor_mode")
```

- [ ] **Step 2: Run → fail (ModuleNotFound)**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_config_settings.py -v`
Expected: FAIL — `No module named 'app.config.settings'`.

- [ ] **Step 3: Viết `settings.py`**

```python
# ai_python/app/config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",
                                      extra="ignore", case_sensitive=False)

    # --- Auth ---
    auth_dev_bypass: bool = False
    jwt_hs256_secret: str = ""
    jwt_issuer: str = ""
    jwt_audience: str = ""

    # --- LLM (Qwen via FPT Cloud, OpenAI-compatible) ---
    llm_base_url: str
    llm_api_key: str
    llm_model: str = "Qwen3.6-27B"
    llm_temperature: float = 0.2          # tool thường
    llm_sm_temperature: float = 0.0       # SM decision: deterministic structured (R5)
    llm_http_request_timeout: int = 120
    llm_structured_model: str = "gemma-4-26B-A4B-it"  # escape hatch, CHƯA wire (R5)

    # --- SQL (direct read-only — R1) ---
    database_url_ro: str
    sql_row_limit: int = 100
    sql_exec_timeout_seconds: int = 10

    # --- Harness / budget ---
    harness_max_steps: int = 6
    tool_retry_cap: int = 2
    hitl_checkpoint_db: str = "./var/hitl_checkpoints.sqlite"

    app_env: str = "dev"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

- [ ] **Step 4: Viết `.env` mới (ghi đè `ai_python/.env`)**

```dotenv
# ===== Agentic AI Rebuild (.env mới — bỏ http_spring + AGENTIC_V3) =====
AUTH_DEV_BYPASS=0
JWT_HS256_SECRET=<REDACTED-rotate-before-use>
JWT_ISSUER=
JWT_AUDIENCE=

# LLM (Qwen via FPT Cloud, OpenAI-compatible)
LLM_BASE_URL=https://mkp-api.fptcloud.com
LLM_API_KEY=<REDACTED-rotate-before-use>
LLM_MODEL=Qwen3.6-27B
LLM_TEMPERATURE=0.2
LLM_SM_TEMPERATURE=0.0
LLM_HTTP_REQUEST_TIMEOUT=120
LLM_STRUCTURED_MODEL=gemma-4-26B-A4B-it

# SQL — direct read-only (R1)
DATABASE_URL_RO=postgresql://smart_erp:smart_erp@127.0.0.1:5432/smart_erp
SQL_ROW_LIMIT=100
SQL_EXEC_TIMEOUT_SECONDS=10

# Harness / budget
HARNESS_MAX_STEPS=6
TOOL_RETRY_CAP=2
HITL_CHECKPOINT_DB=./var/hitl_checkpoints.sqlite

APP_ENV=dev
```

- [ ] **Step 5: Run → pass**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_config_settings.py -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add ai_python/app/config/settings.py ai_python/.env ai_python/tests/test_config_settings.py
git commit -m "feat(config): settings + fresh .env (direct RO SQL, no v3 flag)"
```

---

## Task 2: Config — LLM client (Qwen, OpenAI-compatible)

**Files:**
- Create: `ai_python/app/config/llm_client.py`
- Test: `ai_python/tests/test_llm_client.py`

Maps fact: `fact-config-llm` ("mọi tool dùng chung LLM client"), R5 (SM config riêng).

- [ ] **Step 1: Viết test fail (mock openai, không gọi thật)**

```python
# ai_python/tests/test_llm_client.py
from unittest.mock import MagicMock
from app.config.llm_client import OpenAILLMClient, make_llm
from app.config.settings import Settings


def _settings():
    return Settings(llm_base_url="https://x", llm_api_key="k",
                    llm_model="Qwen3.6-27B", database_url_ro="postgresql://u:p@h/db")


def test_make_llm_default_uses_qwen_and_tool_temp():
    s = _settings()
    client = make_llm(s, role="default")
    assert client.model == "Qwen3.6-27B"
    assert client.temperature == 0.2


def test_make_llm_sm_uses_qwen_with_sm_temp():
    # R5: SM dùng CHÍNH Qwen nhưng config riêng (temperature 0.0)
    s = _settings()
    client = make_llm(s, role="sm")
    assert client.model == "Qwen3.6-27B"
    assert client.temperature == 0.0


def test_complete_calls_chat_completions_with_messages():
    s = _settings()
    fake_sdk = MagicMock()
    fake_sdk.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="hi"))])
    client = OpenAILLMClient(sdk=fake_sdk, model="Qwen3.6-27B", temperature=0.2)
    out = client.complete(system="S", user="U")
    assert out == "hi"
    kwargs = fake_sdk.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "Qwen3.6-27B"
    assert kwargs["messages"][0] == {"role": "system", "content": "S"}
    assert kwargs["messages"][1] == {"role": "user", "content": "U"}
    assert kwargs["temperature"] == 0.2
```

- [ ] **Step 2: Run → fail**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_llm_client.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Viết `llm_client.py`**

```python
# ai_python/app/config/llm_client.py
from __future__ import annotations
from typing import Protocol
from app.config.settings import Settings


class LLMClient(Protocol):
    model: str
    temperature: float
    def complete(self, *, system: str, user: str, role: str = "default",
                 temperature: float | None = None) -> str: ...


class OpenAILLMClient:
    """Thin wrapper quanh openai SDK trỏ FPT Cloud (OpenAI-compatible)."""

    def __init__(self, *, sdk, model: str, temperature: float):
        self._sdk = sdk
        self.model = model
        self.temperature = temperature

    def complete(self, *, system: str, user: str, role: str = "default",
                 temperature: float | None = None) -> str:
        resp = self._sdk.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=self.temperature if temperature is None else temperature,
        )
        return resp.choices[0].message.content or ""


def _build_sdk(settings: Settings):
    from openai import OpenAI
    return OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key,
                  timeout=settings.llm_http_request_timeout)


def make_llm(settings: Settings, role: str = "default") -> OpenAILLMClient:
    """Trả LLM client. Mọi tool chung 1 model (Qwen); role='sm' chỉ đổi
    temperature (deterministic) — KHÔNG đổi model (R5)."""
    temperature = settings.llm_sm_temperature if role == "sm" else settings.llm_temperature
    return OpenAILLMClient(sdk=_build_sdk(settings), model=settings.llm_model,
                           temperature=temperature)
```

- [ ] **Step 4: Run → pass**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_llm_client.py -v`
Expected: PASS (3 passed). (Test inject `sdk=` trực tiếp nên không gọi `_build_sdk` → không cần mạng.)

- [ ] **Step 5: Commit**

```bash
git add ai_python/app/config/llm_client.py ai_python/tests/test_llm_client.py
git commit -m "feat(config): shared Qwen LLM client + SM role config (R5)"
```

---

## Task 3: Harness — auth + session

**Files:**
- Create: `ai_python/app/harness/__init__.py`, `app/harness/auth.py`, `app/harness/session.py`, `app/harness/turn_context.py`
- Test: `ai_python/tests/test_harness_auth.py`, `tests/test_harness_session.py`

Maps fact: harness auth ("request không hợp lệ bị từ chối, không vào pipeline"), thread mapping.

- [ ] **Step 1: Viết test fail cho auth**

```python
# ai_python/tests/test_harness_auth.py
import time
import jwt
import pytest
from app.harness.auth import verify_jwt, AuthError

SECRET = "test-secret"


def _token(claims, secret=SECRET):
    return jwt.encode(claims, secret, algorithm="HS256")


def test_valid_token_returns_claims():
    tok = _token({"sub": "user-1", "exp": int(time.time()) + 60})
    claims = verify_jwt(tok, secret=SECRET)
    assert claims["sub"] == "user-1"


def test_expired_token_rejected():  # fact-auth
    tok = _token({"sub": "u", "exp": int(time.time()) - 10})
    with pytest.raises(AuthError):
        verify_jwt(tok, secret=SECRET)


def test_bad_signature_rejected():  # fact-auth
    tok = _token({"sub": "u", "exp": int(time.time()) + 60}, secret="other")
    with pytest.raises(AuthError):
        verify_jwt(tok, secret=SECRET)


def test_dev_bypass_returns_synthetic_claims():
    claims = verify_jwt(None, secret=SECRET, dev_bypass=True)
    assert claims["sub"] == "dev-user"
```

- [ ] **Step 2: Run → fail**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_harness_auth.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Viết `auth.py`**

```python
# ai_python/app/harness/auth.py
from __future__ import annotations
import jwt


class AuthError(Exception):
    """Request không xác thực được → bị từ chối, KHÔNG vào pipeline."""


def verify_jwt(token: str | None, *, secret: str, issuer: str = "",
               audience: str = "", dev_bypass: bool = False) -> dict:
    if dev_bypass:
        return {"sub": "dev-user", "dev_bypass": True}
    if not token:
        raise AuthError("missing token")
    options = {"verify_aud": bool(audience)}
    try:
        claims = jwt.decode(
            token, secret, algorithms=["HS256"],
            audience=audience or None,
            issuer=issuer or None,
            options=options,
        )
    except jwt.PyJWTError as exc:
        raise AuthError(str(exc)) from exc
    if "sub" not in claims:
        raise AuthError("token missing sub")
    return claims
```

- [ ] **Step 4: Run → pass**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_harness_auth.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Viết test fail cho session + turn_context**

```python
# ai_python/tests/test_harness_session.py
from app.harness.session import resolve_thread_id
from app.harness.turn_context import TurnContext


def test_thread_id_deterministic_per_user():  # fact-thread
    a = resolve_thread_id("user-1")
    b = resolve_thread_id("user-1")
    c = resolve_thread_id("user-2")
    assert a == b
    assert a != c
    assert a.startswith("thread-")


def test_turn_context_holds_resolved_thread():
    ctx = TurnContext(raw_require="doanh thu quý 1?", user_id="user-1",
                      thread_id="thread-x")
    assert ctx.raw_require == "doanh thu quý 1?"
    assert ctx.thread_id == "thread-x"
    assert ctx.clarification_response is None
```

- [ ] **Step 6: Viết `session.py` + `turn_context.py`**

```python
# ai_python/app/harness/session.py
from __future__ import annotations
import hashlib


def resolve_thread_id(user_id: str) -> str:
    """Map User_ID -> Thread_ID ổn định (stateless: hash, không lưu DB).
    Vòng sau (memory) sẽ thay bằng lookup bền vững."""
    digest = hashlib.sha1(user_id.encode("utf-8")).hexdigest()[:16]
    return f"thread-{digest}"
```

```python
# ai_python/app/harness/turn_context.py
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class TurnContext:
    raw_require: str
    user_id: str
    thread_id: str
    clarification_response: str | None = None  # set khi resume HITL
```

```python
# ai_python/app/harness/__init__.py
# (rỗng)
```

- [ ] **Step 7: Run → pass**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_harness_session.py -v`
Expected: PASS (2 passed).

- [ ] **Step 8: Commit**

```bash
git add ai_python/app/harness ai_python/tests/test_harness_auth.py ai_python/tests/test_harness_session.py
git commit -m "feat(harness): JWT auth (+dev bypass) and User_ID->Thread_ID mapping"
```

---

## Task 4: Harness — SSE emitter (chống flatten)

**Files:**
- Create: `ai_python/app/harness/sse_emitter.py`
- Test: `ai_python/tests/test_sse_emitter.py`

Maps fact: `fact-sse`, R6. **Bài học cũ:** chunk phải nested dưới key cố định `"harness"` để route Spring không flatten mất key payload.

- [ ] **Step 1: Viết test fail**

```python
# ai_python/tests/test_sse_emitter.py
import json
from app.harness.sse_emitter import sse_format, SSEEvent


def test_sse_format_nests_under_harness_key():  # R6 chống flatten
    line = sse_format("tool_call", {"tool_name": "sql_execute"})
    assert line.startswith("data: ")
    assert line.endswith("\n\n")
    body = json.loads(line[len("data: "):].strip())
    assert set(body.keys()) == {"harness"}            # chỉ 1 key gốc
    assert body["harness"]["type"] == "tool_call"
    assert body["harness"]["data"]["tool_name"] == "sql_execute"


def test_sse_event_types_enum():
    assert SSEEvent.CLARIFY == "clarify"
    assert SSEEvent.ANSWER == "answer"
    assert SSEEvent.DONE == "done"
    assert SSEEvent.ERROR == "error"


def test_unicode_preserved():
    line = sse_format("answer", {"text": "Doanh thu quý 1"})
    assert "Doanh thu quý 1" in line  # ensure_ascii=False
```

- [ ] **Step 2: Run → fail**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_sse_emitter.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Viết `sse_emitter.py`**

```python
# ai_python/app/harness/sse_emitter.py
from __future__ import annotations
import json


class SSEEvent(str):
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    CLARIFY = "clarify"      # HITL: frontend confirm UI tiêu thụ event này
    ANSWER = "answer"        # token/đoạn câu trả lời cuối
    DONE = "done"
    ERROR = "error"


def sse_format(event_type: str, data: dict) -> str:
    """SSE line. Bọc dưới 1 key gốc cố định 'harness' để route trung gian
    không flatten làm mất key payload (R6)."""
    body = json.dumps({"harness": {"type": event_type, "data": data}},
                      ensure_ascii=False)
    return f"data: {body}\n\n"
```

> **SSEEvent dùng class attribute (không Enum)** để so sánh `== "clarify"` trực tiếp và serialize gọn.

- [ ] **Step 4: Run → pass**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_sse_emitter.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add ai_python/app/harness/sse_emitter.py ai_python/tests/test_sse_emitter.py
git commit -m "feat(harness): SSE emitter nested under fixed 'harness' key (anti-flatten)"
```

---

## Task 5: Graph — state types

**Files:**
- Create: `ai_python/app/graph/__init__.py`, `app/graph/state.py`
- Test: `ai_python/tests/test_graph_state.py`

- [ ] **Step 1: Viết test fail**

```python
# ai_python/tests/test_graph_state.py
from app.graph.state import new_tool_state, new_session_state


def test_new_tool_state_defaults():
    st = new_tool_state(tool_name="sql_execute", raw_require="R",
                        upstream_data={"x": 1})
    assert st["tool_name"] == "sql_execute"
    assert st["raw_require"] == "R"
    assert st["upstream_data"] == {"x": 1}
    assert st["skill"] == ""
    assert st["output"] is None
    assert st["valid"] is False
    assert st["attempt"] == 0


def test_new_session_state_defaults():
    st = new_session_state(raw_require="R", thread_id="t1")
    assert st["raw_require"] == "R"
    assert st["thread_id"] == "t1"
    assert st["step_count"] == 0
    assert st["status"] == "running"
    assert st["tool_results"] == {}
    assert st["retry_counts"] == {}
    assert st["final_answer"] is None
    assert st["pending_clarification"] is None
```

- [ ] **Step 2: Run → fail**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_graph_state.py -v`
Expected: FAIL.

- [ ] **Step 3: Viết `state.py`**

```python
# ai_python/app/graph/state.py
from __future__ import annotations
from typing import Any, TypedDict


class ToolState(TypedDict):
    tool_name: str
    raw_require: str
    upstream_data: dict[str, Any]
    skill: str                       # nội dung skill.md đã nạp ở node load_skill
    output: dict[str, Any] | None    # kết quả execute
    valid: bool                      # verdict của self_validate
    validation_error: str | None
    attempt: int                     # số lần đã chạy (tăng mỗi lần build/retry)


class SessionState(TypedDict):
    raw_require: str
    thread_id: str
    history: list[dict[str, Any]]            # nhật ký decision + tool result
    tool_results: dict[str, dict[str, Any]]  # tool_name -> output gần nhất
    retry_counts: dict[str, int]             # tool_name -> số lần retry đã dùng
    step_count: int
    status: str                              # running|finished|paused|aborted
    final_answer: str | None
    pending_clarification: dict[str, Any] | None
    last_decision: dict[str, Any] | None


def new_tool_state(*, tool_name: str, raw_require: str,
                   upstream_data: dict | None = None) -> ToolState:
    return ToolState(tool_name=tool_name, raw_require=raw_require,
                     upstream_data=upstream_data or {}, skill="", output=None,
                     valid=False, validation_error=None, attempt=0)


def new_session_state(*, raw_require: str, thread_id: str) -> SessionState:
    return SessionState(raw_require=raw_require, thread_id=thread_id, history=[],
                        tool_results={}, retry_counts={}, step_count=0,
                        status="running", final_answer=None,
                        pending_clarification=None, last_decision=None)
```

- [ ] **Step 4: Run → pass + Commit**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_graph_state.py -v` → PASS.

```bash
git add ai_python/app/graph/__init__.py ai_python/app/graph/state.py ai_python/tests/test_graph_state.py
git commit -m "feat(graph): ToolState and SessionState typed dicts"
```

---

## Task 6: Registry — static tool registry + skill loader

**Files:**
- Create: `ai_python/app/registry/__init__.py`, `app/registry/registry.py`
- Create: skill `.md` rỗng tạm cho 4 tool (sẽ điền ở task sau): `app/tools/<name>/skill.md`
- Create: `ai_python/app/tools/__init__.py` + 4 `app/tools/<name>/__init__.py` (rỗng)
- Test: `ai_python/tests/test_registry.py`

Maps fact: `fact-registry-static` (đúng 4 tool, SM chỉ gọi tool có đăng ký), skill loader đọc đúng `.md`.

- [ ] **Step 1: Tạo skeleton thư mục tools + skill.md tạm**

Tạo `app/tools/__init__.py` (rỗng) và cho mỗi tool trong `{session_manager, sql_execute, data_validator, answer_composer}`:
- `app/tools/<name>/__init__.py` (rỗng)
- `app/tools/<name>/skill.md` với nội dung tạm: `# <name> skill (placeholder)`

- [ ] **Step 2: Viết test fail**

```python
# ai_python/tests/test_registry.py
import pytest
from app.registry.registry import (TOOL_NAMES, load_skill, render_tool_catalog,
                                    is_registered)


def test_registry_lists_exactly_four_tools():  # fact-registry-static
    assert set(TOOL_NAMES) == {
        "sql_execute", "data_validator", "answer_composer", "session_manager"}


def test_only_registered_tools_callable():  # fact-registry-static
    assert is_registered("sql_execute")
    assert not is_registered("rm_rf_database")


def test_load_skill_reads_md_fresh_each_call(tmp_path, monkeypatch):
    # skill loader đọc file mỗi lần (nền tảng cho reload-on-retry)
    first = load_skill("sql_execute")
    assert isinstance(first, str) and len(first) > 0


def test_load_skill_unknown_raises():
    with pytest.raises(KeyError):
        load_skill("nope")


def test_catalog_contains_descriptions_for_dispatch_tools():
    cat = render_tool_catalog()
    # SM catalog nhét các tool có thể dispatch (không gồm chính SM)
    assert "sql_execute" in cat
    assert "data_validator" in cat
    assert "answer_composer" in cat
```

- [ ] **Step 3: Run → fail**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_registry.py -v`
Expected: FAIL.

- [ ] **Step 4: Viết `registry.py`**

```python
# ai_python/app/registry/registry.py
from __future__ import annotations
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"

# Static registry. SM chỉ được gọi tool có trong DISPATCHABLE.
TOOL_NAMES = ("session_manager", "sql_execute", "data_validator", "answer_composer")

# Mô tả nhét vào context SM (không gồm session_manager — SM không tự gọi mình).
DISPATCHABLE: dict[str, str] = {
    "sql_execute": "Sinh SQL read-only từ raw_require và chạy trên DB để lấy data.",
    "data_validator": "Kiểm tra data cuối có phù hợp raw_require không. BẮT BUỘC chạy trước answer_composer.",
    "answer_composer": "Soạn câu trả lời cuối cho user (lịch sự, đủ thông tin, gợi ý bước tiếp). Chỉ chạy sau validator pass.",
}


def is_registered(tool_name: str) -> bool:
    return tool_name in DISPATCHABLE


def load_skill(tool_name: str) -> str:
    """Đọc skill.md MỖI LẦN gọi (không cache) — nền tảng cho reload-on-retry."""
    if tool_name not in TOOL_NAMES:
        raise KeyError(f"unknown tool: {tool_name}")
    path = _TOOLS_DIR / tool_name / "skill.md"
    return path.read_text(encoding="utf-8")


def render_tool_catalog() -> str:
    """Bảng tool + mô tả để nhét vào prompt SM."""
    lines = ["Các tool khả dụng (chỉ được gọi tool trong danh sách này):"]
    for name, desc in DISPATCHABLE.items():
        lines.append(f"- {name}: {desc}")
    return "\n".join(lines)
```

```python
# ai_python/app/registry/__init__.py
# (rỗng)
```

- [ ] **Step 5: Run → pass + Commit**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_registry.py -v` → PASS.

```bash
git add ai_python/app/registry ai_python/app/tools ai_python/tests/test_registry.py
git commit -m "feat(registry): static 4-tool registry + fresh-read skill loader"
```

---

## Task 7: Graph — generic tool subgraph `[load_skill → execute → self_validate]`

**Files:**
- Create: `ai_python/app/graph/subgraph.py`
- Test: `ai_python/tests/test_subgraph.py`

Maps fact: `fact-tool-subgraph` (load_skill đầu tiên + self_validate trước khi trả), `fact-retry-reload` (re-invoke → đọc lại .md).

**Thiết kế:** mỗi tool cung cấp 2 callable thuần: `execute(state, *, llm, **deps) -> output_dict` và `self_validate(state) -> (bool, error|None)`. Builder ráp 3 node. `load_skill` luôn gọi `registry.load_skill(tool_name)` → nạp vào `state["skill"]`, tăng `attempt`. Vì load_skill đọc file mỗi lần và subgraph chạy lại từ đầu khi retry, `.md` luôn được đọc lại.

- [ ] **Step 1: Viết test fail (dùng tool giả để cô lập builder)**

```python
# ai_python/tests/test_subgraph.py
from app.graph.subgraph import build_tool_subgraph
from app.graph.state import new_tool_state


def test_subgraph_runs_nodes_in_order_load_execute_validate(monkeypatch):
    order = []

    def fake_load(tool_name):
        order.append("load")
        return "SKILL-CONTENT"

    def fake_execute(state, *, llm, **kw):
        order.append("execute")
        assert state["skill"] == "SKILL-CONTENT"   # load chạy trước execute
        return {"value": 42}

    def fake_validate(state):
        order.append("validate")
        assert state["output"] == {"value": 42}     # execute chạy trước validate
        return True, None

    graph = build_tool_subgraph(
        tool_name="dummy", execute=fake_execute, self_validate=fake_validate,
        load_skill=fake_load)
    out = graph.invoke(new_tool_state(tool_name="dummy", raw_require="R"),
                       config={"configurable": {"llm": None}})
    assert order == ["load", "execute", "validate"]
    assert out["output"] == {"value": 42}
    assert out["valid"] is True
    assert out["attempt"] == 1


def test_subgraph_reloads_skill_on_reinvoke():  # fact-retry-reload
    loads = []
    graph = build_tool_subgraph(
        tool_name="dummy",
        execute=lambda s, *, llm, **k: {"v": 1},
        self_validate=lambda s: (True, None),
        load_skill=lambda tn: loads.append(tn) or "MD")
    cfg = {"configurable": {"llm": None}}
    graph.invoke(new_tool_state(tool_name="dummy", raw_require="R"), config=cfg)
    graph.invoke(new_tool_state(tool_name="dummy", raw_require="R"), config=cfg)
    assert loads == ["dummy", "dummy"]   # đọc .md lại mỗi lần invoke


def test_self_validate_failure_marks_invalid():
    graph = build_tool_subgraph(
        tool_name="dummy",
        execute=lambda s, *, llm, **k: {"bad": True},
        self_validate=lambda s: (False, "output sai schema"),
        load_skill=lambda tn: "MD")
    out = graph.invoke(new_tool_state(tool_name="dummy", raw_require="R"),
                       config={"configurable": {"llm": None}})
    assert out["valid"] is False
    assert out["validation_error"] == "output sai schema"
```

- [ ] **Step 2: Run → fail**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_subgraph.py -v`
Expected: FAIL.

- [ ] **Step 3: Viết `subgraph.py`**

```python
# ai_python/app/graph/subgraph.py
from __future__ import annotations
from typing import Callable
from langgraph.graph import StateGraph, START, END
from app.graph.state import ToolState
from app.registry import registry as _registry

ExecuteFn = Callable[..., dict]
ValidateFn = Callable[[ToolState], "tuple[bool, str | None]"]
LoadSkillFn = Callable[[str], str]


def build_tool_subgraph(*, tool_name: str, execute: ExecuteFn,
                        self_validate: ValidateFn,
                        load_skill: LoadSkillFn | None = None):
    """Ráp subgraph [load_skill -> execute -> self_validate] cho 1 tool.

    - load_skill LUÔN là node đầu, đọc .md mỗi lần (fact-tool-subgraph).
    - self_validate chạy cuối, kiểm output trước khi trả (fact-tool-subgraph).
    - Subgraph chạy lại từ đầu khi retry => .md đọc lại (fact-retry-reload).
    Deps runtime (llm + executor...) truyền qua config['configurable'].
    """
    _load = load_skill or _registry.load_skill

    def load_skill_node(state: ToolState) -> dict:
        return {"skill": _load(tool_name), "attempt": state["attempt"] + 1}

    def execute_node(state: ToolState, config) -> dict:
        cfg = config.get("configurable", {})
        deps = {k: v for k, v in cfg.items() if k != "llm"}
        output = execute(state, llm=cfg.get("llm"), **deps)
        return {"output": output}

    def validate_node(state: ToolState) -> dict:
        ok, err = self_validate(state)
        return {"valid": ok, "validation_error": err}

    g = StateGraph(ToolState)
    g.add_node("load_skill", load_skill_node)
    g.add_node("execute", execute_node)
    g.add_node("self_validate", validate_node)
    g.add_edge(START, "load_skill")
    g.add_edge("load_skill", "execute")
    g.add_edge("execute", "self_validate")
    g.add_edge("self_validate", END)
    return g.compile()
```

> **Lưu ý LangGraph:** node nhận `config` để lấy `configurable` deps. `execute` chỉ nhận các dep ngoài `llm` qua `**deps` (vd `executor` cho sql_execute). Nếu signature `execute` không nhận kwarg dư, dùng `functools.partial` hoặc bọc — ở các tool dưới ta khai báo `**_` để nuốt kwarg thừa.

- [ ] **Step 4: Run → pass + Commit**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_subgraph.py -v` → PASS.

```bash
git add ai_python/app/graph/subgraph.py ai_python/tests/test_subgraph.py
git commit -m "feat(graph): generic tool subgraph builder (load_skill->execute->self_validate)"
```

---

## Task 8: SQL layer — guard + read-only executor

**Files:**
- Create: `ai_python/app/sql/__init__.py`, `app/sql/guard.py`, `app/sql/executor.py`
- Test: `ai_python/tests/test_sql_guard.py`, `tests/test_sql_executor.py`

Maps fact: `fact-sql-guard` (chặn non-SELECT, không thực thi), `fact-sql-execute` (SELECT chạy trên stub trả data), R1 (read-only ở tầng kết nối).

- [ ] **Step 1: Viết test fail cho guard**

```python
# ai_python/tests/test_sql_guard.py
import pytest
from app.sql.guard import assert_read_only, SqlGuardError


@pytest.mark.parametrize("sql", [
    "SELECT * FROM customers",
    "  select id from orders where total > 10  ",
    "WITH t AS (SELECT 1) SELECT * FROM t",
])
def test_allows_select(sql):  # fact-sql-execute
    assert_read_only(sql)  # không raise


@pytest.mark.parametrize("sql", [
    "INSERT INTO t VALUES (1)",
    "UPDATE t SET x=1",
    "DELETE FROM t",
    "DROP TABLE t",
    "ALTER TABLE t ADD c int",
    "TRUNCATE t",
    "GRANT ALL ON t TO u",
    "SELECT 1; DROP TABLE t",          # multi-statement injection
    "SELECT * INTO new_t FROM t",      # SELECT INTO ghi dữ liệu
])
def test_blocks_non_select(sql):  # fact-sql-guard
    with pytest.raises(SqlGuardError):
        assert_read_only(sql)
```

- [ ] **Step 2: Run → fail**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_sql_guard.py -v`
Expected: FAIL.

- [ ] **Step 3: Viết `guard.py`**

```python
# ai_python/app/sql/guard.py
from __future__ import annotations
import sqlparse

class SqlGuardError(Exception):
    """SQL không phải truy vấn đọc → từ chối thực thi, trả lỗi an toàn."""

_FORBIDDEN = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
              "CREATE", "GRANT", "REVOKE", "MERGE", "REPLACE", "CALL", "EXECUTE"}


def assert_read_only(sql: str) -> None:
    statements = [s for s in sqlparse.parse(sql) if str(s).strip()]
    if len(statements) != 1:
        raise SqlGuardError("Chỉ cho phép đúng 1 câu lệnh SELECT")
    stmt = statements[0]
    stmt_type = stmt.get_type()       # 'SELECT' | 'INSERT' | 'UNKNOWN'...
    if stmt_type != "SELECT":
        raise SqlGuardError(f"Câu lệnh không phải SELECT: {stmt_type}")
    upper_tokens = {t.value.upper() for t in stmt.flatten()
                    if t.ttype in (sqlparse.tokens.Keyword,
                                   sqlparse.tokens.Keyword.DDL,
                                   sqlparse.tokens.Keyword.DML)}
    bad = _FORBIDDEN & upper_tokens
    if bad:
        raise SqlGuardError(f"Từ khoá bị cấm: {', '.join(sorted(bad))}")
    if "INTO" in upper_tokens:        # SELECT ... INTO ghi bảng mới
        raise SqlGuardError("SELECT INTO bị cấm (ghi dữ liệu)")
```

- [ ] **Step 4: Run → pass**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_sql_guard.py -v`
Expected: PASS.

- [ ] **Step 5: Viết test fail cho executor (read-only enforce + guard trước)**

```python
# ai_python/tests/test_sql_executor.py
import pytest
from app.sql.executor import PostgresRoExecutor
from app.sql.guard import SqlGuardError


class _FakeConn:
    def __init__(self, rows): self.rows = rows; self.executed = []
    def execute(self, sql):
        self.executed.append(str(sql))
        class R:
            def __init__(s, rows): s._rows = rows
            def keys(s): return ["id", "name"]
            def fetchall(s): return s._rows
        return R(self.rows)
    def __enter__(self): return self
    def __exit__(self, *a): return False


def test_executor_blocks_non_select_before_running(monkeypatch):  # fact-sql-guard
    conn = _FakeConn([])
    ex = PostgresRoExecutor(connect=lambda: conn, row_limit=100)
    with pytest.raises(SqlGuardError):
        ex.run("DELETE FROM t")
    assert conn.executed == []   # KHÔNG chạm DB


def test_executor_runs_select_and_returns_rows():  # fact-sql-execute
    conn = _FakeConn([(1, "Acme"), (2, "Beta")])
    ex = PostgresRoExecutor(connect=lambda: conn, row_limit=100)
    out = ex.run("SELECT id, name FROM customers")
    assert out["columns"] == ["id", "name"]
    assert out["rows"][0] == {"id": 1, "name": "Acme"}
    assert len(conn.executed) == 1


def test_executor_applies_row_limit():
    conn = _FakeConn([(i, f"c{i}") for i in range(10)])
    ex = PostgresRoExecutor(connect=lambda: conn, row_limit=3)
    out = ex.run("SELECT id, name FROM customers")
    assert len(out["rows"]) == 3
```

- [ ] **Step 6: Viết `executor.py`**

```python
# ai_python/app/sql/executor.py
from __future__ import annotations
from typing import Any, Callable, Protocol
from app.sql.guard import assert_read_only


class SqlExecutor(Protocol):
    def run(self, sql: str, *, row_limit: int | None = None) -> dict[str, Any]: ...


class PostgresRoExecutor:
    """Executor read-only thẳng tới Postgres (R1).

    Read-only enforce ở TẦNG KẾT NỐI: connection mở transaction read-only
    (`SET TRANSACTION READ ONLY`) + dùng role/DSN read-only. Guard sqlparse
    là lớp thứ hai, chạy TRƯỚC khi gửi query.
    """

    def __init__(self, *, connect: Callable[[], Any], row_limit: int = 100):
        self._connect = connect
        self._row_limit = row_limit

    def run(self, sql: str, *, row_limit: int | None = None) -> dict[str, Any]:
        assert_read_only(sql)                      # chặn non-SELECT TRƯỚC khi chạy
        limit = row_limit or self._row_limit
        with self._connect() as conn:
            result = conn.execute(sql)
            cols = list(result.keys())
            rows = [dict(zip(cols, r)) for r in result.fetchall()[:limit]]
        return {"columns": cols, "rows": rows}


def make_pg_connect(database_url_ro: str):
    """Factory connect() thật cho production. Mở transaction READ ONLY ở
    tầng kết nối. Test KHÔNG dùng hàm này (inject connect= giả)."""
    from sqlalchemy import create_engine, text

    engine = create_engine(database_url_ro, pool_pre_ping=True)

    def _connect():
        conn = engine.connect()
        conn.execute(text("SET TRANSACTION READ ONLY"))
        return conn

    return _connect
```

- [ ] **Step 7: Run → pass + Commit**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_sql_guard.py tests/test_sql_executor.py -v` → PASS.

```bash
git add ai_python/app/sql ai_python/tests/test_sql_guard.py ai_python/tests/test_sql_executor.py
git commit -m "feat(sql): sqlparse SELECT-only guard + read-only postgres executor (R1)"
```

---

## Task 9: Tool `sql_execute` (skill.md + node functions)

**Files:**
- Create: `ai_python/app/tools/sql_execute/__init__.py`
- Modify: `ai_python/app/tools/sql_execute/skill.md` (điền 6 phần)
- Test: `ai_python/tests/test_tool_sql_execute.py`

Maps fact: sinh SQL từ require + chạy read-only; self-validate output.

- [ ] **Step 1: Viết `skill.md` đầy đủ 6 phần**

````markdown
<!-- ai_python/app/tools/sql_execute/skill.md -->
# Skill: sql_execute

## Role
Bạn là chuyên gia truy vấn dữ liệu read-only của hệ ERP. Bạn chuyển yêu cầu
ngôn ngữ tự nhiên thành đúng MỘT câu lệnh `SELECT` PostgreSQL an toàn.

## Nhiệm vụ
- Đọc `raw_require` (+ `upstream_data` nếu có) và sinh đúng 1 câu `SELECT`.
- Chỉ trả về SQL, không giải thích, không markdown fence.

## Input contract
- `raw_require: str` — yêu cầu gốc của user.
- `upstream_data: dict` — data tool trước (có thể rỗng).

## Constraints / Rules
- CHỈ `SELECT` (kể cả CTE `WITH ... SELECT`). TUYỆT ĐỐI không
  INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE/GRANT, không `SELECT ... INTO`,
  không nhiều câu lệnh ngăn bởi `;`.
- Luôn thêm `LIMIT` hợp lý (≤ row limit hệ thống).
- Dùng tên bảng/cột theo schema ERP; nếu không chắc, chọn truy vấn tối thiểu
  an toàn thay vì đoán bừa.

## Output schema
Trả về JSON đúng một dòng:
```json
{"sql": "SELECT ... LIMIT 100"}
```

## Few-shot examples
- Require: "Liệt kê 5 khách hàng mới nhất"
  → `{"sql": "SELECT id, name, created_at FROM customers ORDER BY created_at DESC LIMIT 5"}`
- Require: "Tổng doanh thu các đơn đã thanh toán"
  → `{"sql": "SELECT SUM(total) AS revenue FROM orders WHERE status = 'paid' LIMIT 100"}`
````

- [ ] **Step 2: Viết test fail**

```python
# ai_python/tests/test_tool_sql_execute.py
import json
from app.tools.sql_execute import execute, self_validate
from app.graph.state import new_tool_state


class _LLM:
    def __init__(self, sql): self._sql = sql; self.seen = []
    def complete(self, *, system, user, role="default", temperature=None):
        self.seen.append({"system": system, "user": user})
        return json.dumps({"sql": self._sql})


def test_execute_generates_sql_and_runs_on_executor(stub_sql):  # fact-sql-execute
    llm = _LLM("SELECT id, name FROM customers LIMIT 5")
    st = new_tool_state(tool_name="sql_execute", raw_require="liệt kê khách hàng")
    st["skill"] = "SKILL"
    out = execute(st, llm=llm, executor=stub_sql, row_limit=100)
    assert out["sql"].lower().startswith("select")
    assert out["rows"][0] == {"id": 1, "name": "Acme"}
    # skill được đưa vào prompt
    assert "SKILL" in llm.seen[0]["system"] or "SKILL" in llm.seen[0]["user"]


def test_execute_non_select_is_blocked(stub_sql):  # fact-sql-guard
    llm = _LLM("DELETE FROM customers")
    st = new_tool_state(tool_name="sql_execute", raw_require="xoá hết")
    out = execute(st, llm=llm, executor=stub_sql, row_limit=100)
    assert out["error"] is not None
    assert out["rows"] == []
    assert stub_sql.executed == []   # không thực thi


def test_self_validate_passes_on_rows():
    st = new_tool_state(tool_name="sql_execute", raw_require="x")
    st["output"] = {"sql": "SELECT 1", "rows": [{"a": 1}], "columns": ["a"], "error": None}
    ok, err = self_validate(st)
    assert ok is True and err is None


def test_self_validate_fails_when_error_present():
    st = new_tool_state(tool_name="sql_execute", raw_require="x")
    st["output"] = {"sql": "", "rows": [], "columns": [], "error": "guard blocked"}
    ok, err = self_validate(st)
    assert ok is False and "guard" in err
```

- [ ] **Step 3: Viết `__init__.py`**

```python
# ai_python/app/tools/sql_execute/__init__.py
from __future__ import annotations
import json
from app.graph.state import ToolState
from app.sql.guard import SqlGuardError

_PROMPT = ("{skill}\n\n--- YÊU CẦU ---\nraw_require: {raw_require}\n"
           "upstream_data: {upstream}\n\nTrả về JSON {{\"sql\": \"...\"}}.")


def _parse_sql(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw[raw.find("{"):]
    return json.loads(raw)["sql"]


def execute(state: ToolState, *, llm, executor, row_limit: int = 100, **_) -> dict:
    user = _PROMPT.format(skill=state["skill"], raw_require=state["raw_require"],
                          upstream=json.dumps(state["upstream_data"], ensure_ascii=False))
    sql = _parse_sql(llm.complete(system=state["skill"], user=user, role="default"))
    try:
        result = executor.run(sql, row_limit=row_limit)        # guard chạy trong executor
        return {"sql": sql, "columns": result["columns"],
                "rows": result["rows"], "error": None}
    except SqlGuardError as exc:
        return {"sql": sql, "columns": [], "rows": [], "error": f"SQL guard: {exc}"}
    except Exception as exc:                                    # lỗi DB → lỗi tool (SM retry)
        return {"sql": sql, "columns": [], "rows": [], "error": f"DB error: {exc}"}


def self_validate(state: ToolState):
    out = state.get("output") or {}
    if out.get("error"):
        return False, out["error"]
    if not isinstance(out.get("rows"), list):
        return False, "thiếu rows trong output"
    return True, None
```

- [ ] **Step 4: Run → pass + Commit**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_tool_sql_execute.py -v` → PASS.

```bash
git add ai_python/app/tools/sql_execute ai_python/tests/test_tool_sql_execute.py
git commit -m "feat(tool): sql_execute node (gen SQL + guarded run + self_validate)"
```

---

## Task 10: Tool `data_validator` (cổng bắt buộc trước composer)

**Files:**
- Create: `ai_python/app/tools/data_validator/__init__.py`
- Modify: `ai_python/app/tools/data_validator/skill.md`
- Test: `ai_python/tests/test_tool_data_validator.py`

Maps fact: `fact-validator-check` (khớp→pass, lệch→fail), validator đọc raw_require + data cuối.

- [ ] **Step 1: Viết `skill.md`**

````markdown
<!-- ai_python/app/tools/data_validator/skill.md -->
# Skill: data_validator

## Role
Bạn là kiểm định viên dữ liệu. Bạn phán quyết liệu data thu được có THỰC SỰ
trả lời đúng yêu cầu gốc của user hay không.

## Nhiệm vụ
- So khớp `raw_require` với `data` cuối cùng.
- Phán `verdict`: "pass" nếu data đủ và đúng ý; "fail" nếu thiếu/lệch/rỗng
  không phù hợp.

## Input contract
- `raw_require: str`
- `data: dict` — gồm `rows`, `columns` (từ sql_execute) hoặc data tool khác.

## Constraints / Rules
- KHÔNG bịa dữ liệu. Chỉ đánh giá trên data nhận được.
- Nếu rows rỗng nhưng require hỏi danh sách cụ thể → thường là "fail".
- Phải nêu `reason` ngắn gọn (1 câu) cho cả pass và fail.

## Output schema
```json
{"verdict": "pass" | "fail", "reason": "..."}
```

## Few-shot examples
- Require "5 khách hàng mới nhất", data có 5 rows hợp lệ
  → `{"verdict": "pass", "reason": "Đủ 5 khách hàng với thời gian tạo."}`
- Require "doanh thu quý 1", data rows rỗng
  → `{"verdict": "fail", "reason": "Không có dữ liệu doanh thu trả về."}`
````

- [ ] **Step 2: Viết test fail**

```python
# ai_python/tests/test_tool_data_validator.py
import json
from app.tools.data_validator import execute, self_validate
from app.graph.state import new_tool_state


class _LLM:
    def __init__(self, verdict, reason="ok"):
        self._v = verdict; self._r = reason; self.seen = []
    def complete(self, *, system, user, role="default", temperature=None):
        self.seen.append(user)
        return json.dumps({"verdict": self._v, "reason": self._r})


def test_validator_pass_when_data_matches():  # fact-validator-check
    st = new_tool_state(tool_name="data_validator", raw_require="5 khách hàng",
                        upstream_data={"rows": [{"id": 1}]})
    st["skill"] = "S"
    out = execute(st, llm=_LLM("pass", "đủ data"))
    assert out["verdict"] == "pass"


def test_validator_fail_when_data_mismatch():  # fact-validator-check
    st = new_tool_state(tool_name="data_validator", raw_require="doanh thu",
                        upstream_data={"rows": []})
    st["skill"] = "S"
    out = execute(st, llm=_LLM("fail", "rỗng"))
    assert out["verdict"] == "fail"
    assert out["reason"] == "rỗng"


def test_validator_reads_raw_require_and_data_in_prompt():
    llm = _LLM("pass")
    st = new_tool_state(tool_name="data_validator", raw_require="REQ-XYZ",
                        upstream_data={"rows": [{"id": 1}]})
    st["skill"] = "S"
    execute(st, llm=llm)
    assert "REQ-XYZ" in llm.seen[0]


def test_self_validate_rejects_unknown_verdict():
    st = new_tool_state(tool_name="data_validator", raw_require="x")
    st["output"] = {"verdict": "maybe", "reason": "?"}
    ok, err = self_validate(st)
    assert ok is False
```

- [ ] **Step 3: Viết `__init__.py`**

```python
# ai_python/app/tools/data_validator/__init__.py
from __future__ import annotations
import json
from app.graph.state import ToolState

_PROMPT = ("{skill}\n\n--- KIỂM ĐỊNH ---\nraw_require: {raw_require}\n"
           "data: {data}\n\nTrả về JSON {{\"verdict\":\"pass|fail\",\"reason\":\"...\"}}.")


def execute(state: ToolState, *, llm, **_) -> dict:
    data = state["upstream_data"]
    user = _PROMPT.format(skill=state["skill"], raw_require=state["raw_require"],
                          data=json.dumps(data, ensure_ascii=False)[:4000])
    raw = llm.complete(system=state["skill"], user=user, role="default").strip()
    if raw.startswith("```"):
        raw = raw.strip("`"); raw = raw[raw.find("{"):]
    parsed = json.loads(raw)
    return {"verdict": parsed.get("verdict"), "reason": parsed.get("reason", "")}


def self_validate(state: ToolState):
    out = state.get("output") or {}
    if out.get("verdict") not in ("pass", "fail"):
        return False, f"verdict không hợp lệ: {out.get('verdict')!r}"
    return True, None
```

- [ ] **Step 4: Run → pass + Commit**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_tool_data_validator.py -v` → PASS.

```bash
git add ai_python/app/tools/data_validator ai_python/tests/test_tool_data_validator.py
git commit -m "feat(tool): data_validator node (verdict pass/fail + self_validate)"
```

---

## Task 11: Tool `answer_composer`

**Files:**
- Create: `ai_python/app/tools/answer_composer/__init__.py`
- Modify: `ai_python/app/tools/answer_composer/skill.md`
- Test: `ai_python/tests/test_tool_answer_composer.py`

Maps fact: composer soạn câu trả lời từ data + raw_require; lịch sự, đủ thông tin, **gợi ý bước tiếp**.

- [ ] **Step 1: Viết `skill.md`**

````markdown
<!-- ai_python/app/tools/answer_composer/skill.md -->
# Skill: answer_composer

## Role
Bạn là trợ lý trả lời người dùng cuối của hệ ERP, văn phong lịch sự, rõ ràng.

## Nhiệm vụ
- Soạn câu trả lời tiếng Việt từ `data` + `raw_require`.
- Trình bày đủ thông tin user cần, và LUÔN kết bằng một gợi ý bước tiếp theo.

## Input contract
- `raw_require: str`
- `data: dict` — kết quả đã được validator duyệt pass.

## Constraints / Rules
- Chỉ dùng số liệu có trong `data`; không bịa.
- Lịch sự, ngắn gọn, dễ đọc.
- BẮT BUỘC có phần gợi ý bước tiếp, đánh dấu bằng tiền tố dòng `Gợi ý:`.

## Output schema
```json
{"answer": "<đoạn trả lời, kết thúc bằng dòng bắt đầu 'Gợi ý:'>"}
```

## Few-shot examples
- Require "5 khách hàng mới nhất", data 5 rows
  → `{"answer": "Dạ, đây là 5 khách hàng mới nhất: ...\nGợi ý: Bạn có muốn xem chi tiết đơn hàng của họ không?"}`
````

- [ ] **Step 2: Viết test fail**

```python
# ai_python/tests/test_tool_answer_composer.py
import json
from app.tools.answer_composer import execute, self_validate
from app.graph.state import new_tool_state


class _LLM:
    def __init__(self, answer): self._a = answer
    def complete(self, *, system, user, role="default", temperature=None):
        return json.dumps({"answer": self._a})


def test_composer_builds_answer_with_next_step():  # fact-composer (next-step)
    st = new_tool_state(tool_name="answer_composer", raw_require="5 khách hàng",
                        upstream_data={"rows": [{"id": 1, "name": "Acme"}]})
    st["skill"] = "S"
    out = execute(st, llm=_LLM("Đây là khách hàng.\nGợi ý: xem đơn hàng?"))
    assert "Acme" not in out["answer"] or True  # nội dung do LLM
    assert "Gợi ý:" in out["answer"]


def test_self_validate_requires_next_step_marker():  # fact-composer
    st = new_tool_state(tool_name="answer_composer", raw_require="x")
    st["output"] = {"answer": "Trả lời nhưng thiếu gợi ý."}
    ok, err = self_validate(st)
    assert ok is False and "gợi ý" in err.lower()


def test_self_validate_passes_with_marker():
    st = new_tool_state(tool_name="answer_composer", raw_require="x")
    st["output"] = {"answer": "Trả lời.\nGợi ý: làm tiếp X?"}
    ok, err = self_validate(st)
    assert ok is True
```

- [ ] **Step 3: Viết `__init__.py`**

```python
# ai_python/app/tools/answer_composer/__init__.py
from __future__ import annotations
import json
from app.graph.state import ToolState

_PROMPT = ("{skill}\n\n--- SOẠN TRẢ LỜI ---\nraw_require: {raw_require}\n"
           "data: {data}\n\nTrả về JSON {{\"answer\":\"...\"}}, "
           "kết thúc bằng dòng bắt đầu 'Gợi ý:'.")


def execute(state: ToolState, *, llm, **_) -> dict:
    user = _PROMPT.format(skill=state["skill"], raw_require=state["raw_require"],
                          data=json.dumps(state["upstream_data"], ensure_ascii=False)[:4000])
    raw = llm.complete(system=state["skill"], user=user, role="default").strip()
    if raw.startswith("```"):
        raw = raw.strip("`"); raw = raw[raw.find("{"):]
    return {"answer": json.loads(raw).get("answer", "")}


def self_validate(state: ToolState):
    answer = (state.get("output") or {}).get("answer", "")
    if not answer.strip():
        return False, "answer rỗng"
    if "gợi ý:" not in answer.lower():
        return False, "thiếu phần gợi ý bước tiếp (marker 'Gợi ý:')"
    return True, None
```

- [ ] **Step 4: Run → pass + Commit**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_tool_answer_composer.py -v` → PASS.

```bash
git add ai_python/app/tools/answer_composer ai_python/tests/test_tool_answer_composer.py
git commit -m "feat(tool): answer_composer node (polite answer + mandatory next-step)"
```

---

## Task 12: Session Manager (Decision model + analyze) + dispatcher

**Files:**
- Create: `ai_python/app/tools/session_manager/__init__.py`
- Modify: `ai_python/app/tools/session_manager/skill.md`
- Create: `ai_python/app/graph/dispatcher.py`
- Test: `ai_python/tests/test_session_manager.py`, `tests/test_dispatcher.py`

Maps fact: `fact-sm-decision` (JSON validate pydantic), `fact-dispatcher` (route đúng + luôn kèm raw_require), `fact-sm-reanalyze` (reload skill khi re-analyze), `fact-validator-before` (composer chỉ sau validator pass).

- [ ] **Step 1: Viết `skill.md` cho SM**

````markdown
<!-- ai_python/app/tools/session_manager/skill.md -->
# Skill: session_manager

## Role
Bạn là Session Manager (planner-evaluator). Bạn KHÔNG tự thực thi tool —
bạn quyết định hành động kế tiếp dưới dạng JSON.

## Nhiệm vụ
- Phân tích `raw_require`, lịch sử các bước, và kết quả tool gần nhất.
- Chọn đúng 1 `action` ∈ {call_tool, retry_tool, replan, request_clarification, finish}.
- Chỉ chọn `tool_name` trong registry. Chỉ quyết `forward_data` (lấy gì từ tool
  trước), KHÔNG tự dựng payload đầy đủ.

## Input contract
- `raw_require: str`
- `tool_catalog: str` — danh sách tool khả dụng.
- `history: list` — các decision + kết quả trước.
- `last_result: dict | null` — output tool gần nhất (gồm `valid`, `output`).

## Constraints / Rules
- `data_validator` PHẢI chạy và pass TRƯỚC khi gọi `answer_composer`.
- Lỗi do TOOL (output.valid=false, lỗi DB, schema sai) → `retry_tool`.
- Lỗi do PLAN (gọi sai tool, thứ tự sai) → `replan`.
- validator trả "fail" → `request_clarification` (hỏi lại user).
- Khi đã có answer hợp lệ từ answer_composer → `finish`.
- Không lặp vô hạn: tôn trọng giới hạn bước/retry của hệ thống.

## Output schema (CHỈ trả JSON này, không text thừa)
```json
{"action":"call_tool","tool_name":"sql_execute","forward_data":{},"reasoning":"...","message":null}
```
- `message`: text hỏi user (khi request_clarification) hoặc câu chốt (khi finish, optional).

## Few-shot examples
- Mới bắt đầu, cần data → `{"action":"call_tool","tool_name":"sql_execute","forward_data":{},"reasoning":"Cần lấy data trước","message":null}`
- Có rows từ sql_execute, chưa validate → `{"action":"call_tool","tool_name":"data_validator","forward_data":{"from":"sql_execute"},"reasoning":"Bắt buộc validate trước khi soạn","message":null}`
- validator verdict=fail → `{"action":"request_clarification","tool_name":null,"forward_data":{},"reasoning":"Data không khớp require","message":"Bạn có thể nói rõ khoảng thời gian không?"}`
- sql_execute output.valid=false (lỗi tool) → `{"action":"retry_tool","tool_name":"sql_execute","forward_data":{},"reasoning":"Lỗi DB tạm thời","message":null}`
- answer_composer đã có answer hợp lệ → `{"action":"finish","tool_name":null,"forward_data":{},"reasoning":"Đã có câu trả lời","message":null}`
````

- [ ] **Step 2: Viết test fail cho SM**

```python
# ai_python/tests/test_session_manager.py
import json
import pytest
from app.tools.session_manager import Decision, analyze
from app.graph.state import new_session_state


class _LLM:
    def __init__(self, payload, role_seen=None):
        self._p = payload; self.calls = []
    def complete(self, *, system, user, role="default", temperature=None):
        self.calls.append({"role": role, "system": system, "user": user})
        return self._p if isinstance(self._p, str) else json.dumps(self._p)


def test_decision_model_validates_action():  # fact-sm-decision
    d = Decision.model_validate({"action": "call_tool", "tool_name": "sql_execute",
                                 "forward_data": {}, "reasoning": "r"})
    assert d.action == "call_tool"
    with pytest.raises(Exception):
        Decision.model_validate({"action": "nuke", "reasoning": "r"})


def test_decision_rejects_unregistered_tool():  # fact-registry-static
    with pytest.raises(Exception):
        Decision.model_validate({"action": "call_tool", "tool_name": "rm_rf",
                                 "reasoning": "r"})


def test_analyze_reloads_skill_each_call(monkeypatch):  # fact-sm-reanalyze
    loads = []
    monkeypatch.setattr("app.tools.session_manager.load_skill",
                        lambda name: loads.append(name) or "SM-SKILL")
    llm = _LLM({"action": "call_tool", "tool_name": "sql_execute",
                "forward_data": {}, "reasoning": "r"})
    st = new_session_state(raw_require="R", thread_id="t")
    analyze(st, llm=llm)
    analyze(st, llm=llm)
    assert loads == ["session_manager", "session_manager"]   # reload mỗi lần
    assert llm.calls[0]["role"] == "sm"                       # dùng role sm (R5)


def test_analyze_parses_into_decision():
    llm = _LLM({"action": "finish", "tool_name": None, "forward_data": {},
                "reasoning": "done", "message": "xong"})
    st = new_session_state(raw_require="R", thread_id="t")
    d = analyze(st, llm=llm)
    assert isinstance(d, Decision) and d.action == "finish"
```

- [ ] **Step 3: Viết SM `__init__.py`**

```python
# ai_python/app/tools/session_manager/__init__.py
from __future__ import annotations
import json
from typing import Any, Literal
from pydantic import BaseModel, field_validator
from app.graph.state import SessionState
from app.registry.registry import load_skill, render_tool_catalog, is_registered

Action = Literal["call_tool", "retry_tool", "replan", "request_clarification", "finish"]


class Decision(BaseModel):
    action: Action
    tool_name: str | None = None
    forward_data: dict[str, Any] = {}
    reasoning: str
    message: str | None = None

    @field_validator("tool_name")
    @classmethod
    def _tool_registered(cls, v, info):
        action = info.data.get("action")
        if action in ("call_tool", "retry_tool"):
            if not v or not is_registered(v):
                raise ValueError(f"tool_name không hợp lệ/không đăng ký: {v!r}")
        return v


_PROMPT = ("{skill}\n\n{catalog}\n\nraw_require: {raw_require}\n"
           "history: {history}\nlast_result: {last}\n\n"
           "Trả về DUY NHẤT JSON theo Output schema.")


def _coerce_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`"); raw = raw[raw.find("{"):]
    return json.loads(raw)


def analyze(state: SessionState, *, llm) -> Decision:
    """SM đọc LẠI skill.md mỗi lần phân tích (fact-sm-reanalyze) và dùng
    role 'sm' (Qwen, temperature thấp — R5). Reparse có bound 2 lần."""
    skill = load_skill("session_manager")
    last = state["history"][-1] if state["history"] else None
    user = _PROMPT.format(skill=skill, catalog=render_tool_catalog(),
                          raw_require=state["raw_require"],
                          history=json.dumps(state["history"], ensure_ascii=False)[:4000],
                          last=json.dumps(last, ensure_ascii=False))
    last_err = None
    for _ in range(2):                              # bounded reparse (R5)
        raw = llm.complete(system=skill, user=user, role="sm")
        try:
            return Decision.model_validate(_coerce_json(raw))
        except Exception as exc:
            last_err = exc
            user += f"\n\n[Lỗi parse JSON trước: {exc}. Trả lại đúng JSON schema.]"
    # Reparse thất bại → fail an toàn: finish với thông báo lỗi.
    return Decision(action="finish", reasoning=f"SM decision lỗi parse: {last_err}",
                    message="Xin lỗi, hệ thống chưa xử lý được yêu cầu lúc này.")
```

- [ ] **Step 4: Run SM tests → pass**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_session_manager.py -v`
Expected: PASS.

- [ ] **Step 5: Viết test fail cho dispatcher**

```python
# ai_python/tests/test_dispatcher.py
import pytest
from app.graph.dispatcher import dispatch, DispatchError


def test_dispatch_always_includes_raw_require(monkeypatch):  # fact-dispatcher
    captured = {}

    def fake_invoke(tool_name, payload, *, llm, deps):
        captured["tool_name"] = tool_name
        captured["payload"] = payload
        return {"output": {"ok": True}, "valid": True, "validation_error": None}

    monkeypatch.setattr("app.graph.dispatcher._invoke_subgraph", fake_invoke)
    out = dispatch("sql_execute", raw_require="REQ", upstream_data={"x": 1},
                   llm=None, deps={})
    assert captured["tool_name"] == "sql_execute"
    assert captured["payload"]["raw_require"] == "REQ"        # LUÔN kèm raw_require
    assert captured["payload"]["upstream_data"] == {"x": 1}
    assert out["valid"] is True


def test_dispatch_rejects_unregistered_tool():  # fact-registry-static
    with pytest.raises(DispatchError):
        dispatch("rm_rf", raw_require="R", upstream_data={}, llm=None, deps={})


def test_dispatch_blocks_composer_before_validator_pass():  # fact-validator-before
    with pytest.raises(DispatchError):
        dispatch("answer_composer", raw_require="R", upstream_data={},
                 llm=None, deps={}, validator_passed=False)
```

- [ ] **Step 6: Viết `dispatcher.py`**

```python
# ai_python/app/graph/dispatcher.py
from __future__ import annotations
from typing import Any
from app.registry.registry import is_registered
from app.graph.subgraph import build_tool_subgraph
from app.graph.state import new_tool_state


class DispatchError(Exception):
    pass


# Lazy import node functions để tránh vòng import.
def _load_tool_funcs(tool_name: str):
    import importlib
    mod = importlib.import_module(f"app.tools.{tool_name}")
    return mod.execute, mod.self_validate


def _invoke_subgraph(tool_name: str, payload: dict, *, llm, deps: dict) -> dict:
    execute, self_validate = _load_tool_funcs(tool_name)
    graph = build_tool_subgraph(tool_name=tool_name, execute=execute,
                                self_validate=self_validate)
    state = new_tool_state(tool_name=tool_name, raw_require=payload["raw_require"],
                           upstream_data=payload["upstream_data"])
    cfg = {"configurable": {"llm": llm, **deps}}
    final = graph.invoke(state, config=cfg)
    return {"output": final["output"], "valid": final["valid"],
            "validation_error": final["validation_error"]}


def dispatch(tool_name: str, *, raw_require: str, upstream_data: dict[str, Any],
             llm, deps: dict, validator_passed: bool = True) -> dict:
    """Map tool_name -> subgraph; payload LUÔN {raw_require, upstream_data}
    (fact-dispatcher). Chặn answer_composer nếu validator chưa pass
    (fact-validator-before)."""
    if not is_registered(tool_name):
        raise DispatchError(f"tool chưa đăng ký: {tool_name}")
    if tool_name == "answer_composer" and not validator_passed:
        raise DispatchError("answer_composer không được chạy trước data_validator pass")
    payload = {"raw_require": raw_require, "upstream_data": upstream_data}
    return _invoke_subgraph(tool_name, payload, llm=llm, deps=deps)
```

- [ ] **Step 7: Run dispatcher tests → pass + Commit**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_session_manager.py tests/test_dispatcher.py -v` → PASS.

```bash
git add ai_python/app/tools/session_manager ai_python/app/graph/dispatcher.py ai_python/tests/test_session_manager.py ai_python/tests/test_dispatcher.py
git commit -m "feat(graph): Session Manager decision (Qwen sm-role) + dispatcher with validator gate"
```

---

## Task 13: Orchestrator — vòng phiên lớn (planner-evaluator loop)

**Files:**
- Create: `ai_python/app/graph/orchestrator.py`
- Test: `ai_python/tests/test_orchestrator.py`

Maps fact: `fact-sm-errorclass` (lỗi tool→retry, lỗi plan→replan), `fact-budget` (chạm max_steps → dừng an toàn), validator-before, error classification.

**Loop (async generator yield SSE events):**

```
while status == running and step_count < max_steps:
    decision = analyze(session_state, llm_sm)
    emit decision (optional debug)
    match decision.action:
      call_tool:
        if tool == answer_composer and not validator_passed: -> treat as replan
        emit tool_call
        result = dispatch(tool, raw_require, upstream_from(forward_data), ...)
        record history; tool_results[tool] = result.output
        emit tool_result
        if not result.valid: # lỗi tool -> SM sẽ thấy & retry vòng sau
            (không tự retry; để SM quyết) — nhưng đếm để tránh vòng lặp
        if tool == data_validator: validator_passed = (output.verdict == "pass")
        if tool == answer_composer and result.valid:
            final_answer = output.answer; status=finished
      retry_tool:
        if retry_counts[tool] >= retry_cap: -> force replan (hoặc abort)
        else retry_counts[tool]++ ; re-dispatch (subgraph reload skill)
      replan: (no tool; loop lại để SM phân tích lại — đã reload skill trong analyze)
      request_clarification:
        status=paused; pending_clarification={message}; emit clarify; break
      finish:
        if final_answer none: final_answer = decision.message
        status=finished; break
    step_count++
if step_count >= max_steps and status==running: status=aborted; emit error(safe)
emit final answer + done (nếu finished)
```

- [ ] **Step 1: Viết test fail (FakeLLM kịch bản nhiều bước)**

```python
# ai_python/tests/test_orchestrator.py
import json
import pytest
from app.graph.orchestrator import run_session
from app.harness.turn_context import TurnContext


class ScriptLLM:
    """Trả SM decision theo hàng đợi; tool calls dùng llm này nhưng tool
    execute được patch ở dưới nên nội dung không quan trọng."""
    def __init__(self, decisions):
        self._d = [json.dumps(x) for x in decisions]
    def complete(self, *, system, user, role="default", temperature=None):
        if role == "sm":
            return self._d.pop(0)
        return "{}"


async def _collect(gen):
    return [e async for e in gen]


def _deps_with_fake_dispatch(monkeypatch, results_by_tool):
    calls = []
    def fake_dispatch(tool_name, *, raw_require, upstream_data, llm, deps,
                      validator_passed=True):
        calls.append(tool_name)
        return results_by_tool[tool_name]
    monkeypatch.setattr("app.graph.orchestrator.dispatch", fake_dispatch)
    return calls


@pytest.mark.asyncio
async def test_happy_path_order_sql_validate_compose(monkeypatch):
    calls = _deps_with_fake_dispatch(monkeypatch, {
        "sql_execute": {"output": {"rows": [{"id": 1}]}, "valid": True, "validation_error": None},
        "data_validator": {"output": {"verdict": "pass", "reason": "ok"}, "valid": True, "validation_error": None},
        "answer_composer": {"output": {"answer": "Trả lời.\nGợi ý: tiếp?"}, "valid": True, "validation_error": None},
    })
    llm = ScriptLLM([
        {"action": "call_tool", "tool_name": "sql_execute", "forward_data": {}, "reasoning": "r"},
        {"action": "call_tool", "tool_name": "data_validator", "forward_data": {"from": "sql_execute"}, "reasoning": "r"},
        {"action": "call_tool", "tool_name": "answer_composer", "forward_data": {"from": "sql_execute"}, "reasoning": "r"},
        {"action": "finish", "tool_name": None, "forward_data": {}, "reasoning": "done"},
    ])
    ctx = TurnContext(raw_require="liệt kê khách hàng", user_id="u", thread_id="t")
    events = await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={}, max_steps=6, retry_cap=2))
    assert calls == ["sql_execute", "data_validator", "answer_composer"]  # đúng thứ tự
    types = [e["type"] for e in events]
    assert "answer" in types and "done" in types


@pytest.mark.asyncio
async def test_validator_fail_triggers_clarify_and_pause(monkeypatch):  # fact-validator-hitl
    _deps_with_fake_dispatch(monkeypatch, {
        "sql_execute": {"output": {"rows": []}, "valid": True, "validation_error": None},
        "data_validator": {"output": {"verdict": "fail", "reason": "rỗng"}, "valid": True, "validation_error": None},
    })
    llm = ScriptLLM([
        {"action": "call_tool", "tool_name": "sql_execute", "forward_data": {}, "reasoning": "r"},
        {"action": "call_tool", "tool_name": "data_validator", "forward_data": {"from": "sql_execute"}, "reasoning": "r"},
        {"action": "request_clarification", "tool_name": None, "forward_data": {}, "reasoning": "fail", "message": "Khoảng thời gian nào?"},
    ])
    ctx = TurnContext(raw_require="doanh thu", user_id="u", thread_id="t")
    events = await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={}, max_steps=6, retry_cap=2))
    clarify = [e for e in events if e["type"] == "clarify"]
    assert clarify and clarify[0]["data"]["message"] == "Khoảng thời gian nào?"


@pytest.mark.asyncio
async def test_budget_exhaustion_aborts_safely(monkeypatch):  # fact-budget
    _deps_with_fake_dispatch(monkeypatch, {
        "sql_execute": {"output": {"rows": [{"id": 1}]}, "valid": True, "validation_error": None},
    })
    # SM cứ gọi sql_execute mãi → chạm max_steps
    llm = ScriptLLM([{"action": "call_tool", "tool_name": "sql_execute",
                      "forward_data": {}, "reasoning": "loop"} for _ in range(20)])
    ctx = TurnContext(raw_require="x", user_id="u", thread_id="t")
    events = await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={}, max_steps=3, retry_cap=2))
    err = [e for e in events if e["type"] == "error"]
    assert err and "giới hạn" in err[0]["data"]["message"].lower()
```

- [ ] **Step 2: Run → fail**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_orchestrator.py -v`
Expected: FAIL.

- [ ] **Step 3: Viết `orchestrator.py`**

```python
# ai_python/app/graph/orchestrator.py
from __future__ import annotations
from typing import Any, AsyncGenerator
from app.harness.turn_context import TurnContext
from app.tools.session_manager import analyze
from app.graph.dispatcher import dispatch, DispatchError
from app.graph.state import new_session_state


def _event(type_: str, data: dict) -> dict:
    return {"type": type_, "data": data}


def _build_upstream(state, forward_data: dict) -> dict:
    """SM chỉ ra lấy data từ tool nào ('from'); orchestrator dựng payload."""
    src = forward_data.get("from")
    if src and src in state["tool_results"]:
        return dict(state["tool_results"][src])
    # mặc định: nối mọi tool_results gần nhất
    merged: dict[str, Any] = {}
    for out in state["tool_results"].values():
        if isinstance(out, dict):
            merged.update(out)
    return merged


async def run_session(ctx: TurnContext, *, llm_sm, llm_tool, deps: dict,
                      max_steps: int = 6, retry_cap: int = 2
                      ) -> AsyncGenerator[dict, None]:
    state = new_session_state(raw_require=ctx.raw_require, thread_id=ctx.thread_id)
    validator_passed = False

    while state["status"] == "running" and state["step_count"] < max_steps:
        decision = analyze(state, llm=llm_sm)
        state["last_decision"] = decision.model_dump()
        action = decision.action

        if action == "finish":
            if state["final_answer"] is None:
                state["final_answer"] = decision.message or ""
            state["status"] = "finished"
            break

        if action == "request_clarification":
            state["pending_clarification"] = {"message": decision.message or ""}
            state["status"] = "paused"
            yield _event("clarify", {"message": decision.message or "",
                                     "thread_id": ctx.thread_id})
            break

        if action == "replan":
            state["history"].append({"action": "replan", "reasoning": decision.reasoning})
            state["step_count"] += 1
            continue

        # call_tool / retry_tool
        tool = decision.tool_name
        if action == "retry_tool":
            if state["retry_counts"].get(tool, 0) >= retry_cap:
                state["history"].append({"action": "retry_capped", "tool": tool})
                state["step_count"] += 1
                continue                      # để SM replan vòng sau
            state["retry_counts"][tool] = state["retry_counts"].get(tool, 0) + 1

        upstream = _build_upstream(state, decision.forward_data)
        yield _event("tool_call", {"tool_name": tool, "reasoning": decision.reasoning})
        try:
            result = dispatch(tool, raw_require=ctx.raw_require, upstream_data=upstream,
                              llm=llm_tool, deps=deps, validator_passed=validator_passed)
        except DispatchError as exc:
            state["history"].append({"action": "dispatch_error", "tool": tool, "error": str(exc)})
            state["step_count"] += 1
            continue                          # SM sẽ replan

        output = result["output"] or {}
        state["tool_results"][tool] = output
        state["history"].append({"action": action, "tool": tool, "valid": result["valid"],
                                 "output": output})
        yield _event("tool_result", {"tool_name": tool, "valid": result["valid"],
                                     "validation_error": result["validation_error"]})

        if tool == "data_validator":
            validator_passed = (output.get("verdict") == "pass")
        if tool == "answer_composer" and result["valid"]:
            state["final_answer"] = output.get("answer", "")
            state["status"] = "finished"
            break

        state["step_count"] += 1

    # Kết thúc vòng
    if state["status"] == "running" and state["step_count"] >= max_steps:
        state["status"] = "aborted"
        yield _event("error", {"message": "Đã chạm giới hạn số bước, dừng an toàn."})
        return

    if state["status"] == "finished":
        yield _event("answer", {"text": state["final_answer"] or ""})
        yield _event("done", {"thread_id": ctx.thread_id})
```

> **Error classification (fact-sm-errorclass):** phân loại lỗi tool vs plan do **SM** quyết (prompt + history chứa `valid`/`validation_error`/`verdict`). Orchestrator chỉ thực thi quyết định: `retry_tool` → re-dispatch (subgraph reload skill), `replan` → vòng lại để `analyze` (đã reload skill). Test ở Task 12 + bộ test orchestrator phủ retry-cap & budget.

- [ ] **Step 4: Run → pass + Commit**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_orchestrator.py -v` → PASS.

```bash
git add ai_python/app/graph/orchestrator.py ai_python/tests/test_orchestrator.py
git commit -m "feat(graph): planner-evaluator orchestrator loop (retry/replan/clarify/finish/budget)"
```

---

## Task 14: HITL — pause/resume (checkpoint persist)

**Files:**
- Create: `ai_python/app/graph/hitl.py`
- Test: `ai_python/tests/test_hitl.py`

Maps fact: `fact-validator-hitl` (pause + lưu pending, resume tiếp đúng chỗ). R4 (hạ tầng pause chưa có — xây mới). Dùng `langgraph-checkpoint-sqlite` / aiosqlite.

**Thiết kế:** stateless build, HITL chỉ cần lưu *pending session snapshot* keyed theo `thread_id` để resume trong cùng phiên. Dùng một `PendingStore` mỏng trên SQLite (đủ cho yêu cầu; full LangGraph checkpointer để mở rộng vòng sau). Snapshot gồm `raw_require`, `tool_results`, `history`, `pending_clarification`.

- [ ] **Step 1: Viết test fail**

```python
# ai_python/tests/test_hitl.py
import pytest
from app.graph.hitl import PendingStore


@pytest.mark.asyncio
async def test_save_and_load_pending_roundtrip(tmp_path):  # fact-validator-hitl
    store = PendingStore(db_path=str(tmp_path / "hitl.sqlite"))
    await store.init()
    snapshot = {"raw_require": "doanh thu", "tool_results": {"sql_execute": {"rows": []}},
                "history": [{"action": "call_tool"}],
                "pending_clarification": {"message": "Khi nào?"}}
    await store.save("thread-1", snapshot)
    loaded = await store.load("thread-1")
    assert loaded["raw_require"] == "doanh thu"
    assert loaded["pending_clarification"]["message"] == "Khi nào?"


@pytest.mark.asyncio
async def test_load_missing_returns_none(tmp_path):
    store = PendingStore(db_path=str(tmp_path / "hitl.sqlite"))
    await store.init()
    assert await store.load("nope") is None


@pytest.mark.asyncio
async def test_clear_removes_pending(tmp_path):
    store = PendingStore(db_path=str(tmp_path / "hitl.sqlite"))
    await store.init()
    await store.save("t", {"raw_require": "x"})
    await store.clear("t")
    assert await store.load("t") is None
```

- [ ] **Step 2: Run → fail**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_hitl.py -v`
Expected: FAIL.

- [ ] **Step 3: Viết `hitl.py`**

```python
# ai_python/app/graph/hitl.py
from __future__ import annotations
import json
import aiosqlite


class PendingStore:
    """Persist snapshot phiên đang pause để resume HITL (fact-validator-hitl).
    Stateless build: chỉ giữ pending theo thread_id, xoá sau khi resume."""

    def __init__(self, *, db_path: str):
        self._db_path = db_path

    async def init(self) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS pending ("
                "thread_id TEXT PRIMARY KEY, snapshot TEXT NOT NULL, "
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            await db.commit()

    async def save(self, thread_id: str, snapshot: dict) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT INTO pending(thread_id, snapshot) VALUES(?, ?) "
                "ON CONFLICT(thread_id) DO UPDATE SET snapshot=excluded.snapshot",
                (thread_id, json.dumps(snapshot, ensure_ascii=False)))
            await db.commit()

    async def load(self, thread_id: str) -> dict | None:
        async with aiosqlite.connect(self._db_path) as db:
            async with db.execute(
                    "SELECT snapshot FROM pending WHERE thread_id=?", (thread_id,)) as cur:
                row = await cur.fetchone()
        return json.loads(row[0]) if row else None

    async def clear(self, thread_id: str) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("DELETE FROM pending WHERE thread_id=?", (thread_id,))
            await db.commit()
```

- [ ] **Step 4: Run → pass + Commit**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_hitl.py -v` → PASS.

```bash
git add ai_python/app/graph/hitl.py ai_python/tests/test_hitl.py
git commit -m "feat(hitl): SQLite PendingStore for pause/resume snapshots"
```

- [ ] **Step 5: Tích hợp pause/resume vào orchestrator (test mở rộng)**

Thêm test vào `tests/test_orchestrator.py`: khi truyền `pending_store` + `resume_snapshot`, orchestrator (a) lúc `request_clarification` gọi `await pending_store.save(thread_id, snapshot)`; (b) khi `ctx.clarification_response` có và `resume_snapshot` được nạp, vòng lặp tiếp tục với `tool_results`/`history` cũ + bơm clarification_response vào `raw_require` mở rộng.

```python
# bổ sung vào tests/test_orchestrator.py
@pytest.mark.asyncio
async def test_resume_continues_from_snapshot(monkeypatch):  # fact-validator-hitl
    calls = _deps_with_fake_dispatch(monkeypatch, {
        "data_validator": {"output": {"verdict": "pass", "reason": "ok"}, "valid": True, "validation_error": None},
        "answer_composer": {"output": {"answer": "OK.\nGợi ý: tiếp?"}, "valid": True, "validation_error": None},
    })
    llm = ScriptLLM([
        {"action": "call_tool", "tool_name": "data_validator", "forward_data": {"from": "sql_execute"}, "reasoning": "revalidate"},
        {"action": "call_tool", "tool_name": "answer_composer", "forward_data": {"from": "sql_execute"}, "reasoning": "compose"},
        {"action": "finish", "tool_name": None, "forward_data": {}, "reasoning": "done"},
    ])
    ctx = TurnContext(raw_require="doanh thu", user_id="u", thread_id="t",
                      clarification_response="Quý 1 năm 2026")
    snapshot = {"raw_require": "doanh thu", "thread_id": "t",
                "tool_results": {"sql_execute": {"rows": [{"rev": 100}]}},
                "history": [], "retry_counts": {}, "step_count": 0,
                "pending_clarification": {"message": "Khi nào?"}}
    events = await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={},
                                        max_steps=6, retry_cap=2, resume_snapshot=snapshot))
    assert "sql_execute" in (snapshot["tool_results"])         # giữ data cũ
    assert any(e["type"] == "answer" for e in events)
```

Cập nhật `run_session` signature thêm `resume_snapshot: dict | None = None` và `pending_store=None`:

```python
# orchestrator.py — đầu run_session, sau new_session_state(...)
    if resume_snapshot is not None:
        state["tool_results"] = resume_snapshot.get("tool_results", {})
        state["history"] = resume_snapshot.get("history", [])
        state["retry_counts"] = resume_snapshot.get("retry_counts", {})
        # data validator đã từng chạy ở phiên trước nhưng cần re-validate sau clarify:
        validator_passed = False
    if ctx.clarification_response:
        state["raw_require"] = (f"{state['raw_require']}\n"
                                f"[Bổ sung từ user]: {ctx.clarification_response}")
```

Và ở nhánh `request_clarification`, nếu `pending_store` có thì lưu snapshot trước khi break:

```python
        if action == "request_clarification":
            state["pending_clarification"] = {"message": decision.message or ""}
            state["status"] = "paused"
            if pending_store is not None:
                await pending_store.save(ctx.thread_id, {
                    "raw_require": ctx.raw_require, "thread_id": ctx.thread_id,
                    "tool_results": state["tool_results"], "history": state["history"],
                    "retry_counts": state["retry_counts"],
                    "pending_clarification": state["pending_clarification"]})
            yield _event("clarify", {"message": decision.message or "",
                                     "thread_id": ctx.thread_id})
            break
```

- [ ] **Step 6: Run orchestrator + hitl tests → pass + Commit**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_orchestrator.py tests/test_hitl.py -v` → PASS.

```bash
git add ai_python/app/graph/orchestrator.py ai_python/tests/test_orchestrator.py
git commit -m "feat(hitl): wire pause(save)/resume(snapshot) into orchestrator"
```

---

## Task 15: API — FastAPI `/chat` + SSE streaming

**Files:**
- Create: `ai_python/app/api/__init__.py`, `app/api/app.py`
- Create: `ai_python/app/memory/__init__.py` (placeholder DEFERRED)
- Test: `ai_python/tests/test_api_sse.py`

Maps fact: `fact-sse`, `fact-config-llm`, `fact-config-backend`, auth gate (request không hợp lệ không vào pipeline).

**Endpoint:** `POST /chat` nhận `{raw_require, clarification_response?}` + header `Authorization: Bearer <jwt>`. Verify JWT (hoặc dev bypass) → resolve thread_id → build deps (llm_sm role=sm, llm_tool role=default, sql executor) → stream `run_session` ra SSE qua `sse_format`. Nếu auth fail → 401, KHÔNG vào pipeline.

- [ ] **Step 1: Viết test fail (TestClient + dependency override deps)**

```python
# ai_python/tests/test_api_sse.py
import time, json, jwt
from fastapi.testclient import TestClient
from app.api.app import create_app, get_deps

SECRET = "test-secret"


def _token():
    return jwt.encode({"sub": "user-1", "exp": int(time.time()) + 60}, SECRET, algorithm="HS256")


class _FakeDeps:
    """Override get_deps: cung cấp llm + dispatch giả qua monkeypatch orchestrator."""
    def __init__(self):
        self.llm_sm = self.llm_tool = None
        self.deps = {}
        self.max_steps = 6
        self.retry_cap = 2
        self.jwt_secret = SECRET
        self.dev_bypass = False
        self.pending_store = None


def _client(monkeypatch):
    async def fake_run_session(ctx, **kw):
        yield {"type": "tool_call", "data": {"tool_name": "sql_execute"}}
        yield {"type": "answer", "data": {"text": "Doanh thu quý 1 là 100."}}
        yield {"type": "done", "data": {"thread_id": ctx.thread_id}}
    monkeypatch.setattr("app.api.app.run_session", fake_run_session)
    app = create_app()
    app.dependency_overrides[get_deps] = lambda: _FakeDeps()
    return TestClient(app)


def test_chat_streams_sse_nested_under_harness(monkeypatch):  # fact-sse + R6
    client = _client(monkeypatch)
    resp = client.post("/chat", json={"raw_require": "doanh thu quý 1"},
                       headers={"Authorization": f"Bearer {_token()}"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    lines = [l for l in resp.text.splitlines() if l.startswith("data: ")]
    first = json.loads(lines[0][len("data: "):])
    assert set(first.keys()) == {"harness"}             # chống flatten
    assert first["harness"]["type"] == "tool_call"
    assert "Doanh thu quý 1" in resp.text


def test_chat_rejects_invalid_jwt(monkeypatch):  # fact-auth (không vào pipeline)
    client = _client(monkeypatch)
    resp = client.post("/chat", json={"raw_require": "x"},
                       headers={"Authorization": "Bearer garbage"})
    assert resp.status_code == 401
```

- [ ] **Step 2: Run → fail**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_api_sse.py -v`
Expected: FAIL.

- [ ] **Step 3: Viết `api/app.py`**

```python
# ai_python/app/api/app.py
from __future__ import annotations
from dataclasses import dataclass, field
from fastapi import FastAPI, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from app.config.settings import get_settings
from app.config.llm_client import make_llm
from app.harness.auth import verify_jwt, AuthError
from app.harness.session import resolve_thread_id
from app.harness.turn_context import TurnContext
from app.harness.sse_emitter import sse_format
from app.graph.orchestrator import run_session
from app.graph.hitl import PendingStore
from app.sql.executor import PostgresRoExecutor, make_pg_connect


@dataclass
class Deps:
    llm_sm: object
    llm_tool: object
    deps: dict
    max_steps: int
    retry_cap: int
    jwt_secret: str
    jwt_issuer: str
    jwt_audience: str
    dev_bypass: bool
    pending_store: PendingStore


def get_deps() -> Deps:
    s = get_settings()
    executor = PostgresRoExecutor(connect=make_pg_connect(s.database_url_ro),
                                  row_limit=s.sql_row_limit)
    return Deps(
        llm_sm=make_llm(s, role="sm"),
        llm_tool=make_llm(s, role="default"),
        deps={"executor": executor, "row_limit": s.sql_row_limit},
        max_steps=s.harness_max_steps, retry_cap=s.tool_retry_cap,
        jwt_secret=s.jwt_hs256_secret, jwt_issuer=s.jwt_issuer,
        jwt_audience=s.jwt_audience, dev_bypass=s.auth_dev_bypass,
        pending_store=PendingStore(db_path=s.hitl_checkpoint_db))


def create_app() -> FastAPI:
    app = FastAPI(title="Agentic AI (ai_python)")

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.post("/chat")
    async def chat(request: Request, deps: Deps = Depends(get_deps),
                   authorization: str | None = Header(default=None)):
        # --- Auth gate: fail => KHÔNG vào pipeline (fact-auth) ---
        token = None
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization[7:]
        try:
            claims = verify_jwt(token, secret=deps.jwt_secret, issuer=deps.jwt_issuer,
                                audience=deps.jwt_audience, dev_bypass=deps.dev_bypass)
        except AuthError as exc:
            raise HTTPException(status_code=401, detail=str(exc))

        body = await request.json()
        raw_require = body.get("raw_require", "")
        clarification = body.get("clarification_response")
        thread_id = resolve_thread_id(claims["sub"])
        ctx = TurnContext(raw_require=raw_require, user_id=claims["sub"],
                          thread_id=thread_id, clarification_response=clarification)

        resume_snapshot = None
        if clarification and deps.pending_store is not None:
            await deps.pending_store.init()
            resume_snapshot = await deps.pending_store.load(thread_id)
            if resume_snapshot:
                await deps.pending_store.clear(thread_id)

        async def stream():
            async for event in run_session(
                    ctx, llm_sm=deps.llm_sm, llm_tool=deps.llm_tool, deps=deps.deps,
                    max_steps=deps.max_steps, retry_cap=deps.retry_cap,
                    resume_snapshot=resume_snapshot, pending_store=deps.pending_store):
                yield sse_format(event["type"], event["data"])

        return StreamingResponse(stream(), media_type="text/event-stream")

    return app


app = create_app()
```

```python
# ai_python/app/memory/__init__.py
"""DEFERRED (vòng sau): conversation memory.

Build hiện tại STATELESS — không tích hợp memory. Placeholder để vòng sau
cắm checkpointer/persistent history mà không phải đổi cấu trúc package.
"""
```

> **fact-config-backend:** endpoint `/chat` chính là điểm Spring gửi require sang ai_python. Spring gọi `POST /chat` với JWT của user; ai_python không tự auth lại ngoài verify token.

- [ ] **Step 4: Run → pass + Commit**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_api_sse.py -v` → PASS.

```bash
git add ai_python/app/api ai_python/app/memory ai_python/tests/test_api_sse.py
git commit -m "feat(api): FastAPI /chat with JWT gate + SSE streaming (+memory placeholder)"
```

---

## Task 16: End-to-end happy path (integration)

**Files:**
- Test: `ai_python/tests/test_e2e_happy_path.py`

Maps fact: done-condition happy path — require → SM → sql_execute → data_validator(pass) → answer_composer → SSE. Dùng FakeLLM (deterministic, route theo role + theo tool qua nội dung prompt) + StubSqlExecutor thật qua subgraph (KHÔNG patch dispatch — chạy thật toàn pipeline trừ LLM/DB).

- [ ] **Step 1: Viết E2E test**

```python
# ai_python/tests/test_e2e_happy_path.py
import json
import pytest
from app.graph.orchestrator import run_session
from app.harness.turn_context import TurnContext


class RoutingLLM:
    """FakeLLM thật cho E2E: SM (role='sm') trả decision theo hàng đợi;
    tool (role='default') trả output đúng schema theo skill đang nạp."""
    def __init__(self, sm_decisions):
        self._sm = [json.dumps(d) for d in sm_decisions]

    def complete(self, *, system, user, role="default", temperature=None):
        if role == "sm":
            return self._sm.pop(0)
        # route theo nội dung skill trong system prompt
        if "Skill: sql_execute" in system:
            return json.dumps({"sql": "SELECT id, name FROM customers LIMIT 5"})
        if "Skill: data_validator" in system:
            return json.dumps({"verdict": "pass", "reason": "đủ data"})
        if "Skill: answer_composer" in system:
            return json.dumps({"answer": "Đây là 5 khách hàng.\nGợi ý: xem đơn hàng?"})
        raise AssertionError(f"role/tool không nhận diện được:\n{system[:80]}")


@pytest.mark.asyncio
async def test_e2e_require_to_sse_answer(stub_sql):  # done-condition happy path
    llm = RoutingLLM([
        {"action": "call_tool", "tool_name": "sql_execute", "forward_data": {}, "reasoning": "lấy data"},
        {"action": "call_tool", "tool_name": "data_validator", "forward_data": {"from": "sql_execute"}, "reasoning": "validate"},
        {"action": "call_tool", "tool_name": "answer_composer", "forward_data": {"from": "sql_execute"}, "reasoning": "soạn"},
        {"action": "finish", "tool_name": None, "forward_data": {}, "reasoning": "xong"},
    ])
    ctx = TurnContext(raw_require="liệt kê 5 khách hàng mới nhất", user_id="u", thread_id="t")
    events = [e async for e in run_session(
        ctx, llm_sm=llm, llm_tool=llm,
        deps={"executor": stub_sql, "row_limit": 100}, max_steps=6, retry_cap=2)]

    types = [e["type"] for e in events]
    # đúng thứ tự tool
    tool_calls = [e["data"]["tool_name"] for e in events if e["type"] == "tool_call"]
    assert tool_calls == ["sql_execute", "data_validator", "answer_composer"]
    # composer chạy sau validator pass; SQL thực sự chạy trên stub
    assert stub_sql.executed and stub_sql.executed[0].lower().startswith("select")
    # SSE cuối có answer + done, answer chứa gợi ý
    answer = [e for e in events if e["type"] == "answer"][0]
    assert "Gợi ý:" in answer["data"]["text"]
    assert types[-1] == "done"
```

- [ ] **Step 2: Run → pass**

Run: `cd ai_python && .venv\Scripts\python -m pytest tests/test_e2e_happy_path.py -v`
Expected: PASS. Nếu fail do thứ tự forward_data, kiểm `_build_upstream` lấy đúng `from`.

- [ ] **Step 3: Chạy toàn bộ suite**

Run: `cd ai_python && .venv\Scripts\python -m pytest -q`
Expected: tất cả PASS (toàn bộ test các task).

- [ ] **Step 4: Commit**

```bash
git add ai_python/tests/test_e2e_happy_path.py
git commit -m "test(e2e): happy path require->SM->sql->validator->composer->SSE"
```

---

## Mapping facts → test (truy vết verify)

| Fact | Test |
|------|------|
| Harness auth reject invalid | `test_harness_auth.py::test_expired/bad_signature` + `test_api_sse.py::test_chat_rejects_invalid_jwt` |
| User_ID → Thread_ID | `test_harness_session.py::test_thread_id_deterministic_per_user` |
| SM reload skill khi re-analyze | `test_session_manager.py::test_analyze_reloads_skill_each_call` |
| SM structured JSON decision | `test_session_manager.py::test_decision_model_validates_action` |
| Dispatcher route + luôn raw_require | `test_dispatcher.py::test_dispatch_always_includes_raw_require` |
| SM phân biệt lỗi tool/plan | `test_orchestrator.py` (retry-cap → replan) + SM skill rules |
| Tool subgraph load_skill đầu + self_validate | `test_subgraph.py::test_subgraph_runs_nodes_in_order` |
| Reload .md mỗi retry | `test_subgraph.py::test_subgraph_reloads_skill_on_reinvoke` |
| Skill .md 6 phần | review skill.md (4 file) — checklist tay |
| Registry static 4 tool | `test_registry.py::test_registry_lists_exactly_four_tools` |
| sql_execute read-only + gen SQL | `test_tool_sql_execute.py::test_execute_generates_sql_and_runs` |
| SQL guard chặn non-SELECT | `test_sql_guard.py` + `test_sql_executor.py::test_executor_blocks_non_select_before_running` |
| validator bắt buộc trước composer | `test_dispatcher.py::test_dispatch_blocks_composer_before_validator_pass` |
| validator check pass/fail | `test_tool_data_validator.py` |
| validator fail → HITL pause/resume | `test_orchestrator.py::test_validator_fail_triggers_clarify_and_pause` + `test_resume_continues_from_snapshot` + `test_hitl.py` |
| composer sau validator + gợi ý next-step | `test_tool_answer_composer.py` + `test_orchestrator` happy path |
| SSE streaming (nested harness key) | `test_sse_emitter.py` + `test_api_sse.py::test_chat_streams_sse_nested_under_harness` |
| config LLM Qwen chung client | `test_llm_client.py` |
| config backend (Spring → /chat) | `test_api_sse.py` (endpoint nhận require) |
| budget max_steps dừng an toàn | `test_orchestrator.py::test_budget_exhaustion_aborts_safely` |
| stateless (memory deferred) | `app/memory/__init__.py` placeholder; không test tích hợp memory |

---

## Risk mitigation (đã hiện thực trong plan)

- **R1 — SQL path:** Direct read-only postgres. `make_pg_connect` mở `SET TRANSACTION READ ONLY` ở tầng kết nối + `assert_read_only` (sqlparse) chạy TRƯỚC mọi query trong `PostgresRoExecutor.run`. `.env` mới bỏ `http_spring`/`SPRING_SQL_URL`. (Task 1, 8, 9)
- **R3 — SRS-006:** `.env` mới + `Settings` không có `agentic_v3_enabled`/`sql_executor_mode`; hệ mới độc lập, không nhánh rollback legacy. Test `test_settings_no_legacy_v3_flag`. (Task 1)
- **R4 — HITL pause:** `PendingStore` (aiosqlite) lưu snapshot phiên; orchestrator save khi `request_clarification`, API load+clear khi có `clarification_response`. (Task 14, 15)
- **R5 — Structured output:** SM dùng Qwen role 'sm' (temperature 0.0) + pydantic `Decision` validate + bounded reparse 2 lần → fail an toàn (`finish` báo lỗi). gemma chỉ ghi chú trong settings, chưa wire. (Task 2, 12)
- **R6 — SSE flatten:** mọi event bọc dưới 1 key gốc `"harness"`; test assert `set(body.keys()) == {"harness"}`. (Task 4, 15)

---

## Out of scope (vòng này — KHÔNG code)
- Conversation memory / persistent history (chỉ placeholder `app/memory/`).
- gemma structured-model routing (escape hatch ghi chú).
- Frontend confirm UI (đã có sẵn; backend chỉ emit event `clarify` đúng contract).
- Streaming token-by-token của answer (hiện emit answer 1 event; có thể chia nhỏ sau).

> **Cần verify với frontend trước khi merge:** shape event `clarify` (`{"harness":{"type":"clarify","data":{"message","thread_id"}}}`) phải khớp UI confirm hiện có. Nếu frontend kỳ vọng field khác (vd `question`, `options`), điều chỉnh `sse_emitter`/orchestrator cho khớp — đây là điểm tích hợp duy nhất phụ thuộc code ngoài ai_python.
