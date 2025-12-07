from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class FoodCreate(BaseModel):
    date: date
    marker: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    amount: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=50)
    calories: int = Field(ge=0)
    protein_g: float = Field(ge=0)
    carbs_g: float = Field(ge=0)
    fats_g: float = Field(ge=0)
    sodium_mg: int = Field(default=0, ge=0)


class FoodFromRecipe(BaseModel):
    recipe_id: int = Field(gt=0)
    date: date
    marker: str = Field(min_length=1, max_length=100)
    scale: float = Field(default=1.0, gt=0)


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
    marker: Optional[str] = Field(default=None, min_length=1, max_length=100)
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    amount: Optional[float] = Field(default=None, gt=0)
    unit: Optional[str] = Field(default=None, min_length=1, max_length=50)
    calories: Optional[int] = Field(default=None, ge=0)
    protein_g: Optional[float] = Field(default=None, ge=0)
    carbs_g: Optional[float] = Field(default=None, ge=0)
    fats_g: Optional[float] = Field(default=None, ge=0)
    sodium_mg: Optional[int] = Field(default=None, ge=0)
