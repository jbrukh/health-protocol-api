from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class IngredientBase(BaseModel):
    name: str
    brand: Optional[str] = None
    serving_size: float
    serving_unit: str
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    sodium_mg: float = 0
    calories: float = 0


class IngredientCreate(IngredientBase):
    pass


class IngredientUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    serving_size: Optional[float] = None
    serving_unit: Optional[str] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    calories: Optional[float] = None


class IngredientResponse(IngredientBase):
    id: int
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True
