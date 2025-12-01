from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import date
from typing import List
import os

import models
import schemas
from database import engine, get_db

# API Key configuration
API_KEY = os.getenv("API_KEY")  # Set this in Railway environment variables
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Verify API key if one is configured.
    If no API_KEY environment variable is set, allows all requests (development mode).
    """
    if API_KEY is None:
        # No API key configured - allow request (useful for local development)
        return None

    if api_key is None or api_key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing API key. Provide X-API-Key header."
        )
    return api_key


# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Health Protocol API",
    description="API for tracking daily macros and health metrics. Compatible with ChatGPT Custom GPT actions.",
    version="1.0.0",
)

# CORS middleware for ChatGPT integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chat.openai.com", "https://chatgpt.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "Health Protocol API",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.post("/macros/", response_model=schemas.MacroEntry, tags=["Macros"])
def create_or_update_macro_entry(
    entry: schemas.MacroEntryCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Create or update a macro entry for a specific date.
    If an entry already exists for that date, it will be updated.
    """
    db_entry = db.query(models.MacroEntry).filter(
        models.MacroEntry.date == entry.date
    ).first()

    if db_entry:
        # Update existing entry
        db_entry.protein = entry.protein
        db_entry.carbs = entry.carbs
        db_entry.fat = entry.fat
    else:
        # Create new entry
        db_entry = models.MacroEntry(**entry.model_dump())
        db.add(db_entry)

    db.commit()
    db.refresh(db_entry)
    return db_entry


@app.get("/macros/", response_model=List[schemas.MacroEntry], tags=["Macros"])
def get_all_macro_entries(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get all macro entries, ordered by date (most recent first).
    """
    entries = db.query(models.MacroEntry).order_by(
        models.MacroEntry.date.desc()
    ).offset(skip).limit(limit).all()
    return entries


@app.get("/macros/{entry_date}", response_model=schemas.MacroEntry, tags=["Macros"])
def get_macro_entry(
    entry_date: date,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get macro entry for a specific date (format: YYYY-MM-DD).
    """
    db_entry = db.query(models.MacroEntry).filter(
        models.MacroEntry.date == entry_date
    ).first()

    if db_entry is None:
        raise HTTPException(status_code=404, detail="Entry not found for this date")

    return db_entry


@app.patch("/macros/{entry_date}", response_model=schemas.MacroEntry, tags=["Macros"])
def update_macro_entry(
    entry_date: date,
    entry_update: schemas.MacroEntryUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Partially update a macro entry for a specific date.
    Only provided fields will be updated.
    """
    db_entry = db.query(models.MacroEntry).filter(
        models.MacroEntry.date == entry_date
    ).first()

    if db_entry is None:
        raise HTTPException(status_code=404, detail="Entry not found for this date")

    update_data = entry_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_entry, field, value)

    db.commit()
    db.refresh(db_entry)
    return db_entry


@app.put("/macros/{entry_date}/add", response_model=schemas.MacroEntry, tags=["Macros"])
def add_to_macro_entry(
    entry_date: date,
    entry_update: schemas.MacroEntryUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Add values to an existing macro entry (incremental update).
    Creates entry with provided values if it doesn't exist.
    """
    db_entry = db.query(models.MacroEntry).filter(
        models.MacroEntry.date == entry_date
    ).first()

    if db_entry is None:
        # Create new entry
        db_entry = models.MacroEntry(
            date=entry_date,
            protein=entry_update.protein or 0.0,
            carbs=entry_update.carbs or 0.0,
            fat=entry_update.fat or 0.0
        )
        db.add(db_entry)
    else:
        # Add to existing values
        if entry_update.protein is not None:
            db_entry.protein += entry_update.protein
        if entry_update.carbs is not None:
            db_entry.carbs += entry_update.carbs
        if entry_update.fat is not None:
            db_entry.fat += entry_update.fat

    db.commit()
    db.refresh(db_entry)
    return db_entry


@app.delete("/macros/{entry_date}", tags=["Macros"])
def delete_macro_entry(
    entry_date: date,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Delete a macro entry for a specific date.
    """
    db_entry = db.query(models.MacroEntry).filter(
        models.MacroEntry.date == entry_date
    ).first()

    if db_entry is None:
        raise HTTPException(status_code=404, detail="Entry not found for this date")

    db.delete(db_entry)
    db.commit()
    return {"message": f"Entry for {entry_date} deleted successfully"}


@app.get("/macros/{entry_date}/summary", tags=["Macros"])
def get_macro_summary(
    entry_date: date,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get macro entry with calculated totals (calories, etc.).
    """
    db_entry = db.query(models.MacroEntry).filter(
        models.MacroEntry.date == entry_date
    ).first()

    if db_entry is None:
        raise HTTPException(status_code=404, detail="Entry not found for this date")

    # Calculate calories: protein=4cal/g, carbs=4cal/g, fat=9cal/g
    total_calories = (db_entry.protein * 4) + (db_entry.carbs * 4) + (db_entry.fat * 9)

    return {
        "date": db_entry.date,
        "protein": db_entry.protein,
        "carbs": db_entry.carbs,
        "fat": db_entry.fat,
        "total_calories": round(total_calories, 1),
        "protein_calories": round(db_entry.protein * 4, 1),
        "carbs_calories": round(db_entry.carbs * 4, 1),
        "fat_calories": round(db_entry.fat * 9, 1)
    }
