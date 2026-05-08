from typing import Protocol

from ..contracts import (
    DescribeObjectIn,
    DescribeObjectOut,
    McpToolError,
    QueryReadonlyIn,
    QueryReadonlyOut,
)


class DbReadonlyMcpPort(Protocol):
    async def sql_query_readonly(
        self,
        body: QueryReadonlyIn,
        *,
        correlation_id: str,
    ) -> tuple[QueryReadonlyOut | None, McpToolError | None]: ...

    async def sql_describe_optional(
        self,
        body: DescribeObjectIn,
        *,
        correlation_id: str,
        limit_budget: bool = True,
    ) -> tuple[DescribeObjectOut | None, McpToolError | None]: ...
