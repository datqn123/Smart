"""PlanGraph contracts and async DAG executor for agentic harness flows."""

from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, Field

from app.harness.policy import HarnessPolicy
from app.harness.runtime import AgentHarness, ToolCallContext
from app.harness.tool_registry import ToolInput, ToolRegistry, ToolResult, TurnContext


class PlanNode(BaseModel):
    id: str
    tool: str
    needs: list[str] = Field(default_factory=list)
    input_spec: dict[str, Any] = Field(default_factory=dict)
    output_expect: str = ""


class PlanGraph(BaseModel):
    nodes: list[PlanNode] = Field(default_factory=list)


class PlanGraphOutput(PlanGraph):
    pass


class NodeResult(BaseModel):
    node_id: str
    ok: bool
    output_meets_expect: bool
    tool_result: dict[str, Any] = Field(default_factory=dict)
    observation_text: str = ""
    error: str = ""


_PLANNER_SYSTEM = (
    "You design an execution PlanGraph (a DAG) for a Smart ERP assistant.\n"
    "Output JSON: nodes=[{id, tool, needs, input_spec, output_expect}].\n"
    "Rules:\n"
    "- id: unique short string. tool: MUST be one of the listed tools.\n"
    "- needs: ids of nodes whose output this node depends on; independent nodes "
    "(empty needs) run in parallel, so only add a dependency when data must flow.\n"
    "- input_spec: arguments for the tool. To pass a parent node's output into a "
    "child, reference it as \"${parent_id.field}\" (e.g. {\"rows\": \"${rev.rows}\"} "
    "or {\"observations\": [{\"rows\": \"${rev.rows}\"}]}). Only reference ids listed "
    "in this node's needs.\n"
    "- output_expect: short phrase, use 'rows' for tabular data, 'answer' for the "
    "final composed answer.\n"
    "- Keep the plan minimal. End read/report plans with an answer_composer node "
    "(when available) that needs the data nodes."
)


class PlannerSubagent:
    def __init__(self, *, llm_registry: Any, settings: Any | None = None) -> None:
        self._llm_registry = llm_registry
        self._settings = settings

    async def plan(self, intent: Any, dictionary_text: str = "", tools_manifest: str = "") -> PlanGraph:
        _ = self._settings
        client = self._llm_registry.get("planner")
        user = f"Tools:\n{tools_manifest or '(none listed)'}\n\nintent={intent}\ndictionary={dictionary_text}"
        out = await client.astructured_predict(
            [
                {"role": "system", "content": _PLANNER_SYSTEM},
                {"role": "user", "content": user},
            ],
            PlanGraphOutput,
        )
        return PlanGraph(nodes=out.nodes)


class PlanExecutor:
    def __init__(
        self,
        *,
        tool_registry: ToolRegistry,
        policy: HarnessPolicy,
        harness: AgentHarness,
    ) -> None:
        self._tool_registry = tool_registry
        self._policy = policy
        self._harness = harness

    async def execute(self, plan: PlanGraph, ctx: TurnContext) -> list[NodeResult]:
        pending = {node.id: node for node in plan.nodes}
        completed: set[str] = set()
        results: list[NodeResult] = []
        # Outputs of completed nodes, addressable by downstream input_spec refs
        # of the form ``${node_id.path}`` (data-flow binding between DAG nodes).
        outputs: dict[str, dict[str, Any]] = {}
        while pending:
            ready = [
                node
                for node in plan.nodes
                if node.id in pending and all(dep in completed for dep in node.needs)
            ]
            if not ready:
                for node_id in list(pending):
                    results.append(
                        NodeResult(
                            node_id=node_id,
                            ok=False,
                            output_meets_expect=False,
                            error="plan dependency cycle or missing dependency",
                        )
                    )
                break
            # Resolve each ready node's args against already-completed node outputs
            # BEFORE launching the layer (every dependency is guaranteed complete).
            layer = [(node, _resolve_refs(dict(node.input_spec or {}), outputs)) for node in ready]
            layer_results = await asyncio.gather(
                *(self._execute_node(node, args, ctx) for node, args in layer)
            )
            results.extend(layer_results)
            for result in layer_results:
                completed.add(result.node_id)
                pending.pop(result.node_id, None)
                outputs[result.node_id] = result.tool_result if isinstance(result.tool_result, dict) else {}
        return results

    async def execute_with_replan(
        self,
        plan: PlanGraph,
        ctx: TurnContext,
        *,
        replan: Callable[[PlanGraph, list[NodeResult], int], Awaitable[PlanGraph]],
        max_replans: int,
    ) -> tuple[list[NodeResult], int]:
        replan_count = 0
        current = plan
        results = await self.execute(current, ctx)
        while self.needs_replan(results) and replan_count < max_replans:
            replan_count += 1
            current = await replan(current, results, replan_count)
            results = await self.execute(current, ctx)
        return results, replan_count

    def needs_replan(self, results: list[NodeResult]) -> bool:
        return any((not result.ok) or (not result.output_meets_expect) for result in results)

    async def _execute_node(
        self, node: PlanNode, args: dict[str, Any], ctx: TurnContext
    ) -> NodeResult:
        try:
            self._policy.check(node.tool, args, role=ctx.role, tenant_id=ctx.tenant_id)
            tool = self._tool_registry.get_impl(node.tool)
            result: ToolResult = await self._harness.arun_tool(
                tool_name=node.tool,
                tool=lambda: tool.invoke(args, ctx),
                context=ToolCallContext(
                    tool_name=node.tool,
                    correlation_id=ctx.correlation_id,
                    tenant_id=ctx.tenant_id,
                    thread_id=ctx.thread_id,
                ),
            )
            return NodeResult(
                node_id=node.id,
                ok=bool(result.ok),
                output_meets_expect=_output_meets_expect(result, node.output_expect),
                tool_result=dict(result.output or {}),
                observation_text=result.observation_text,
            )
        except Exception as exc:  # noqa: BLE001
            return NodeResult(
                node_id=node.id,
                ok=False,
                output_meets_expect=False,
                error=str(exc),
            )


_REF_FULL = re.compile(r"^\$\{([^}]+)\}$")
_REF_EMBED = re.compile(r"\$\{([^}]+)\}")


def _resolve_refs(value: Any, outputs: dict[str, dict[str, Any]]) -> Any:
    """Resolve ``${node_id.path}`` references in a node's input_spec against the
    outputs of already-completed nodes. Non-reference values pass through unchanged,
    so a static input_spec keeps working exactly as before.
    """
    if isinstance(value, str):
        full = _REF_FULL.match(value.strip())
        if full:
            return _lookup(full.group(1), outputs)
        if "${" in value:
            return _REF_EMBED.sub(lambda m: str(_lookup(m.group(1), outputs) or ""), value)
        return value
    if isinstance(value, dict):
        return {key: _resolve_refs(item, outputs) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_refs(item, outputs) for item in value]
    return value


def _lookup(path: str, outputs: dict[str, dict[str, Any]]) -> Any:
    parts = [p for p in path.split(".") if p]
    if not parts:
        return None
    current: Any = outputs.get(parts[0])
    for part in parts[1:]:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _output_meets_expect(result: ToolResult, output_expect: str) -> bool:
    expect = (output_expect or "").casefold()
    if not expect:
        return True
    output = result.output or {}
    if "rows" in expect:
        rows = output.get("rows")
        if isinstance(rows, list) and rows:
            return True
        query_result = output.get("query_result")
        if isinstance(query_result, dict):
            nested_rows = query_result.get("rows")
            return isinstance(nested_rows, list) and bool(nested_rows)
        return False
    if "answer" in expect:
        return bool(output.get("answer_markdown") or result.observation_text)
    return bool(result.ok)
