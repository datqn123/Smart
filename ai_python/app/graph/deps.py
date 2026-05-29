"""Injectable dependencies for graph compilation."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.config.graph_settings import GraphSettings
from app.harness import AgentHarness
from app.graph.sql_executor import SqlExecutor
from app.llm.registry import LlmRegistry


@dataclass
class GraphDeps:
    """Closed over by compiled graphs — no FastAPI."""

    llm_registry: LlmRegistry | None
    sql_executor: SqlExecutor
    settings: GraphSettings
    harness: AgentHarness = field(default_factory=AgentHarness)
