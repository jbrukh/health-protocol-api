from datetime import date, time, datetime
from typing import Optional

from pydantic import BaseModel, model_validator


class BodyMeasurementCreate(BaseModel):
    date: date
    time: time
    weight_lbs: Optional[float] = None
    waist_cm: Optional[float] = None

    @model_validator(mode="after")
    def check_at_least_one_measurement(self):
        if self.weight_lbs is None and self.waist_cm is None:
            raise ValueError("At least one of weight_lbs or waist_cm must be provided")
        return self


class BodyMeasurementResponse(BaseModel):
    id: int
    date: date
    time: time
    weight_lbs: Optional[float] = None
    waist_cm: Optional[float] = None
    created_at: datetime


class BodyMeasurementUpdate(BaseModel):
    date: Optional[date] = None
    time: Optional[time] = None
    weight_lbs: Optional[float] = None
    waist_cm: Optional[float] = None
