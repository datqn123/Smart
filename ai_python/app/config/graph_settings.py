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

    sql_executor_mode: Literal["stub", "python_ro", "http_spring"] = Field(default="stub")
    app_env: str = Field(default="dev", description="Environment profile: dev/staging/prod.")
    database_url_ro: str | None = Field(default=None)
    spring_sql_url: str | None = Field(default=None)
    checkpoint_sqlite_path: str | None = Field(default=None)
    mask_sql: bool = Field(default=False)
    sql_allowed_tables: str | None = Field(
        default=None,
        description="Comma-separated table names; empty = allow any (dev only).",
    )
    schema_dir: str | None = Field(default=None, description="Schema YAML directory override.")
    sql_limit_max: int = Field(default=1000, description="LIMIT inject ceiling when missing.")

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

    @field_validator("app_env", mode="before")
    @classmethod
    def lower_app_env(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @model_validator(mode="after")
    def validate_prod_sql_mode(self) -> "GraphSettings":
        if self.app_env in ("prod", "production") and self.sql_executor_mode != "http_spring":
            raise ValueError("APP_ENV=prod requires SQL_EXECUTOR_MODE=http_spring")
        return self


def load_graph_settings() -> GraphSettings:
    return GraphSettings()
