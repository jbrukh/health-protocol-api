from datetime import date, datetime
from typing import Optional, Any

from pydantic import BaseModel


class ExerciseCreate(BaseModel):
    date: date
    exercise_type: str
    duration_minutes: int
    details: Optional[dict[str, Any]] = None


class ExerciseResponse(BaseModel):
    id: int
    date: date
    exercise_type: str
    duration_minutes: int
    details: Optional[dict[str, Any]] = None
    created_at: datetime


class ExerciseUpdate(BaseModel):
    date: Optional[date] = None
    exercise_type: Optional[str] = None
    duration_minutes: Optional[int] = None
    details: Optional[dict[str, Any]] = None
