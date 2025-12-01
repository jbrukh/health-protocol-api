from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from app.schemas.ingredient import IngredientResponse


class RecipeIngredientBase(BaseModel):
    ingredient_id: int
    quantity: float
    unit: str


class RecipeIngredientCreate(RecipeIngredientBase):
    pass


class RecipeIngredientResponse(RecipeIngredientBase):
    id: int
    ingredient: Optional[IngredientResponse] = None

    class Config:
        from_attributes = True


class RecipeBase(BaseModel):
    name: str
    description: Optional[str] = None


class RecipeCreate(RecipeBase):
    ingredients: List[RecipeIngredientCreate]


class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[List[RecipeIngredientCreate]] = None


class RecipeResponse(RecipeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    ingredients: List[RecipeIngredientResponse] = []
    # Computed totals
    total_protein_g: float = 0
    total_carbs_g: float = 0
    total_fat_g: float = 0
    total_sodium_mg: float = 0
    total_calories: float = 0

    class Config:
        from_attributes = True
