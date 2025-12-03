from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class TimeOfDay(str, Enum):
    morning = "morning"
    midday = "midday"
    afternoon = "afternoon"
    evening = "evening"
    bedtime = "bedtime"


class SupplementCreate(BaseModel):
    name: str
    dosage: str
    purpose: str
    time_of_day: TimeOfDay
    with_food: bool = False
    notes: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None


class SupplementResponse(BaseModel):
    id: int
    name: str
    dosage: str
    purpose: str
    time_of_day: TimeOfDay
    with_food: bool
    notes: Optional[str]
    start_date: date
    end_date: Optional[date]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SupplementUpdate(BaseModel):
    name: Optional[str] = None
    dosage: Optional[str] = None
    purpose: Optional[str] = None
    time_of_day: Optional[TimeOfDay] = None
    with_food: Optional[bool] = None
    notes: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class SupplementScheduleItem(BaseModel):
    id: int
    name: str
    dosage: str
    with_food: bool
    notes: Optional[str]


class SupplementScheduleSummary(BaseModel):
    total_supplements: int
    with_food_count: int
    without_food_count: int


class SupplementScheduleResponse(BaseModel):
    date: date
    schedule: dict[str, list[SupplementScheduleItem]]
    summary: SupplementScheduleSummary


class SupplementHistoryItem(BaseModel):
    id: int
    name: str
    dosage: str
    purpose: str
    time_of_day: TimeOfDay
    with_food: bool
    notes: Optional[str]
    start_date: date
    end_date: Optional[date]
    was_active_entire_period: bool


class SupplementHistoryResponse(BaseModel):
    start_date: date
    end_date: date
    supplements: list[SupplementHistoryItem]


class SupplementListResponse(BaseModel):
    supplements: list[SupplementResponse]
