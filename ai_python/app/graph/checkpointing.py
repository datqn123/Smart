"""Checkpoint factory — Option C."""

from __future__ import annotations

import sqlite3

import aiosqlite
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.config.graph_settings import GraphSettings


def build_checkpointer(settings: GraphSettings) -> MemorySaver | SqliteSaver:
    path = settings.checkpoint_sqlite_path
    if path:
        conn = sqlite3.connect(path, check_same_thread=False)
        return SqliteSaver(conn)
    return MemorySaver()


async def build_async_checkpointer(settings: GraphSettings) -> MemorySaver | AsyncSqliteSaver:
    path = settings.checkpoint_sqlite_path
    if path:
        conn = await aiosqlite.connect(path)
        return AsyncSqliteSaver(conn)
    return MemorySaver()
