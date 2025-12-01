from typing import Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel


class ExerciseBase(BaseModel):
    date: date
    exercise_type: str
    duration_minutes: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class ExerciseCreate(ExerciseBase):
    pass


class ExerciseUpdate(BaseModel):
    date: Optional[date] = None
    exercise_type: Optional[str] = None
    duration_minutes: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class ExerciseResponse(ExerciseBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
