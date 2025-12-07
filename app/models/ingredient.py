from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class IngredientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    default_amount: float = Field(gt=0)
    default_unit: str = Field(min_length=1, max_length=50)
    calories: int = Field(ge=0)
    protein_g: float = Field(ge=0)
    carbs_g: float = Field(ge=0)
    fats_g: float = Field(ge=0)
    sodium_mg: int = Field(default=0, ge=0)


class IngredientResponse(BaseModel):
    id: int
    name: str
    default_amount: float
    default_unit: str
    calories: int
    protein_g: float
    carbs_g: float
    fats_g: float
    sodium_mg: int
    created_at: datetime


class IngredientUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    default_amount: Optional[float] = Field(default=None, gt=0)
    default_unit: Optional[str] = Field(default=None, min_length=1, max_length=50)
    calories: Optional[int] = Field(default=None, ge=0)
    protein_g: Optional[float] = Field(default=None, ge=0)
    carbs_g: Optional[float] = Field(default=None, ge=0)
    fats_g: Optional[float] = Field(default=None, ge=0)
    sodium_mg: Optional[int] = Field(default=None, ge=0)
