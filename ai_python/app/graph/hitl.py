from __future__ import annotations
import json
import aiosqlite


class PendingStore:
    """Persist snapshot phien dang pause de resume HITL (fact-validator-hitl).
    Stateless build: chi giu pending theo thread_id, xoa sau khi resume."""

    def __init__(self, *, db_path: str):
        self._db_path = db_path

    async def init(self) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS pending ("
                "thread_id TEXT PRIMARY KEY, snapshot TEXT NOT NULL, "
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            await db.commit()

    async def save(self, thread_id: str, snapshot: dict) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT INTO pending(thread_id, snapshot) VALUES(?, ?) "
                "ON CONFLICT(thread_id) DO UPDATE SET snapshot=excluded.snapshot",
                (thread_id, json.dumps(snapshot, ensure_ascii=False)))
            await db.commit()

    async def load(self, thread_id: str) -> dict | None:
        async with aiosqlite.connect(self._db_path) as db:
            async with db.execute(
                    "SELECT snapshot FROM pending WHERE thread_id=?", (thread_id,)) as cur:
                row = await cur.fetchone()
        return json.loads(row[0]) if row else None

    async def clear(self, thread_id: str) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("DELETE FROM pending WHERE thread_id=?", (thread_id,))
            await db.commit()
