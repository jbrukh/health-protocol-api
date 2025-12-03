from datetime import date, time, datetime
from typing import Optional

from fastapi import HTTPException, status

from app.database import get_db
from app.models.body import BodyMeasurementCreate, BodyMeasurementResponse, BodyMeasurementUpdate


async def create_measurement(data: BodyMeasurementCreate, db_path: str | None = None) -> BodyMeasurementResponse:
    """Create a body measurement."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            """
            INSERT INTO body_measurements (date, time, weight_lbs, waist_cm)
            VALUES (?, ?, ?, ?)
            """,
            (
                data.date.isoformat(),
                data.time.isoformat(),
                data.weight_lbs,
                data.waist_cm,
            ),
        )
        await db.commit()
        measurement_id = cursor.lastrowid

    return await get_measurement(measurement_id, db_path)


async def get_measurement(measurement_id: int, db_path: str | None = None) -> BodyMeasurementResponse:
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

        return BodyMeasurementResponse(
            id=row["id"],
            date=date.fromisoformat(row["date"]),
            time=time.fromisoformat(row["time"]),
            weight_lbs=row["weight_lbs"],
            waist_cm=row["waist_cm"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )


async def get_measurements(measurement_date: date, db_path: str | None = None) -> list[BodyMeasurementResponse]:
    """Get all body measurements for a date."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM body_measurements WHERE date = ? ORDER BY time",
            (measurement_date.isoformat(),),
        )
        rows = await cursor.fetchall()

        return [
            BodyMeasurementResponse(
                id=row["id"],
                date=date.fromisoformat(row["date"]),
                time=time.fromisoformat(row["time"]),
                weight_lbs=row["weight_lbs"],
                waist_cm=row["waist_cm"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]


async def get_latest_measurement(db_path: str | None = None) -> Optional[BodyMeasurementResponse]:
    """Get the most recent body measurement."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM body_measurements ORDER BY date DESC, time DESC LIMIT 1"
        )
        row = await cursor.fetchone()

        if row is None:
            return None

        return BodyMeasurementResponse(
            id=row["id"],
            date=date.fromisoformat(row["date"]),
            time=time.fromisoformat(row["time"]),
            weight_lbs=row["weight_lbs"],
            waist_cm=row["waist_cm"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )


async def get_measurements_range(
    start_date: date, end_date: date, db_path: str | None = None
) -> list[BodyMeasurementResponse]:
    """Get body measurements within a date range."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM body_measurements WHERE date >= ? AND date <= ? ORDER BY date DESC, time",
            (start_date.isoformat(), end_date.isoformat()),
        )
        rows = await cursor.fetchall()

        return [
            BodyMeasurementResponse(
                id=row["id"],
                date=date.fromisoformat(row["date"]),
                time=time.fromisoformat(row["time"]),
                weight_lbs=row["weight_lbs"],
                waist_cm=row["waist_cm"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]


async def update_measurement(
    measurement_id: int, data: BodyMeasurementUpdate, db_path: str | None = None
) -> BodyMeasurementResponse:
    """Update a body measurement."""
    await get_measurement(measurement_id, db_path)

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

    return await get_measurement(measurement_id, db_path)


async def delete_measurement(measurement_id: int, db_path: str | None = None) -> None:
    """Delete a body measurement."""
    await get_measurement(measurement_id, db_path)

    async with get_db(db_path) as db:
        await db.execute("DELETE FROM body_measurements WHERE id = ?", (measurement_id,))
        await db.commit()
