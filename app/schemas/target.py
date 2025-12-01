from datetime import date, datetime
from pydantic import BaseModel


class TargetBase(BaseModel):
    name: str
    value: float
    unit: str


class TargetCreate(TargetBase):
    effective_from: date


class TargetResponse(TargetBase):
    id: int
    effective_from: date
    created_at: datetime

    class Config:
        from_attributes = True
