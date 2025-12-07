from datetime import date, datetime
from typing import Optional, Any

from pydantic import BaseModel, Field


class ExerciseCreate(BaseModel):
    date: date
    exercise_type: str = Field(min_length=1, max_length=100)
    duration_minutes: int = Field(gt=0, le=1440)  # Max 24 hours
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
    exercise_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    duration_minutes: Optional[int] = Field(default=None, gt=0, le=1440)
    details: Optional[dict[str, Any]] = None
