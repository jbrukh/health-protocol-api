from datetime import date

from fastapi import APIRouter, Depends, Query

from app.auth import verify_token
from app.models.exercise import ExerciseCreate, ExerciseResponse, ExerciseUpdate
from app.services import exercise_service

router = APIRouter()


@router.post("", response_model=ExerciseResponse, status_code=201)
async def create_exercise(
    data: ExerciseCreate,
    _: str = Depends(verify_token),
) -> ExerciseResponse:
    """Log an exercise."""
    return await exercise_service.create_exercise(data)


@router.get("", response_model=list[ExerciseResponse])
async def get_exercises(
    date: date = Query(..., description="Date to get exercises for (YYYY-MM-DD)"),
    _: str = Depends(verify_token),
) -> list[ExerciseResponse]:
    """Get exercises for a date."""
    return await exercise_service.get_exercises(date)


@router.get("/history", response_model=list[ExerciseResponse])
async def get_exercise_history(
    days: int = Query(7, description="Number of days to look back"),
    _: str = Depends(verify_token),
) -> list[ExerciseResponse]:
    """Get exercise history for the last N days."""
    return await exercise_service.get_exercise_history(days)


@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: int,
    _: str = Depends(verify_token),
) -> ExerciseResponse:
    """Get an exercise by ID."""
    return await exercise_service.get_exercise(exercise_id)


@router.put("/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(
    exercise_id: int,
    data: ExerciseUpdate,
    _: str = Depends(verify_token),
) -> ExerciseResponse:
    """Update an exercise."""
    return await exercise_service.update_exercise(exercise_id, data)


@router.delete("/{exercise_id}", status_code=204)
async def delete_exercise(
    exercise_id: int,
    _: str = Depends(verify_token),
) -> None:
    """Delete an exercise."""
    await exercise_service.delete_exercise(exercise_id)
