from app.config.settings import Settings


def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://mkp-api.fptcloud.com")
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_MODEL", "Qwen3.6-27B")
    monkeypatch.setenv("DATABASE_URL_RO", "postgresql://u:p@127.0.0.1:5432/db")
    s = Settings()
    assert s.llm_base_url == "https://mkp-api.fptcloud.com"
    assert s.llm_model == "Qwen3.6-27B"
    assert s.llm_sm_temperature == 0.0
    assert s.harness_max_steps == 6
    assert s.tool_retry_cap == 2
    assert s.database_url_ro.startswith("postgresql://")


def test_memory_settings_defaults(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://x")
    monkeypatch.setenv("LLM_API_KEY", "k")
    monkeypatch.setenv("DATABASE_URL_RO", "postgresql://x")
    s = Settings(_env_file=None)
    assert s.memory_window_turns == 10
    assert s.memory_summary_max_chars == 2000


def test_settings_no_legacy_v3_flag():
    # R3: he moi khong doc AGENTIC_V3_ENABLED / SQL_EXECUTOR_MODE
    assert not hasattr(Settings, "agentic_v3_enabled")
    assert not hasattr(Settings, "sql_executor_mode")
