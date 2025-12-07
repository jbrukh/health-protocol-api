from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import verify_token
from app.models.blood_pressure import BloodPressureResponse, BloodPressureListResponse
from app.services import blood_pressure_service

router = APIRouter()


@router.get("", response_model=BloodPressureListResponse)
async def get_readings(date: date_type = Query(None), _: str = Depends(verify_token)):
    """Get blood pressure readings for a date."""
    if date is None:
        date = date_type.today()

    readings = await blood_pressure_service.get_readings(date)
    return BloodPressureListResponse(readings=readings)


@router.get("/latest", response_model=BloodPressureResponse | None)
async def get_latest(_: str = Depends(verify_token)):
    """Get the most recent blood pressure reading."""
    reading = await blood_pressure_service.get_latest()
    if reading is None:
        raise HTTPException(status_code=404, detail="No blood pressure readings found")
    return reading
