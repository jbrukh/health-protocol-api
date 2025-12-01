from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class BiomarkerBase(BaseModel):
    name: str
    value: float
    unit: str
    notes: Optional[str] = None


class BiomarkerCreate(BiomarkerBase):
    measured_at: datetime


class BiomarkerResponse(BiomarkerBase):
    id: int
    measured_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class BiomarkerComparison(BaseModel):
    name: str
    unit: str
    readings: List[BiomarkerResponse]
    min_value: float
    max_value: float
    change: Optional[float] = None  # Difference between first and last reading
    change_percent: Optional[float] = None
