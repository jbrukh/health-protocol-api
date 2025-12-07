from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RecipeItemCreate(BaseModel):
    ingredient_id: int = Field(gt=0)
    amount: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=50)


class RecipeItemResponse(BaseModel):
    id: int
    ingredient_id: int
    ingredient_name: str
    amount: float
    unit: str
    calories: int
    protein_g: float
    carbs_g: float
    fats_g: float
    sodium_mg: int


class RecipeTotals(BaseModel):
    calories: int
    protein_g: float
    carbs_g: float
    fats_g: float
    sodium_mg: int


class RecipeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    items: list[RecipeItemCreate] = []


class RecipeResponse(BaseModel):
    id: int
    name: str
    items: list[RecipeItemResponse] = []
    totals: RecipeTotals
    created_at: datetime
    updated_at: datetime


class RecipeListResponse(BaseModel):
    id: int
    name: str
    totals: RecipeTotals
    created_at: datetime
    updated_at: datetime


class RecipeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)


class RecipeItemUpdate(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0)
    unit: Optional[str] = Field(default=None, min_length=1, max_length=50)
