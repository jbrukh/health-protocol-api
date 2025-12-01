from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base


class NutritionLabel(Base):
    """Nutrition label from packaged food - can be converted to ingredient."""

    __tablename__ = "nutrition_labels"

    id = Column(Integer, primary_key=True)
    barcode = Column(String(50), unique=True, nullable=True, index=True)
    product_name = Column(String(255), nullable=False)
    brand = Column(String(255), nullable=True)

    # Serving info
    serving_size = Column(Float, nullable=False)
    serving_unit = Column(String(20), nullable=False)
    servings_per_container = Column(Float, nullable=True)

    # Macros per serving
    calories = Column(Float, nullable=False, default=0)
    protein_g = Column(Float, nullable=False, default=0)
    carbs_g = Column(Float, nullable=False, default=0)
    fat_g = Column(Float, nullable=False, default=0)
    fiber_g = Column(Float, nullable=True)
    sugar_g = Column(Float, nullable=True)
    sodium_mg = Column(Float, nullable=False, default=0)

    # Optional additional nutrients
    saturated_fat_g = Column(Float, nullable=True)
    cholesterol_mg = Column(Float, nullable=True)
    potassium_mg = Column(Float, nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
