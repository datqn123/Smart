"""Minimal chat agent state scaffold (expand with LangGraph)."""

from typing import TypedDict


class ChatState(TypedDict, total=False):
    query: str
