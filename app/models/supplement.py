from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, computed_field


class TimeOfDay(str, Enum):
    morning = "morning"
    midday = "midday"
    afternoon = "afternoon"
    evening = "evening"
    bedtime = "bedtime"


def format_human_readable(amount: float) -> str:
    """Format a number in human-readable form (e.g., 10B, 5M, 1K)."""
    if amount >= 1_000_000_000:
        val = amount / 1_000_000_000
        return f"{val:g}B" if val != int(val) else f"{int(val)}B"
    elif amount >= 1_000_000:
        val = amount / 1_000_000
        return f"{val:g}M" if val != int(val) else f"{int(val)}M"
    elif amount >= 1_000:
        val = amount / 1_000
        return f"{val:g}K" if val != int(val) else f"{int(val)}K"
    else:
        return f"{amount:g}" if amount != int(amount) else str(int(amount))


class SupplementCreate(BaseModel):
    name: str
    dosage_amount: float
    dosage_unit: str
    purpose: str
    time_of_day: TimeOfDay
    with_food: bool = False
    notes: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None


class SupplementResponse(BaseModel):
    id: int
    name: str
    dosage_amount: float
    dosage_unit: str
    purpose: str
    time_of_day: TimeOfDay
    with_food: bool
    notes: Optional[str]
    start_date: date
    end_date: Optional[date]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def dosage_display(self) -> str:
        """Human-readable dosage string."""
        return f"{format_human_readable(self.dosage_amount)} {self.dosage_unit}"


class SupplementUpdate(BaseModel):
    name: Optional[str] = None
    dosage_amount: Optional[float] = None
    dosage_unit: Optional[str] = None
    purpose: Optional[str] = None
    time_of_day: Optional[TimeOfDay] = None
    with_food: Optional[bool] = None
    notes: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class SupplementScheduleItem(BaseModel):
    id: int
    name: str
    dosage_amount: float
    dosage_unit: str
    with_food: bool
    notes: Optional[str]

    @computed_field
    @property
    def dosage_display(self) -> str:
        """Human-readable dosage string."""
        return f"{format_human_readable(self.dosage_amount)} {self.dosage_unit}"


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
    dosage_amount: float
    dosage_unit: str
    purpose: str
    time_of_day: TimeOfDay
    with_food: bool
    notes: Optional[str]
    start_date: date
    end_date: Optional[date]
    was_active_entire_period: bool

    @computed_field
    @property
    def dosage_display(self) -> str:
        """Human-readable dosage string."""
        return f"{format_human_readable(self.dosage_amount)} {self.dosage_unit}"


class SupplementHistoryResponse(BaseModel):
    start_date: date
    end_date: date
    supplements: list[SupplementHistoryItem]


class SupplementListResponse(BaseModel):
    supplements: list[SupplementResponse]
