from typing import Optional, List
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_db
from app.models import Exercise
from app.schemas import ExerciseCreate, ExerciseUpdate, ExerciseResponse

router = APIRouter(prefix="/exercises", tags=["Exercises"])


@router.post("", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    data: ExerciseCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Log an exercise."""
    exercise = Exercise(**data.model_dump())
    db.add(exercise)
    await db.flush()
    await db.refresh(exercise)
    return exercise


@router.get("", response_model=List[ExerciseResponse])
async def get_exercises(
    exercise_date: Optional[date] = Query(None, alias="date", description="Get exercises for a specific date"),
    start: Optional[date] = Query(None, description="Start date for range query"),
    end: Optional[date] = Query(None, description="End date for range query"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get exercises for a date or date range."""
    query = select(Exercise)

    if exercise_date:
        query = query.where(Exercise.date == exercise_date)
    elif start and end:
        query = query.where(Exercise.date >= start, Exercise.date <= end)
    else:
        # Default to last 30 days if no filter
        thirty_days_ago = date.today() - timedelta(days=30)
        query = query.where(Exercise.date >= thirty_days_ago)

    query = query.order_by(Exercise.date.desc(), Exercise.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{exercise_id}", response_model=ExerciseResponse, include_in_schema=False)
async def get_exercise(
    exercise_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get a specific exercise."""
    result = await db.execute(
        select(Exercise).where(Exercise.id == exercise_id)
    )
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return exercise


@router.patch("/{exercise_id}", response_model=ExerciseResponse, include_in_schema=False)
async def update_exercise(
    exercise_id: int,
    data: ExerciseUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update an exercise."""
    result = await db.execute(
        select(Exercise).where(Exercise.id == exercise_id)
    )
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(exercise, key, value)

    await db.flush()
    await db.refresh(exercise)
    return exercise


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
async def delete_exercise(
    exercise_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Delete an exercise."""
    result = await db.execute(
        select(Exercise).where(Exercise.id == exercise_id)
    )
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    await db.delete(exercise)
