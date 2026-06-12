# ai_python/tests/eval/conftest.py
"""Fixtures cho golden eval: LLM THAT tu env/.env, DB GIA (FakeExecutor).

Dao chieu so voi unit test (FakeLLM + StubSqlExecutor): o day LLM that,
tang I/O cuoi la vat the than. Khong sua dong code production nao.
Doi model = doi LLM_BASE_URL/LLM_API_KEY/LLM_MODEL (env de len .env);
dieu kien: endpoint ho tro native tool-calling (tool_choice ep buoc).
"""
from pathlib import Path

import pytest
from pydantic_settings import BaseSettings, SettingsConfigDict

_AI_PYTHON_DIR = Path(__file__).resolve().parent.parent.parent  # tests/eval -> ai_python


class EvalSettings(BaseSettings):
    """Chi cac truong LLM — KHONG dung app Settings vi no bat buoc
    database_url_ro (eval khong cham DB). Default trung voi Settings.
    env_file neo theo vi tri file nay de chay duoc tu bat ky CWD nao."""
    model_config = SettingsConfigDict(env_file=str(_AI_PYTHON_DIR / ".env"),
                                      env_file_encoding="utf-8",
                                      extra="ignore", case_sensitive=False)
    llm_base_url: str = ""
    llm_api_key: str = ""
    # SYNC: default 3 truong duoi giu trung app/config/settings.py Settings
    llm_model: str = "Qwen3.6-27B"
    llm_temperature: float = 0.2          # tool thuong (nhu make_llm)
    llm_sm_temperature: float = 0.0       # SM deterministic (nhu make_llm)
    llm_http_request_timeout: int = 120
    llm_max_tokens: int = 1500
    llm_disable_thinking: bool = True


class FakeExecutor:
    """Vat the than cho PostgresRoExecutor: ghi lai SQL da qua guard,
    tra rows gia de pipeline khong vo."""

    def __init__(self):
        self.captured_sql: str | None = None

    def run(self, sql: str, *, row_limit: int = 100):
        if not sql.strip().lower().startswith("select"):
            raise AssertionError("FakeExecutor nhan non-SELECT — guard da khong chan")
        self.captured_sql = sql
        return {"columns": ["name", "total"],
                "rows": [{"name": "X", "total": 1}]}


@pytest.fixture(scope="session")
def eval_settings():
    s = EvalSettings()
    if not s.llm_api_key or not s.llm_base_url:
        pytest.skip("golden eval can LLM_API_KEY + LLM_BASE_URL (env hoac ai_python/.env)")
    return s


def _make_client(s: "EvalSettings", temperature: float):
    from openai import OpenAI
    from app.config.llm_client import OpenAILLMClient
    sdk = OpenAI(base_url=s.llm_base_url, api_key=s.llm_api_key,
                 timeout=s.llm_http_request_timeout)
    return OpenAILLMClient(sdk=sdk, model=s.llm_model, temperature=temperature,
                           max_tokens=s.llm_max_tokens,
                           disable_thinking=s.llm_disable_thinking)


@pytest.fixture(scope="session")
def llm_sm(eval_settings):
    """LLM cho Session Manager — temperature 0.0 nhu make_llm(role='sm')."""
    return _make_client(eval_settings, eval_settings.llm_sm_temperature)


@pytest.fixture(scope="session")
def llm_tool(eval_settings):
    """LLM cho tool — temperature 0.2 nhu make_llm(role='default')."""
    return _make_client(eval_settings, eval_settings.llm_temperature)


@pytest.fixture
def fake_executor():
    return FakeExecutor()
