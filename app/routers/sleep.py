from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import verify_token
from app.models.sleep import SleepResponse
from app.services import sleep_service

router = APIRouter()


@router.get("", response_model=SleepResponse | None)
async def get_sleep(date: date_type = Query(None), _: str = Depends(verify_token)):
    """Get sleep data for a date."""
    if date is None:
        date = date_type.today()

    sleep = await sleep_service.get_sleep(date)
    if sleep is None:
        raise HTTPException(status_code=404, detail=f"No sleep data found for {date}")
    return sleep


@router.get("/latest", response_model=SleepResponse | None)
async def get_latest(_: str = Depends(verify_token)):
    """Get the most recent sleep record."""
    sleep = await sleep_service.get_latest()
    if sleep is None:
        raise HTTPException(status_code=404, detail="No sleep records found")
    return sleep
