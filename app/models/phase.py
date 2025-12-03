from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class PhaseCreate(BaseModel):
    name: str
    description: str
    start_date: date
    end_date: date
    is_recurring: bool = False
    recurrence_interval_days: Optional[int] = None


class PhaseResponse(BaseModel):
    id: int
    name: str
    description: str
    start_date: date
    end_date: date
    is_recurring: bool
    recurrence_interval_days: Optional[int]
    is_active: bool
    days_remaining: Optional[int]
    created_at: datetime
    updated_at: datetime


class PhaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_recurring: Optional[bool] = None
    recurrence_interval_days: Optional[int] = None


class PhaseListResponse(BaseModel):
    phases: list[PhaseResponse]


class UpcomingPhase(BaseModel):
    id: int
    name: str
    description: str
    start_date: date
    end_date: date
    days_until_start: int


class ActivePhase(BaseModel):
    id: int
    name: str
    description: str
    start_date: date
    end_date: date
    days_remaining: int
    is_recurring: bool


class ActivePhasesResponse(BaseModel):
    date: date
    active_phases: list[ActivePhase]
    upcoming_phases: list[UpcomingPhase]
    total_active: int
    total_upcoming: int
