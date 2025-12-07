from datetime import datetime
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
