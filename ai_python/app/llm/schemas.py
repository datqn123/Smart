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
        "inventory_data_entry",
    ]


class DomainIssue(BaseModel):
    type: Literal[
        "term_mismatch",
        "unknown_entity",
        "wrong_workflow",
        "out_of_scope",
        "missing_slot",
        "ambiguous_module",
        "sql_table_missing",
    ]
    user_text: str = ""
    canonical_vi: str | None = None
    canonical_en: str | None = None
    guide_ref: str | None = None
    severity: Literal["block", "warn"] = "warn"


class DomainGuardOutput(BaseModel):
    action: Literal["proceed", "clarify", "reject"]
    in_scope: bool = True
    matched_modules: list[str] = Field(default_factory=list)
    coverage: Literal["full", "partial", "unknown"] = "full"
    issues: list[DomainIssue] = Field(default_factory=list)
    missing_slots: list[str] = Field(default_factory=list)
    normalized_question: str = ""
    clarification_questions: list[str] = Field(default_factory=list)
    assistant_message: str = ""


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


class InventoryEntityPickOutput(BaseModel):
    doc_type: Literal["stock_receipt", "stock_dispatch"] = "stock_receipt"
    line_count_hint: int = Field(default=1, ge=1, le=20)


class InventoryDraftSlotsOutput(BaseModel):
    """Slots for DB lookup before inventory draft (see inventory_draft_slots.md)."""

    doc_type: Literal["stock_receipt", "stock_dispatch"] = "stock_receipt"
    line_count_hint: int = Field(default=1, ge=1, le=20)
    quantity: int | None = Field(default=None, ge=1)
    product_query: str | None = None
    product_sku: str | None = None
    supplier_query: str | None = None
    supplier_code: str | None = None


class CatalogDraftSlotsOutput(BaseModel):
    """Slots for DB lookup before catalog draft (see catalog_draft_slots.md)."""

    entity_type: Literal["product", "category", "supplier", "customer"] = "product"
    row_count_hint: int = Field(default=3, ge=1, le=50)
    quantity: int | None = Field(default=None, ge=1)
    product_query: str | None = None
    product_sku: str | None = None
    category_query: str | None = None
    category_code: str | None = None
    supplier_query: str | None = None
    supplier_code: str | None = None
    customer_query: str | None = None


class InventoryDraftLineOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    lineId: str = "l1"
    values: dict[str, Any] = Field(default_factory=dict)


class InventoryDraftColumnOutput(BaseModel):
    key: str
    label: str = ""
    type: str = "string"
    required: bool = False


class InventoryDraftGenerateOutput(BaseModel):
    header: dict[str, Any] = Field(default_factory=dict)
    lineColumns: list[InventoryDraftColumnOutput] = Field(default_factory=list)
    lines: list[InventoryDraftLineOutput] = Field(default_factory=list)
