from typing import List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import verify_api_key
from app.database import get_db
from app.models import DailyLog, FoodEntry, Ingredient
from app.schemas import (
    FoodEntryCreate,
    FoodEntryUpdate,
    FoodEntryResponse,
    DailySummary,
    CalorieHistoryEntry,
)
from app.services.nutrition import calculate_entry_nutrition

router = APIRouter(prefix="/food", tags=["Food Tracking"])


async def get_or_create_daily_log(db: AsyncSession, log_date: date) -> DailyLog:
    """Get or create a daily log for the given date."""
    result = await db.execute(
        select(DailyLog).where(DailyLog.date == log_date)
    )
    daily_log = result.scalar_one_or_none()
    if not daily_log:
        daily_log = DailyLog(date=log_date)
        db.add(daily_log)
        await db.flush()
    return daily_log


@router.post("", response_model=FoodEntryResponse, status_code=status.HTTP_201_CREATED)
async def log_food(
    data: FoodEntryCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Log a food entry with ingredients."""
    daily_log = await get_or_create_daily_log(db, data.date)

    # Calculate nutrition from ingredient if provided
    nutrition = {}
    ingredient = None
    if data.ingredient_id:
        result = await db.execute(
            select(Ingredient).where(Ingredient.id == data.ingredient_id)
        )
        ingredient = result.scalar_one_or_none()
        if not ingredient:
            raise HTTPException(status_code=404, detail="Ingredient not found")
        nutrition = calculate_entry_nutrition(ingredient, data.quantity, data.unit)
    else:
        # Use manually provided values or defaults
        nutrition = {
            "protein_g": data.protein_g or 0,
            "carbs_g": data.carbs_g or 0,
            "fat_g": data.fat_g or 0,
            "sodium_mg": data.sodium_mg or 0,
            "calories": data.calories or 0,
        }

    entry = FoodEntry(
        daily_log_id=daily_log.id,
        ingredient_id=data.ingredient_id,
        quantity=data.quantity,
        unit=data.unit,
        meal_label=data.meal_label,
        description=data.description,
        **nutrition,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)

    # Load ingredient for response
    if entry.ingredient_id:
        result = await db.execute(
            select(FoodEntry)
            .options(selectinload(FoodEntry.ingredient))
            .where(FoodEntry.id == entry.id)
        )
        entry = result.scalar_one()

    return entry


@router.get("", response_model=List[FoodEntryResponse])
async def get_food_entries(
    date: date = Query(..., description="Date to get entries for (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get all food entries for a date."""
    result = await db.execute(
        select(FoodEntry)
        .join(DailyLog)
        .options(selectinload(FoodEntry.ingredient))
        .where(DailyLog.date == date)
        .order_by(FoodEntry.created_at)
    )
    return result.scalars().all()


@router.get("/summary", response_model=DailySummary)
async def get_daily_summary(
    date: date = Query(..., description="Date to get summary for (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get daily macro/calorie summary."""
    result = await db.execute(
        select(
            func.coalesce(func.sum(FoodEntry.protein_g), 0).label("total_protein_g"),
            func.coalesce(func.sum(FoodEntry.carbs_g), 0).label("total_carbs_g"),
            func.coalesce(func.sum(FoodEntry.fat_g), 0).label("total_fat_g"),
            func.coalesce(func.sum(FoodEntry.sodium_mg), 0).label("total_sodium_mg"),
            func.coalesce(func.sum(FoodEntry.calories), 0).label("total_calories"),
            func.count(FoodEntry.id).label("entry_count"),
        )
        .join(DailyLog)
        .where(DailyLog.date == date)
    )
    row = result.one()
    return DailySummary(
        date=date,
        total_protein_g=round(row.total_protein_g, 2),
        total_carbs_g=round(row.total_carbs_g, 2),
        total_fat_g=round(row.total_fat_g, 2),
        total_sodium_mg=round(row.total_sodium_mg, 2),
        total_calories=round(row.total_calories, 2),
        entry_count=row.entry_count,
    )


@router.get("/history", response_model=List[CalorieHistoryEntry])
async def get_calorie_history(
    start: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end: date = Query(..., description="End date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get calorie history for a date range."""
    result = await db.execute(
        select(
            DailyLog.date,
            func.coalesce(func.sum(FoodEntry.calories), 0).label("total_calories"),
            func.coalesce(func.sum(FoodEntry.protein_g), 0).label("total_protein_g"),
            func.coalesce(func.sum(FoodEntry.carbs_g), 0).label("total_carbs_g"),
            func.coalesce(func.sum(FoodEntry.fat_g), 0).label("total_fat_g"),
            func.coalesce(func.sum(FoodEntry.sodium_mg), 0).label("total_sodium_mg"),
        )
        .join(FoodEntry, isouter=True)
        .where(DailyLog.date >= start, DailyLog.date <= end)
        .group_by(DailyLog.date)
        .order_by(DailyLog.date)
    )
    return [
        CalorieHistoryEntry(
            date=row.date,
            total_calories=round(row.total_calories, 2),
            total_protein_g=round(row.total_protein_g, 2),
            total_carbs_g=round(row.total_carbs_g, 2),
            total_fat_g=round(row.total_fat_g, 2),
            total_sodium_mg=round(row.total_sodium_mg, 2),
        )
        for row in result
    ]


@router.patch("/{entry_id}", response_model=FoodEntryResponse)
async def update_food_entry(
    entry_id: int,
    data: FoodEntryUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update a food entry."""
    result = await db.execute(
        select(FoodEntry)
        .options(selectinload(FoodEntry.ingredient))
        .where(FoodEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Food entry not found")

    update_data = data.model_dump(exclude_unset=True)

    # If quantity or unit changed and we have an ingredient, recalculate nutrition
    if ("quantity" in update_data or "unit" in update_data) and entry.ingredient:
        new_quantity = update_data.get("quantity", entry.quantity)
        new_unit = update_data.get("unit", entry.unit)
        nutrition = calculate_entry_nutrition(entry.ingredient, new_quantity, new_unit)
        update_data.update(nutrition)

    for key, value in update_data.items():
        setattr(entry, key, value)

    await db.flush()
    await db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_food_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Delete a food entry."""
    result = await db.execute(
        select(FoodEntry).where(FoodEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Food entry not found")

    await db.delete(entry)
