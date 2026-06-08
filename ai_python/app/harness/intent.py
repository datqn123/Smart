"""Intent object and confidence gate for the harness loop."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ResolvedEntity(BaseModel):
    raw: str
    matched: str = ""
    score: float = 0.0


class Ambiguity(BaseModel):
    field: str
    options: list[str] = Field(default_factory=list)
    reason: str = ""


class RequiredDataItem(BaseModel):
    field: str
    source: str = ""        # bảng/entity cung cấp data này
    required: bool = True
    resolved: bool = False  # đã có trong context chưa


class IntentAnalysisResult(BaseModel):
    goal: str
    intent_type: str        # data_query | catalog_draft | inventory_draft | chart_report | chat
    required_data: list[RequiredDataItem] = Field(default_factory=list)
    resolved_entities: list[ResolvedEntity] = Field(default_factory=list)
    confidence: float = 0.0
    ambiguities: list[Ambiguity] = Field(default_factory=list)
    # --- LLM judge fields ---
    mode: Literal["run", "clarify", "auto_assume"] = "run"
    clarify_questions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    reasoning: str = ""     # LLM tự lý giải quyết định (lightweight CoT)
    schema_refs: list[str] = Field(default_factory=list)  # bảng LLM đã tham chiếu
    # --- backward-compat fields (old IntentObject) ---
    missing_required: list[str] = Field(default_factory=list)

    @field_validator("required_data", mode="before")
    @classmethod
    def _coerce_required_data(cls, v: object) -> object:
        """Accept list[str] (legacy format) or list[RequiredDataItem]."""
        if isinstance(v, list):
            return [RequiredDataItem(field=item) if isinstance(item, str) else item for item in v]
        return v


# Backward-compat aliases — orchestrator và tests cũ dùng tên cũ
IntentObject = IntentAnalysisResult
IntentObjectOutput = IntentAnalysisResult
IntentDecision = IntentAnalysisResult


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
        return IntentContext(
            schema_text=schema_text,
            history_text=history_text,
            memory_text=memory_text,
        )


class EntityResolver:
    def __init__(
        self,
        *,
        synonym_map: dict[str, list[str]] | None = None,
        catalog: list[dict[str, Any]] | None = None,
    ) -> None:
        self._synonym_map = synonym_map or {}
        self._catalog = catalog or []

    def score_sync(self, raw: str, entity_type: str) -> ResolvedEntity:
        raw_norm = _norm(raw)
        best_display = ""
        best_score = 0.0
        for row in self._catalog:
            if str(row.get("entity_type") or "") != entity_type:
                continue
            display = str(row.get("display") or "")
            score = SequenceMatcher(None, raw_norm, _norm(display)).ratio()
            if raw_norm and raw_norm in _norm(display):
                score = max(score, 0.8)
            if score > best_score:
                best_score = score
                best_display = display
        if best_display:
            return ResolvedEntity(raw=raw, matched=best_display, score=round(best_score, 3))
        for term, targets in self._synonym_map.items():
            score = SequenceMatcher(None, raw_norm, _norm(term)).ratio()
            if raw_norm and raw_norm in _norm(term):
                score = max(score, 0.8)
            if score > best_score:
                best_score = score
                best_display = targets[0] if targets else term
        return ResolvedEntity(raw=raw, matched=best_display, score=round(best_score, 3))


class IntentSubagent:
    def __init__(
        self,
        *,
        llm_registry: Any | None = None,
        entity_resolver: EntityResolver | None = None,
        settings: Any,
    ) -> None:
        self._llm_registry = llm_registry
        self._entity_resolver = entity_resolver or EntityResolver()
        self._settings = settings

    async def analyze(
        self,
        question: str,
        memory_text: str = "",
        dictionary_text: str = "",  # kept for backward compat — ignored
        intent_context: "IntentContext | None" = None,
    ) -> IntentAnalysisResult:
        ctx = intent_context or IntentContext(memory_text=memory_text)
        prompt_blocks = ctx.to_prompt_blocks()

        if self._llm_registry is None:
            return self._heuristic(question)
        client = self._llm_registry.get("intent")
        try:
            return await client.astructured_predict(
                [
                    {
                        "role": "system",
                        "content": (
                            "You are an intent analysis expert for a Vietnamese ERP system. "
                            "Analyze the user's request using the context below and return a structured result. "
                            "Decide the mode: 'run' if you have enough info, 'clarify' if critical info is missing, "
                            "'auto_assume' if you can make safe assumptions. "
                            "Write contextual clarify_questions in Vietnamese if mode='clarify'. "
                            "Write a 1-2 sentence reasoning explaining your decision.\n\n"
                            f"{prompt_blocks}"
                        ),
                    },
                    {
                        "role": "user",
                        "content": question,
                    },
                ],
                IntentAnalysisResult,
            )
        except Exception:
            return self._heuristic(question)

    def decide(self, intent: IntentAnalysisResult) -> IntentAnalysisResult:
        # Stub — orchestrator will be updated in Task 5 to read intent.mode directly
        return intent

    @staticmethod
    def _heuristic(question: str) -> IntentAnalysisResult:
        text = (question or "").lower()
        if any(token in text for token in ("tạo sản phẩm", "tạo danh mục", "catalog")):
            intent_type = "catalog_draft"
        elif any(token in text for token in ("nhập kho", "xuất kho", "tạo phiếu")):
            intent_type = "inventory_draft"
        elif any(token in text for token in ("biểu đồ", "chart", "vẽ")):
            intent_type = "chart_report"
        elif any(token in text for token in ("doanh thu", "tồn kho", "báo cáo", "công nợ")):
            intent_type = "data_query"
        else:
            intent_type = "chat"
        return IntentAnalysisResult(
            goal=question or intent_type,
            intent_type=intent_type,
            required_data=[],
            confidence=0.9,
            mode="run",
            reasoning="heuristic fallback",
        )


def _norm(text: str) -> str:
    return " ".join((text or "").casefold().split())
