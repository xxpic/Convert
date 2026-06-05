import aiosqlite
import json
from datetime import datetime, timezone
from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER PRIMARY KEY,
                chat_id INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS rate_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                rates TEXT NOT NULL,
                base TEXT NOT NULL DEFAULT 'USD'
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_rate_history_timestamp
            ON rate_history(timestamp)
        """)
        await db.commit()


async def subscribe(user_id: int, chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO subscriptions (user_id, chat_id, created_at) VALUES (?, ?, ?)",
            (user_id, chat_id, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()


async def unsubscribe(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM subscriptions WHERE user_id = ?", (user_id,))
        await db.commit()


async def is_subscribed(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM subscriptions WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None


async def get_all_subscribers():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id, chat_id FROM subscriptions") as cursor:
            rows = await cursor.fetchall()
            return [(row[0], row[1]) for row in rows]


async def save_rate_snapshot(rates: dict, base: str = "USD"):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO rate_history (timestamp, rates, base) VALUES (?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), json.dumps(rates), base),
        )
        await db.execute(
            "DELETE FROM rate_history WHERE id NOT IN (SELECT id FROM rate_history ORDER BY id DESC LIMIT 48)"
        )
        await db.commit()


async def get_previous_rates() -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT rates FROM rate_history ORDER BY id DESC LIMIT 1 OFFSET 1"
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None
