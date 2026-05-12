"""Graph / SQL executor / checkpoint env (Task 2)."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GraphSettings(BaseSettings):
    """Uppercase env vars match PRD (no prefix)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    sql_executor_mode: Literal["stub", "python_ro", "http_spring"] = Field(default="http_spring")
    app_env: str = Field(default="dev", description="Environment profile: dev/staging/prod.")
    database_url_ro: str | None = Field(default=None)
    database_url_metadata_ro: str | None = Field(
        default=None,
        description="Read-only Postgres URL for ai_table_description + introspection (optional; falls back to DATABASE_URL_RO).",
    )
    spring_sql_url: str | None = Field(
        default="http://127.0.0.1:8080/api/v1/ai/db/sql/query-readonly-raw",
        description="Spring AiDbReadonlyController raw SQL endpoint (same host as Mini ERP API by default).",
    )
    spring_sql_bearer_token: str | None = Field(
        default=None,
        description="Optional Bearer token for Spring SQL endpoint (never logged).",
    )
    sql_executor_timeout_seconds: int = Field(
        default=10,
        ge=1,
        le=30,
        description="Hard timeout for executor dispatch (HTTP or future DB).",
    )
    sql_executor_row_limit: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Max rows returned per executor call (Python boundary).",
    )
    checkpoint_sqlite_path: str | None = Field(default=None)
    mask_sql: bool = Field(default=False)
    agent_terminal_trace: bool = Field(
        default=True,
        description="Log intent / SQL / review steps at INFO (AGENT_TERMINAL_TRACE=0 to disable).",
    )
    sql_allowed_tables: str | None = Field(
        default=None,
        description="Comma-separated table names; empty = allow any (dev only).",
    )
    schema_dir: str | None = Field(
        default=None,
        description="Optional YAML dir for FileSchemaLoader (tests/CLI only); SQL graph always uses Postgres.",
    )
    sql_limit_max: int = Field(default=1000, description="LIMIT inject ceiling when missing.")
    pg_metadata_schema: str = Field(default="public", description="Postgres schema for registry + introspection.")
    pg_ai_description_table: str = Field(
        default="ai_table_description",
        description="Registry table (table_name, description) per Task103.",
    )
    pg_ai_column_description_table: str = Field(
        default="ai_column_description",
        description="Registry table (table_name, column_name, description) for per-column AI hints.",
    )
    pg_metadata_connect_timeout_seconds: int = Field(default=3, ge=1, le=30)
    # --- Task007 SQL-Factory-lite (defaults off / safe fallbacks) ---
    sql_enriched_schema_prompt: bool = Field(
        default=False,
        description="Include PK/FK/table description lines in gen_sql schema block.",
    )
    sql_table_selection_enabled: bool = Field(
        default=False,
        description="Subset schema in gen_sql via heuristic / optional LLM table pick.",
    )
    sql_table_pick_use_llm: bool = Field(
        default=False,
        description="When selection enabled and schema large enough, call structured sql_table_pick.",
    )
    sql_table_pick_min_tables_for_llm: int = Field(
        default=6,
        ge=1,
        le=64,
        description="Minimum artifact table count before LLM table-pick may run.",
    )
    sql_max_selected_tables: int = Field(default=8, ge=1, le=32)
    sql_hybrid_similarity_enabled: bool = Field(
        default=False,
        description="Compare new SQL to local pool (SimTok + SimAST); may add policy feedback.",
    )
    sql_similarity_threshold: float = Field(default=0.92, ge=0.0, le=1.0)
    sql_similarity_token_weight: float = Field(
        default=0.55,
        ge=0.0,
        le=1.0,
        description="Weight for token Jaccard vs AST fingerprint overlap in hybrid score.",
    )
    sql_local_pool_max: int = Field(default=32, ge=1, le=128)
    sql_exploit_on_retry: bool = Field(
        default=True,
        description="After first gen_sql attempt, use exploitation-style prompt with seed SQL.",
    )
    sql_separate_select_tables_node: bool = Field(
        default=False,
        description="If true, subgraph may insert select_tables before gen_sql (reserved).",
    )
    sql_dialog_tail_max_messages: int = Field(
        default=12,
        ge=0,
        le=48,
        description="Max chat messages (Human+AI) appended to gen_sql/summarize prompts; 0 disables tail.",
    )
    sql_dialog_tail_max_chars: int = Field(
        default=2000,
        ge=0,
        le=16000,
        description="Max characters for dialog tail in SQL prompts; 0 disables tail.",
    )
    ai_display_timezone: str | None = Field(
        default="Asia/Ho_Chi_Minh",
        description="IANA zone for SQL summarize prompts: ISO timestamps with Z/offset → local wall time. Empty = raw.",
    )

    @field_validator("ai_display_timezone", mode="before")
    @classmethod
    def strip_ai_display_timezone(cls, v: object) -> object:
        if isinstance(v, str) and not v.strip():
            return None
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("pg_metadata_schema", "pg_ai_description_table", "pg_ai_column_description_table", mode="before")
    @classmethod
    def strip_pg_identifiers(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("spring_sql_url", mode="before")
    @classmethod
    def strip_spring_sql_url(cls, v: object) -> object:
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("sql_executor_mode", mode="before")
    @classmethod
    def lower_mode(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("mask_sql", mode="before")
    @classmethod
    def coerce_mask(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().lower() in ("1", "true", "yes")
        return bool(v)

    @field_validator("agent_terminal_trace", mode="before")
    @classmethod
    def coerce_agent_terminal_trace(cls, v: object) -> object:
        if isinstance(v, str):
            s = v.strip().lower()
            if s in ("0", "false", "no", "off"):
                return False
            if s in ("1", "true", "yes", "on"):
                return True
            return bool(s)
        return bool(v)

    @field_validator(
        "sql_enriched_schema_prompt",
        "sql_table_selection_enabled",
        "sql_table_pick_use_llm",
        "sql_hybrid_similarity_enabled",
        "sql_exploit_on_retry",
        "sql_separate_select_tables_node",
        mode="before",
    )
    @classmethod
    def coerce_sql_factory_flags(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().lower() in ("1", "true", "yes", "on")
        return bool(v)

    @field_validator("app_env", mode="before")
    @classmethod
    def lower_app_env(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("sql_dialog_tail_max_messages", "sql_dialog_tail_max_chars", mode="before")
    @classmethod
    def coerce_sql_dialog_tail_ints(cls, v: object) -> object:
        if isinstance(v, str):
            s = v.strip()
            try:
                return int(s)
            except ValueError:
                return v
        return v

    @model_validator(mode="after")
    def validate_prod_sql_mode(self) -> "GraphSettings":
        if self.app_env in ("prod", "production") and self.sql_executor_mode != "http_spring":
            raise ValueError("APP_ENV=prod requires SQL_EXECUTOR_MODE=http_spring")
        if self.sql_executor_mode == "http_spring" and not self.spring_sql_url:
            raise ValueError("SQL_EXECUTOR_MODE=http_spring requires a non-empty SPRING_SQL_URL")
        return self


def load_graph_settings() -> GraphSettings:
    return GraphSettings()
