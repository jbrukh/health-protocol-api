from datetime import date, datetime
from typing import Optional

from app.database import get_db
from app.models.sleep import SleepResponse


def _row_to_response(row) -> SleepResponse:
    """Convert a database row to a SleepResponse."""
    return SleepResponse(
        id=row["id"],
        date=row["date"],
        sleep_start=datetime.fromisoformat(row["sleep_start"]) if row["sleep_start"] else None,
        sleep_end=datetime.fromisoformat(row["sleep_end"]) if row["sleep_end"] else None,
        duration_minutes=row["duration_minutes"],
        deep_minutes=row["deep_minutes"],
        light_minutes=row["light_minutes"],
        rem_minutes=row["rem_minutes"],
        awake_minutes=row["awake_minutes"],
        source=row["source"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


async def get_sleep(sleep_date: date, db_path: str | None = None) -> Optional[SleepResponse]:
    """Get sleep data for a specific date."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM sleep WHERE date = ? ORDER BY created_at DESC LIMIT 1",
            (sleep_date.isoformat(),),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return _row_to_response(row)


async def get_latest(db_path: str | None = None) -> Optional[SleepResponse]:
    """Get the most recent sleep record."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM sleep ORDER BY date DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return _row_to_response(row)


async def get_sleep_range(
    start_date: date, end_date: date, db_path: str | None = None
) -> list[SleepResponse]:
    """Get sleep data within a date range."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM sleep WHERE date >= ? AND date <= ? ORDER BY date DESC",
            (start_date.isoformat(), end_date.isoformat()),
        )
        rows = await cursor.fetchall()
        return [_row_to_response(row) for row in rows]
