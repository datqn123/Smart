from typing import Any

from pydantic import BaseModel, Field


class SearchDocsIn(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=10)
    filters: dict[str, Any] | None = None


class Chunk(BaseModel):
    id: str
    text: str
    source: dict[str, Any]
    score: float = Field(default=0.0)


class SearchDocsOut(BaseModel):
    chunks: list[Chunk]
    summary: str
    correlation_id: str


class CatalogCandidate(BaseModel):
    id: str
    name: str
    code: str
    score: float


class SearchCatalogOut(SearchDocsOut):
    candidates: list[CatalogCandidate] = Field(default_factory=list)


class McpToolError(BaseModel):
    """SRS §4 error model parity for MCP tool failures."""

    code: str
    message: str
    retryable: bool = False
    details: dict[str, Any] | None = None
    correlation_id: str = ""

    model_config = {"frozen": False}


class QueryReadonlyIn(BaseModel):
    template_id: str
    params: dict[str, Any]


class SqlColumn(BaseModel):
    name: str
    type: str


class QueryReadonlyOut(BaseModel):
    columns: list[SqlColumn]
    rows: list[list[Any]]
    row_count: int
    summary: str
    correlation_id: str


class DescribeObjectIn(BaseModel):
    object_name: str


class DescribeObjectOut(BaseModel):
    object_name: str
    columns: list[SqlColumn]
    summary: str
    correlation_id: str


# Aliases aligned with SRS naming
SearchSchemaIn = SearchDocsIn
SearchSchemaOut = SearchDocsOut
