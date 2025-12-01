from sqlalchemy import Column, Integer, Float, Date
from database import Base


class MacroEntry(Base):
    __tablename__ = "macro_entries"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    protein = Column(Float, default=0.0)
    carbs = Column(Float, default=0.0)
    fat = Column(Float, default=0.0)
