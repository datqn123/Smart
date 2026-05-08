from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SliceIntent = Literal["query", "clarify"]
RagNamespace = Literal["docs", "schema", "catalog"]


class DbTemplateFootprint(BaseModel):
    template_id: str
    param_keys: list[str] = Field(default_factory=list)


class ChatStateTask003(BaseModel):
    """Task003 extension fields (SRS §3) merged with conversational context."""

    model_config = ConfigDict(extra="ignore")

    user_message: str = ""
    correlation_id: str = ""

    intent: SliceIntent | None = None

    rag_context_ids: list[str] = Field(default_factory=list)
    rag_namespaces_hit: list[RagNamespace] = Field(default_factory=list)

    db_readonly_attempted: bool = False
    db_template_last: DbTemplateFootprint | None = None
    readonly_gate_reason: str | None = None

    @field_validator("user_message")
    @classmethod
    def user_message_strip(cls, v: str) -> str:
        t = v.strip()
        return t

    @field_validator("intent", mode="before")
    @classmethod
    def reject_write_like_intents(cls, v: object) -> SliceIntent | None:
        """Slice executes only query/clarify; write/excel paths refuse upstream."""
        if v is None or v == "":
            return None
        if v in ("query", "clarify"):
            return v  # type: ignore[return-value]
        raise ValueError("Task003 ChatState accepts intent in {query, clarify, None}")

    @field_validator("rag_context_ids")
    @classmethod
    def rag_ids_unique_stable(cls, v: list[str]) -> list[str]:
        seen: set[str] = set()
        order: list[str] = []
        for x in v:
            if x not in seen:
                seen.add(x)
                order.append(x)
        return order

    def apply_rag_chunks(self, *, chunk_ids: list[str], namespaces: list[RagNamespace]) -> None:
        merged_ids = list(self.rag_context_ids)
        for cid in chunk_ids:
            if cid not in merged_ids:
                merged_ids.append(cid)
        self.rag_context_ids = merged_ids
        merged_ns: list[RagNamespace] = list(self.rag_namespaces_hit)
        for ns in namespaces:
            if ns not in merged_ns:
                merged_ns.append(ns)
        self.rag_namespaces_hit = merged_ns
