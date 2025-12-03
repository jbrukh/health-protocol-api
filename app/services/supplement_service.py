from datetime import date, datetime
from typing import Optional

from fastapi import HTTPException, status

from app.database import get_db
from app.models.supplement import (
    SupplementCreate,
    SupplementResponse,
    SupplementUpdate,
    SupplementScheduleItem,
    SupplementScheduleResponse,
    SupplementScheduleSummary,
    SupplementHistoryItem,
    SupplementHistoryResponse,
    SupplementListResponse,
    TimeOfDay,
)


def _is_active(start_date: date, end_date: Optional[date]) -> bool:
    """Check if a supplement is currently active."""
    today = date.today()
    if start_date > today:
        return False
    if end_date is None:
        return True
    return end_date >= today


def _row_to_response(row) -> SupplementResponse:
    """Convert a database row to a SupplementResponse."""
    start_dt = date.fromisoformat(row["start_date"])
    end_dt = date.fromisoformat(row["end_date"]) if row["end_date"] else None
    return SupplementResponse(
        id=row["id"],
        name=row["name"],
        dosage=row["dosage"],
        purpose=row["purpose"],
        time_of_day=TimeOfDay(row["time_of_day"]),
        with_food=bool(row["with_food"]),
        notes=row["notes"],
        start_date=start_dt,
        end_date=end_dt,
        is_active=_is_active(start_dt, end_dt),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


async def create_supplement(data: SupplementCreate, db_path: str | None = None) -> SupplementResponse:
    """Create a new supplement entry."""
    async with get_db(db_path) as db:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            """
            INSERT INTO supplements (name, dosage, purpose, time_of_day, with_food, notes, start_date, end_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.name,
                data.dosage,
                data.purpose,
                data.time_of_day.value,
                data.with_food,
                data.notes,
                data.start_date.isoformat(),
                data.end_date.isoformat() if data.end_date else None,
                now,
                now,
            ),
        )
        await db.commit()
        supplement_id = cursor.lastrowid

    return await get_supplement(supplement_id, db_path)


async def get_supplement(supplement_id: int, db_path: str | None = None) -> SupplementResponse:
    """Get a supplement by ID."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM supplements WHERE id = ?",
            (supplement_id,),
        )
        row = await cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplement with id {supplement_id} not found",
            )

        return _row_to_response(row)


async def list_supplements(
    active: Optional[bool] = None,
    time_of_day: Optional[TimeOfDay] = None,
    db_path: str | None = None,
) -> SupplementListResponse:
    """List all supplements with optional filters."""
    async with get_db(db_path) as db:
        query = "SELECT * FROM supplements WHERE 1=1"
        params = []

        if time_of_day is not None:
            query += " AND time_of_day = ?"
            params.append(time_of_day.value)

        query += " ORDER BY time_of_day, name"
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

        supplements = [_row_to_response(row) for row in rows]

        # Filter by active status in Python (since it's computed)
        if active is not None:
            supplements = [s for s in supplements if s.is_active == active]

        return SupplementListResponse(supplements=supplements)


async def get_active_supplements(db_path: str | None = None) -> SupplementListResponse:
    """Get all currently active supplements."""
    return await list_supplements(active=True, db_path=db_path)


async def get_supplement_schedule(db_path: str | None = None) -> SupplementScheduleResponse:
    """Get today's supplement schedule organized by time of day."""
    today = date.today()
    result = await list_supplements(active=True, db_path=db_path)

    # Organize by time of day
    schedule: dict[str, list[SupplementScheduleItem]] = {
        "morning": [],
        "midday": [],
        "afternoon": [],
        "evening": [],
        "bedtime": [],
    }

    with_food_count = 0
    without_food_count = 0

    for supp in result.supplements:
        item = SupplementScheduleItem(
            id=supp.id,
            name=supp.name,
            dosage=supp.dosage,
            with_food=supp.with_food,
            notes=supp.notes,
        )
        schedule[supp.time_of_day.value].append(item)

        if supp.with_food:
            with_food_count += 1
        else:
            without_food_count += 1

    return SupplementScheduleResponse(
        date=today,
        schedule=schedule,
        summary=SupplementScheduleSummary(
            total_supplements=len(result.supplements),
            with_food_count=with_food_count,
            without_food_count=without_food_count,
        ),
    )


async def get_supplement_history(
    start_date: date,
    end_date: date,
    db_path: str | None = None,
) -> SupplementHistoryResponse:
    """Get supplements that were active during a date range."""
    async with get_db(db_path) as db:
        # A supplement was active during the range if:
        # - supplement.start_date <= range.end_date AND
        # - (supplement.end_date IS NULL OR supplement.end_date >= range.start_date)
        cursor = await db.execute(
            """
            SELECT * FROM supplements
            WHERE start_date <= ?
            AND (end_date IS NULL OR end_date >= ?)
            ORDER BY start_date, name
            """,
            (end_date.isoformat(), start_date.isoformat()),
        )
        rows = await cursor.fetchall()

        supplements = []
        for row in rows:
            supp_start = date.fromisoformat(row["start_date"])
            supp_end = date.fromisoformat(row["end_date"]) if row["end_date"] else None

            # Check if it was active the entire period
            was_active_entire_period = (
                supp_start <= start_date and (supp_end is None or supp_end >= end_date)
            )

            supplements.append(
                SupplementHistoryItem(
                    id=row["id"],
                    name=row["name"],
                    dosage=row["dosage"],
                    purpose=row["purpose"],
                    time_of_day=TimeOfDay(row["time_of_day"]),
                    with_food=bool(row["with_food"]),
                    notes=row["notes"],
                    start_date=supp_start,
                    end_date=supp_end,
                    was_active_entire_period=was_active_entire_period,
                )
            )

        return SupplementHistoryResponse(
            start_date=start_date,
            end_date=end_date,
            supplements=supplements,
        )


async def update_supplement(
    supplement_id: int,
    data: SupplementUpdate,
    db_path: str | None = None,
) -> SupplementResponse:
    """Update a supplement."""
    await get_supplement(supplement_id, db_path)

    async with get_db(db_path) as db:
        updates = ["updated_at = ?"]
        values = [datetime.now().isoformat()]

        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                updates.append(f"{field} = ?")
                if isinstance(value, date):
                    values.append(value.isoformat())
                elif hasattr(value, "value"):  # Enum
                    values.append(value.value)
                else:
                    values.append(value)

        if len(updates) > 1:  # More than just updated_at
            values.append(supplement_id)
            query = f"UPDATE supplements SET {', '.join(updates)} WHERE id = ?"
            await db.execute(query, values)
            await db.commit()

    return await get_supplement(supplement_id, db_path)


async def delete_supplement(supplement_id: int, db_path: str | None = None) -> None:
    """Delete a supplement."""
    await get_supplement(supplement_id, db_path)

    async with get_db(db_path) as db:
        await db.execute("DELETE FROM supplements WHERE id = ?", (supplement_id,))
        await db.commit()
