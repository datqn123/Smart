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
    llm_temperature: float = 0.2          # tool thuong
    llm_sm_temperature: float = 0.0       # SM decision: deterministic structured (R5)
    llm_http_request_timeout: int = 120
    llm_structured_model: str = "gemma-4-26B-A4B-it"  # escape hatch, CHUA wire (R5)

    # --- SQL (direct read-only -- R1) ---
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
