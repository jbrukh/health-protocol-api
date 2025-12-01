from typing import Optional
import datetime as dt
from sqlalchemy import String, Float, Boolean, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Supplement(Base):
    __tablename__ = "supplements"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    dosage: Mapped[float] = mapped_column(Float)
    dosage_unit: Mapped[str] = mapped_column(String(20))
    time_of_day: Mapped[Optional[str]] = mapped_column(String(50))  # morning, afternoon, evening, with_meals
    with_food: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow
    )
