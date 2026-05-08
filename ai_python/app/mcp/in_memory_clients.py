"""Test/dev MCP stubs; no outbound network here."""

from __future__ import annotations

import time

from ..contracts import (
    Chunk,
    DescribeObjectIn,
    DescribeObjectOut,
    McpToolError,
    QueryReadonlyIn,
    QueryReadonlyOut,
    SearchCatalogOut,
    SearchDocsIn,
    SearchDocsOut,
    SqlColumn,
)


class ScriptedVectorRagMcp:
    def __init__(self, *, simulate_error: str | None = None) -> None:
        self._simulate_error = simulate_error

    async def rag_search_docs(
        self,
        body: SearchDocsIn,
        *,
        correlation_id: str,
    ) -> tuple[SearchDocsOut | None, McpToolError | None]:
        if self._simulate_error == "rag_docs":
            return None, self._mk_err("RAG_TIMEOUT", correlation_id)

        ck = Chunk(
            id="c_doc_1",
            text="Định khoản và quy trình nhập liệu (ví dụ).",
            source={"path": "docs/erp_intro.md"},
            score=0.42,
        )
        return (
            SearchDocsOut(chunks=[ck], summary=f"docs_hits={1}", correlation_id=correlation_id),
            None,
        )

    async def rag_search_schema(
        self,
        body: SearchDocsIn,
        *,
        correlation_id: str,
    ) -> tuple[SearchDocsOut | None, McpToolError | None]:
        if self._simulate_error == "rag_schema":
            return None, self._mk_err("RAG_UPSTREAM_ERROR", correlation_id)

        ck = Chunk(
            id="c_sch_1",
            text="Phiếu nhập lien ket SanPham qua ReceiptLine.stock_item_id FK.",
            source={"kind": "table", "table": "receipt_note"},
            score=0.88,
        )
        return SearchDocsOut(
            chunks=[ck],
            summary=f"schema_hits={body.top_k}",
            correlation_id=correlation_id,
        ), None

    async def rag_search_catalog_optional(
        self,
        body: SearchDocsIn,
        *,
        correlation_id: str,
    ) -> tuple[SearchCatalogOut | None, McpToolError | None]:
        out, err = await self.rag_search_docs(body, correlation_id=correlation_id)
        if err:
            return None, err
        assert out is not None
        return (
            SearchCatalogOut(
                chunks=out.chunks,
                summary=out.summary,
                correlation_id=correlation_id,
                candidates=[],
            ),
            None,
        )

    def _mk_err(self, code: str, corr: str) -> McpToolError:
        return McpToolError(
            code=code,
            message="simulated rag failure",
            retryable=False,
            correlation_id=corr,
        )


class ScriptedDbReadonlyMcp:
    def __init__(self, *, reject: bool = False, row_total: float = 1_234_567.89) -> None:
        self._reject = reject
        self._row_total = row_total

    async def sql_query_readonly(
        self,
        body: QueryReadonlyIn,
        *,
        correlation_id: str,
    ) -> tuple[QueryReadonlyOut | None, McpToolError | None]:
        await _sleep_budget()
        if self._reject:
            return (
                None,
                McpToolError(
                    code="DB_QUERY_REJECTED",
                    message="blocked by allowlist/policy",
                    retryable=False,
                    correlation_id=correlation_id,
                ),
            )
        cols = [SqlColumn(name="day", type="date"), SqlColumn(name="revenue", type="numeric")]
        rows: list[list[object]] = [["2026-05-01", float(self._row_total)]]
        summary = (
            f"aggregate row_count={len(rows)}; template={body.template_id} "
            f"params_days={body.params.get('days')}"
        )
        out = QueryReadonlyOut(
            columns=cols,
            rows=rows,
            row_count=len(rows),
            summary=summary,
            correlation_id=correlation_id,
        )
        return out, None

    async def sql_describe_optional(
        self,
        body: DescribeObjectIn,
        *,
        correlation_id: str,
        limit_budget: bool = True,
    ) -> tuple[DescribeObjectOut | None, McpToolError | None]:
        await _sleep_budget()
        _ = limit_budget
        out = DescribeObjectOut(
            object_name=body.object_name,
            columns=[SqlColumn(name="id", type="bigint")],
            summary=f"describe {body.object_name}",
            correlation_id=correlation_id,
        )
        return out, None


async def _sleep_budget() -> None:
    """Yield control for async fidelity without blocking loop."""
    t0 = time.perf_counter()
    _ = t0
