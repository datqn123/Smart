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
    goal: str = ""
    intent_type: str = ""   # data_query | catalog_draft | inventory_draft | chart_report | chat
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

    async def analyze(self, question: str, memory_text: str, dictionary_text: str) -> IntentObjectOutput:
        if self._llm_registry is None:
            return self._heuristic(question)
        client = self._llm_registry.get("intent")
        try:
            return await client.astructured_predict(
                [
                    {
                        "role": "user",
                        "content": (
                            f"question={question}\n"
                            f"memory={memory_text}\n"
                            f"dictionary={dictionary_text}"
                        ),
                    }
                ],
                IntentObjectOutput,
            )
        except Exception:
            return self._heuristic(question)

    def decide(self, intent: IntentObject) -> IntentDecision:
        if intent.missing_required:
            return IntentDecision(
                mode="clarify",
                clarify_questions=[_missing_question(intent.missing_required)],
            )
        min_entity = min([e.score for e in intent.resolved_entities], default=1.0)
        if intent.confidence < _float_setting(self._settings, "intent_confidence_hitl", 0.75):
            return IntentDecision(
                mode="clarify",
                clarify_questions=[_low_confidence_question(intent)],
            )
        if min_entity < _float_setting(self._settings, "entity_score_hitl", 0.6):
            return IntentDecision(
                mode="clarify",
                clarify_questions=[_entity_question(intent)],
            )
        if intent.confidence < _float_setting(self._settings, "intent_confidence_run", 0.9):
            return IntentDecision(
                mode="auto_assume",
                assumptions=[f"Tôi sẽ hiểu yêu cầu là: {intent.goal or intent.intent_type}."],
            )
        return IntentDecision(mode="run")

    @staticmethod
    def _heuristic(question: str) -> IntentObjectOutput:
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
        return IntentObjectOutput(
            goal=question or intent_type,
            intent_type=intent_type,
            required_data=[],
            confidence=0.9,
        )


def _norm(text: str) -> str:
    return " ".join((text or "").casefold().split())


def _float_setting(settings: Any, name: str, default: float) -> float:
    return float(getattr(settings, name, default) or default)


def _missing_question(missing: list[str]) -> str:
    if any("time" in item or "period" in item or "thời" in item for item in missing):
        return "Bạn muốn xem trong khoảng thời gian nào? Vui lòng chọn ví dụ: hôm nay, tháng này hoặc một khoảng ngày cụ thể."
    return "Bạn vui lòng bổ sung thông tin còn thiếu để tôi xử lý chính xác hơn."


def _low_confidence_question(intent: IntentObject) -> str:
    _ = intent
    return "Tôi chưa đủ chắc để xử lý yêu cầu này. Bạn vui lòng nói rõ mục tiêu hoặc dữ liệu cần xem?"


def _entity_question(intent: IntentObject) -> str:
    options: list[str] = []
    for ambiguity in intent.ambiguities:
        options.extend(ambiguity.options)
    for entity in intent.resolved_entities:
        if entity.matched:
            options.append(entity.matched)
    suffix = f" Các lựa chọn gần nhất: {', '.join(options[:3])}." if options else ""
    return f"Bạn muốn dùng chính xác đối tượng nào? Vui lòng chọn hoặc nhập lại tên đầy đủ.{suffix}"
