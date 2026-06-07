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
    spring_api_base_url: str | None = Field(
        default="http://127.0.0.1:8080",
        description="Spring Mini ERP API base (catalog-drafts, relay).",
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
    schema_cache_enabled: bool = Field(
        default=True,
        description="Enable in-process schema metadata cache for Postgres registry/introspection.",
    )
    schema_cache_ttl_seconds: int = Field(
        default=600,
        ge=30,
        le=3600,
        description="TTL for schema metadata cache items.",
    )
    schema_cache_max_items: int = Field(
        default=64,
        ge=1,
        le=256,
        description="LRU capacity for schema metadata cache.",
    )
    schema_fingerprint_check_interval_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Interval between lightweight DB fingerprint checks.",
    )
    sql_review_max_retries: int = Field(
        default=2,
        ge=0,
        le=8,
        description="Max structured retries for sql_review LLM call.",
    )
    sql_review_skip_low_risk: bool = Field(
        default=True,
        description="Skip sql_review LLM for low-risk SQL queries when deterministic checks already pass.",
    )
    sql_repair_max_attempts: int = Field(
        default=3,
        ge=1,
        le=12,
        description="Global SQL repair attempts budget (retry loop cap).",
    )
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
    sql_allowlist_fk_expand: bool = Field(
        default=True,
        description="When table selection is on, add FK ref_table neighbors to validation/prompt allowlist.",
    )
    sql_allowlist_fk_hops: int = Field(
        default=1,
        ge=0,
        le=4,
        description="FK expansion depth for effective SQL allowlist (0 = selected tables only).",
    )
    sql_allowlist_fk_extra_slots: int = Field(
        default=6,
        ge=0,
        le=16,
        description="Extra table slots beyond sql_max_selected_tables for FK join partners.",
    )
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
    # --- Ledger-first schema explorer ---
    sql_schema_explorer_enabled: bool = Field(
        default=False,
        description="Insert schema_explore node before gen_sql (list_tables + schema_plan + describe).",
    )
    sql_schema_explorer_describe_max_tables: int = Field(
        default=6,
        ge=0,
        le=16,
        description="Max Spring describe HTTP calls per schema_explore turn.",
    )
    sql_ledger_first_prompts: bool = Field(
        default=True,
        description="Ledger-first gen_sql prompts even when schema explorer is off.",
    )
    sql_validate_ledger_metric: bool = Field(
        default=True,
        description="Policy check: revenue/expense questions must use financeledger.",
    )
    # --- LLM-first chart pipeline ---
    chart_readiness_enabled: bool = Field(
        default=True,
        description="After SQL for system_data_chart, run shape checks (+ optional LLM critic) before agent_chart.",
    )
    chart_readiness_use_llm_critic: bool = Field(
        default=True,
        description="Use chart_critic LLM when heuristics warn or fail (requires LLM registry).",
    )
    chart_brief_catalog_max_tables: int = Field(
        default=40,
        ge=0,
        le=128,
        description="Max registry tables in Agent_Idea catalog snippet; 0 disables.",
    )
    chart_thread_context_max_turns: int = Field(
        default=2,
        ge=0,
        le=6,
        description="Prior user/assistant turns passed into chart brief and gen_sql.",
    )
    # --- ERP domain guard (Task112) ---
    erp_domain_guard_enabled: bool = Field(
        default=True,
        description="Run domain_guard before intent (scope, terminology, clarify).",
    )
    erp_guide_data_dir: str | None = Field(
        default=None,
        description="Override path to app/data/erp; default package data dir.",
    )
    erp_guide_retrieve_max_chunks: int = Field(
        default=3,
        ge=0,
        le=8,
        description="Max GUID chunks retrieved per turn for domain_guard.",
    )
    # --- Planner (pre-intent strategy) ---
    planner_enabled: bool = Field(
        default=True,
        description="Enable pre-intent planner node for flexible strategy selection.",
    )
    planner_md_context_enabled: bool = Field(
        default=True,
        description="Load curated markdown snippets (runtime docs) into planner context.",
    )
    planner_max_md_chars: int = Field(
        default=2600,
        ge=400,
        le=12000,
        description="Maximum markdown context characters passed to planner prompts.",
    )
    planner_confidence_threshold: float = Field(
        default=0.55,
        ge=0.0,
        le=1.0,
        description="Minimum planner confidence to apply intent override from planner output.",
    )
    # --- Context compaction (conversation memory) ---
    context_compact_enabled: bool = Field(
        default=True,
        description="Summarize and prune old messages when human turn count exceeds max.",
    )
    context_compact_max_turns: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Max user turns before compaction runs.",
    )
    context_compact_summary_lines: int = Field(
        default=8,
        ge=1,
        le=32,
        description="Target line count for LLM conversation summary.",
    )
    context_compact_keep_last_turns: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Recent user turns kept verbatim after compaction.",
    )
    # --- Answer quality (final_answer enrich) ---
    answer_quality_enabled: bool = Field(
        default=True,
        description="Heuristic gate + optional LLM enrich on final_answer (ANSWER_QUALITY_ENABLED=0 to disable).",
    )
    answer_quality_max_chars: int = Field(
        default=2000,
        ge=200,
        le=16000,
        description="Truncate final_answer after quality pass.",
    )
    answer_enrich_timeout_sec: float = Field(
        default=15.0,
        ge=3.0,
        le=120.0,
        description="Max seconds for one answer_enrich LLM call.",
    )
    # --- Harness execution boundary ---
    harness_enabled: bool = Field(
        default=True,
        description="Enable harness permission gating + lifecycle hooks for tool execution.",
    )
    harness_audit_jsonl_path: str | None = Field(
        default=None,
        description="Optional JSONL audit sink for beforeToolCall/afterToolCall events.",
    )
    harness_loop_enabled: bool = Field(
        default=False,
        description="Enable Strangler route for harness-orchestrated agentic loop.",
    )
    harness_max_steps: int = Field(
        default=6,
        ge=1,
        le=20,
        description="Maximum LLM/tool decision steps per harness loop turn.",
    )
    harness_loop_intents: list[str] = Field(
        default_factory=list,
        description="Optional override for intents routed to harness loop.",
    )
    harness_planner_role: str = Field(
        default="harness_planner",
        description="LLM registry role used for harness next-action decisions.",
    )
    # --- Agentic AI target completion P0: async boundary + budgets ---
    agentic_async_enabled: bool = Field(
        default=False,
        description="Use native async harness stream path when available.",
    )
    harness_token_budget: int = Field(
        default=0,
        ge=0,
        description="Per-turn token budget for harness loop; 0 disables token budget.",
    )
    harness_cost_budget_usd: float = Field(
        default=0.05,
        ge=0.0,
        description="Per-turn cost budget in USD for harness loop; 0 disables cost budget.",
    )
    harness_wallclock_timeout_s: float = Field(
        default=30.0,
        ge=0.0,
        description="Per-turn wall-clock timeout in seconds for harness loop; 0 disables timeout.",
    )
    # --- Agentic AI target completion P1: intent object gate ---
    agentic_intent_object_enabled: bool = Field(
        default=False,
        description="Analyze requests with IntentObject before the harness loop.",
    )
    intent_confidence_run: float = Field(default=0.9, ge=0.0, le=1.0)
    intent_confidence_hitl: float = Field(default=0.75, ge=0.0, le=1.0)
    entity_score_hitl: float = Field(default=0.6, ge=0.0, le=1.0)
    # --- Agentic AI target completion P3: SQL self-correct + data validator ---
    sql_regen_max: int = Field(default=3, ge=0, le=10)
    sql_empty_retry_max: int = Field(default=2, ge=0, le=10)
    agentic_data_validator_enabled: bool = Field(
        default=False,
        description="Enable data_validator tool in agentic flows.",
    )
    # --- Agentic AI target completion P2: PlanGraph DAG ---
    agentic_plan_dag_enabled: bool = Field(
        default=False,
        description="Enable opt-in plan-driven DAG execution for selected harness intents.",
    )
    plan_replan_max: int = Field(default=2, ge=0, le=10)
    # --- Agentic AI target completion P4: answer/chart tools ---
    agentic_answer_composer_enabled: bool = Field(
        default=False,
        description="Enable answer_composer as the final agentic answer tool.",
    )
    # --- Agentic AI target completion P6: capability guard ---
    agentic_capability_guard_enabled: bool = Field(
        default=False,
        description="Enable capability/RBAC guard extensions for agentic tools.",
    )
    # --- Agentic AI target completion P5: memory + compact ---
    working_memory_pairs: int = Field(default=6, ge=0, le=20)
    compact_context_ratio: float = Field(default=0.70, ge=0.0, le=1.0)
    semantic_store_mode: str = Field(default="memory")
    semantic_expire_days: int = Field(default=90, ge=1, le=3650)
    # --- Agentic AI target completion P7: model routing + cache ---
    agentic_model_routing_enabled: bool = Field(default=False)
    agentic_semantic_cache_enabled: bool = Field(default=False)
    opt_escalate_replan_count: int = Field(default=2, ge=0, le=10)
    # --- Agentic AI target completion P8: observability ---
    agentic_trace_enabled: bool = Field(default=True)
    # --- Agentic AI v3.0 (SRS-006) planner-brain upgrade (defaults off) ---
    agentic_v3_enabled: bool = Field(
        default=False,
        description="Master flag for v3 planner-brain runtime (observation contract, result_ref, planner-owned replan).",
    )
    agentic_v3_plan_template_enabled: bool = Field(
        default=False,
        description="Enable execution-tier fast-path using validated, version-pinned plan templates.",
    )
    agentic_v3_template_store_path: str | None = Field(
        default=None,
        description="SQLite path for PlanTemplateStore; in-memory when unset.",
    )
    agentic_v3_history_store_path: str | None = Field(
        default=None,
        description="SQLite path for K15 IntentHistoryStore; in-memory when unset.",
    )
    agentic_v3_route_accuracy_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum K12 route accuracy required before agentic_v3_enabled may roll out.",
    )
    agentic_v3_observation_sample_limit: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Max masked sample rows in an ObservationEnvelope; full data stays behind result_ref.",
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

    @field_validator("answer_quality_enabled", mode="before")
    @classmethod
    def coerce_answer_quality_enabled(cls, v: object) -> object:
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
        "sql_allowlist_fk_expand",
        "sql_table_pick_use_llm",
        "sql_hybrid_similarity_enabled",
        "sql_exploit_on_retry",
        "sql_separate_select_tables_node",
        "sql_schema_explorer_enabled",
        "sql_ledger_first_prompts",
        "sql_validate_ledger_metric",
        "chart_readiness_enabled",
        "chart_readiness_use_llm_critic",
        "planner_enabled",
        "planner_md_context_enabled",
        "context_compact_enabled",
        "schema_cache_enabled",
        "sql_review_skip_low_risk",
        "harness_enabled",
        "harness_loop_enabled",
        "agentic_async_enabled",
        "agentic_intent_object_enabled",
        "agentic_data_validator_enabled",
        "agentic_plan_dag_enabled",
        "agentic_answer_composer_enabled",
        "agentic_capability_guard_enabled",
        "agentic_model_routing_enabled",
        "agentic_semantic_cache_enabled",
        "agentic_trace_enabled",
        "agentic_v3_enabled",
        "agentic_v3_plan_template_enabled",
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

    @field_validator(
        "sql_dialog_tail_max_messages",
        "sql_dialog_tail_max_chars",
        "context_compact_max_turns",
        "context_compact_summary_lines",
        "context_compact_keep_last_turns",
        "schema_cache_ttl_seconds",
        "schema_cache_max_items",
        "schema_fingerprint_check_interval_seconds",
        "sql_review_max_retries",
        "sql_repair_max_attempts",
        "planner_max_md_chars",
        "harness_max_steps",
        "harness_token_budget",
        "sql_regen_max",
        "sql_empty_retry_max",
        "plan_replan_max",
        "working_memory_pairs",
        "semantic_expire_days",
        "opt_escalate_replan_count",
        "agentic_v3_observation_sample_limit",
        mode="before",
    )
    @classmethod
    def coerce_sql_dialog_tail_ints(cls, v: object) -> object:
        if isinstance(v, str):
            s = v.strip()
            try:
                return int(s)
            except ValueError:
                return v
        return v

    @field_validator("harness_loop_intents", mode="before")
    @classmethod
    def coerce_harness_loop_intents(cls, v: object) -> object:
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            if s.startswith("["):
                return v
            return [item.strip() for item in s.split(",") if item.strip()]
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
