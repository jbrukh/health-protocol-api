from typing import List
from datetime import date
from pydantic import BaseModel
from app.schemas.food import DailySummary, FoodEntryResponse
from app.schemas.exercise import ExerciseResponse
from app.schemas.target import TargetResponse


class TargetProgress(BaseModel):
    target: TargetResponse
    current_value: float
    remaining: float
    percent_complete: float


class DashboardResponse(BaseModel):
    date: date
    food_summary: DailySummary
    food_entries: List[FoodEntryResponse]
    exercises: List[ExerciseResponse]
    target_progress: List[TargetProgress]
