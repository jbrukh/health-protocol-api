from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status

from app.database import get_db
from app.models.phase import (
    PhaseCreate,
    PhaseResponse,
    PhaseUpdate,
    PhaseListResponse,
    ActivePhase,
    UpcomingPhase,
    ActivePhasesResponse,
)
from app.utils.timezone import current_date_in_timezone


def _compute_is_active(start_date: date, end_date: date, today: date) -> bool:
    """Check if a phase is currently active."""
    return start_date <= today <= end_date


def _compute_days_remaining(end_date: date, today: date) -> Optional[int]:
    """Compute days remaining until phase ends."""
    if end_date < today:
        return None
    return (end_date - today).days


def _row_to_response(row, today: date) -> PhaseResponse:
    """Convert a database row to a PhaseResponse."""
    start_dt = date.fromisoformat(row["start_date"])
    end_dt = date.fromisoformat(row["end_date"])
    return PhaseResponse(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        start_date=start_dt,
        end_date=end_dt,
        is_recurring=bool(row["is_recurring"]),
        recurrence_interval_days=row["recurrence_interval_days"],
        is_active=_compute_is_active(start_dt, end_dt, today),
        days_remaining=_compute_days_remaining(end_dt, today),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


async def create_phase(data: PhaseCreate, db_path: str | None = None) -> PhaseResponse:
    """Create a new phase."""
    async with get_db(db_path) as db:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            """
            INSERT INTO phases (name, description, start_date, end_date, is_recurring, recurrence_interval_days, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.name,
                data.description,
                data.start_date.isoformat(),
                data.end_date.isoformat(),
                data.is_recurring,
                data.recurrence_interval_days,
                now,
                now,
            ),
        )
        await db.commit()
        phase_id = cursor.lastrowid

    return await get_phase(phase_id, db_path)


async def get_phase(phase_id: int, db_path: str | None = None, timezone: str | None = None) -> PhaseResponse:
    """Get a phase by ID."""
    today = current_date_in_timezone(timezone)
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM phases WHERE id = ?",
            (phase_id,),
        )
        row = await cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Phase with id {phase_id} not found",
            )

        return _row_to_response(row, today)


async def list_phases(
    active: Optional[bool] = None,
    include_past: bool = True,
    db_path: str | None = None,
    timezone: str | None = None,
) -> PhaseListResponse:
    """List all phases with optional filters."""
    today = current_date_in_timezone(timezone)
    async with get_db(db_path) as db:
        query = "SELECT * FROM phases"
        params = []

        if not include_past:
            query += " WHERE end_date >= ?"
            params.append(today.isoformat())

        query += " ORDER BY start_date, end_date"
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

        phases = [_row_to_response(row, today) for row in rows]

        # Filter by active status in Python (since it's computed)
        if active is not None:
            phases = [p for p in phases if p.is_active == active]

        return PhaseListResponse(phases=phases)


async def get_active_phases(db_path: str | None = None, timezone: str | None = None) -> ActivePhasesResponse:
    """Get all currently active phases and upcoming phases (next 7 days)."""
    today = current_date_in_timezone(timezone)
    upcoming_window = today + timedelta(days=7)

    async with get_db(db_path) as db:
        # Get active phases (start_date <= today <= end_date)
        cursor = await db.execute(
            """
            SELECT * FROM phases
            WHERE start_date <= ? AND end_date >= ?
            ORDER BY end_date
            """,
            (today.isoformat(), today.isoformat()),
        )
        active_rows = await cursor.fetchall()

        # Get upcoming phases (start_date > today AND start_date <= today + 7 days)
        cursor = await db.execute(
            """
            SELECT * FROM phases
            WHERE start_date > ? AND start_date <= ?
            ORDER BY start_date
            """,
            (today.isoformat(), upcoming_window.isoformat()),
        )
        upcoming_rows = await cursor.fetchall()

        active_phases = [
            ActivePhase(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                start_date=date.fromisoformat(row["start_date"]),
                end_date=date.fromisoformat(row["end_date"]),
                days_remaining=(date.fromisoformat(row["end_date"]) - today).days,
                is_recurring=bool(row["is_recurring"]),
            )
            for row in active_rows
        ]

        upcoming_phases = [
            UpcomingPhase(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                start_date=date.fromisoformat(row["start_date"]),
                end_date=date.fromisoformat(row["end_date"]),
                days_until_start=(date.fromisoformat(row["start_date"]) - today).days,
            )
            for row in upcoming_rows
        ]

        return ActivePhasesResponse(
            date=today,
            active_phases=active_phases,
            upcoming_phases=upcoming_phases,
            total_active=len(active_phases),
            total_upcoming=len(upcoming_phases),
        )


async def update_phase(
    phase_id: int,
    data: PhaseUpdate,
    db_path: str | None = None,
) -> PhaseResponse:
    """Update a phase."""
    await get_phase(phase_id, db_path)

    async with get_db(db_path) as db:
        updates = ["updated_at = ?"]
        values = [datetime.now().isoformat()]

        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                updates.append(f"{field} = ?")
                if isinstance(value, date):
                    values.append(value.isoformat())
                else:
                    values.append(value)

        if len(updates) > 1:  # More than just updated_at
            values.append(phase_id)
            query = f"UPDATE phases SET {', '.join(updates)} WHERE id = ?"
            await db.execute(query, values)
            await db.commit()

    return await get_phase(phase_id, db_path)


async def delete_phase(phase_id: int, db_path: str | None = None) -> None:
    """Delete a phase."""
    await get_phase(phase_id, db_path)

    async with get_db(db_path) as db:
        await db.execute("DELETE FROM phases WHERE id = ?", (phase_id,))
        await db.commit()
