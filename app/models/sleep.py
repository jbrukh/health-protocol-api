from datetime import datetime
from pydantic import BaseModel


class SleepCreate(BaseModel):
    date: str  # YYYY-MM-DD (night of sleep)
    sleep_start: datetime | None = None
    sleep_end: datetime | None = None
    duration_minutes: int | None = None
    deep_minutes: int | None = None
    light_minutes: int | None = None
    rem_minutes: int | None = None
    awake_minutes: int | None = None
    source: str = "manual"


class SleepResponse(BaseModel):
    id: int
    date: str
    sleep_start: datetime | None = None
    sleep_end: datetime | None = None
    duration_minutes: int | None = None
    deep_minutes: int | None = None
    light_minutes: int | None = None
    rem_minutes: int | None = None
    awake_minutes: int | None = None
    source: str
    created_at: datetime
