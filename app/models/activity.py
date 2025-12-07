from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DailyActivityCreate(BaseModel):
    date: str  # YYYY-MM-DD
    steps: int | None = None
    distance_miles: float | None = None
    active_calories: int | None = None
    elevation_ft: float | None = None
    source: str = "manual"


class DailyActivityResponse(BaseModel):
    id: int
    date: str
    steps: int | None = None
    distance_miles: float | None = None
    active_calories: int | None = None
    elevation_ft: float | None = None
    source: str
    created_at: datetime
    updated_at: datetime | None = None


class DailyActivityListResponse(BaseModel):
    activities: list[DailyActivityResponse]
    total_in_range: int
    limit: int
    offset: int


class DailyActivitySummaryResponse(BaseModel):
    earliest_date: Optional[str] = None
    latest_date: Optional[str] = None
    total_count: int
