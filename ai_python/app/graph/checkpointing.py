"""Checkpoint factory — Option C."""

from __future__ import annotations

import sqlite3

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

from app.config.graph_settings import GraphSettings


def build_checkpointer(settings: GraphSettings) -> MemorySaver | SqliteSaver:
    path = settings.checkpoint_sqlite_path
    if path:
        conn = sqlite3.connect(path, check_same_thread=False)
        return SqliteSaver(conn)
    return MemorySaver()
