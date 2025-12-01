from typing import Optional, Dict, Any
import datetime as dt
from sqlalchemy import Date, String, Integer, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    exercise_type: Mapped[str] = mapped_column(String(100))
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Flexible storage for type-specific data
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
