from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class ProfileTargets(BaseModel):
    calories_min: int
    calories_max: int
    protein_min_g: int
    protein_max_g: int
    carbs_min_g: int
    carbs_max_g: int
    fats_min_g: int
    fats_max_g: int
    sodium_max_mg: int


class ProfileResponse(BaseModel):
    birthdate: Optional[date] = None
    age: Optional[int] = None
    height_inches: Optional[float] = None
    targets: ProfileTargets
    updated_at: Optional[datetime] = None


class ProfileUpdate(BaseModel):
    birthdate: Optional[date] = None
    height_inches: Optional[float] = None
    calories_min: Optional[int] = None
    calories_max: Optional[int] = None
    protein_min_g: Optional[int] = None
    protein_max_g: Optional[int] = None
    carbs_min_g: Optional[int] = None
    carbs_max_g: Optional[int] = None
    fats_min_g: Optional[int] = None
    fats_max_g: Optional[int] = None
    sodium_max_mg: Optional[int] = None
