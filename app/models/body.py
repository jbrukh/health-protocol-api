from datetime import date, time, datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class BodyMeasurementCreate(BaseModel):
    date: date
    time: time
    weight_lbs: Optional[float] = Field(default=None, gt=0, le=1500)  # Reasonable human weight
    waist_cm: Optional[float] = Field(default=None, gt=0, le=500)
    fat_mass_lbs: Optional[float] = Field(default=None, ge=0, le=1000)
    muscle_mass_lbs: Optional[float] = Field(default=None, ge=0, le=500)
    bone_mass_lbs: Optional[float] = Field(default=None, ge=0, le=100)
    body_water_pct: Optional[float] = Field(default=None, ge=0, le=100)
    source: str = Field(default="manual", max_length=50)

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
    fat_mass_lbs: Optional[float] = None
    muscle_mass_lbs: Optional[float] = None
    bone_mass_lbs: Optional[float] = None
    body_water_pct: Optional[float] = None
    source: str = "manual"
    created_at: datetime


class BodyMeasurementUpdate(BaseModel):
    date: Optional[date] = None
    time: Optional[time] = None
    weight_lbs: Optional[float] = Field(default=None, gt=0, le=1500)
    waist_cm: Optional[float] = Field(default=None, gt=0, le=500)
    fat_mass_lbs: Optional[float] = Field(default=None, ge=0, le=1000)
    muscle_mass_lbs: Optional[float] = Field(default=None, ge=0, le=500)
    bone_mass_lbs: Optional[float] = Field(default=None, ge=0, le=100)
    body_water_pct: Optional[float] = Field(default=None, ge=0, le=100)
