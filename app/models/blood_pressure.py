from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class BloodPressureCreate(BaseModel):
    date: str  # YYYY-MM-DD
    time: str  # HH:MM:SS
    systolic: int
    diastolic: int
    heart_rate: int | None = None
    source: str = "manual"


class BloodPressureResponse(BaseModel):
    id: int
    date: str
    time: str
    systolic: int
    diastolic: int
    heart_rate: int | None = None
    source: str
    created_at: datetime


class BloodPressureListResponse(BaseModel):
    readings: list[BloodPressureResponse]
    total_in_range: int
    limit: int
    offset: int


class BloodPressureSummaryResponse(BaseModel):
    earliest_date: Optional[str] = None
    latest_date: Optional[str] = None
    total_count: int
