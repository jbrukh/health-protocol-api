from typing import Optional, TYPE_CHECKING
import datetime as dt
from sqlalchemy import ForeignKey, String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.daily_log import DailyLog
    from app.models.ingredient import Ingredient


class FoodEntry(Base):
    __tablename__ = "food_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    daily_log_id: Mapped[int] = mapped_column(ForeignKey("daily_logs.id"), index=True)
    ingredient_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ingredients.id"))

    # Quantity consumed
    quantity: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20))

    # Denormalized nutrition values (computed at time of entry)
    protein_g: Mapped[float] = mapped_column(Float, default=0)
    carbs_g: Mapped[float] = mapped_column(Float, default=0)
    fat_g: Mapped[float] = mapped_column(Float, default=0)
    sodium_mg: Mapped[float] = mapped_column(Float, default=0)
    calories: Mapped[float] = mapped_column(Float, default=0)

    # Optional label for meal (breakfast, lunch, dinner, snack)
    meal_label: Mapped[Optional[str]] = mapped_column(String(50))

    # Description for custom entries without ingredient reference
    description: Mapped[Optional[str]] = mapped_column(String(255))

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    daily_log: Mapped["DailyLog"] = relationship("DailyLog", back_populates="food_entries")
    ingredient: Mapped[Optional["Ingredient"]] = relationship("Ingredient")
