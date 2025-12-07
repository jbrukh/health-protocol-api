from datetime import date as date_type, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import verify_token
from app.models.blood_pressure import (
    BloodPressureResponse,
    BloodPressureListResponse,
    BloodPressureSummaryResponse,
)
from app.services import blood_pressure_service

router = APIRouter()


@router.get("", response_model=BloodPressureListResponse)
async def get_readings(
    start_date: Optional[date_type] = Query(None, description="Start date (YYYY-MM-DD), defaults to 30 days ago"),
    end_date: Optional[date_type] = Query(None, description="End date (YYYY-MM-DD), defaults to today"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    _: str = Depends(verify_token),
):
    """Get blood pressure readings for a date range with pagination. Defaults to last 30 days."""
    if end_date is None:
        end_date = date_type.today()
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    readings = await blood_pressure_service.get_readings_range(start_date, end_date, limit, offset)
    return BloodPressureListResponse(
        readings=readings,
        total_in_range=len(readings),
        limit=limit,
        offset=offset,
    )


@router.get("/summary", response_model=BloodPressureSummaryResponse)
async def get_summary(_: str = Depends(verify_token)):
    """Get summary of all blood pressure readings (earliest date, latest date, total count)."""
    summary = await blood_pressure_service.get_summary()
    return BloodPressureSummaryResponse(**summary)


@router.get("/latest", response_model=BloodPressureResponse | None)
async def get_latest(_: str = Depends(verify_token)):
    """Get the most recent blood pressure reading."""
    reading = await blood_pressure_service.get_latest()
    if reading is None:
        raise HTTPException(status_code=404, detail="No blood pressure readings found")
    return reading
