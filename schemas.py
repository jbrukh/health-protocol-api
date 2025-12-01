from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class MacroEntryBase(BaseModel):
    date: date
    protein: float = Field(default=0.0, ge=0, description="Protein in grams")
    carbs: float = Field(default=0.0, ge=0, description="Carbohydrates in grams")
    fat: float = Field(default=0.0, ge=0, description="Fat in grams")


class MacroEntryCreate(MacroEntryBase):
    pass


class MacroEntryUpdate(BaseModel):
    protein: Optional[float] = Field(default=None, ge=0, description="Protein in grams")
    carbs: Optional[float] = Field(default=None, ge=0, description="Carbohydrates in grams")
    fat: Optional[float] = Field(default=None, ge=0, description="Fat in grams")


class MacroEntry(MacroEntryBase):
    id: int

    class Config:
        from_attributes = True
