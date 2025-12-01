from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class SupplementBase(BaseModel):
    name: str
    dosage: float
    dosage_unit: str
    time_of_day: Optional[str] = None
    with_food: bool = False
    notes: Optional[str] = None


class SupplementCreate(SupplementBase):
    pass


class SupplementUpdate(BaseModel):
    name: Optional[str] = None
    dosage: Optional[float] = None
    dosage_unit: Optional[str] = None
    time_of_day: Optional[str] = None
    with_food: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class SupplementResponse(SupplementBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
