from datetime import date, time, datetime
from typing import Optional

from app.database import get_db
from app.models.blood_pressure import BloodPressureResponse


def _row_to_response(row) -> BloodPressureResponse:
    """Convert a database row to a BloodPressureResponse."""
    return BloodPressureResponse(
        id=row["id"],
        date=row["date"],
        time=row["time"],
        systolic=row["systolic"],
        diastolic=row["diastolic"],
        heart_rate=row["heart_rate"],
        source=row["source"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


async def get_readings(measurement_date: date, db_path: str | None = None) -> list[BloodPressureResponse]:
    """Get all blood pressure readings for a date."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM blood_pressure WHERE date = ? ORDER BY time",
            (measurement_date.isoformat(),),
        )
        rows = await cursor.fetchall()
        return [_row_to_response(row) for row in rows]


async def get_latest(db_path: str | None = None) -> Optional[BloodPressureResponse]:
    """Get the most recent blood pressure reading."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM blood_pressure ORDER BY date DESC, time DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return _row_to_response(row)


async def get_readings_range(
    start_date: date,
    end_date: date,
    limit: int = 100,
    offset: int = 0,
    db_path: str | None = None,
) -> list[BloodPressureResponse]:
    """Get blood pressure readings within a date range with pagination."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM blood_pressure WHERE date >= ? AND date <= ? ORDER BY date DESC, time LIMIT ? OFFSET ?",
            (start_date.isoformat(), end_date.isoformat(), limit, offset),
        )
        rows = await cursor.fetchall()
        return [_row_to_response(row) for row in rows]


async def get_summary(db_path: str | None = None) -> dict:
    """Get summary statistics for blood pressure readings."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            """
            SELECT
                MIN(date) as earliest_date,
                MAX(date) as latest_date,
                COUNT(*) as total_count
            FROM blood_pressure
            """
        )
        row = await cursor.fetchone()

        if row is None or row["total_count"] == 0:
            return {
                "earliest_date": None,
                "latest_date": None,
                "total_count": 0,
            }

        return {
            "earliest_date": row["earliest_date"],
            "latest_date": row["latest_date"],
            "total_count": row["total_count"],
        }
