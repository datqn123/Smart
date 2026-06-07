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
            "You are the Smart ERP assistant planner. The system covers: inventory & "
            "warehouse documents, products/catalog, orders, finance, and AI chat over "
            "this ERP's data.\n"
            "Choose exactly one next action: call_tool, clarify, or final_answer. Use "
            "only the listed tools.\n"
            "Decision rules:\n"
            "- If the user asks about ERP data/operations and a listed tool fits, call "
            "that tool. After you have enough observations to answer, return "
            "final_answer.\n"
            "- For greetings, thanks, or small talk, skip tools and return a short, "
            "friendly final_answer.\n"
            "- If the question is OUT OF SCOPE for this ERP (e.g. general knowledge, "
            "weather, unrelated software), do NOT call any tool — return a final_answer "
            "that politely declines and names what you can help with (inventory, "
            "products, orders, finance), with 1-2 example questions.\n"
            "- If the request is in-scope but MISSING a key detail needed to run a tool "
            "(e.g. a report with no time period, an ambiguous entity), choose action "
            "'clarify': put 1-3 short questions in clarify.questions and, when you can "
            "infer it, a complete corrected question in clarify.suggested_rewrite. Only "
            "clarify when the missing detail truly blocks execution — do not clarify "
            "for optional filters you can default sensibly.\n"
            "- NEVER repeat a tool call that already ran with the same arguments — the "
            "result will be identical. Look at the Observations before deciding.\n"
            "- If a data query returned 0 rows because a name/label filter may not "
            "exist or is misspelled, do ONE of: (a) retry once with a broader "
            "case-insensitive partial match, or (b) choose action 'clarify' to confirm "
            "the exact value with the user, or (c) return a final_answer stating no "
            "matching data was found. Do not keep re-running the same query.\n"
            "All user-facing text (final_answer, clarify.questions, "
            "clarify.suggested_rewrite) MUST be in Vietnamese (vi-VN)."
        )
        user = f"Tools:\n{tools_manifest}\n\nObservations:\n{obs}"
        return [SystemMessage(content=system), *self.messages, HumanMessage(content=user)]

    def observation_summary(self) -> str:
        if not self.observations:
            return "Không đủ dữ liệu để trả lời trong giới hạn bước hiện tại."
        return "\n".join(obs.observation_text for obs in self.observations[-3:] if obs.observation_text)
