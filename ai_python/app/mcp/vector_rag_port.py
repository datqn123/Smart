from typing import Protocol

from ..contracts import McpToolError, SearchCatalogOut, SearchDocsIn, SearchDocsOut


class VectorRagMcpPort(Protocol):
    async def rag_search_docs(
        self,
        body: SearchDocsIn,
        *,
        correlation_id: str,
    ) -> tuple[SearchDocsOut | None, McpToolError | None]: ...

    async def rag_search_schema(
        self,
        body: SearchDocsIn,
        *,
        correlation_id: str,
    ) -> tuple[SearchDocsOut | None, McpToolError | None]: ...

    async def rag_search_catalog_optional(
        self,
        body: SearchDocsIn,
        *,
        correlation_id: str,
    ) -> tuple[SearchCatalogOut | None, McpToolError | None]: ...
