from __future__ import annotations
import json
from pathlib import Path
import aiosqlite


class PendingStore:
    """Persist snapshot phien dang pause de resume HITL (fact-validator-hitl).
    Stateless build: chi giu pending theo thread_id, xoa sau khi resume.

    Table duoc tu dam bao truoc moi thao tac (lazy init 1 lan/instance) —
    khong phu thuoc caller nho goi init() truoc; nhanh save lan dau (pause
    truoc khi co bat ky resume nao) tung crash 'no such table: pending'."""

    def __init__(self, *, db_path: str):
        self._db_path = db_path
        self._initialized = False

    async def init(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS pending ("
                "thread_id TEXT PRIMARY KEY, snapshot TEXT NOT NULL, "
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            await db.commit()
        self._initialized = True

    async def _ensure_init(self) -> None:
        if not self._initialized:
            await self.init()

    async def save(self, thread_id: str, snapshot: dict) -> None:
        await self._ensure_init()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT INTO pending(thread_id, snapshot) VALUES(?, ?) "
                "ON CONFLICT(thread_id) DO UPDATE SET snapshot=excluded.snapshot",
                (thread_id, json.dumps(snapshot, ensure_ascii=False)))
            await db.commit()

    async def load(self, thread_id: str) -> dict | None:
        await self._ensure_init()
        async with aiosqlite.connect(self._db_path) as db:
            async with db.execute(
                    "SELECT snapshot FROM pending WHERE thread_id=?", (thread_id,)) as cur:
                row = await cur.fetchone()
        return json.loads(row[0]) if row else None

    async def clear(self, thread_id: str) -> None:
        await self._ensure_init()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("DELETE FROM pending WHERE thread_id=?", (thread_id,))
            await db.commit()
