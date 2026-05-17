"""Pydantic schemas for structured LLM outputs (intent, SQL review)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class IntentOutput(BaseModel):
    intent: Literal[
        "general_chat",
        "system_data_query",
        "system_data_chart",
        "catalog_data_entry",
    ]


class SqlReviewOutput(BaseModel):
    ok: bool
    issues: list[str] = Field(default_factory=list)


class SqlTablePickOutput(BaseModel):
    """Structured output for optional table subset selection (Task007)."""

    tables: list[str] = Field(
        default_factory=list,
        description="Table names from the allowlist most relevant to the question.",
    )


class SchemaPlanOutput(BaseModel):
    """Schema explorer — tables and metric before gen_sql."""

    metric_id: Literal[
        "ledger_revenue",
        "ledger_expense",
        "ledger_net_cashflow",
        "ledger_by_dimension",
    ] = "ledger_revenue"
    tables: list[str] = Field(
        default_factory=list,
        description="Registry table names to include; must include financeledger for ledger metrics.",
    )
    dimensions: list[str] = Field(
        default_factory=list,
        description="Optional breakdown: order_channel, customer, product, fund.",
    )
    ambiguity_note: str | None = Field(
        default=None,
        description="If set, caller may ask user to clarify (MVP: passed to gen_sql prompt).",
    )


class IdeaPlannerOutput(BaseModel):
    """Chart brief — flexible objects; LLM chooses metric wording (no fixed table names required)."""

    data_request: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Business metric in natural language: expected_result_shape "
            "(time_series|single_kpi|breakdown), time range, filters, aggregation intent."
        ),
    )
    chart_idea: dict[str, Any] = Field(
        default_factory=dict,
        description="Visualization: chart_type hint, axis semantics in business language.",
    )


class ChartReadinessOutput(BaseModel):
    """LLM critic — is query result adequate for the chart brief?"""

    ok: bool
    issues: list[str] = Field(default_factory=list)
    retry_hint: str = Field(
        default="",
        description="Natural-language hint for gen_sql retry when ok=false.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal issues (e.g. single time bucket) for review/chart UI.",
    )


class ChartSpecDraftOutput(BaseModel):
    """Agent_Chart — column keys before review."""

    chart_type: Literal["line", "bar", "pie"]
    x_key: str
    y_key: str
    title: str = ""


class ChartReviewOutput(BaseModel):
    """Agent_Review — aligned keys + summary."""

    chart_type: Literal["line", "bar", "pie"]
    x_key: str
    y_key: str
    title: str = ""
    final_answer: str = ""


class CatalogEntityPickOutput(BaseModel):
    entity_type: Literal["product", "category", "supplier", "customer"] = "product"
    row_count_hint: int = Field(default=3, ge=1, le=50)


class CatalogDraftColumnOutput(BaseModel):
    key: str
    label: str = ""
    type: str = "string"
    required: bool = False
    options: list[str] | None = None


class CatalogDraftRowOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    rowId: str = "r1"
    values: dict[str, Any] = Field(default_factory=dict)


class CatalogDraftGenerateOutput(BaseModel):
    columns: list[CatalogDraftColumnOutput] = Field(default_factory=list)
    rows: list[CatalogDraftRowOutput] = Field(default_factory=list)
