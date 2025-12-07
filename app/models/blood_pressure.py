from datetime import datetime
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
