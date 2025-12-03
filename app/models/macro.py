from datetime import date, time
from typing import Optional

from pydantic import BaseModel


class MacroTotals(BaseModel):
    calories: int
    protein_g: float
    carbs_g: float
    fats_g: float
    sodium_mg: int


class MacroTargetStatus(BaseModel):
    min: Optional[int] = None
    max: Optional[int] = None
    current: float
    percent_of_min: Optional[float] = None
    percent_of_max: Optional[float] = None


class SodiumTargetStatus(BaseModel):
    max: int
    current: int
    percent_of_max: float


class MacroTargets(BaseModel):
    calories: MacroTargetStatus
    protein_g: MacroTargetStatus
    carbs_g: MacroTargetStatus
    fats_g: MacroTargetStatus
    sodium_mg: SodiumTargetStatus


class MacroTodayResponse(BaseModel):
    date: date
    totals: MacroTotals
    targets: MacroTargets


class MacroRemainingItem(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    note: Optional[str] = None


class SodiumRemainingItem(BaseModel):
    max: float


class MacroRemaining(BaseModel):
    calories: MacroRemainingItem
    protein_g: MacroRemainingItem
    carbs_g: MacroRemainingItem
    fats_g: MacroRemainingItem
    sodium_mg: SodiumRemainingItem


class MacroRemainingResponse(BaseModel):
    date: date
    remaining: MacroRemaining
    suggestion: Optional[str] = None


class BodyMeasurementSummary(BaseModel):
    time: time
    weight_lbs: Optional[float] = None
    waist_cm: Optional[float] = None


class BodyDaySummary(BaseModel):
    weight_lbs: Optional[float] = None
    waist_cm: Optional[float] = None
    measurements: list[BodyMeasurementSummary]


class MacroHistoryDay(BaseModel):
    date: date
    macros: MacroTotals
    body: Optional[BodyDaySummary] = None


class MacroHistoryResponse(BaseModel):
    days: list[MacroHistoryDay]
