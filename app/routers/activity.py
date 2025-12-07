from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import verify_token
from app.models.activity import DailyActivityResponse
from app.services import activity_service

router = APIRouter()


@router.get("", response_model=DailyActivityResponse | None)
async def get_activity(date: date_type = Query(None), _: str = Depends(verify_token)):
    """Get activity for a date."""
    if date is None:
        date = date_type.today()

    activity = await activity_service.get_activity(date)
    if activity is None:
        raise HTTPException(status_code=404, detail=f"No activity found for {date}")
    return activity


@router.get("/latest", response_model=DailyActivityResponse | None)
async def get_latest(_: str = Depends(verify_token)):
    """Get the most recent activity record."""
    activity = await activity_service.get_latest()
    if activity is None:
        raise HTTPException(status_code=404, detail="No activity records found")
    return activity
