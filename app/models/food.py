from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class FoodCreate(BaseModel):
    date: date
    marker: str
    name: str
    amount: float
    unit: str
    calories: int
    protein_g: float
    carbs_g: float
    fats_g: float
    sodium_mg: int = 0


class FoodFromRecipe(BaseModel):
    recipe_id: int
    date: date
    marker: str
    scale: float = 1.0


class FoodResponse(BaseModel):
    id: int
    date: date
    marker: str
    name: str
    amount: float
    unit: str
    calories: int
    protein_g: float
    carbs_g: float
    fats_g: float
    sodium_mg: int
    ingredient_id: Optional[int] = None
    recipe_id: Optional[int] = None
    created_at: datetime


class FoodUpdate(BaseModel):
    marker: Optional[str] = None
    name: Optional[str] = None
    amount: Optional[float] = None
    unit: Optional[str] = None
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fats_g: Optional[float] = None
    sodium_mg: Optional[int] = None
