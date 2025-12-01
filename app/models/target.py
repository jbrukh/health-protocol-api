from typing import Optional
import datetime as dt
from sqlalchemy import Date, String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Target(Base):
    __tablename__ = "targets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)  # e.g., "calories", "protein_g", "sodium_mg"
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(50))
    effective_from: Mapped[dt.date] = mapped_column(Date, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
