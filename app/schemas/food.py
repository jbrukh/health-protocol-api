from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel
from app.schemas.ingredient import IngredientResponse


class FoodEntryBase(BaseModel):
    quantity: float
    unit: str
    meal_label: Optional[str] = None
    description: Optional[str] = None


class FoodEntryCreate(FoodEntryBase):
    date: date
    ingredient_id: Optional[int] = None
    # Allow manual macro entry for custom foods
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    calories: Optional[float] = None


class FoodEntryUpdate(BaseModel):
    quantity: Optional[float] = None
    unit: Optional[str] = None
    meal_label: Optional[str] = None
    description: Optional[str] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    calories: Optional[float] = None


class FoodEntryResponse(FoodEntryBase):
    id: int
    daily_log_id: int
    ingredient_id: Optional[int]
    protein_g: float
    carbs_g: float
    fat_g: float
    sodium_mg: float
    calories: float
    created_at: datetime
    ingredient: Optional[IngredientResponse] = None

    class Config:
        from_attributes = True


class DailySummary(BaseModel):
    date: date
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    total_sodium_mg: float
    total_calories: float
    entry_count: int


class CalorieHistoryEntry(BaseModel):
    date: date
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    total_sodium_mg: float
