from datetime import date, time, datetime
from typing import Optional

from fastapi import HTTPException, status

from app.database import get_db
from app.models.body import BodyMeasurementCreate, BodyMeasurementResponse, BodyMeasurementUpdate
from app.utils.timezone import convert_date_time_to_tz


def _row_to_response(row, timezone: str | None = None) -> BodyMeasurementResponse:
    """Convert a database row to a BodyMeasurementResponse."""
    row_date = date.fromisoformat(row["date"]) if isinstance(row["date"], str) else row["date"]
    row_time = time.fromisoformat(row["time"]) if isinstance(row["time"], str) else row["time"]

    # Convert to user timezone if specified
    converted_date, converted_time = convert_date_time_to_tz(row_date, row_time, timezone)

    return BodyMeasurementResponse(
        id=row["id"],
        date=converted_date,
        time=converted_time,
        weight_lbs=row["weight_lbs"],
        waist_cm=row["waist_cm"],
        fat_mass_lbs=row["fat_mass_lbs"] if "fat_mass_lbs" in row.keys() else None,
        muscle_mass_lbs=row["muscle_mass_lbs"] if "muscle_mass_lbs" in row.keys() else None,
        bone_mass_lbs=row["bone_mass_lbs"] if "bone_mass_lbs" in row.keys() else None,
        body_water_pct=row["body_water_pct"] if "body_water_pct" in row.keys() else None,
        source=row["source"] if "source" in row.keys() else "manual",
        created_at=datetime.fromisoformat(row["created_at"]),
    )


async def create_measurement(data: BodyMeasurementCreate, db_path: str | None = None) -> BodyMeasurementResponse:
    """Create a body measurement."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            """
            INSERT INTO body_measurements (date, time, weight_lbs, waist_cm, fat_mass_lbs, muscle_mass_lbs, bone_mass_lbs, body_water_pct, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.date.isoformat(),
                data.time.isoformat(),
                data.weight_lbs,
                data.waist_cm,
                data.fat_mass_lbs,
                data.muscle_mass_lbs,
                data.bone_mass_lbs,
                data.body_water_pct,
                data.source,
            ),
        )
        await db.commit()
        measurement_id = cursor.lastrowid

    return await get_measurement(measurement_id, db_path=db_path)


async def get_measurement(measurement_id: int, timezone: str | None = None, db_path: str | None = None) -> BodyMeasurementResponse:
    """Get a body measurement by ID."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM body_measurements WHERE id = ?",
            (measurement_id,),
        )
        row = await cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Body measurement with id {measurement_id} not found",
            )

        return _row_to_response(row, timezone)


async def get_measurements(measurement_date: date, timezone: str | None = None, db_path: str | None = None) -> list[BodyMeasurementResponse]:
    """Get all body measurements for a date."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM body_measurements WHERE date = ? ORDER BY time",
            (measurement_date.isoformat(),),
        )
        rows = await cursor.fetchall()

        return [_row_to_response(row, timezone) for row in rows]


async def get_latest_measurement(timezone: str | None = None, db_path: str | None = None) -> Optional[BodyMeasurementResponse]:
    """Get the most recent body measurement."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM body_measurements ORDER BY date DESC, time DESC LIMIT 1"
        )
        row = await cursor.fetchone()

        if row is None:
            return None

        return _row_to_response(row, timezone)


async def get_measurements_range(
    start_date: date,
    end_date: date,
    limit: int = 100,
    offset: int = 0,
    timezone: str | None = None,
    db_path: str | None = None,
) -> list[BodyMeasurementResponse]:
    """Get body measurements within a date range with pagination."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM body_measurements WHERE date >= ? AND date <= ? ORDER BY date DESC, time LIMIT ? OFFSET ?",
            (start_date.isoformat(), end_date.isoformat(), limit, offset),
        )
        rows = await cursor.fetchall()

        return [_row_to_response(row, timezone) for row in rows]


async def get_summary(db_path: str | None = None) -> dict:
    """Get summary statistics for body measurements."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            """
            SELECT
                MIN(date) as earliest_date,
                MAX(date) as latest_date,
                COUNT(*) as total_count
            FROM body_measurements
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


async def get_measurement_by_withings_id(withings_id: str, db_path: str | None = None) -> Optional[BodyMeasurementResponse]:
    """Get a body measurement by Withings ID (for deduplication)."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM body_measurements WHERE withings_id = ?",
            (withings_id,),
        )
        row = await cursor.fetchone()

        if row is None:
            return None

        return _row_to_response(row)


async def update_measurement(
    measurement_id: int, data: BodyMeasurementUpdate, db_path: str | None = None
) -> BodyMeasurementResponse:
    """Update a body measurement."""
    await get_measurement(measurement_id, db_path=db_path)

    async with get_db(db_path) as db:
        updates = []
        values = []
        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                updates.append(f"{field} = ?")
                if isinstance(value, (date, time)):
                    values.append(value.isoformat())
                else:
                    values.append(value)

        if updates:
            values.append(measurement_id)
            query = f"UPDATE body_measurements SET {', '.join(updates)} WHERE id = ?"
            await db.execute(query, values)
            await db.commit()

    return await get_measurement(measurement_id, db_path=db_path)


async def delete_measurement(measurement_id: int, db_path: str | None = None) -> None:
    """Delete a body measurement."""
    await get_measurement(measurement_id, db_path=db_path)

    async with get_db(db_path) as db:
        await db.execute("DELETE FROM body_measurements WHERE id = ?", (measurement_id,))
        await db.commit()
