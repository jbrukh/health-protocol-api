from datetime import date, datetime
from typing import Optional

from app.database import get_db
from app.models.activity import DailyActivityResponse


def _row_to_response(row) -> DailyActivityResponse:
    """Convert a database row to a DailyActivityResponse."""
    return DailyActivityResponse(
        id=row["id"],
        date=row["date"],
        steps=row["steps"],
        distance_miles=row["distance_miles"],
        active_calories=row["active_calories"],
        elevation_ft=row["elevation_ft"],
        source=row["source"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
    )


async def get_activity(activity_date: date, db_path: str | None = None) -> Optional[DailyActivityResponse]:
    """Get activity for a specific date."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM daily_activity WHERE date = ?",
            (activity_date.isoformat(),),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return _row_to_response(row)


async def get_latest(db_path: str | None = None) -> Optional[DailyActivityResponse]:
    """Get the most recent activity record."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM daily_activity ORDER BY date DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return _row_to_response(row)


async def get_activity_range(
    start_date: date, end_date: date, db_path: str | None = None
) -> list[DailyActivityResponse]:
    """Get activity within a date range."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM daily_activity WHERE date >= ? AND date <= ? ORDER BY date DESC",
            (start_date.isoformat(), end_date.isoformat()),
        )
        rows = await cursor.fetchall()
        return [_row_to_response(row) for row in rows]
