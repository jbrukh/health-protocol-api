from datetime import date as date_type, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import verify_token
from app.models.activity import (
    DailyActivityResponse,
    DailyActivityListResponse,
    DailyActivitySummaryResponse,
)
from app.services import activity_service
from app.services.profile_service import get_profile
from app.utils.timezone import current_date_in_timezone

router = APIRouter()


@router.get("", response_model=DailyActivityListResponse)
async def get_activity(
    start_date: Optional[date_type] = Query(None, description="Start date (YYYY-MM-DD), defaults to 30 days ago"),
    end_date: Optional[date_type] = Query(None, description="End date (YYYY-MM-DD), defaults to today"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    _: str = Depends(verify_token),
):
    """Get daily activity for a date range with pagination. Defaults to last 30 days."""
    profile = await get_profile()
    if end_date is None:
        end_date = current_date_in_timezone(profile.timezone)
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    activities = await activity_service.get_activity_range(start_date, end_date, limit, offset)
    return DailyActivityListResponse(
        activities=activities,
        total_in_range=len(activities),
        limit=limit,
        offset=offset,
    )


@router.get("/summary", response_model=DailyActivitySummaryResponse)
async def get_summary(_: str = Depends(verify_token)):
    """Get summary of all daily activity (earliest date, latest date, total count)."""
    summary = await activity_service.get_summary()
    return DailyActivitySummaryResponse(**summary)


@router.get("/latest", response_model=DailyActivityResponse | None)
async def get_latest(_: str = Depends(verify_token)):
    """Get the most recent activity record."""
    activity = await activity_service.get_latest()
    if activity is None:
        raise HTTPException(status_code=404, detail="No activity records found")
    return activity
