from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RecipeItemCreate(BaseModel):
    ingredient_id: int
    amount: float
    unit: str


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
    name: str
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
    name: Optional[str] = None


class RecipeItemUpdate(BaseModel):
    amount: Optional[float] = None
    unit: Optional[str] = None
