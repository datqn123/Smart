"""Intent recognition — LLM-centric skill-based approach."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class IntentDecision(BaseModel):
    """Simple intent decision from LLM."""

    action: Literal["direct_answer", "call_tool", "final_answer", "clarify"]
    goal_text: str = ""
    tool_name: str | None = None
    tool_args: dict[str, Any] = Field(default_factory=dict)
    answer: str | None = None
    clarify_questions: list[str] = Field(default_factory=list)
    reasoning: str = ""


class IntentClassifier:
    """LLM-based intent classifier using skill.md prompt."""

    def __init__(
        self,
        llm_client: Any,
        skill_path: str = "skill.md",
    ) -> None:
        self._llm_client = llm_client
        self._skill_path = skill_path
        self._skill_prompt: str | None = None

    def _load_skill_prompt(self) -> str:
        if self._skill_prompt is None:
            path = Path(self._skill_path)
            if path.exists():
                self._skill_prompt = path.read_text(encoding="utf-8")
            else:
                self._skill_prompt = self._default_skill_prompt()
        return self._skill_prompt

    def _build_system_prompt(self, context: dict[str, Any]) -> str:
        skill = self._load_skill_prompt()
        parts = [skill]

        schema_text = context.get("schema_text", "")
        if schema_text:
            parts.append(f"\n\n## Database Schema\n{schema_text}")

        system_info = context.get("system_info", "")
        if system_info:
            parts.append(f"\n\n## System Info\n{system_info}")

        return "\n".join(parts)

    async def classify(
        self,
        question: str,
        context: dict[str, Any],
        history: list[dict[str, Any]] | None = None,
    ) -> IntentDecision:
        system_prompt = self._build_system_prompt(context)

        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": question})

        response = await self._llm_client.chat(
            system=system_prompt,
            messages=messages,
        )

        if isinstance(response, IntentDecision):
            return response

        return IntentDecision.model_validate(response)

    @staticmethod
    def _default_skill_prompt() -> str:
        return (
            "You are an ERP data analyst assistant. "
            "Analyze the user's request and return a JSON response with action, goal_text, "
            "tool_name, tool_args, answer, clarify_questions, and reasoning."
        )


# ---------------------------------------------------------------------------
# Backward-compat aliases — will be removed in Task 4 cleanup
# ---------------------------------------------------------------------------
import warnings


class RequiredDataItem(BaseModel):
    field: str
    source: str = ""
    required: bool = True
    resolved: bool = False


class IntentAnalysisResult(BaseModel):
    goal: str = ""
    intent_type: str = "chat"
    required_data: list[RequiredDataItem] = Field(default_factory=list)
    confidence: float = 0.0
    ambiguities: list[dict[str, Any]] = Field(default_factory=list)
    mode: Literal["run", "clarify", "auto_assume"] = "run"
    clarify_questions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    reasoning: str = ""
    schema_refs: list[str] = Field(default_factory=list)
    missing_required: list[str] = Field(default_factory=list)

    def to_intent_decision(self) -> IntentDecision:
        action_map: dict[str, str] = {
            "data_query": "call_tool",
            "catalog_draft": "call_tool",
            "inventory_draft": "call_tool",
            "chart_report": "call_tool",
            "chat": "direct_answer",
        }
        mapped = action_map.get(self.intent_type, "direct_answer")
        if self.mode == "clarify":
            mapped = "clarify"
        return IntentDecision(
            action=mapped,
            goal_text=self.goal,
            tool_name="sql_query" if self.intent_type == "data_query" else None,
            tool_args={},
            answer=None,
            clarify_questions=self.clarify_questions,
            reasoning=self.reasoning,
        )


class IntentContext(BaseModel):
    schema_text: str = ""
    history_text: str = ""
    memory_text: str = ""

    def to_prompt_blocks(self) -> str:
        parts: list[str] = []
        if self.schema_text:
            parts.append(f"[SCHEMA]\n{self.schema_text}")
        if self.history_text:
            parts.append(f"[QUERY HISTORY]\n{self.history_text}")
        if self.memory_text:
            parts.append(f"[CONVERSATION]\n{self.memory_text}")
        return "\n\n".join(parts)


class IntentContextBuilder:
    def build(
        self,
        *,
        schema_text: str = "",
        history_text: str = "",
        memory_text: str = "",
    ) -> IntentContext:
        warnings.warn(
            "IntentContextBuilder is deprecated; use IntentClassifier instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return IntentContext(
            schema_text=schema_text,
            history_text=history_text,
            memory_text=memory_text,
        )


class IntentSubagent:
    def __init__(
        self,
        *,
        llm_registry: Any | None = None,
        entity_resolver: Any | None = None,
        settings: Any | None = None,
    ) -> None:
        warnings.warn(
            "IntentSubagent is deprecated; use IntentClassifier instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._llm_registry = llm_registry
        self._settings = settings

    async def analyze(
        self,
        question: str,
        memory_text: str = "",
        dictionary_text: str = "",
        intent_context: IntentContext | None = None,
    ) -> IntentDecision:
        warnings.warn(
            "IntentSubagent.analyze is deprecated; use IntentClassifier.classify instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        ctx = intent_context or IntentContext(memory_text=memory_text)
        classifier = IntentClassifier(llm_client=self._llm_registry.get("intent") if self._llm_registry else None)
        context: dict[str, Any] = {"schema_text": ctx.schema_text, "system_info": ""}
        return await classifier.classify(question=question, context=context)