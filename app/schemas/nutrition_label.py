from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class NutritionLabelCreate(BaseModel):
    barcode: Optional[str] = None
    product_name: str
    brand: Optional[str] = None
    serving_size: float
    serving_unit: str
    servings_per_container: Optional[float] = None
    calories: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    sodium_mg: float = 0
    saturated_fat_g: Optional[float] = None
    cholesterol_mg: Optional[float] = None
    potassium_mg: Optional[float] = None
    notes: Optional[str] = None


class NutritionLabelUpdate(BaseModel):
    barcode: Optional[str] = None
    product_name: Optional[str] = None
    brand: Optional[str] = None
    serving_size: Optional[float] = None
    serving_unit: Optional[str] = None
    servings_per_container: Optional[float] = None
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    cholesterol_mg: Optional[float] = None
    potassium_mg: Optional[float] = None
    notes: Optional[str] = None


class NutritionLabelResponse(BaseModel):
    id: int
    barcode: Optional[str]
    product_name: str
    brand: Optional[str]
    serving_size: float
    serving_unit: str
    servings_per_container: Optional[float]
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: Optional[float]
    sugar_g: Optional[float]
    sodium_mg: float
    saturated_fat_g: Optional[float]
    cholesterol_mg: Optional[float]
    potassium_mg: Optional[float]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
