"""Tool manifest, result, and decision contracts for the harness loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class TurnContext:
    tenant_id: str | None
    user_id: str | None
    thread_id: str | None
    correlation_id: str
    bearer_token: str | None
    schema_version: str | None
    clarification_response: dict[str, Any] | None = None
    pending_hitl_tool: str | None = None
    pending_hitl_payload: dict[str, Any] | None = None
    intent_object: dict[str, Any] | None = None
    assumptions: list[str] = field(default_factory=list)
    role: str | None = None


@dataclass(frozen=True)
class ToolInput:
    tool_name: str
    args: dict[str, Any]
    context: TurnContext


@dataclass
class HitlSpec:
    event_name: str
    payload: dict[str, Any]
    resume_token: str


@dataclass
class ToolResult:
    ok: bool
    output: dict[str, Any]
    observation_text: str
    sse_payload: dict[str, Any] | None = None
    pending_hitl: HitlSpec | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class ToolManifest:
    name: str
    description: str
    args_schema: str
    has_hitl: bool = False


class AsyncTool(Protocol):
    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
        ...


class ToolRegistry:
    def __init__(self) -> None:
        self._manifests: dict[str, ToolManifest] = {}
        self._impls: dict[str, AsyncTool] = {}

    def register(self, manifest: ToolManifest, impl: AsyncTool) -> None:
        self._manifests[manifest.name] = manifest
        self._impls[manifest.name] = impl

    def get_impl(self, name: str) -> AsyncTool:
        try:
            return self._impls[name]
        except KeyError as exc:
            raise KeyError(f"unknown tool: {name}") from exc

    def tools_manifest_text(self) -> str:
        lines: list[str] = []
        for manifest in self._manifests.values():
            hitl = " HITL" if manifest.has_hitl else ""
            lines.append(f"- {manifest.name}{hitl}: {manifest.description} Args: {manifest.args_schema}")
        return "\n".join(lines)


class ToolCall(BaseModel):
    tool_name: str
    args: dict[str, Any] = Field(default_factory=dict)
    reasoning: str = ""


class ClarifyRequest(BaseModel):
    """Ask the user a clarifying question (rendered as a UI bubble, not plain text)."""

    questions: list[str] = Field(default_factory=list)
    suggested_rewrite: str = ""


class DecisionSchema(BaseModel):
    action: Literal["call_tool", "final_answer", "clarify"]
    tool_call: ToolCall | None = None
    final_answer: str | None = None
    clarify: ClarifyRequest | None = None
