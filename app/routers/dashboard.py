from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import verify_api_key
from app.database import get_db
from app.models import DailyLog, FoodEntry, Exercise, Target
from app.schemas import DailySummary, DashboardResponse
from app.schemas.dashboard import TargetProgress

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_date: Optional[date] = Query(None, alias="date", description="Date for dashboard (defaults to today)"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get daily overview including food, exercise, and progress vs targets."""
    if dashboard_date is None:
        dashboard_date = date.today()

    # Get food entries
    food_result = await db.execute(
        select(FoodEntry)
        .join(DailyLog)
        .options(selectinload(FoodEntry.ingredient))
        .where(DailyLog.date == dashboard_date)
        .order_by(FoodEntry.created_at)
    )
    food_entries = food_result.scalars().all()

    # Calculate food summary
    summary_result = await db.execute(
        select(
            func.coalesce(func.sum(FoodEntry.protein_g), 0).label("total_protein_g"),
            func.coalesce(func.sum(FoodEntry.carbs_g), 0).label("total_carbs_g"),
            func.coalesce(func.sum(FoodEntry.fat_g), 0).label("total_fat_g"),
            func.coalesce(func.sum(FoodEntry.sodium_mg), 0).label("total_sodium_mg"),
            func.coalesce(func.sum(FoodEntry.calories), 0).label("total_calories"),
            func.count(FoodEntry.id).label("entry_count"),
        )
        .join(DailyLog)
        .where(DailyLog.date == dashboard_date)
    )
    summary_row = summary_result.one()
    food_summary = DailySummary(
        date=dashboard_date,
        total_protein_g=round(summary_row.total_protein_g, 2),
        total_carbs_g=round(summary_row.total_carbs_g, 2),
        total_fat_g=round(summary_row.total_fat_g, 2),
        total_sodium_mg=round(summary_row.total_sodium_mg, 2),
        total_calories=round(summary_row.total_calories, 2),
        entry_count=summary_row.entry_count,
    )

    # Get exercises
    exercise_result = await db.execute(
        select(Exercise)
        .where(Exercise.date == dashboard_date)
        .order_by(Exercise.created_at)
    )
    exercises = exercise_result.scalars().all()

    # Get current targets and calculate progress
    subquery = (
        select(Target.name, func.max(Target.effective_from).label("max_date"))
        .where(Target.effective_from <= dashboard_date)
        .group_by(Target.name)
        .subquery()
    )

    target_result = await db.execute(
        select(Target)
        .join(
            subquery,
            (Target.name == subquery.c.name)
            & (Target.effective_from == subquery.c.max_date),
        )
    )
    targets = target_result.scalars().all()

    # Map nutrition summary to target names
    current_values = {
        "calories": food_summary.total_calories,
        "protein_g": food_summary.total_protein_g,
        "carbs_g": food_summary.total_carbs_g,
        "fat_g": food_summary.total_fat_g,
        "sodium_mg": food_summary.total_sodium_mg,
    }

    target_progress: List[TargetProgress] = []
    for target in targets:
        current = current_values.get(target.name, 0)
        remaining = max(0, target.value - current)
        percent = (current / target.value * 100) if target.value > 0 else 0

        target_progress.append(
            TargetProgress(
                target=target,
                current_value=round(current, 2),
                remaining=round(remaining, 2),
                percent_complete=round(percent, 1),
            )
        )

    return DashboardResponse(
        date=dashboard_date,
        food_summary=food_summary,
        food_entries=food_entries,
        exercises=exercises,
        target_progress=target_progress,
    )
