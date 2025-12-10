from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import verify_token
from app.models.sleep import SleepResponse
from app.services import sleep_service
from app.services.profile_service import get_profile
from app.utils.timezone import current_date_in_timezone

router = APIRouter()


@router.get("", response_model=SleepResponse | None)
async def get_sleep(date: date_type = Query(None), _: str = Depends(verify_token)):
    """Get sleep data for a date."""
    profile = await get_profile()
    if date is None:
        date = current_date_in_timezone(profile.timezone)

    sleep = await sleep_service.get_sleep(date, timezone=profile.timezone)
    if sleep is None:
        raise HTTPException(status_code=404, detail=f"No sleep data found for {date}")
    return sleep


@router.get("/latest", response_model=SleepResponse | None)
async def get_latest(_: str = Depends(verify_token)):
    """Get the most recent sleep record."""
    profile = await get_profile()
    sleep = await sleep_service.get_latest(timezone=profile.timezone)
    if sleep is None:
        raise HTTPException(status_code=404, detail="No sleep records found")
    return sleep
