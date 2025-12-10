from datetime import date, timedelta
from typing import Optional

from app.models.macro import (
    MacroTotals,
    MacroTargetStatus,
    SodiumTargetStatus,
    MacroTargets,
    MacroTodayResponse,
    MacroRemainingResponse,
    MacroRemaining,
    MacroRemainingItem,
    SodiumRemainingItem,
    MacroHistoryResponse,
    MacroHistoryDay,
    BodyDaySummary,
    BodyMeasurementSummary,
)
from app.services.profile_service import get_profile
from app.services.snapshot_service import compute_snapshot, get_or_create_snapshot
from app.services.body_service import get_measurements_range
from app.utils.timezone import current_date_in_timezone


async def get_today_macros(db_path: str | None = None) -> MacroTodayResponse:
    """Get today's macro totals with target percentages."""
    profile = await get_profile(db_path)
    today = current_date_in_timezone(profile.timezone)
    totals = await compute_snapshot(today, db_path)

    targets = MacroTargets(
        calories=MacroTargetStatus(
            min=profile.targets.calories_min,
            max=profile.targets.calories_max,
            current=totals.calories,
            percent_of_min=round(totals.calories / profile.targets.calories_min * 100, 1)
            if profile.targets.calories_min > 0
            else 0,
        ),
        protein_g=MacroTargetStatus(
            min=profile.targets.protein_min_g,
            max=profile.targets.protein_max_g,
            current=totals.protein_g,
            percent_of_min=round(totals.protein_g / profile.targets.protein_min_g * 100, 1)
            if profile.targets.protein_min_g > 0
            else 0,
        ),
        carbs_g=MacroTargetStatus(
            min=profile.targets.carbs_min_g,
            max=profile.targets.carbs_max_g,
            current=totals.carbs_g,
            percent_of_min=round(totals.carbs_g / profile.targets.carbs_min_g * 100, 1)
            if profile.targets.carbs_min_g > 0
            else 0,
        ),
        fats_g=MacroTargetStatus(
            min=profile.targets.fats_min_g,
            max=profile.targets.fats_max_g,
            current=totals.fats_g,
            percent_of_min=round(totals.fats_g / profile.targets.fats_min_g * 100, 1)
            if profile.targets.fats_min_g > 0
            else 0,
        ),
        sodium_mg=SodiumTargetStatus(
            max=profile.targets.sodium_max_mg,
            current=totals.sodium_mg,
            percent_of_max=round(totals.sodium_mg / profile.targets.sodium_max_mg * 100, 1)
            if profile.targets.sodium_max_mg > 0
            else 0,
        ),
    )

    return MacroTodayResponse(
        date=today,
        totals=totals,
        targets=targets,
    )


async def get_remaining_macros(db_path: str | None = None) -> MacroRemainingResponse:
    """Get remaining macro budget for today."""
    profile = await get_profile(db_path)
    today = current_date_in_timezone(profile.timezone)
    totals = await compute_snapshot(today, db_path)

    def calc_remaining(current: float, min_target: int, max_target: int) -> MacroRemainingItem:
        remaining_min = max(0, min_target - current)
        remaining_max = max(0, max_target - current)
        note = None
        if remaining_min == 0 and current >= min_target:
            note = "minimum already met"
        return MacroRemainingItem(min=round(remaining_min, 1), max=round(remaining_max, 1), note=note)

    remaining = MacroRemaining(
        calories=calc_remaining(totals.calories, profile.targets.calories_min, profile.targets.calories_max),
        protein_g=calc_remaining(totals.protein_g, profile.targets.protein_min_g, profile.targets.protein_max_g),
        carbs_g=calc_remaining(totals.carbs_g, profile.targets.carbs_min_g, profile.targets.carbs_max_g),
        fats_g=calc_remaining(totals.fats_g, profile.targets.fats_min_g, profile.targets.fats_max_g),
        sodium_mg=SodiumRemainingItem(max=max(0, profile.targets.sodium_max_mg - totals.sodium_mg)),
    )

    suggestion = None
    protein_remaining = remaining.protein_g.min or 0
    if protein_remaining > 20:
        suggestion = f"You need at least {protein_remaining}g more protein. Consider a high-protein option."

    return MacroRemainingResponse(
        date=today,
        remaining=remaining,
        suggestion=suggestion,
    )


async def get_macro_history(
    start_date: date,
    end_date: date,
    limit: int = 100,
    offset: int = 0,
    timezone: str | None = None,
    db_path: str | None = None,
) -> MacroHistoryResponse:
    """Get macro and body measurement history for a date range with pagination."""
    # Calculate total days in range
    total_days = (end_date - start_date).days + 1

    # Get body measurements for the full range
    body_measurements = await get_measurements_range(start_date, end_date, limit=1000, offset=0, timezone=timezone, db_path=db_path)

    body_by_date: dict[date, list] = {}
    for m in body_measurements:
        if m.date not in body_by_date:
            body_by_date[m.date] = []
        body_by_date[m.date].append(m)

    # Generate all days in range, then apply pagination
    all_days = []
    current = end_date
    while current >= start_date:
        all_days.append(current)
        current -= timedelta(days=1)

    # Apply pagination to the days list
    paginated_days = all_days[offset:offset + limit]

    history_days = []
    for day in paginated_days:
        macros = await get_or_create_snapshot(day, db_path)

        body_summary = None
        if day in body_by_date:
            measurements = body_by_date[day]
            first = measurements[0]
            body_summary = BodyDaySummary(
                weight_lbs=first.weight_lbs,
                waist_cm=first.waist_cm,
                measurements=[
                    BodyMeasurementSummary(
                        time=m.time,
                        weight_lbs=m.weight_lbs,
                        waist_cm=m.waist_cm,
                    )
                    for m in measurements
                ],
            )

        history_days.append(
            MacroHistoryDay(
                date=day,
                macros=macros,
                body=body_summary,
            )
        )

    return MacroHistoryResponse(
        days=history_days,
        start_date=start_date,
        end_date=end_date,
        total_days=total_days,
        limit=limit,
        offset=offset,
    )
