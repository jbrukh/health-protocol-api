import json
from datetime import date, datetime
from typing import Optional

from fastapi import HTTPException, status

from app.database import get_db
from app.models.exercise import ExerciseCreate, ExerciseResponse, ExerciseUpdate


async def create_exercise(data: ExerciseCreate, db_path: str | None = None) -> ExerciseResponse:
    """Create an exercise entry."""
    async with get_db(db_path) as db:
        details_json = json.dumps(data.details) if data.details else None
        cursor = await db.execute(
            """
            INSERT INTO exercises (date, exercise_type, duration_minutes, details)
            VALUES (?, ?, ?, ?)
            """,
            (
                data.date.isoformat(),
                data.exercise_type,
                data.duration_minutes,
                details_json,
            ),
        )
        await db.commit()
        exercise_id = cursor.lastrowid

    return await get_exercise(exercise_id, db_path)


async def get_exercise(exercise_id: int, db_path: str | None = None) -> ExerciseResponse:
    """Get an exercise by ID."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM exercises WHERE id = ?",
            (exercise_id,),
        )
        row = await cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exercise with id {exercise_id} not found",
            )

        details = json.loads(row["details"]) if row["details"] else None
        return ExerciseResponse(
            id=row["id"],
            date=date.fromisoformat(row["date"]),
            exercise_type=row["exercise_type"],
            duration_minutes=row["duration_minutes"],
            details=details,
            created_at=datetime.fromisoformat(row["created_at"]),
        )


async def get_exercises(exercise_date: date, db_path: str | None = None) -> list[ExerciseResponse]:
    """Get all exercises for a date."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM exercises WHERE date = ? ORDER BY created_at",
            (exercise_date.isoformat(),),
        )
        rows = await cursor.fetchall()

        return [
            ExerciseResponse(
                id=row["id"],
                date=date.fromisoformat(row["date"]),
                exercise_type=row["exercise_type"],
                duration_minutes=row["duration_minutes"],
                details=json.loads(row["details"]) if row["details"] else None,
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]


async def get_exercise_history(days: int, db_path: str | None = None) -> list[ExerciseResponse]:
    """Get exercises from the last N days."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            """
            SELECT * FROM exercises
            WHERE date >= date('now', ?)
            ORDER BY date DESC, created_at
            """,
            (f"-{days} days",),
        )
        rows = await cursor.fetchall()

        return [
            ExerciseResponse(
                id=row["id"],
                date=date.fromisoformat(row["date"]),
                exercise_type=row["exercise_type"],
                duration_minutes=row["duration_minutes"],
                details=json.loads(row["details"]) if row["details"] else None,
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]


async def update_exercise(
    exercise_id: int, data: ExerciseUpdate, db_path: str | None = None
) -> ExerciseResponse:
    """Update an exercise."""
    await get_exercise(exercise_id, db_path)

    async with get_db(db_path) as db:
        updates = []
        values = []
        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                updates.append(f"{field} = ?")
                if field == "details":
                    values.append(json.dumps(value))
                elif isinstance(value, date):
                    values.append(value.isoformat())
                else:
                    values.append(value)

        if updates:
            values.append(exercise_id)
            query = f"UPDATE exercises SET {', '.join(updates)} WHERE id = ?"
            await db.execute(query, values)
            await db.commit()

    return await get_exercise(exercise_id, db_path)


async def delete_exercise(exercise_id: int, db_path: str | None = None) -> None:
    """Delete an exercise."""
    await get_exercise(exercise_id, db_path)

    async with get_db(db_path) as db:
        await db.execute("DELETE FROM exercises WHERE id = ?", (exercise_id,))
        await db.commit()
