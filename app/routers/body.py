from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.auth import verify_token
from app.models.body import (
    BodyMeasurementCreate,
    BodyMeasurementResponse,
    BodyMeasurementUpdate,
    BodyMeasurementListResponse,
    BodyMeasurementSummaryResponse,
)
from app.services import body_service
from app.services.profile_service import get_profile
from app.utils.timezone import current_date_in_timezone

router = APIRouter()


@router.post("", response_model=BodyMeasurementResponse, status_code=201)
async def create_measurement(
    data: BodyMeasurementCreate,
    _: str = Depends(verify_token),
) -> BodyMeasurementResponse:
    """Log a body measurement."""
    return await body_service.create_measurement(data)


@router.get("", response_model=BodyMeasurementListResponse)
async def get_measurements(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD), defaults to 30 days ago"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD), defaults to today"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    _: str = Depends(verify_token),
) -> BodyMeasurementListResponse:
    """Get body measurements for a date range with pagination. Defaults to last 30 days."""
    profile = await get_profile()
    if end_date is None:
        end_date = current_date_in_timezone(profile.timezone)
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    measurements = await body_service.get_measurements_range(
        start_date, end_date, limit, offset, timezone=profile.timezone
    )
    return BodyMeasurementListResponse(
        measurements=measurements,
        total_in_range=len(measurements),
        limit=limit,
        offset=offset,
    )


@router.get("/summary", response_model=BodyMeasurementSummaryResponse)
async def get_summary(
    _: str = Depends(verify_token),
) -> BodyMeasurementSummaryResponse:
    """Get summary of all body measurements (earliest date, latest date, total count)."""
    summary = await body_service.get_summary()
    return BodyMeasurementSummaryResponse(**summary)


@router.get("/latest", response_model=Optional[BodyMeasurementResponse])
async def get_latest_measurement(
    _: str = Depends(verify_token),
) -> Optional[BodyMeasurementResponse]:
    """Get the most recent body measurement."""
    profile = await get_profile()
    return await body_service.get_latest_measurement(timezone=profile.timezone)


@router.get("/{measurement_id}", response_model=BodyMeasurementResponse)
async def get_measurement(
    measurement_id: int,
    _: str = Depends(verify_token),
) -> BodyMeasurementResponse:
    """Get a body measurement by ID."""
    profile = await get_profile()
    return await body_service.get_measurement(measurement_id, timezone=profile.timezone)


@router.put("/{measurement_id}", response_model=BodyMeasurementResponse)
async def update_measurement(
    measurement_id: int,
    data: BodyMeasurementUpdate,
    _: str = Depends(verify_token),
) -> BodyMeasurementResponse:
    """Update a body measurement."""
    return await body_service.update_measurement(measurement_id, data)


@router.delete("/{measurement_id}", status_code=204)
async def delete_measurement(
    measurement_id: int,
    _: str = Depends(verify_token),
) -> None:
    """Delete a body measurement."""
    await body_service.delete_measurement(measurement_id)
