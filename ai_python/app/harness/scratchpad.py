"""Per-turn scratchpad for harness-orchestrated decisions."""

from __future__ import annotations

from dataclasses import dataclass, field

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.harness.tool_registry import ToolResult

_OBSERVATION_MAX_CHARS = 800


@dataclass
class Observation:
    tool_name: str
    observation_text: str
    ok: bool


@dataclass
class TurnScratchpad:
    messages: list[BaseMessage]
    observations: list[Observation] = field(default_factory=list)
    step: int = 0

    def add_observation(self, result: ToolResult, tool_name: str) -> None:
        text = result.observation_text or result.error_message or ""
        if len(text) > _OBSERVATION_MAX_CHARS:
            text = text[:_OBSERVATION_MAX_CHARS] + "[truncated]"
        self.observations.append(
            Observation(tool_name=tool_name, observation_text=text, ok=bool(result.ok))
        )

    def to_decision_prompt(self, tools_manifest: str) -> list[BaseMessage]:
        obs = "\n".join(
            f"{idx + 1}. {item.tool_name} ({'ok' if item.ok else 'error'}): {item.observation_text}"
            for idx, item in enumerate(self.observations)
        )
        obs = obs or "(none)"
        system = (
            "You are a Smart ERP harness planner. Choose exactly one next action: "
            "call_tool or final_answer. Use only the listed tools."
        )
        user = f"Tools:\n{tools_manifest}\n\nObservations:\n{obs}"
        return [SystemMessage(content=system), *self.messages, HumanMessage(content=user)]

    def observation_summary(self) -> str:
        if not self.observations:
            return "Không đủ dữ liệu để trả lời trong giới hạn bước hiện tại."
        return "\n".join(obs.observation_text for obs in self.observations[-3:] if obs.observation_text)
